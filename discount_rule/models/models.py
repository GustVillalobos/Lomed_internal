# -*- coding: utf-8 -*-
##############################################################################
#
#    Odoo
#
##############################################################################
import base64
import time
from datetime import datetime,date
from odoo import api, fields, models,_
from odoo.exceptions import UserError,ValidationError
import logging
_logger = logging.getLogger(__name__)

class ResPartnerDiscoutRules(models.Model):
    _inherit = 'res.partner'

    def action_show_rules(self):
        ctx = {
            "default_partner_id":self.id,
        }
        return{
            'type':'ir.actions.act_window'
            ,'name':'Reglas de descuento'
            ,'view_mode':'tree,form'
            ,'res_model':'partner.discount.rules'
            ,'domain':[('partner_id','=',self.id)]
            ,'context':ctx
        }

class SaleOrderLineDiscountRule(models.Model):
    _inherit = 'sale.order.line'

    is_auto_discount = fields.Boolean("Descuento automático")

    def _get_discount_from_rules(self):
        self.ensure_one()
        order = self.order_id
        partner = order.partner_id

        if not partner or not self.product_id:
            return 0.0
        
        eval_date = order.date_order.date() if order.date_order else date.today()

        rules = self.env['partner.discount.rules'].search([
            ('partner_id','=',partner.id),
            ('active','=',True),
            ('date_start','<=',eval_date),
            '|',
            ('date_end','=',False),
            ('date_end','>=',eval_date),
        ], order='priority desc')

        if not rules:
            return 0.0
        
        tmpl = self.product_id.product_tmpl_id
        category = self.product_id.categ_id

        for rule in rules:
            if rule.application_range == 'all':
                return rule.discount
            elif rule.application_range == 'product' and tmpl in rule.product_ids:
                return rule.discount
            elif rule.application_range == 'category' and category in rule.category_ids:
                return rule.discount

        return 0.0
    
    @api.model_create_multi
    def create(self,vals_list):
        lines = super().create(vals_list)
        for line in lines:
            discount = line._get_discount_from_rules()
            if discount > 0:
                line.discount = discount
                line.x_descuento = 'other'
                line.is_auto_discount = True
        return lines
    
    def write(self,vals):
        if self.env.context.get('skip_discount_rule'):
            return super().write(vals)
        SENSITIVE_FIELDS = {
            'product_id',
            'order_id',
        }

        if not SENSITIVE_FIELDS.intersection(vals.keys()):
            return super().write(vals)
        
        result = super().write(vals)

        for line in self:
            if line.discount and not line.is_auto_discount:
                continue
            discount = line._get_discount_from_rules()

            if discount > 0:
                line.discount = discount
                line.line.x_descuento = 'other'
                line.is_auto_discount = True
            elif line.is_auto_discount:
                line.discount = 0.0
                line.line.x_descuento = '0'
                line.is_auto_discount = False
        
        return result