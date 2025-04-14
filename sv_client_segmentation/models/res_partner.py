# -*- coding: utf-8 -*-
##############################################################################
#
#    Odoo
#
##############################################################################
import logging
import time
from datetime import datetime,timedelta,time,date
from dateutil import relativedelta
from odoo import api, fields, models,_
from odoo.exceptions import ValidationError
from odoo.exceptions import UserError
_logger = logging.getLogger(__name__)


class sv_technical_profile(models.Model):
    _inherit = 'res.partner'
    hisory_profile_ids = fields.One2many(comodel_name='sv.partner.history.data',inverse_name='partner_id', string="Historial de perfil")
    order_frequency = fields.Float(string="Frecuencia de compra",readonly=True,copy=False)
    sku = fields.Float(string="SKU",readonly=True,copy=False)
    branches = fields.Integer(string="Número de sucursales",store=True,copy=False,compute='compute_branches',readonly=True)
    turnover = fields.Float("Compra mensual",readonly=True,copy=False)
    target_product = fields.Float(string="Producto Objetivo",copy=False,readonly=True)
    target_product_string = fields.Char(string="Producto Objetivo",store=False,readonly="True",copy=False,compute='compute_percent_tps')
    date_start = fields.Date(string="Fecha inicio",readonly=True,copy=False)
    date_end = fields.Date("Fecha fin",copy=False,readonly=True)
    suggested =fields.Many2one(comodel_name='res.partner.category',string="Categoria sugerida",readonly=True,copy=False)
    of_trend = fields.Selection([
        ('upgrade','△')
        ,('equal','◉')
        ,('downgrade','▽')],readonly=True,copy=False)
    sku_trend = fields.Selection([
        ('upgrade','△')
        ,('equal','◉')
        ,('downgrade','▽')],readonly=True,copy=False)
    to_trend = fields.Selection([
        ('upgrade','△')
        ,('equal','◉')
        ,('downgrade','▽')],readonly=True,copy=False)
    tp_trend = fields.Selection([
        ('upgrade','△')
        ,('equal','◉')
        ,('downgrade','▽')],readonly=True,copy=False)
    
    @api.depends('child_ids')
    def compute_branches(self):
        for r in self:
            total_branch = r.child_ids.filtered(lambda s: s.type == 'delivery' and s.active == True)
            r.branches = len(total_branch) if len(total_branch) > 0 else 1
    
    @api.depends('target_product')
    def compute_percent_tps(self):
        self.ensure_one()
        res = '{0} %'
        per = round(self.target_product*100,2)
        self.target_product_string = res.format(per)

    def action_calculate_profile(self):
        self.ensure_one()
        self.save_history()
        self.update_period()
        self.order_frequency = self.get_order_frequency_value()
        self.sku= self.get_sku_value()
        self.turnover = self.get_turnover_value()
        self.target_product = self.get_percent_value()
        result_suggested = self.get_suggested_value()
        same = self.category_id.filtered(lambda f:f.id == result_suggested)
        self.suggested = result_suggested if result_suggested > 0 and not same else False
        last_profile = self.get_last_history_record()
        if last_profile:
            self.of_trend = self.calculate_trend(self.order_frequency,last_profile.order_frequency)
            self.sku_trend = self.calculate_trend(self.sku,last_profile.sku)
            self.to_trend = self.calculate_trend(self.turnover,last_profile.turnover)
            self.tp_trend = self.calculate_trend(self.target_product,last_profile.target_product)


    #Check for funtion to update dates
    def update_period(self):
        setting = self.get_current_setting()
        if setting:
            setting.last_calculate = datetime.now()
            self.date_start = setting.date_start
            self.date_end = setting.date_end
        if not setting:
            raise ValidationError('No existe una configuración activa para ninguna de las categorias asociadas a este contacto')

    def get_current_setting(self):
        setting = False
        for c in self.category_id:
            setting = self.env['sv.segmentation.settings'].search([('state','=','current'),('reference_categ_id','=',c.id)],limit = 1)
            if setting:
                break
        return setting

    def save_history(self):
        self.ensure_one()
        today = datetime.now()
        exist = self.hisory_profile_ids.filtered(lambda t: t.replace_date.month == today.month)
        if not exist:
            #name_record = self.x_studio_nombre_comercial if self.x_studio_nombre_comercial else self.name
            name_record = self.name if self.name else 'Cliente genérico'
            msj = 'Historico de {name_record} guardado el {replace_date}'
            dic = {}
            dic['name'] = msj.format(name_record=name_record,replace_date=today.strftime('%d-%m-%Y'))
            dic['replace_date'] = today
            dic['partner_id'] = self.id
            dic['date_start'] = self.date_start
            dic['date_end'] = self.date_end
            dic['order_frequency'] = self.order_frequency
            dic['sku'] = self.sku
            dic['branches'] = self.branches
            dic['turnover'] = self.turnover
            dic['target_product'] = self.target_product
            try:
                self.env['sv.partner.history.data'].create(dic)
            except Exception as error:
                raise UserError('Error al guardar historial:'+str(error))

    def get_order_frequency_value(self):
        self.ensure_one()
        frequency = {}
        start_d = datetime.combine(self.date_start,time(0,0,0))
        end_d = datetime.combine(self.date_end,time(23,59,59))
        last_month = start_d.month
        date_year = start_d.year
        control_date = start_d
        average = 0

        orders = self.sale_order_ids.filtered(lambda p: (p.state not in ('draft','cancel') and (p.date_order >= start_d and p.date_order <= end_d)))
        #Inicializando obj para almacenar la frecuencia agrupada por mes
        while end_d >= control_date:
            frequency[control_date.strftime('%b%y')]=0
            if last_month+1 > 12:
                last_month = 1
                date_year += 1
                control_date = datetime(date_year,last_month,control_date.day,0,0,0)
            else:
                last_month += 1
                control_date = datetime(date_year,last_month,control_date.day,0,0,0)
        #Reestablecer fecha de control
        if control_date != start_d:
            control_date = start_d
        
        #Calcular frecuencia
        while control_date <= end_d:
            end_day = control_date.replace(hour=23,minute=59,second=59)
            exist_order = orders.filtered(lambda t: t.date_order >= control_date and t.date_order <= end_day)
            if exist_order:
                frequency[control_date.strftime('%b%y')] = frequency[control_date.strftime('%b%y')]+1
            control_date = control_date + timedelta(days=1)
        if len(frequency) > 0:
            total = sum(frequency.values())
            months = len(frequency)
            average = total/months
        return average   

    def get_sku_value(self):
        self.ensure_one()
        total_sku = {}
        start_d = datetime.combine(self.date_start,time(0,0,0))
        end_d = datetime.combine(self.date_end,time(23,59,59))
        last_month = start_d.month
        date_year = start_d.year
        control_date = start_d
        average = 0
        
        #Recuperando todas las facturas del cliente
        invoices = self.invoice_ids.filtered(lambda f:(f.move_type=='out_invoice' and f.state == 'posted' and f.payment_state != 'reversed'))
        while end_d >= control_date:
            invoice_month = invoices.filtered(lambda ff: ff.invoice_date.month == last_month and ff.invoice_date.year == date_year)
            product = {}
            #Calcular producto cosumidos del mes
            for f in invoice_month:
                for l in f.invoice_line_ids:
                    try:
                        product[str(l.product_id.id)]=product[str(l.product_id.id)]+1
                    except:
                        product[str(l.product_id.id)]=0
                        product[str(l.product_id.id)]=product[str(l.product_id.id)]+1
            #Guardando para calcular promedio
            try:
                total_sku[control_date.strftime('%b%y')] = total_sku[control_date.strftime('%b%y')]+len(product)
            except:
                total_sku[control_date.strftime('%b%y')] = 0
                total_sku[control_date.strftime('%b%y')] = total_sku[control_date.strftime('%b%y')] + len(product)
            #Aumentando la fecha de control
            if last_month+1 > 12:
                last_month = 1
                date_year += 1
                control_date = datetime(date_year,last_month,control_date.day)
            else:
                last_month += 1
                control_date = datetime(date_year,last_month,control_date.day)
            
        if len(total_sku) > 0:
            total = sum(total_sku.values())
            months = len(total_sku)
            average = total/months
        return average
    
    def get_turnover_value(self):
        self.ensure_one()
        turnover_months = {}
        start_d = self.date_start
        end_d = self.date_end
        last_month = start_d.month
        date_year = start_d.year
        control_date = start_d
        average = 0
        #resul_value = 0

        invoices = self.invoice_ids.filtered(lambda f:(f.move_type=='out_invoice' and f.state=='posted' and f.payment_state!='reversed' and (f.invoice_date>=start_d and f.invoice_date<=end_d)))
        #inicializando objeto para calculos
        while end_d >= control_date:
            turnover_months[control_date.strftime('%b%y')]=0
            if last_month+1 > 12:
                last_month = 1
                date_year += 1
                control_date = date(date_year,last_month,control_date.day)
            else:
                last_month += 1
                control_date = date(date_year,last_month,control_date.day)
        #sumando venta por mes
        for i in invoices:
            try:
                turnover_months[i.invoice_date.strftime('%b%y')] = round(turnover_months[i.invoice_date.strftime('%b%y')]+i.amount_untaxed,2)
            except:
                turnover_months[i.invoice_date.strftime('%b%y')] = 0
                turnover_months[i.invoice_date.strftime('%b%y')] = round(turnover_months[i.invoice_date.strftime('%b%y')]+i.amount_untaxed,2)
        if len(turnover_months) > 0:
            total = sum(turnover_months.values())
            months = len(turnover_months)
            average = total/months
        
        return average
    
    def get_percent_value(self):
        self.ensure_one()
        percent = {}
        start_d = self.date_start
        end_d = self.date_end
        last_month = start_d.month
        date_year = start_d.year
        control_date = start_d
        average = 0
        setting = self.get_current_setting()

        invoices = self.invoice_ids.filtered(lambda f:(f.move_type=='out_invoice' and f.state=='posted' and f.payment_state!='reversed' and (f.invoice_date>=start_d and f.invoice_date<=end_d)))
        while end_d >= control_date:
            percent[control_date.strftime('%b%y')]=0
            if last_month+1 > 12:
                last_month = 1
                date_year += 1
                control_date = date(date_year,last_month,control_date.day)
            else:
                last_month += 1
                control_date = date(date_year,last_month,control_date.day)
        
        for i in invoices:
            for l in i.invoice_line_ids:
                if l.product_id and setting.focus_sku_ids.filtered(lambda f: f.id == l.product_id.product_tmpl_id.id):
                    percent[i.invoice_date.strftime('%b%y')] = percent[i.invoice_date.strftime('%b%y')] + round(l.price_subtotal,2)
        
        if len(percent) > 0:
            total = sum(percent.values())
            months = len(percent)
            average = total/months
            result_value = round(average/self.turnover,2)

        return result_value
    
    def get_suggested_value(self):
        self.ensure_one()
        setting = self.get_current_setting()
        aplicable_categories = False
        result = False
        #determinar categorias aplicables basado en la cantidad de sucursales
        if self.branches <= 1:
            aplicable_categories = setting.line_ids.filtered(lambda c: c.branch <= 1).sorted(key = lambda n: n.categ_id.name,reverse=True)
        elif self.branches > 1:
            aplicable_categories = setting.line_ids.filtered(lambda c: c.branch > 1).sorted(key = lambda n: n.categ_id.name,reverse=True)
        
        #Calcular categoria sugerida
        if aplicable_categories:
            for c in aplicable_categories:
                percent = 0
                if c.percent <= 1:
                    percent = c.percent
                elif c.percent > 1:
                    percent = round(c.percent/100,2)
                if self.order_frequency >= c.order_frequency and self.sku >= c.sku and self.branches >= c.branch and self.turnover >= (c.min_value*c.branch) and self.target_product >= percent:
                    result = c.categ_id.id
        
        return result
    
    def get_last_history_record(self):
        self.ensure_one()
        return self.hisory_profile_ids[-1]
    
    def calculate_trend(self,actual_value,past_value):
        result = 'equal'
        if actual_value > past_value:
            result = 'upgrade'
        elif actual_value < past_value:
            result = 'downgrade'
        
        return result
    
    def apply_suggested(self):
        self.ensure_one()
        categ_list = []
        setting = self.get_current_setting()

        #Crea lista de categorias disponibles para clasificar
        for l in setting.line_ids:
            categ_list.append(l.categ_id.id)
        #Quitar categoria actual
        old_category = self.category_id.filtered(lambda f: f.id in categ_list)
        if old_category and self.suggested:
            for oc in old_category:
                self.write({'category_id':[(3,oc.id)]})
        #Escribe la sugerencia en la ficha del cliente
        if self.suggested:
            self.write({'category_id':[(4,self.suggested.id)]})
            self.suggested = False

    def ignore_suggested(self):
        self.ensure_one()
        self.suggested = False