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

class HelpdeskTagSv(models.Model):
    _inherit = 'helpdesk.tag'

    is_parent = fields.Boolean("Categoria padre")
    parent_id = fields.Many2one(comodel_name='helpdesk.tag',string="Categoria padre",domain="[('is_parent','=',True),('active','=',True)]")

class HelpdeskTicketSv(models.Model):
    _inherit = 'helpdesk.ticket'

    code = fields.Char("Código",readonly=True)
    parent_tag_id = fields.Many2one(comodel_name='helpdesk.tag',string="Categoria padre",domain="[('is_parent','=',True),('active','=',True)]")
    ticket_type = fields.Selection([
        ('Reclamo','Reclamo'),
        ('Consulta','Consulta')
    ],default='Consulta',string="Tipo de ticket")
    order_id = fields.Many2one(comodel_name='sale.order',string="Orden relacionada")

    @api.model
    def create(self,vals):
        new_ticket = super(HelpdeskTicketSv,self).create(vals)
        if new_ticket.ticket_type == 'Consulta':
            new_ticket.code = self.env['ir.sequence'].next_by_code("CSTT")
        else:
           new_ticket.code = self.env['ir.sequence'].next_by_code("CLMT")
        return new_ticket


class HelpdeskOrder(models.Model):
    _inherit = 'sale.order'

    ticket_ids = fields.One2many(comodel_name='helpdesk.ticket',inverse_name='order_id',string="Consultas y reclamos")