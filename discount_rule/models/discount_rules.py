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

class DiscountRulesSv(models.Model):
    _name = 'partner.discount.rules'
    _description = 'Reglas de descuento'
    _inherit = ['mail.thread']
    _order = 'priority desc, date_start desc'

    name = fields.Char("Regla")
    partner_id = fields.Many2one(comodel_name='res.partner',string="Cliente",domain="[('customer_rank','>',0)]")
    active = fields.Boolean("Activo",default=True)
    date_start = fields.Date("Desde")
    date_end = fields.Date("Hasta")
    application_range = fields.Selection([
        ('product','Productos'),
        ('category','Categorias'),
        ('all','Todo')
    ],string="Aplicar en",default='product')
    product_ids = fields.Many2many(
        comodel_name='product.template',
        relation='discount_rule_product_template_rel',
        column1='rule_id',
        column2='product_template_id',
        string="Productos")
    category_ids = fields.Many2many(
        comodel_name='product.category',
        relation='discount_rule_product_category_rel',
        column1='rule_id',
        column2='category_id',
        string="Categorias")
    discount = fields.Float("Descuento (%)",required=True,digits=(16,2))
    priority = fields.Integer("Prioridad",default=10,help="Orden de aplicación de reglas a mayor numero más prioridad")
    
    @api.constrains('date_start', 'date_end')
    def _check_dates(self):
        for rule in self:
            if rule.date_end and rule.date_end < rule.date_start:
                raise ValidationError(
                    "La fecha final no puede ser menor a la fecha inicial."
                )

    @api.constrains('discount')
    def _check_discount_range(self):
        for rule in self:
            if rule.discount <= 0 or rule.discount > 100:
                raise ValidationError(
                    "El descuento debe estar entre 0.01 y 100."
                )

    @api.constrains('application_range', 'product_ids', 'category_ids')
    def _check_application_scope(self):
        for rule in self:
            if rule.application_range == 'product' and not rule.product_ids:
                raise ValidationError(
                    "Debe seleccionar al menos un producto."
                )
            if rule.application_range == 'category' and not rule.category_ids:
                raise ValidationError(
                    "Debe seleccionar al menos una categoría."
                )
            if rule.application_range == 'all' and (rule.product_ids or rule.category_ids):
                raise ValidationError(
                    "Las reglas aplicadas a todo no deben tener productos ni categorías."
                )