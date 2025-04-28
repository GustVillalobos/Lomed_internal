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
import uuid
import logging
_logger = logging.getLogger(__name__)


class medical_referrals(models.Model):
    _name = 'medical.referrals'
    _description = 'Referencia médica'

    name = fields.Char("Referencia")
    patient_name = fields.Char("Paciente")
    dui = fields.Char("DUI")
    code_qr = fields.Char("Código de descuento")
    comments = fields.Html("Comentarios")
    redeemed = fields.Boolean("Canjeado")
    generation_date = fields.Datetime("Fecha de generación")
    exchange_date = fields.Datetime("Fecha de canje")

    @api.model
    def create(self,vals):
        if not 'name' in vals or not vals.get('name'):
            vals['name'] = self.env['ir.sequence'].next_by_code('REF1')
        vals['code_qr'] = str(uuid.uuid4()).upper()
        vals['generation_date'] = datetime.now()
        vals['redeemed'] = False
        reference = super(medical_referrals,self).create(vals)
        return reference
    
    def exchange_code(self):
        self.ensure_one()
        self.redeemed = True
        self.exchange_date = datetime.now()

class validate_referral(models.TransientModel):
    _name = 'validate.referrals'
    _description = 'Validación referencia'

    name = fields.Char("Nombre",compute='_compute_name')
    barcode = fields.Char("Código de referencia")
    referral_id = fields.Many2one(comodel_name='medical.referrals',string="Referencia")
    state = fields.Selection([
        ('wait','Iniciando proceso'),
        ('valid','Valido'),
        ('redeemed','Canjeado'),
        ('invalid','No Válido')
    ],default='wait',string="Estado")
    patient = fields.Char("Paciente",related='referral_id.patient_name')
    code = fields.Char("Código",related='referral_id.code_qr')
    dui = fields.Char("DUI",related='referral_id.dui')
    exchange_date = fields.Datetime("Fecha de canje",related='referral_id.exchange_date')
    
    @api.onchange('barcode')
    def evaluate_referrals(self):
        self.ensure_one()
        _logger.info('Iniciando proceso de busqueda')
        if self.barcode:
            barcode =  self.barcode.replace('\'','-')
            _logger.info('Code depurado: '+barcode)
            referral = self.env['medical.referrals'].search([('code_qr','=',barcode)], limit = 1)
            if referral and not referral.redeemed:
                self.referral_id = referral.id
                self.state = 'valid'
            elif referral and referral.redeemed:
                self.state = 'redeemed'
            else:
                self.state='invalid'
        else:
            self.state = 'wait'
        _logger.info('Fin del proceso: '+str(self.state))
    
    def action_exchange_code(self):
        self.ensure_one()
        try:
            self.referral_id.exchange_code()
        except Exception as error:
            raise UserError('Error: '+str(error))
        
    @api.depends('referral_id')
    def _compute_name(self):
        for r in self:
            r.name = r.referral_id.name if r.referral_id else 'Nuevo'