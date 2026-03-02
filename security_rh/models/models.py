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
from odoo.exceptions import AccessError
import logging
_logger = logging.getLogger(__name__)

class SecurityRhHrContract(models.Model):
    _inherit = 'hr.contract'

    copy_wage = fields.Monetary(string="Salario (solo lectura)",compute='_compute_copy_wage')

    @api.depends('wage')
    def _compute_copy_wage(self):
        for record in self:
            record.copy_wage = record.wage
    
    def write(self,vals):
        if 'wage' in vals:
            if not self.env.user.has_group('security_rh.wage_admin_group'):
                raise AccessError("No tiene permiso para modificar salarios")
        for contract in self:
            company = contract.company_id
            sensitive_fields = company.sensitive_fields_ids.mapped('name')

            modified_sensitive = set(vals.keys() & set(sensitive_fields))
            if not modified_sensitive:
                continue
            if not self.env.user.has_group('security_rh.sensitive_fields_group'):
                raise AccessError("No tiene permitido modificar campos sensibles de los contratos")
            
            changes = []
            for field in company.sensitive_fields_ids.filtered(lambda f: f.name in modified_sensitive):
                if not field.tracking:
                    old_value = getattr(contract, field.name)
                    new_value = vals[field.name]

                    old_str = self._get_formatted_value(field,old_value)
                    new_str = self._get_formatted_value(field,new_value)
                    changes.append(f"<li><span style='font-weight:550'>{old_str}  → </span> <span style='color:teal;font-weight:550'>{new_str}</span>  <i style='font-weiht:100'>({field.field_description or field.display_name})</i></li>")

            if changes:
                body = (
                    f"Cambios detectados:<br/><ul>{' '.join(changes)}</ul>"
                )
            contract.message_post(
                body=body,
                message_type="comment",
                subtype_xmlid="mail.mt_note",
            )

        result = super().write(vals)
        return result
    
    def _get_formatted_value(self,field, value):
        if field.ttype in ('char','text','integer','float','monetary'):
            return str(value)
        
        if field.ttype == 'boolean':
            return "Sí" if value else "No"
        
        if field.ttype == 'selection':
            selection_dict = dict(field.selection)
            return selection_dict.get(value,str(value))

        if field.ttype == 'many2one':
            if isinstance(value,models.BaseModel):
                return value.display_name or ''
            elif isinstance(value,int):
                record = self.env[field.relation].browse(value)
                return record.display_name or ''
        
        if field.ttype in ('many2many','one2many'):
            if isinstance(value,models.BaseModel):
                return ', '.join(value.mapped('display_name'))
            elif isinstance(value,list):
                records = self.env[field.relation].browse(value)
                return ', '.join(records.mapped('display_name'))

class SecurityRhCompany(models.Model):
    _inherit = 'res.company'

    sensitive_fields_ids = fields.Many2many(
        'ir.model.fields',
        'company_sensitive_contract_field_rel',
        'company_id',
        'field_id',
        string="Campos sensibles en contratos",
        domain = [('model','=','hr.contract')],
        help="Campos del contrato que solo pueden ser modificados por el grupo autorizado."
    )