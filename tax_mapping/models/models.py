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

class FiscalDocumentTaxMap(models.Model):
    _inherit = 'odoosv.fiscal.document'

    sale_tax_id = fields.Many2one(comodel_name="account.tax",string="Impuestos de venta",domain="[('type_tax_use','=','sale'),('company_id','=',company_id)]")

class TaxMappingAccountMove(models.Model):
    _inherit = 'account.move'

    def _apply_fiscal_document_taxes(self):
        for move in self:
            if move.move_type != 'out_invoice':
                continue
            
            if move.state != 'draft':
                continue
            
            if not move.tipo_documento_id or not move.invoice_line_ids:
                continue

            base_tax = move.tipo_documento_id.sale_tax_id
            fiscal_position = move.fiscal_position_id 

            for line in move.invoice_line_ids:
                if line.display_type in ('line_note','line_section'):
                    continue
                
                if (line.tax_ids and base_tax in line.tax_ids):
                    continue
                taxes = base_tax
                if fiscal_position:
                    taxes = fiscal_position.map_tax(taxes)

                line.tax_ids = taxes
    
    @api.onchange('tipo_documento_id','fiscal_position_id')
    def _apply_changes(self):
        self._apply_fiscal_document_taxes()
    
    @api.model_create_multi
    def create(self,vals_list):
        moves = super().create(vals_list)
        moves._apply_fiscal_document_taxes()
        return moves
    
    def write(self,vals):
        result = super().write(vals)

        FIELDS_REF = {'tipo_documento_id','fiscal_position_id','document_type_id'}
        
        if FIELDS_REF.intersection(vals.keys()):
            self._apply_fiscal_document_taxes()
        
        return result
    
class TaxMappingAccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    @api.onchange('product_id')
    def _apply_tax_line(self):
        for line in self:
            if not line.move_id:
                continue
            if line.move_id.state != 'draft':
                continue
            line.move_id._apply_fiscal_document_taxes()