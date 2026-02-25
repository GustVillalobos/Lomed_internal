# -*- coding: utf-8 -*-
##############################################################################
#
#    Odoo
#
##############################################################################
import base64
import time
import json
from datetime import datetime,date
from odoo import api, fields, models,_
from odoo.exceptions import UserError,ValidationError
import logging
_logger = logging.getLogger(__name__)

class AccountAssetsLomed(models.Model):
    _inherit = 'account.asset'

    label = fields.Text("Etiqueta ZPL",compute='_compute_asset_label')
    barcode = fields.Char(string="Código de barras")
    responsible = fields.Char(string="Responsable")
    notes = fields.Html("Notas")
    area= fields.Char("Areá designada")
    size = fields.Char("Medidas")
    sequence_id = fields.Many2one(comodel_name='ir.sequence',string="Secuencia",help='Secuencia o correlativo de código de barra')

    def action_create_barcode(self):
        self.ensure_one()
        sequence = self.model_id.sequence_id if self.model_id.sequence_id else self.sequence_id
       
        if not sequence:
            raise UserError("No hay una secuencia definida para asignar al activo")
        if self.barcode:
            raise UserError(f"El activo {self.name} ya posee un código de barras")
        self.barcode = sequence.next_by_id()
    
    @api.depends('barcode','name')
    def _compute_asset_label(self):
        for record in self:
            text = f"CT~~CD,~CC^~CT~^XA~TA000~JSN^LT0^MNW^MTT^PON^PMN^LH0,0^JMA^PR4,4~SD15^JUS^LRN^CI0^XZ^XA^MMT^PW831^LL0200^LS0^FT17,27^A0N,20,21^FH\^FD{record.company_id.name.upper() if record.company_id else ''}^FS^BY2,3,67^FT74,136^BCN,,Y,N^FD{record.barcode}^FS^FT17,43^A0N,12,14^FH\^FD{record.responsible}^FS^FT261,184^A0N,12,14^FH\^FDActualizado el:^FS^FT328,186^A0N,14,14^FH\^FD{record.write_date.strftime('%d-%m-%Y')if record.write_date else ''}^FS^FT17,60^A0N,12,14^FH\^FD{record.model_id.name}^FS^FT457,27^A0N,20,21^FH\^FD{record.company_id.name.upper() if record.company_id else ''}^FS^BY2,3,67^FT514,136^BCN,,Y,N^FD{record.barcode}^FS^FT457,43^A0N,12,14^FH\^FD{record.responsible}^FS^FT701,184^A0N,12,14^FH\^FDActualizado el:^FS^FT768,186^A0N,14,14^FH\^FD{record.write_date.strftime('%d-%m-%Y') if record.write_date else ''}^FS^FT457,60^A0N,12,14^FH\^FD{record.model_id.name}^FS^PQ1,0,1,Y^XZ"
            record.label = text

    def print_label(self):
        self.ensure_one()
        return{
            "type":"ir.actions.client",
            "tag":"print_label_action",
            "context":{"zpl":self.label}
        }
    
    def get_assets(self,month=datetime.now().month,year=datetime.now().year,include_all=False):
        domain = [('state','=','open')]
        if not include_all:
            domain.append(('value_residual','!=',0))
        report_data={}
        report_data['asset_list'] = self.get_records(domain=domain,month=month,year=year)
        return report_data
    
    def get_records(self,domain,month,year):
        assets = self.env['account.asset'].search(domain)
        record_list = []
        for asset in assets:
            line = self.get_depreciation_line(asset,month,year)
            data = {}
            data['clasificacion_activo']=asset.model_id.name 
            data['fecha_adquisicion']=asset.acquisition_date.strftime("%d/%m/%Y")
            data['nombre_activo']=asset.name
            data['depreciacion']=self.get_depreciation_percent(asset)
            data['valor_adquisicion']=asset.original_value 
            data['depreciacion_acumulada']= line.asset_depreciated_value - line.depreciation_value if line else 0 
            data['cuota_mensual']= line.depreciation_value if line else 0 
            data['acumulado_mes']= line.asset_depreciated_value if line else 0 
            data['analitica']= self.env['account.analytic.account'].browse(line.analytic_distribution.get('100')) if line.analytic_distribution.get('100') else False
            data['responsable'] = asset.responsible
            record_list.append(data)
        return record_list
    
    def get_depreciation_percent(self,asset):
        years = 0
        if asset.method_period in (1,'1'):
            years = asset.method_number/12
        else:
            years = asset.method_number
        return str(100/years)+'%'
    
    def get_depreciation_line(self,asset,month,year):
        res = 0
        line = asset.depreciation_move_ids.filtered(lambda ln:ln.date.month == month and ln.date.year == year)
        return line[0] if line else False
