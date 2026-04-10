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

class PrintContractEmployee(models.Model):
    _inherit = 'hr.employee'

    is_legal_representative = fields.Boolean(string="Representante legal")

    def _unset_other_legal_representative(self):
        for record in self:
            if record.is_legal_representative:
                others = self.env['hr.employee'].search([
                    ('id','!=',record.id),
                    ('company_id','=',record.company_id.id),
                    ('is_legal_representative','=', True)
                ])
                if others:
                    others.write({'is_legal_representative':False})
    
    def write(self,vals):
        res = super().write(vals)
        if vals.get('is_legal_representative'):
            self._unset_other_legal_representative()
        return res

class PrintContractHrContract(models.Model):
    _inherit = 'hr.contract'

    def action_print_contract(self):
        self.ensure_one()
        report = self.env.ref('print_contract.contract_report')
        return report.with_context(lang='es_ES').report_action(self)
    
    def get_legal_representative(self):
        legal_representative = self.env['hr.employee'].search([('company_id','=',self.company_id.id),('is_legal_representative','=',True)],limit = 1)
        return legal_representative

class PrintContractHrDepartment(models.Model):
    _inherit = 'hr.department'

    valid_schedules = fields.Html("Horarios disponibles")
    
class PrintContractHrJob(models.Model):
    _inherit = 'hr.job'

    contract_equipment = fields.Html("Equipos relacionados")
