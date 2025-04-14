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

class sv_product_product(models.Model):
    _inherit = ['product.template']

    type_optic = fields.Selection([
        ('product','Producto regular'),
        ('accesories','Accesorio Incluido'),
        ('ar_component','Componente AR')
    ],default='product',string="Confuguración opticas")

class sv_product_product(models.Model):
    _inherit = ['product.product']

    type_optic = fields.Selection(string="Confuguración opticas",related='product_tmpl_id.type_optic')

class sv_sale_order(models.Model):
    _inherit = ['sale.order']

    appointment_ids = fields.One2many(string="Examenes visuales",comodel_name='op.appointment',inverse_name='order_id')
    appointment_count = fields.Integer(string="Total examenes",compute='_compute_apponintment_count')

    @api.depends('appointment_ids')
    def _compute_apponintment_count(self):
        for r in self:
            res = 0
            if r.appointment_ids:
                res = len(r.appointment_ids)
            r.appointment_count = res
    
    def get_oppointment_list(self):
        self.ensure_one()
        return{
            'type':'ir.actions.act_window'
            ,'name':'Examenes visuales'
            ,'view_mode':'tree,form'
            ,'res_model':'op.appointment'
            ,'domain':[('order_id','=',self.id)]
            ,'context':"{'create':False}"
        }