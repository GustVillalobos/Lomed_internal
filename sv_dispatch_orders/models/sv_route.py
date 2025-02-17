# -*- coding: utf-8 -*-
##############################################################################
#
#    Odoo
#
##############################################################################
import logging
import time
from datetime import datetime,timedelta
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models,_
from odoo.exceptions import ValidationError,UserError
_logger = logging.getLogger(__name__)

class sv_route(models.Model):
    _name='sv.route'
    _inherit=['mail.thread']
    _description='Rutas programadas'

    name = fields.Char("Nombre",copy=False)
    code = fields.Char("Código",copy=False)
    employee_id = fields.Many2one(comodel_name='hr.employee',string="Mensajero preferido",copy=False)
    route_dispatch_ids = fields.One2many(comodel_name='sv.route.dispatch',inverse_name='route_id',string="Todas las rutas asociadas")
    route_dispatch_count = fields.Integer("Rutas totales",copy=False,store=False,compute='compute_total_routes')
    active_routes = fields.Integer("Rutas activas",copy=False,store=False,compute='compute_active_routes')
    tour_date = fields.Date(string="Último recorrido",copy=False,store=True,compute='compute_tour_date')
    active = fields.Boolean("Activo",default=True)
    department_id = fields.Integer("Departamento",compute='compute_department_id')

    @api.depends('route_dispatch_ids')
    def compute_total_routes(self):
        for r in self:
            r.route_dispatch_count = len(r.route_dispatch_ids)

    @api.depends('route_dispatch_ids')
    def compute_active_routes(self):
        for r in self:
            active_routes = r.route_dispatch_ids.filtered(lambda r: r.state in ('confirm','progress'))
            if active_routes:
                r.active_routes = len(active_routes)
            else:
                r.active_routes = 0

    @api.depends('route_dispatch_ids')
    def compute_tour_date(self):
        for r in self:
            last_record = False
            if len(r.route_dispatch_ids)>=1:
                last_record = r.route_dispatch_ids[-1]
            if last_record:
                r.tour_date = last_record.dispatch_date
            else:
                r.tour_date = False
        
    def get_active_route_list(self):
        self.ensure_one()
        return{
            'type':'ir.actions.act_window'
            ,'name':'Despachos activos'
            ,'view_mode':'tree,form'
            ,'res_model':'sv.route.dispatch'
            ,'domain':[('state','in',('confirm','progress')),('route_id','=',self.id)]
            ,'context':"{'create':False}"
        }
    
    def get_route_list(self):
        self.ensure_one()
        return{
            'type':'ir.actions.act_window'
            ,'name':'Todos los despachos'
            ,'view_mode':'tree,form'
            ,'res_model':'sv.route.dispatch'
            ,'domain':[('route_id','=',self.id)]
            ,'context':"{'create':False}"
        }
    
    def compute_department_id(self):
        for r in self:
            depart_param = r.env['ir.config_parameter'].sudo().get_param('sv_route.deapartment_ref_id')
            r.department_id = int(depart_param) if depart_param else 0
