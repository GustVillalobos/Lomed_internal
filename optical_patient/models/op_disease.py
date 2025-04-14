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

class op_disease(models.Model):
    _name = 'op.disease'
    _description = 'Padecimientos o enfermedades'

    name = fields.Char("Enfermedad")
    description = fields.Text("Descripción")
    code = fields.Char(string="Código",readonly=True)
    type = fields.Selection([
        ('optical','Óptico'),
        ('clinical','Clínico')
    ],default='optical',string="Típo",required=True)

    @api.model
    def create(self,vals):
        if 'code' not in vals:
            vals['code'] = self.compute_code(vals.get('type'))
        disease = super(op_disease,self).create(vals)
        return disease

    def compute_code(self,d_type):
        code = 'OPT' if d_type == 'optical' else 'CLN'
        last_record = self.env['op.disease'].search([('type','=',d_type)],order='id desc',limit = 1)
        try:
            next_number = int(last_record.code[-4:])+1
        except:
            next_number = 1
        return code+str(next_number).zfill(4)
