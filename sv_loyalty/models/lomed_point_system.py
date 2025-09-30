# -*- coding: utf-8 -*-
##############################################################################
#
#    Odoo
#
##############################################################################
import base64
import time
from datetime import datetime,date
import calendar
from odoo import api, fields, models,_
from odoo.exceptions import UserError,ValidationError
import logging
_logger = logging.getLogger(__name__)

class LoyaltyPlanPointsSystem(models.Model):
    _name = 'loyalty.plan.point_system'
    _description = 'Configuraciones del sistema de puntos'

    name = fields.Char("Configuración")
    product_ids = fields.Many2many(comodel_name='product.template',
                                   relation="lp_point_system_required_ids",
                                   colum1="ps_config_id",
                                   colum2="product_req_id",
                                   string="Productos objetivo",
                                   domain="[('categ_id.available_in_plan','=',True),('sale_ok','=',True)]")
    amount = fields.Float("Monto")
    points = fields.Integer("Puntos que otorga")
    enablers = fields.Many2many(comodel_name='product.template',
                                elation="lp_point_system_enabler_ids",
                                   colum1="ps_config_id",
                                   colum2="product_enab_id",
                                   string="Habilitadores",
                                   domain="[('categ_id.available_in_plan','=',True),('sale_ok','=',True)]")
    plan_id = fields.Many2one(comodel_name='loyalty.plan',string="Plan relacionado")
    mode = fields.Selection(string="Método de acumulación",related='plan_id.mode')

    @api.model
    def create(self,vals):
        config_line = super(LoyaltyPlanPointsSystem,self).create(vals)
        config_line.name = f"config-line-{str(config_line.id).zfill(6)}"
        return config_line

class LoyaltyPlanResumeWizard(models.TransientModel):
    _name = 'loyalty.plan.resume_wizard'
    _description = 'Calculo de puntos'

    name = fields.Char("Cálculo")
    partner_id = fields.Many2one(comodel_name='res.partner',string="Cliente/Asesor")
    
    def _get_current_month(self):
        return str(date.today().month)
    
    def _get_current_year(self):
        return date.today().year
    
    month = fields.Selection([
        ('1','Enero'),('2','Febrero'),('3','Marzo'),
        ('4','Abril'),('5','Mayo'),('6','Junio'),
        ('7','Julio'),('8','Agosto'),('9','Septiembre'),
        ('10','Octubre'),('11','Noviembre'),('12','Diciembre'),
    ],default=_get_current_month,string="Mes")
    year = fields.Integer(string="Año",default=_get_current_year)
    order_ids = fields.Many2many(comodel_name='sale.order',string="Ordenes consideradas")
    points_result = fields.Html("Resultado",compute='_compute_output_field')
    points_earned = fields.Integer("Puntos ganados")
    points_pending = fields.Integer("Puntos a confirmar")
    total_points = fields.Integer("Puntos totales")

    def action_get_points(self):
        self.ensure_one()
        res = 0
        plan = self.get_plan()
        if not plan:
            raise ValidationError("El contacto no pertenece a ningun plan de fidelización")
        if not plan.use_points:
            raise UserError(f"El plan de fidelización no tiene habilitado el sistema de puntos")
        res = self.compute_points(plan.mode)
        self.points_earned = res[0]
        self.points_pending = res[1]
        self.total_points = sum(res)
        self.name= "LPR/"+str(self.id).zfill(6)
        return{
            'name':_('Puntos acumulados'),
            'type': 'ir.actions.act_window',
            'view_mode':'form',
            'res_model':'loyalty.plan.resume_wizard',
            'target':'new',
            'res_id':self.id,
        }
    
    def get_order_list(self):
        self.ensure_one()
        last_day = calendar.monthrange(self.year,int(self.month))[1]
        date_start = datetime(self.year,int(self.month),1,0,0,0)
        date_end = datetime(self.year,int(self.month),last_day,23,59,59)
        domain = [
            ('state','in',('sale','done')),
            ('advisor_id','=',self.partner_id.id),
            ('date_order','>=',date_start),
            ('date_order','<=',date_end)
            ]
        order = self.env['sale.order'].search(domain)
        if order:
            return order
        else:
            return False
    
    def compute_points(self,mode='none'):
        orders = self.get_order_list()
        plan = self.get_plan()
        earned = 0
        pending = 0
        if orders:
            self.order_ids = [(5,0,0)]
            for o in orders:
                product_ids = o.order_line.mapped('product_template_id.id')
                if plan and plan.config_line_ids:
                    for config_line in plan.config_line_ids:
                        has_required = bool(set(config_line.product_ids.ids) & set(product_ids))
                        has_mandatory = bool(set(config_line.enablers.ids) & set(product_ids))
                        if has_required and has_mandatory:
                            self.order_ids = [(4,o.id)]
                            if mode == 'point_pd':
                                if o.invoice_status == 'invoiced':
                                    earned += int(o.amount_untaxed)
                                elif o.invoice_status != 'invoiced':
                                    pending += int(o.amount_untaxed)
                            elif mode == 'point_pa':
                                if o.invoice_status == 'invoiced':
                                    earned += (int(o.amount_untaxed)/config_line.amount)*config_line.points
                                elif o.invoice_status != 'invoiced':
                                    pending += (int(o.amount_untaxed)/config_line.amount)*config_line.points
                            elif mode == 'point_pp':
                                if o.invoice_status == 'invoiced':
                                    earned += config_line.points
                                elif o.invoice_status != 'invoiced':
                                    pending += config_line.points
                            elif mode == 'point_po':
                                if o.invoice_status == 'invoiced':
                                    earned += 1
                                elif o.invoice_status != 'invoiced':
                                    pending += 1
                            break
        return [earned,pending]

    def get_plan(self):
        self.ensure_one()
        return self.partner_id.plan_id
    
    @api.depends('points_earned','points_pending','total_points')
    def _compute_output_field(self):
        for record in self:
            record.points_result = f"""
            <div style="font-size:14px;line-height:1.6;font-family:Roboto;padding:10px 10px 10px 10px;border-radius:10px;width:50%;border:1px solid #ccc" class="card">
                <img src="web/image/res.company/1/logo" style="position:absolute;opacity:0.3;width:50%;margin-left:25%"/>
                <div style="width:100%;text-align:center;"><h1 style="color:#1d195c;">Resumen de puntos calculados</h1></div>
                <div style="width:100%;text-align:center;"><h3 style="color:#1d195c;">{record.partner_id.name}</h3></div>
                <p style="color:#1d195c;font-family:Roboto;"><b>Puntos ganados:</b> <span style="font-size:20px">{record.points_earned}</span></p>
                <p style="color:#1d195c;font-family:Roboto;"><b>Puntos sin confirmar:</b> <span style="font-size:20px">{record.points_pending}</span></p>
                <p style="color:#1d195c;font-family:Roboto;"><b>Puntos totales:</b> <span style="font-size:20px">{record.total_points}</span></p>
            </div>
                """
    
    def print_point_report(self):
        self.ensure_one()
        return self.env.ref('sv_loyalty.point_system_report').report_action(self)