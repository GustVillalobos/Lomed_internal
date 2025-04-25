# -*- coding: utf-8 -*-
##############################################################################
#
#    Odoo
#
##############################################################################
import logging
import time
from datetime import datetime,timedelta,date
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models,_
from odoo.exceptions import ValidationError
from odoo.exceptions import UserError
_logger = logging.getLogger(__name__)

class sv_segmentation_settings(models.Model):
    _name='sv.segmentation.settings'
    _inherit=['mail.thread']
    _description='Configuración de segmentación'
    name=fields.Char(string="Configuración")
    state = fields.Selection([
        ('draft','Borrador')
        ,('current','En uso')
        ,('obsolete','Obsoleto')],default='draft',string="Estado")
    reference_categ_id = fields.Many2one(comodel_name='res.partner.category',string="Categoria de referencia",copy=False)
    date_start = fields.Date(string="Fecha inicio",compute = 'compute_date_start',store=True,readonly=True)
    date_end = fields.Date(string="Fecha fin",compute='compute_date_end',store=True,readonly=True)
    end_interval = fields.Selection([
        ('today','Fecha actual')
        ,('end_month','Fin del mes anterior')
        ,('half_month','Mediados mes actual')],default='today')
    interval = fields.Integer("Intervalo")
    #focus_sku = fields.Many2many('product.template','segmentation_setting_product_template_rel','setting_id','product_tmpl_id',string="Producto Objetivo",copy=False)
    focus_sku_ids = fields.Many2many('product.template','segmentation_setting_product_template_rel','setting_id','product_tmpl_id',string="Producto Objetivo",copy=False)
    interval_type = fields.Selection([
        ('day','Días')
        ,('week','Semanas')
        ,('month','Meses')
        ,('year','Años')],default='month')
    line_ids = fields.One2many(comodel_name='sv.segmentation.settings.line',inverse_name='setting_id',string="Lineas de configuración")
    last_calculate = fields.Datetime(string="Último calculo", copy=False, readonly=True)

    @api.depends('interval','interval_type','end_interval','last_calculate')
    def compute_date_end(self):
        self.ensure_one()
        today = datetime.now()
        #Calculando fin del periodo
        if self.end_interval in ('today',False):
            self.date_end = today.date()
        elif self.end_interval == 'end_month':
            self.date_end = date(today.year,today.month,1) - timedelta(days = 1)
        else:
           day = 15
           if today.month == 2:
               day=14
           self.date_end = date(today.year,today.month,day)
    
    @api.depends('date_end')
    def compute_date_start(self):
        self.ensure_one()
        interval_value = abs(self.interval)
        #Calculando fecha inicio
        if self.interval_type == 'day':
            self.date_start = self.date_end - timedelta(days=interval_value)
        elif self.interval_type == 'week':
            self.date_start = self.date_end - timedelta(weeks=interval_value)
        elif self.interval_type == 'month':
           date_ref = self.date_end - relativedelta(months=interval_value)
           if self.end_interval == 'end_month':
              while date_ref.day != 1:
                 date_ref = date_ref+timedelta(days=1)
           self.date_start = date_ref
        else:
           self.date_start = self.date_end - relativedelta(years=interval_value)
            
    def action_set_current(self):
        self.ensure_one()
        other = self.env['sv.segmentation.settings'].search([('reference_categ_id','=',self.reference_categ_id.id),('id','!=',self.id),('state','=','current')],limit = 1)
        if other:
            other.state = 'obsolete'
        self.state = 'current'
    
    def back_to_draft(self):
        self.ensure_one()
        self.state = 'draft'

    def set_obsolete(self):
        self.ensure_one()
        self.state = 'obsolete'
    
class sv_segmentation_settings_line(models.Model):
    _name = 'sv.segmentation.settings.line'
    _description='Linea de configuración de segmentación'
    name = fields.Char(string="Nombre",compute='compute_name_line')
    branch = fields.Integer("Sucursales")
    categ_id = fields.Many2one(comodel_name='res.partner.category',string="Categoria")
    setting_id = fields.Many2one(comodel_name='sv.segmentation.settings',string="Configuración")
    order_frequency = fields.Float("Frecuencia de compra")
    min_value = fields.Float("Desde")
    top_value = fields.Float("Hasta")
    sku = fields.Float("SKU")
    percent = fields.Float("Producto Objetivo (%)")

    @api.depends('categ_id')
    def compute_name_line(self):
        self.ensure_one()
        if self.categ_id:
            self.name="Config_"+self.categ_id.name
        else:
            self.name="Config_nameless"
    
    def _monthly_profile_calculation(self):
        config_list = self.env['sv.segmentation.settings'].search([('state','=','current')])
        for cl in config_list:
            partner_list = self.env['res.partner'].search([
                ('category_id','in',cl.reference_categ_id.id),
                ('active','=',True),
                ('customer_rank','>',0),
                ('parent_id','=',False)
                ])
            for p in partner_list:
                try:
                    p.action_calculate_profile()
                    _logger.info(f'Perfil calculado para {p.name}')
                except Exception as error:
                    _logger.info(f'Error al calcular perfil de {p.name}:\n '+str(error))

class sv_partner_history_data(models.Model):
    _name='sv.partner.history.data'
    _description = 'Historial de perfiles'
    name = fields.Char("Nombre")
    replace_date = fields.Datetime("Reemplazado el")
    partner_id = fields.Many2one(comodel_name='res.partner',string="Contacto")
    date_start = fields.Date("Fecha inicio")
    date_end = fields.Date("Fecha fin")
    order_frequency = fields.Float("Frecuencia de compra")
    sku = fields.Float("SKU")
    branches = fields.Integer("Número de sucursales")
    turnover = fields.Float("Compra mensual")
    target_product = fields.Float("Producto Objetivo")

#class sv_product_category(models.Model):
    #_inherit = 'product.category'
    #is_selectable = fields.Boolean(string="Categoria de interés",copy=False)