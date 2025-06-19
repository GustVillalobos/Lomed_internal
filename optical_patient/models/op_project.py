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

class op_project(models.Model):
    _name = 'op.project'
    _inherit = ['mail.thread']
    _description = 'Proyecto'

    name = fields.Char("Proyecto")
    detail = fields.Text("Detalles")
    code = fields.Char("Código")
    reference_ids = fields.One2many(comodel_name='op.project.contact',string="Referencias",inverse_name='project_id')
    patient_ids = fields.One2many(comodel_name='op.patient', string="Pacientes", inverse_name='project_id')
    patient_count = fields.Integer("Total pacientes", compute='_compute_patient_count')

    def get_patient_list(self):
        self.ensure_one()
        return{
            'type':'ir.actions.act_window'
            ,'name':'Pacientes '+self.name
            ,'view_mode':'tree,form'
            ,'res_model':'op.patient'
            ,'domain':[('project_id','=',self.id)]
            ,'context':"{'create':False}"
        }
    
    @api.depends('patient_ids')
    def _compute_patient_count(self):
        for r in self:
            res = 0
            if r.patient_ids:
                res = len(r.patient_ids)
            r.patient_count = res


class op_project_contact(models.Model):
    _name = 'op.project.contact'
    _description = 'Referencia de proyecto'

    name = fields.Char("Nombre")
    email = fields.Char("Correo electrónico")
    phone = fields.Char("Telefono")
    mobile = fields.Char("Celular")
    type = fields.Selection(selection=[
        ('intern','Interno'),
        ('external','Externo'),
        ('hybrid','Hibrido')
    ],default='intern',string="Tipo")
    project_id = fields.Many2one(comodel_name='op.project',string="Proyecto")
