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
from dateutil.relativedelta import relativedelta

class op_patient(models.Model):
    _name = 'op.patient'
    _inherit= ['mail.thread','mail.activity.mixin']
    _description = 'Paciente'

    name = fields.Char(string="Nombre completo",compute='_compute_patient_name',readonly=True)
    first_name = fields.Char("Nombres",required = True)
    last_name = fields.Char("Apellidos", required = True)
    birthdate = fields.Date("Fecha de nacimiento")
    age = fields.Integer(string="Edad",compute='_compute_age',store=True)
    occupation = fields.Char(string="Ocupación")
    related_company_id = fields.Many2one(string="Empresa",comodel_name='res.partner')#crear el dominio pendiente
    address = fields.Char("Dirección")
    gender = fields.Selection([
        ('female','Mujer'),
        ('male','Hombre'),
        ('lgbt','Diverso')
    ],default='female',string="Género")
    document_type = fields.Selection(selection=[
        ('01','DUI')
        ,('02','Pasaporte')
        ,('03','Carné de minoridad')
        ,('04','Carné de residente')
        ,('00','Otro')
    ],default="01",string="Tipo de documento",tracking=True)
    document = fields.Char("Número de documento",tracking=True)
    phone = fields.Char("Telefono")
    mobile = fields.Char("Celular")
    email = fields.Char("Correo electrónico")
    medical_history_ids = fields.One2many(string="Historial clinico",comodel_name="op.medical.history",inverse_name='patient_id')
    optical_history_ids = fields.One2many(string="Antecente óptico",comodel_name='op.optical.history',inverse_name='patient_id')
    tag_ids = fields.Many2many(string="Categorias",comodel_name="op.patient.tags")
    partner_id = fields.Many2one(string="Contacto relacionado",comodel_name='res.partner')
    appointment_ids = fields.One2many(string="Citas",comodel_name='op.appointment',inverse_name='patient_id')
    appointment_count = fields.Integer("Total citas",compute='_count_appointment')
    last_appointment_date = fields.Date("Última revisión",compute='_compute_last_date')
    is_birthday_today = fields.Boolean(string="Es su cumpleaños hoy?",compute='_compute_is_birthday_today')
    is_minor = fields.Boolean("Es menor",compute='_verify_is_minor')
    #Información del guardian
    guardian_name = fields.Char("Nombres")
    guardian_last_name = fields.Char("Apellidos")
    guardian_document = fields.Char("DUI")
    relationship = fields.Selection([
        ('parent','Madre/Padre'),
        ('familiar','Familiar'),
        ('guardian','Tutor legal'),
        ('other','Otro')
    ],default='parent',string="Parentezco")
    color = fields.Integer("Color",compute='_get_color')

    @api.depends('first_name','last_name')
    def _compute_patient_name(self):
        for r in self:
            name = r.first_name.upper() if r.first_name else ''
            last_name = r.last_name.upper() if r.last_name else ''
            name = _('%s %s',name,last_name)
            if r.name != name:
                r.name = name
    
    @api.model
    def create(self,vals):
        if 'first_name' in vals:
            vals['first_name'] = vals.get('first_name').title()
        if 'last_name' in vals:
            vals['last_name'] = vals.get('last_name').title()
        patient = super(op_patient,self).create(vals)
        return patient
    
    def write(self,vals):
        if 'first_name' in vals:
            vals['first_name'] = vals.get('first_name').title()
        if 'last_name' in vals:
            vals['last_name'] = vals.get('last_name').title()
        patient = super(op_patient,self).write(vals)
        return patient
    
    @api.depends('appointment_ids')
    def _count_appointment(self):
        for r in self:
            res = 0
            if r.appointment_ids:
                res = len(r.appointment_ids)
            r.appointment_count = res
    
    @api.depends('birthdate','appointment_ids')
    def _compute_age(self):
        for r in self:
            res = 0
            if r.birthdate:
                delta = relativedelta(date.today(),r.birthdate)
                res = delta.years
                if res < 0:
                    res = 0
            r.age = res
    
    @api.depends('appointment_ids')
    def _compute_last_date(self):
        for r in self:
            res = False
            last_record = False
            if r.appointment_ids:
                last_record = r.appointment_ids[-1]
            if last_record:
                res = last_record.date
            r.last_appointment_date = res
    
    @api.depends('birthdate')
    def _compute_is_birthday_today(self):
        for r in self:
            res = False
            today = date.today()
            if r.birthdate:
                res = r.birthdate.month == today.month and r.birthdate.day == today.day
            r.is_birthday_today = res
    
    def get_oppointment_list(self):
        self.ensure_one()
        return{
            'type':'ir.actions.act_window'
            ,'name':'Visita de paciente'
            ,'view_mode':'tree,form'
            ,'res_model':'op.appointment'
            ,'domain':[('patient_id','=',self.id)]
            ,'context':"{'create':False}"
        }
    
    def create_partner(self):
        self.ensure_one()
        reception = self.get_reception()
        partner = {}
        partner['name'] = self.name if not self.is_minor else self.guardian_name + ' ' + self.guardian_last_name
        partner['names'] = self.first_name if not self.is_minor else self.guardian_name
        partner['last_names'] = self.last_name if not self.is_minor else self.guardian_last_name
        partner['dui'] = self.document if not self.is_minor else self.guardian_document
        partner['company_type'] = 'person'
        partner['type'] = 'contact'
        partner['street'] = self.address
        partner['phone'] = self.phone
        partner['mobile'] = self.mobile
        partner['email'] = self.email
        partner['lang'] = 'es_ES'
        partner['country_id'] = self.env.ref('base.sv').id
        partner['property_payment_term_id'] = 1
        if reception.categ_id:
            partner['category_id'] = [(6,0,[reception.categ_id.id])]
        if self.related_company_id:
            partner['parent_id'] = self.related_company_id.id
        try:
            new_partner = self.env['res.partner'].create(partner)
        except Exception as error:
            raise UserError('Error: '+str(error))
        self.partner_id = new_partner.id
    
    @api.depends('age')
    def _verify_is_minor(self):
        for r in self:
            res = False
            if r.age < 18:
                res = True
            r.is_minor = res

    def create_appointment(self):
        self.ensure_one()
        reception = self.get_reception()
        ctx = {'default_date':date.today(),
               'default_reception_id':reception.id,
               'default_patient_id':self.id,
               'default_physician_id':reception.physician_id.id}
        return{
            'name':_('Nuevo examen visual'),
            'type': 'ir.actions.act_window',
            'view_mode':'form',
            'res_model':'op.appointment',
            'view_id':self.env.ref('optical_patient.op_appointment_form_view').id,
            'context':ctx
        }
    
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
 
class op_medical_history(models.Model):
    _name='op.medical.history'
    _description = 'Historia clinica'

    name = fields.Char("Nombre",related="patient_id.name")
    disease_id = fields.Many2one(string="Padecimiento",comodel_name='op.disease',domain="[('type','=','clinical')]")
    diagnosis_date = fields.Date("Fecha de diagnóstico")
    underwent_surgery = fields.Boolean("Cirugía",help="Marque esta opción en caso el paciente haya sido sometido a cirugía")
    comment = fields.Text("Comentarios")
    patient_id = fields.Many2one(string="Paciente",comodel_name='op.patient')

class op_optical_history(models.Model):
    _name = 'op.optical.history'
    _description = 'Historial óptico'

    name = fields.Char("Nombre",related='patient_id.name')
    disease_id = fields.Many2one(string="Padecimiento",comodel_name='op.disease',domain="[('type','=','optical')]")
    personal = fields.Boolean("Personal")
    underwent_surgery = fields.Boolean("Cirugía",help="Marque esta opción en caso el paciente haya sido sometido a cirugía")
    family = fields.Boolean("Familiar")
    comment = fields.Text("Comentario")
    patient_id = fields.Many2one(string="Paciente",comodel_name='op.patient')