# -*- coding: utf-8 -*-
##############################################################################
#
#    Odoo
#
##############################################################################
import base64
import time
from datetime import datetime,date
from collections import defaultdict
from odoo.tools import date_utils
from odoo import api, fields, models,_
from odoo.exceptions import UserError,ValidationError
import logging
_logger = logging.getLogger(__name__)

class SalesSummary(models.TransientModel):
    _name = 'sales.summary'
    _description = 'Resumen de ventas'

    name = fields.Char("Resumen")
    partner_ids = fields.Many2many('res.partner','res_partner_sales_summary_rel','summary_id','partner_id',string="Clientes")
    date_from = fields.Date("Desde")
    date_to = fields.Date("Hasta")
    summary_mode = fields.Selection([
        ('simple','Simple'),
        ('grouped','Agrupado por fecha'),
    ],default="simple",string="Modo de resumen")
    period = fields.Selection([
        ('month','Mes'),
        ('week','Semana'),
        ('quarter','Trimestre')
    ],default='month',string="Agrupar por")
    summary_line_ids = fields.One2many('sales.summary.line','summary_id',string="Resultados")

    def load_summary_data(self):
        self.ensure_one()
        self.summary_line_ids.unlink()

        SaleOrder = self.env['sale.order']
        domain = [('state', 'in', ['sale', 'done'])]

        if self.partner_ids:
            domain.append(('partner_id', 'in', self.partner_ids.ids))
        else:
            domain.append(('partner_id.user_id', '=', self.env.user.id))

        if self.date_from:
            domain.append(('date_order', '>=', self.date_from))
        if self.date_to:
            domain.append(('date_order', '<=', self.date_to))

        # Leer las ventas agrupadas por cliente
        sales = SaleOrder.search(domain)

        lines = []
        if self.summary_mode == 'simple':
            # == MODO SIMPLE ==
            grouped_data = sales.read_group(
                domain, ['partner_id', 'id:count'], ['partner_id']
            )
            for sale in grouped_data:
                partner = sale['partner_id'][0] if sale['partner_id'] else False
                order_count = sale['partner_id_count']

                order_ids = SaleOrder.search([('partner_id', '=', partner)]).ids
                OrderLine = self.env['sale.order.line']
                lines_data = OrderLine.read_group(
                    [('order_id', 'in', order_ids), ('product_id.categ_id.show_optic', '=', True)],
                    ['product_id', 'product_uom_qty:sum'],
                    ['product_id'],
                    limit=10,
                    orderby='product_uom_qty desc'
                )
                top_products = ''.join(
                    f"[{l['product_uom_qty']}] {l['product_id'][1]}\n"
                    for l in lines_data if l.get('product_id') and l.get('product_uom_qty') != 0
                )

                lines.append((0, 0, {
                    'partner_id': partner,
                    'order_count': order_count,
                    'top_products': top_products,
                    'period_label': 'General'
                }))

        else:
            # == MODO AGRUPADO ==
            grouped = defaultdict(list)

            for order in sales:
                period_label = self._get_period_label(order.date_order, self.period)
                grouped[period_label].append(order)

            for period_label, orders in grouped.items():
                orders_by_partner = defaultdict(list)
                for o in orders:
                    orders_by_partner[o.partner_id.id].append(o)

                for partner_id, partner_orders in orders_by_partner.items():
                    order_ids = [o.id for o in partner_orders]
                    order_count = len(order_ids)

                    OrderLine = self.env['sale.order.line']
                    lines_data = OrderLine.read_group(
                        [('order_id', 'in', order_ids), ('product_id.categ_id.show_optic', '=', True)],
                        ['product_id', 'product_uom_qty:sum'],
                        ['product_id'],
                        limit=10,
                        orderby='product_uom_qty desc'
                    )
                    top_products = ''.join(
                        f"[{l['product_uom_qty']}] {l['product_id'][1]}\n"
                        for l in lines_data if l.get('product_id') and l.get('product_uom_qty') != 0
                    )

                    lines.append((0, 0, {
                        'partner_id': partner_id,
                        'order_count': order_count,
                        'top_products': top_products,
                        'period_label': period_label
                    }))

        self.summary_line_ids = lines
        return {
            'name': _('Resumen de ventas'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'sales.summary',
            'target': 'new',
            'res_id': self.id,
        }

    def _get_period_label(self, date_value, period_type):
        if not date_value:
            return 'Sin fecha'

        if period_type == 'month':
            month_es = {'Jan':'Enero','Feb':'Febrero','Apr':'Abril','May':'Mayo',
                        'Jun':'Junio','Jul':'Julio','Aug':'Agosto','Sep':'Septiembre',
                        'Oct':'Octubre','Nov':'Noviembre','Mar':'Marzo','Dec':'Diciembre'}
            return f"{month_es.get(date_value.strftime('%b'))} - {date_value.strftime('%Y')}"
        elif period_type == 'week':
            year, week, _ = date_value.isocalendar()
            return f'{year}-W{week:02d}'
        elif period_type == 'quarter':
            quarter = (date_value.month - 1) // 3 + 1
            return f'{date_value.year}-Q{quarter}'
        return 'General'

    def action_print_summary(self):
        self.ensure_one()
        return self.env.ref('sales_summary_portal.report_sales_summary').report_action(self)

class SalesSummaryLine(models.TransientModel):
    _name='sales.summary.line'
    _description = 'Linea de resumen de venta'

    summary_id = fields.Many2one('sales.summary',string="Resumen")
    partner_id = fields.Many2one('res.partner',string="Cliente")
    period_label = fields.Char('Período')
    order_count = fields.Integer('Órdenes')
    top_products = fields.Text("Top 10 productos")