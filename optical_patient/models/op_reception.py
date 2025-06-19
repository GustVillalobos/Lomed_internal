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

class op_reception(models.Model):
    _name='op.reception'
    _inherit=['mail.thread','barcodes.barcode_events_mixin']
    _description='Sala de recepción'

    name = fields.Char("Nombre de sala")
    user_id = fields.Many2one(string="Usuario responsable",comodel_name='res.users',tracking=True)
    recepcionist_id = fields.Many2one(string="Asesor",comodel_name='hr.employee')
    physician_id = fields.Many2one(string="Optometra asignado",comodel_name='op.physician',domain="[('reception_ids','in',id)]")
    appointment_ids = fields.One2many(string="Examenes visuales",comodel_name='op.appointment',inverse_name='reception_id')
    today_appointment = fields.Integer(string="Examenes de hoy",compute='_compute_today_appointment')
    sequence_id = fields.Many2one(string="Numeración de examenes",comodel_name='ir.sequence')
    color = fields.Integer("Color")
    categ_id = fields.Many2one(string="Categoria para contactos",comodel_name='res.partner.category')
    project_id = fields.Many2one(comodel_name='op.project',string="Proyecto")
    
    @api.depends('appointment_ids')
    def _compute_today_appointment(self):
        for r in self:
            res = 0
            if r.appointment_ids:
                today = r.appointment_ids.filtered(lambda a: a.date == date.today())
                res = len(today)
            r.today_appointment = res
    
    def get_all_appointment(self):
        self.ensure_one()
        return{
            'type':'ir.actions.act_window'
            ,'name':'Todos los examenes de sala'
            ,'view_mode':'tree,kanban,form'
            ,'res_model':'op.appointment'
            ,'domain':[('reception_id','=',self.id)]
            ,'context':"{'create':True}"
        }
    
    def get_today_apponitment(self):
        self.ensure_one()
        return{
            'type':'ir.actions.act_window'
            ,'name':'Examenes de hoy'
            ,'view_mode':'tree,kanban,form'
            ,'res_model':'op.appointment'
            ,'domain':[('reception_id','=',self.id)]
            ,'context':"{'create':True,'search_default_today':1}"
        }
    
    def action_create_record(self):
        ctx = {'default_date':date.today(),
               'default_reception_id':self.id,
               'default_physician_id':self.physician_id.id}
        return{
            'name':_('Nuevo examen visual'),
            'type': 'ir.actions.act_window',
            'view_mode':'form',
            'res_model':'op.appointment',
            'view_id':self.env.ref('optical_patient.op_appointment_form_view').id,
            'context':ctx
        }
    
    def action_create_patient(self):
        ctx={}
        if self.project_id:
            ctx['default_project_id'] = self.project_id.id
        return{
            'name':_('Nuevo paciente'),
            'type': 'ir.actions.act_window',
            'view_mode':'form',
            'res_model':'op.patient',
            'view_id':self.env.ref('optical_patient.op_patient_form_view').id,
            'context':ctx
        }
    
    def on_barcode_scanned(self,barcode):
        for r in self:
            if not barcode.isdigit():
                raise UserError('El formato de código que solicita no es válido')
            employee = self.env['hr.employee'].search(['|',('barcode','=',barcode),('pin','=',barcode)],limit = 1,order="id")
            if not employee:
                raise UserError(_('No existe ningun empleado registrado con el pin: %s',barcode))
            if employee and not employee.active:
                raise UserError(_('El empleado %s no se encuentra activo actualmente en la empresa',employee.name))
            physician = self.env['op.physician'].search([('employee_id','=',employee.id)],limit = 1, order="id")
            if physician:
                self.physician_id = physician.id
            elif not physician and employee:
                self.recepcionist_id = employee.id