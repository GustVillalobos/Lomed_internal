# -*- coding: utf-8 -*-
##############################################################################
#
#    Odoo
#
##############################################################################
import logging
import time
from datetime import datetime,timedelta
from dateutil import relativedelta
from odoo import api, fields, models,_
from odoo.exceptions import ValidationError
from odoo.exceptions import UserError
_logger = logging.getLogger(__name__)

class sv_type_sale_order(models.Model):
    _inherit = 'sale.order'
    type_order = fields.Selection([
        ('normal','Normal')
        ,('assembly','Montaje')
        ,('claim','Reclamo')
        ,('warranty','Garantia')
        ,('rectification','Rectificación')
        ,('courtesy','Cortesia')
        ,('other','Otros')],default="normal",copy=False,string="Tipo de trabajo")
    incidence_ids = fields.Many2many(comodel_name="sv.incidence",string="Incidencias",copy=False)
    incidence_note = fields.Text(string="Detalle",copy=False)

    def confirm_data(self):
        self.ensure_one()
        compose_form = self.env.ref('sv_type_sale_order.sv_confirmation_data_form',False)
        ctx = dict()
        return{
            'name':'Confirmación de datos escenciales'
            ,'type':'ir.actions.act_window'
            ,'view_type':'form'
            ,'view_mode':'form'
            ,'res_model':'sale.order'
            ,'res_id':self.id
            ,'target':'new'
            ,'view_id':compose_form.id
            ,'flags':{'action_buttons':False}
            ,'context':ctx
        }
    
class sv_order_incidence(models.Model):
    _name='sv.incidence'
    _description='Incidencias de orden venta'
    name = fields.Char("Incidencia")
    active = fields.Boolean(string="Activo",copy=False,default=True)

