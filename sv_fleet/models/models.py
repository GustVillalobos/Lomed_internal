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

class sv_fleet_model(models.Model):
    _inherit = 'fleet.vehicle.model'

    vehicle_type = fields.Selection(
        selection_add=[
            ('motorcicle','Moticicleta'),
            ],
            ondelete={'motorcicle':'set default'}
        )

class sv_flee_vehicle(models.Model):
    _inherit = 'fleet.vehicle'

    dispatch_ids = fields.One2many(comodel_name='sv.route.dispatch',inverse_name="vehicle_id",string="Despachos asociados")
    dispatch_count = fields.Integer("Total despachos",compute='compute_dispatch_count')
    dispatch_active = fields.Integer("Total depachos activos",compute='compute_active_dispatch')

    @api.depends('dispatch_ids')
    def compute_dispatch_count(self):
        for r in self:
            r.dispatch_count = len(r.dispatch_ids)

    @api.depends('dispatch_ids')
    def compute_active_dispatch(self):
        for r in self:
            res = 0
            active_list = r.dispatch_ids.filtered(lambda a: a.state in ('progress','confirm'))
            if active_list:
                res = len(active_list)
            r.dispatch_active = res
    
    def get_active_route_list(self):
        self.ensure_one()
        return{
            'type':'ir.actions.act_window'
            ,'name':'Despachos activos'
            ,'view_mode':'tree,kanban,form'
            ,'res_model':'sv.route.dispatch'
            ,'domain':[('state','in',('confirm','progress')),('vehicle_id','=',self.id)]
            ,'context':"{'create':False}"
        }
    
    def get_route_list(self):
        self.ensure_one()
        return{
            'type':'ir.actions.act_window'
            ,'name':'Todos los despachos'
            ,'view_mode':'tree,kanban,form'
            ,'res_model':'sv.route.dispatch'
            ,'domain':[('vehicle_id','=',self.id)]
            ,'context':"{'create':False}"
        }

    


