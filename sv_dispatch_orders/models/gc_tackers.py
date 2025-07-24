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
import pytz
from datetime import datetime,timedelta
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models,_
from odoo.exceptions import ValidationError,UserError
_logger = logging.getLogger(__name__)

class sv_trackers(models.Model):
    _name='gc.tracker'
    _inherit=['mail.thread']
    _description = 'Rastreadores'

    name = fields.Char("Tracker")
    tracker_id = fields.Integer("Identificador GlobalCom")
    device_id = fields.Char("IMEI")
    model = fields.Char("Modelo")
    blocked = fields.Boolean("Bloqueado")
    creation_date = fields.Date("Dado de alta el")
    phone = fields.Char("Teléfono")
    active = fields.Boolean("Activo",default=True)
    tariff_date_due = fields.Date("Fecha de vencimiento de tarifa")
    last_sync_date = fields.Datetime("Ultima sincronización")
    gc_response = fields.Text("Respuesta API")
    task_template_ids = fields.One2many(comodel_name='gc.task.template',inverse_name='tracker_id',string="Tareas recurrentes")
    group_id = fields.Many2one(comodel_name='gc.group',string="Grupo asignado")
    employee_id = fields.Many2one(comodel_name='hr.employee',string="Empleado relacionado")
    tag_ids = fields.Many2many(comodel_name='gc.tag',string="Etiquetas")
    lat = fields.Float("Latitud",digits=(16,8))
    long = fields.Float("Longitud",digits=(16,8))
    presition = fields.Integer("Presición")
    satellites = fields.Integer("Satelites",help="Cantidad de satelites usados para triangular la posición")
    date_position = fields.Datetime("Fecha de la posición")
    heading = fields.Float("Ángulo",help="Dirección en grados (0-360)")
    speed = fields.Float("Velocidad")
    
    def _get_current_company(self):
        return self.env.context['allowed_company_ids'][0]
    
    company_id = fields.Many2one(comodel_name='res.company',string="Compañia",default=_get_current_company)

    def update_tracker_list(self):
        self.env['gc.group'].update_list()
        self.env['gc.tag'].update_tag_list()
        companies = self.env['res.company'].search([('gps_url','!=',False),('gps_hash','!=',False)])
        for company in companies:
            headers = {"Content-Type":"application/json","User-Agent":"Odoo/16"}
            data = {"hash":company.gps_hash}
            try:
                response = requests.post(company.gps_url+'/tracker/list/',headers=headers,json=data)
                response.raise_for_status()
                #result = response.text
                result = response.json()
            except requests.exceptions.RequestException as e:
                result = f"Error: {str(e)}"
                _logger.info(result)

            for data in result['list']:
                exist = self.env['gc.tracker'].search([('tracker_id','=',data['id'])],limit = 1)
                _logger.info('ID: '+str(data['id'])+' Registros encontrados: '+str(len(exist)))
                if not exist:
                    tracker = {}
                    tracker['name'] = data['label']
                    tracker['tracker_id'] = data['id']
                    tracker['device_id'] = data['source']['device_id']
                    tracker['blocked'] = data['source']['blocked']
                    tracker['model'] = data['source']['model']
                    tracker['creation_date'] = data['source']['creation_date']
                    tracker['tariff_date_due'] = data['source']['tariff_end_date']
                    tracker['phone'] = data['source']['phone']
                    tracker['last_sync_date'] = datetime.now()
                    tracker['gc_response'] = 'Listando: ' + str(data)
                    tracker['group_id'] = self.get_group(data['group_id'])
                    _logger.info('Registro ingresado: '+str(tracker))                    
                    try:
                        trc = self.env['gc.tracker'].create(tracker)
                        trc.write({'tag_ids':[(6,0,self.get_tags(data['tag_bindings']))]})
                    except Exception as error:
                        raise UserError('Error: '+str(error))
                else:
                    exist.name = data['label']
                    exist.device_id = data['source']['device_id']
                    exist.blocked = data['source']['blocked']
                    exist.creation_date = data['source']['creation_date']
                    exist.model = data['source']['model']
                    exist.tariff_date_due = data['source']['tariff_end_date']
                    exist.phone = data['source']['phone']
                    exist.last_sync_date = datetime.now()
                    exist.group_id = self.get_group(data['group_id'])
                    exist.gc_response = 'Listando: '+str(data)
                    exist.write({'tag_ids':[(6,0,self.get_tags(data['tag_bindings']))]})
                    
                    _logger.info('Registro editado: '+str(exist))
            return {
                'type':'ir.actions.client',
                'tag':'reload',
            }
            #_logger.info(result)
    
    def get_group(self,gc_id):
        group = self.env['gc.group'].search([('gc_id','=',gc_id)])
        res = False
        if group:
            res = group.id
        return res

    def get_tags(self,gc_r):
        result = []
        for data in gc_r:
            exist = self.env['gc.tag'].search([('gc_id','=',data['tag_id'])],limit = 1)
            if exist:
                result.append(exist.id)
        return result
    
    def read_tracker_data(self):
        self.ensure_one()
        company = self.company_id
        headers = {"Content-Type":"application/json","User-Agent":"Odoo/16"}
        data = {"hash":company.gps_hash,"tracker_id":self.tracker_id}
        _logger.info(str(data))
        result = {"status":404}
        try:
            response = requests.post(company.gps_url+"/tracker/read",headers=headers,json=data)
            response.raise_for_status()
            result = response.json()
        except requests.exceptions.RequestException as e:
            _logger.info(f"Error: {str(e)}")
        data = result['value']
        self.name = data['label']
        self.device_id = data['source']['device_id']
        self.blocked = data['source']['blocked']
        self.creation_date = data['source']['creation_date']
        self.model = data['source']['model']
        self.tariff_date_due = data['source']['tariff_end_date']
        self.phone = data['source']['phone']
        self.last_sync_date = datetime.now()
        self.group_id = self.get_group(data['group_id'])
        self.gc_response = 'Actualizando: '+str(result)
        self.write({'tag_ids':[(6,0,self.get_tags(data['tag_bindings']))]})
        #_logger.info("Resultado o respuesta: "+str(result))

    def get_last_location(self):
        self.ensure_one()
        company = self.company_id
        headers = {"Content-Type":"application/json","User-Agent":"Odoo/16"}
        data = {"hash":company.gps_hash,"tracker_id":self.tracker_id}
        _logger.info(str(data))
        result = {"status":404}
        try:
            response = requests.post(company.gps_url+"/tracker/get_last_gps_point",headers=headers,json=data)
            response.raise_for_status()
            result = response.json()
        except requests.exceptions.RequestException as e:
            _logger.info(f"Error: {str(e)}")
        if response.status_code == 200:
            data = result.get('value')
            self.lat = data.get('lat')
            self.long = data.get('lng')
            self.presition = data.get('precision')
            self.satellites = data.get('satellites')
            gmt6 = pytz.timezone("Etc/GMT+6")
            local_date = gmt6.localize(datetime.strptime(data.get('get_time'),"%Y-%m-%d %H:%M:%S"))
            utc_date = local_date.astimezone(pytz.utc)
            self.date_position = utc_date.replace(tzinfo=None)
            self.heading = data.get('heading')
            self.speed = data.get('speed')
            self.gc_response = 'Última ubicación: '+str(data)
            _logger.info("Respuesta: "+str(result))
    

'''class sv_employee(models.Model):
    _inherit = 'hr.employee'

    tracker_id = fields.Many2one(comodel_name = 'sv.tracker',string="Rasteador asociado")

    def show_tracker(self):
        self.ensure_one()
        return{
            'type':'ir.actions.act_window'
            ,'name':'Rastreador asignado'
            ,'view_mode':'tree,form'
            ,'res_model':'sv.tracker'
            ,'domain':[('id','=',self.tracker_id.id)]
            ,'context':"{'create':False}"
        }'''