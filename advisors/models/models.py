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

class ResPartnerOpticalAdvisor(models.Model):
    _inherit = 'res.partner'

    is_advisor = fields.Boolean("Es asesor visual")
    
    def get_advisor_sales(self):
        self.ensure_one()
        return{
            'type':'ir.actions.act_window',
            'name':'Pedidos del asesor',
            'view_mode':'tree,form',
            'res_model':'sale.order',
            'domain':[('advisor_id','=',self.id),('state','in',('sale','done'))],
            'context':"{'create':False}"
        }


class SaleOrderOpticalAdvisor(models.Model):
    _inherit = 'sale.order'

    advisor_id = fields.Many2one(comodel_name='res.partner',string="Asesor óptico")

class AccountMoveOpticalAdvisor(models.Model):
    _inherit = 'account.move'

    advisor_name = fields.Char(string="Asesor óptico",compute='_compute_optical_advisor')

    @api.depends('invoice_origin')
    def _compute_optical_advisor(self):
        for r in self:
            order = False
            origin = r.invoice_origin if r.invoice_origin else False
            if origin and ',' in origin:
                origin = r.invoice_origin.split(', ')
                order = self.env['sale.order'].search([('name','=',origin[0])],limit = 1)
            elif origin and ',' not in origin:
                order = self.env['sale.order'].search([('name','=',origin)],limit = 1)
            r.advisor_name = order.advisor_id.name if order and order.advisor_id else False