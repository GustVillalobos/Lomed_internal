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

class sv_delivery_envelope(models.Model):
    _name='sv.delivery.envelope'
    _description='Registro de entrega de sobres'

    partner_id = fields.Many2one(comodel_name='res.partner',string="cliente",copy=False)
    name = fields.Char("Despacho")
    delivery_date = fields.Datetime("Fecha de entrega")
    number_from = fields.Integer("Del")
    number_to = fields.Integer("Al")
    total_delivered = fields.Integer(string="Despachados",compute='compute_total_delivered')
    total_return = fields.Integer("Retornos",compute="compute_total_return",store=True)
    total_remaining = fields.Integer("Restastes",compute="compute_total_remaining")
    return_ids = fields.One2many(comodel_name='sv.returns.envelope',inverse_name='delivery_id',string="Retornos registrados")
    usable = fields.Boolean(string="Disponible para retorno",default=True)

    @api.depends('number_from','number_to')
    def compute_total_delivered(self):
        for r in self:
            res = 0
            if r.number_to > 0 and r.number_from > 0:
                res = (r.number_to - r.number_from) + 1
            r.name = 'Despacho: '+str(r.id)
            r.delivery_date = datetime.now()
            r.total_delivered = res

    @api.depends('return_ids')
    def compute_total_return(self):
        for r in self:
            if r.return_ids:
                r.total_return = len(r.return_ids)
            else:
                r.total_return = 0
    
    @api.depends('total_return')
    def compute_total_remaining(self):
        for r in self:
            r.total_remaining = r.total_delivered - r.total_return
    
class sv_returns_envelope(models.Model):
    _name='sv.returns.envelope'
    _description='Registro de retorno de sobres'

    name = fields.Char("Número de sobre",required=True)
    dispatch_id = fields.Many2one(string="Despacho de ruta",comodel_name='sv.route.dispatch')
    partner_id = fields.Many2one(string="Cliente",comodel_name='res.partner')
    delivery_id = fields.Many2one(comodel_name='sv.delivery.envelope',string="Despacho de sobre",compute='compute_delivery_id',store=True)
    date_sent = fields.Datetime("Fecha de retorno")
    state = fields.Selection([
        ('collected','Recolectado'),
        ('received','Recibido'),
        ('waiting','En consulta'),
        ('rejected','Rechazado')
    ],default='collected',string="Estado",copy=False)
    comments = fields.Text("Comentarios")

    @api.depends('name')
    def compute_delivery_id(self):
        for r in self:
            envelope_number = 0
            res = False
            try:
                envelope_number = int(r.name)
            except Exception as error:
                raise UserError('Error: '+str(error))
            if envelope_number > 0:
                res = self.env['sv.delivery.envelope'].search([('number_from','<=',envelope_number),('number_to','>=',envelope_number),('usable','=',True)],limit=1)
            r.date_sent = datetime.now()
            if res:
                r.partner_id = res.partner_id.id
            r.delivery_id = res.id if res else False
    
    def action_receive(self):
        self.ensure_one()
        self.state = 'received'
    
    def action_consult(self):
        self.ensure_one()
        self.state = 'waiting'

    def action_cancel(self):
        self.ensure_one()
        self.state = 'rejected'

class sv_envelope_partner(models.Model):
    _inherit='res.partner'

    envelope_delivered_ids = fields.One2many(comodel_name='sv.delivery.envelope',inverse_name='partner_id',string="Sobres despachados")
