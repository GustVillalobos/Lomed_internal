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

    parent_tag_id = fields.Many2one(comodel_name='helpdesk.tag',string="Categoria padre",domain="[('is_parent','=',True),('active','=',True)]")