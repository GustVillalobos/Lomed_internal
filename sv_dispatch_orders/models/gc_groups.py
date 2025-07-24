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

class gc_group(models.Model):
    _name='gc.group'
    _description = 'Grupo GPS'

    name = fields.Char("Grupo")
    gc_id = fields.Integer("Identificador GlobalCom")
    color = fields.Char("Color",default="#CCCCCC")
    gc_response = fields.Text("Respuesta API")
    last_sync = fields.Datetime("Última sincronización")
    active = fields.Boolean("Activo",default=True)

    def update_list(self):
        company = self.get_company()
        data = {"hash":company.gps_hash}
        try:
            response = requests.post(company.gps_url+'/tracker/group/list',headers=self.get_header(),json=data)
            response.raise_for_status()
            result = response.json()
        except requests.exceptions.RequestException as e:
                result = f"Error: {str(e)}"
                _logger.info(result)
        for data in result['list']:
            exist = self.env['gc.group'].search([('gc_id','=',data['id'])])
            if not exist:
                new_group={}
                new_group['name'] = data['title']
                new_group['gc_id'] = data['id']
                new_group['color'] = data['color']
                new_group['last_sync'] = datetime.now()
                new_group['gc_response'] = 'Listando: '+str(data)
                try:
                    self.env['gc.group'].create(new_group)
                except Exception as e:
                     _logger.info('Error: '+str(e))
            else:
                exist.name = data['title']
                exist.color = data['color']
                exist.last_sync = datetime.now()
                exist.gc_response = 'Listando: '+str(data)
    
    def update_list_reload(self):
        self.update_list()
        return{
            'type':'ir.actions.client',
            'tag':'reload',
        }

    def upload_group(self):
        self.ensure_one()
        company = self.get_company()
        new_group = {"hash":company.gps_hash,
                     "title":self.name,
                     "color":self.color.replace('#','')}
        #_logger.info(str(new_group))
        try:
            response = requests.post(company.gps_url+'/tracker/group/create',headers=self.get_header(),json=new_group)
            response.raise_for_status()
            result = response.json()
        except requests.exceptions.RequestException as e:
                result = f"Error: {str(e)}"
                _logger.info(result)
        if response.status_code == 200:
             self.gc_id = result.get('id')
             self.gc_response = 'Creando: '+str(result)
             return {
                  'type':'ir.actions.client',
                  'tag': 'display_notification',
                  'params':{
                       'title':'¡Exito!',
                       'type':'success',
                       'message':'Grupo creado exitosamente',
                       'sticky':False,
                  }
             }
    
    def update_group(self):
        self.ensure_one()
        company = self.get_company()
        group = {"hash":company.gps_hash,
                    "id":self.gc_id,
                    "title":self.name,
                    "color":self.color.replace('#','')}
        try:
            response = requests.post(company.gps_url+'/tracker/group/update',headers=self.get_header(),json=group)
            response.raise_for_status()
            result = response.json()
        except requests.exceptions.RequestException as e:
                result = f"Error: {str(e)}"
                _logger.info(result)
        if response.status_code == 200:
             self.gc_response = 'Editando: '+str(result)
        return{
             'type':'ir.actions.client',
             'tag': 'display_notification',
             'params':{
                  'title':'¡Exito!',
                  'type':'success',
                  'message':'Cambios guardados correctamente',
                  'sticky':False,
             }
        }
    
    def delete_group(self):
        self.ensure_one()
        company = self.get_company()
        group = {"hash":company.gps_hash,
                    "id":self.gc_id}
        try:
            response = requests.post(company.gps_url+'/tracker/group/delete',headers=self.get_header(),json=group)
            response.raise_for_status()
            result = response.json()
        except requests.exceptions.RequestException as e:
            result = f"Error: {str(e)}"
            _logger.info(result)
        if response.status_code == 200:
            self.active = False
            self.gc_id = 0
            self.gc_response = 'Eliminando: '+str(result)
        return{
             'type':'ir.actions.client',
             'tag': 'display_notification',
             'params':{
                  'title':'¡Exito!',
                  'type':'success',
                  'message':'Registro eliminado con éxito',
                  'sticky':False,
             }
        }
    
    def get_header(self):
         return {"Content-Type":"application/json","User-Agent":"Odoo/16"}
    
    def get_company(self):
        company = self.env['res.company'].browse(self.env.context['allowed_company_ids'][0])
        if not company.gps_hash:
            raise UserError('No hay un hash para realizar la conección')
        if not company.gps_url:
            raise UserError('No hay una URL a la que realizar la conección')
        return company