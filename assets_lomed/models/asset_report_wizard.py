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

class AssetsReportWizard(models.TransientModel):
    _name = 'assets.report.wizard'
    _description = 'Reporte de activos'

    name = fields.Char("Reporte")

    def _get_default_month(self):
        return str(datetime.now().month)
    
    month = fields.Selection([
        ('1','Enero'),('2','Febrero'),('3','Marzo'),('4','Abril'),
        ('5','Mayo'),('6','Junio'),('7','Julio'),('8','Agosto'),
        ('9','Septiembre'),('10','Octubre'),('11','Noviembre'),('12','Diciembre')
    ],string="Mes",default=_get_default_month, required=True)

    def _get_default_year(self):
        return datetime.now().year
    
    year = fields.Integer(string="Año",default=_get_default_year)
    include_all = fields.Boolean("Incluir activos depreciados")

    def action_print_report(self):
        return self.env.ref('assets_lomed.assets_report_action').report_action(self)

    def get_assets_list(self):
        data = {
            'report_month':int(self.month),
            'report_year': self.year,
            'include_all':self.include_all,
            'asset_json':self.env['account.asset'].get_assets(month=int(self.month),year=self.year,include_all=self.include_all)
        }
        return data