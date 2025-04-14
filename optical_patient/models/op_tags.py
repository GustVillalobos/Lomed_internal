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
from random import random

class op_tags(models.Model):
    _name = 'op.patient.tags'
    _description = 'Etiquetas paciente'

    name = fields.Char("Etiqueta")
    
    def _get_random_color(self):
        return random.randint(1,11)
    
    color = fields.Integer("Color",default=_get_random_color)
    active = fields.Boolean("Activo")
    patient_ids = fields.Many2many(string="Pacientes",comodel_name='op.patient')
