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

class gc_tags(models.Model):
    _name = 'gc.tag'
    _description = 'Etiquetas GPS'

    name = fields.Char("Etiqueta")
    color = fields.Char("Color",default='#CCCCCC')
    gc_id = fields.Integer("Identificador GlobalCom")
    gc_response = fields.Text("Respuesta API")
    last_sync = fields.Datetime("Última sincronización")
    active = fields.Boolean("Activo",default=True)

    def update_tag_list(self):
        company = self.get_company()
        data = {"hash":company.gps_hash}
        try:
            response = requests.post(company.gps_url+'/tag/list',headers=self.get_header(),json=data)
            response.raise_for_status()
            result = response.json()
            #_logger.info(result)
        except requests.exceptions.RequestException as e:
            _logger.info(f"Error: {str(e)}")
        if result['list']:
            for data in result['list']:
                exist = self.env['gc.tag'].search([('gc_id','=',data.get('id'))])
                if not exist:
                    tag = {}
                    tag['gc_id'] = data.get('id')
                    tag['name'] = data.get('name')
                    tag['color'] = data.get('color')
                    tag['gc_response'] = 'Listando: '+str(data)
                    tag['last_sync'] = datetime.now()
                    try:
                        self.env['gc.tag'].create(tag)
                    except Exception as e:
                        raise UserError(f"Error: {str(e)}")
                else:
                    exist.name = data.get('name')
                    exist.color = data.get('color')
                    exist.gc_response = 'Listando: '+str(data)
                    exist.last_sync = datetime.now()

    def update_reload_tag_list(self):
        self.update_tag_list()
        return{
            'type':'ir.actions.client',
            'tag':'reload',
        }
    
    def upload_tag(self):
        self.ensure_one()
        company = self.get_company()
        tag = {'hash':company.gps_hash,'tag':{'name':self.name,'color':self.color.replace('#','')}}
        try:
            response = requests.post(company.gps_url+'/tag/create',headers=self.get_header(),json=tag)
            response.raise_for_status()
            result = response.json()
        except requests.exceptions.RequestException as e:
            _logger.info(f"Error: {str(e)}")
        if response.status_code == 200:
            self.gc_id = result.get('id')
            self.gc_response = 'Creando: '+str(result)
            return {
                  'type':'ir.actions.client',
                  'tag': 'display_notification',
                  'params':{
                       'title':'¡Exito!',
                       'type':'success',
                       'message':'Etiqueta creada exitosamente',
                       'sticky':False,
                  }
             }
    
    def update_tag(self):
        self.ensure_one()
        company = self.get_company()
        tag = {'hash':company.gps_hash,'tag':{'id':self.gc_id,'name':self.name,'color':self.color.replace('#','')}}
        try:
            response = requests.post(company.gps_url+"/tag/update",headers=self.get_header(),json=tag)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            _logger.info(str(e))
        if response.status_code == 200:
            self.gc_response = 'Editando: '+response.text
            return {
                  'type':'ir.actions.client',
                  'tag': 'display_notification',
                  'params':{
                       'title':'¡Exito!',
                       'type':'success',
                       'message':'Etiqueta actualizada exitosamente',
                       'sticky':False,
                  }
             }

    def delete_tag(self):
        self.ensure_one()
        company = self.get_company()
        tag = {'hash':company.gps_hash,'tag_id':self.gc_id}
        try:
            response = requests.post(company.gps_url+"/tag/delete",headers=self.get_header(),json=tag)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            _logger.info(f"Error: {str(e)}")
        if response.status_code == 200:
            #Borrar registro o marcar para borrar
            self.active = False
            self.gc_id = 0
            self.gc_response = 'Eliminando: '+response.text
            return {
                  'type':'ir.actions.client',
                  'tag': 'display_notification',
                  'params':{
                       'title':'¡Exito!',
                       'type':'success',
                       'message':'Etiqueta eliminada correctamente',
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