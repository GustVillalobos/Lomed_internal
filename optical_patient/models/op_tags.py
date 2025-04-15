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
import random

class op_tags(models.Model):
    _name = 'op.patient.tags'
    _description = 'Etiquetas paciente'

    name = fields.Char("Etiqueta")
    
    def _get_random_color(self):
        return random.randint(1,11)
    
    color = fields.Integer("Color",default=_get_random_color)
    active = fields.Boolean("Activo",default=True)
    patient_ids = fields.Many2many(string="Pacientes",comodel_name='op.patient')
    patient_count = fields.Integer("Pacientes actuales",compute='_compute_total_patient')

    def get_patient_list(self):
        self.ensure_one()
        ctx = {'create':False}
        return{
            'name':_('Pacientes de la categoria'),
            'type':'ir.actions.act_window',
            'view_mode':'tree',
            'res_model':'op.patient',
            'domain':[('tag_ids','in',self.id)],
            'context':ctx
        }
    
    @api.depends('patient_ids')
    def _compute_total_patient(self):
        for r in self:
            res = 0
            if r.patient_ids:
                res = len(r.patient_ids)
            r.patient_count = res
