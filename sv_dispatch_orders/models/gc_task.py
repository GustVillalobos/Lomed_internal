# -*- coding: utf-8 -*-
##############################################################################
#
#    Odoo
#
##############################################################################
import logging
import time
import json
import requests
from datetime import datetime,timedelta
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models,_
from odoo.exceptions import ValidationError,UserError
_logger = logging.getLogger(__name__)

class gc_task(models.Model):
    _name = 'gc.task'
    _description = 'GlobalCom tarea'

    name = fields.Char("Tarea")
    description = fields.Text("Descripción")
    gc_id = fields.Integer("Identificador GLobalCom",)
    tracker_id = fields.Many2one(comodel_name='gc.tracker',string="Rastreador")
    lat = fields.Float("Latitud")
    lng = fields.Float("Longitud")
    date_from = fields.Datetime("Desde")
    date_to = fields.Datetime("Hasta")
    max_delay = fields.Integer("Retraso tolerado",help="Tiempo maximo de retraso tolerado en minutos.")
    min_stay_duration = fields.Integer("Estancia minima",help="Tiempo minimo en minutos para considerar completa la tarea.")
    gc_response = fields.Text("Respuesta API")

    def upload_task(self):
        self.ensure_one()
        header = self.get_header()
        company = self.get_company()
        data = {}
        data['hash'] = company.gps_hash
        data['task'] = self.get_task_data()
        data['create_form'] = False
        _logger.info("Subiendo registro: "+str(data))
        try:
            response = requests.post(company.gps_url+'/task/create',headers=header,json=data)
            response.raise_for_status()
            result = response.json()
        except requests.exceptions.RequestException as e:
            _logger.info("Error:\n"+str(e))
        if response.status_code == 200:
            self.gc_id = result.get('id')
            self.gc_response = str(result)
    
    def get_task_data(self):
        self.ensure_one()
        task = {}
        task['tracker_id'] = self.tracker_id.tracker_id
        task['location'] = self.get_location()
        task['label'] = self.name
        task['description'] = self.description
        task['from'] = self.date_from
        task['to'] = self.date_to
        task['max_delay'] = self.max_delay
        task['min_stay_duration'] = self.min_stay_duration
        return task

    def get_location(self):
        self.ensure_one()
        location = {}
        location['lat'] = self.lat
        location['lng'] = self.lng
        return location
    
    def update_list(self):
        header = self.get_header()
        company = self.get_company()
        data = {"hash":company.gps_hash}
        try:
            response = requests.post(company.gps_url+"/task/list",headers=header,json=data)
            response.raise_for_status()
            result = response.json()
        except requests.exceptions.RequestException as e:
            _logger.info("Error: "+str(e))
        if response.status_code == 200:
            _logger.info(str(result))

    def get_company(self):
        company = self.env['res.company'].browse(self.env.context['allowed_company_ids'][0])
        if not company.gps_hash:
            raise UserError('No hay un hash para realizar la conección')
        if not company.gps_url:
            raise UserError('No hay una URL a la que realizar la conección')
        return company
    
    def get_header(self):
         return {"Content-Type":"application/json","User-Agent":"Odoo/16"}

class gc_task_template(models.Model):
    _name = 'gc.task.template'
    _description = 'Plantilla de tarea GlobalCom'

    name = fields.Char("Tarea")
    description = fields.Text("Descripción")
    partner_id = fields.Many2one(comodel_name='res.partner',string="Contacto")
    duration_value = fields.Integer("Duración")
    interval = fields.Selection([
        ('minute','Minutos'),
        ('hour','Horas'),
        ('day','Todo el dia')
    ],default='hour',string="Intervalo")
    tracker_id = fields.Many2one(comodel_name='gc.tracker',string="Rastreador")
    date_from = fields.Datetime("Fecha inicio")
    max_delay = fields.Integer("Retraso tolerado",help="Tiempo maximo de retraso tolerado en minutos.")
    min_stay_duration = fields.Integer("Estancia minima",help="Tiempo minimo en minutos para considerar completa la tarea.")
    sequence = fields.Integer("Secuencia",default="5")

    def create_task(self):
        self.ensure_one()
        today = datetime.today()
        date_from = self.date_from.date()
        if date_from != today:
            date_from.replace(day=today.day,month=today.month,year=today.year)
            self.date_from = date_from
        new_task = {}
        new_task['name'] = self.name
        new_task['description'] = self.description
        new_task['tracker_id'] = self.tracker_id.id
        new_task['lat'] = self.partner_id.partner_latitude
        new_task['lng'] = self.partner_id.partner_longitude
        new_task['date_from'] = self.date_from
        new_task['date_to'] = self.get_date_to()
        new_task['max_delay'] = self.max_delay
        new_task['min_stay_duration'] = self.min_stay_duration
        try:
            task = self.env['gc.task'].create(new_task)
            task.upload_task()
        except Exception as e:
            raise UserError("Error:\n"+str(e))
        return{
            'type':'ir.actions.client',
             'tag': 'display_notification',
             'params':{
                  'title':'¡Exito!',
                  'type':'success',
                  'message':'Tarea guardada correctamente',
                  'sticky':False,
             }
        }

    def get_date_to(self):
        self.ensure_one()
        result = self.date_from
        if self.interval == 'hour':
            result = self.date_from + timedelta(hours = self.duration_value)
        elif self.interval == 'minute':
            result = self.date_from + timedelta(minutes=self.duration_value)
        else:
            result = self.date_from.replace(hour=23,minute=59,second=59)
        return result