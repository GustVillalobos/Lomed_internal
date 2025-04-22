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

class op_professional(models.Model):
    _name='op.physician'
    _inherit = ['mail.thread']
    _description = 'Perfil profecional'

    name = fields.Char("Nombre completo")
    code = fields.Char(string="Código",readonly=True,store=True)
    professional_ID = fields.Char("Cédula profesional",tracking=True,copy=False)
    specialty_id = fields.Many2one(string="Especialidad",comodel_name='op.specialty',required=True)
    degree = fields.Char("Titulo",tracking=True)
    employee_id = fields.Many2one(string="Empleado relacionado",comodel_name='hr.employee',tracking=True)
    gender = fields.Selection([
        ('female','Mujer'),
        ('male','Hombre'),
        ('lgbt','Diverso')
    ],default='female',string="Género")
    address = fields.Char("Dirección")
    email = fields.Char("Correo electrónico")
    reception_ids = fields.Many2many(string="Salas autorizadas",comodel_name='op.reception')
    color = fields.Integer("Color",compute='_get_color')

    @api.model
    def create(self,vals):
        if 'code' in vals and not vals.get('code'):
            _logger.info('Agregando código a profesional')
            vals['code'] = self.generate_code(vals.get('specialty_id'))
        physician = super(op_professional,self).create(vals)
        return physician

    @api.onchange('employee_id')
    def update_name(self):
        self.ensure_one()
        self.name = self.employee_id.name

    def generate_code(self,val):
        specialty = self.env['op.specialty'].browse(int(val))
        res = ''
        if specialty:
            last_code = self.get_last_code(specialty)
            number = 0
            if last_code:
                number = int(last_code[-3:])
        res = specialty.prefix + str(number + 1).zfill(3)
        return res

    def get_last_code(self,specialty):
        res = False
        record = self.env['op.physician'].search([('specialty_id','=',specialty.id)],order="id desc",limit=1)
        if record:
            res = record.code
        return res
    
    def get_reception(self):
        res = self.env['op.reception'].browse(1)
        reception = self.env['op.reception'].search([('user_id','=',self.env.user.id)],limit = 1)
        if reception:
            res = reception
        return res

    def _get_color(self):
        for r in self:
            reception = self.get_reception()
            r.color = reception.color
    
class op_specialty(models.Model):
    _name='op.specialty'
    _description='Especialidades del profesional'
    _sql_constraints = [
        ('unique_prefix','unique(prefix)','Prefijo ya utilizado, seleccione uno diferente'),
    ]

    name = fields.Char("Especialidad",required=True)
    prefix = fields.Char("Prefijo",required=True,help="Letras o números utilizados para generar los códigos de profecionales, máximo 3 caracteres")

    @api.model
    def create(self,vals):
        if 'prefix' in vals:
            vals['prefix'] = (vals.get('prefix')[:3]).upper()
        specialty = super(op_specialty,self).create(vals)
        return specialty
    
    def write(self,vals):
        if 'prefix' in vals:
            vals['prefix'] = (vals.get('prefix')[:3]).upper()
        specialty = super(op_specialty,self).write(vals)
        return specialty