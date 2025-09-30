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



class ResPartnerPlan(models.Model):
    _inherit = 'res.partner'

    plan_id = fields.Many2one(string="Plan",comodel_name='loyalty.plan')
    rank_id = fields.Many2one(string="Rango",comodel_name='loyalty.plan.rank',domain="[('plan_id','=',plan_id)]")
    benefit_ids = fields.One2many(string="Beneficios",comodel_name='loyalty.plan.partner_benefit',inverse_name='partner_id')

    @api.depends('plan_id')
    def _compute_rank_ids(self):
        for r in self:
            res = []
            if r.plan_id:
                for rk in r.plan_id.rank_ids:
                    res.append(rk.id)
            r._rank_ids = [(6,0,res)]
    
    def write(self,vals):
        partner = super(ResPartnerPlan,self).write(vals)
        if 'rank_id' in vals:
            _logger.info("partner_id: "+str(self.id))
            lines = self.env['loyalty.plan.partner_benefit'].search([('partner_id','=',self.id),('benefit_id.rank_id','!=',vals.get('rank_id')),('state','!=','done')])
            rank = self.env['loyalty.plan.rank'].browse(int(vals.get('rank_id')))
            if lines:
                lines.unlink()
            for rb in rank.benefit_ids:
                self.create_partner_benefit(rb)
        return partner
    
    def create_partner_benefit(self,rb):
        benefit = {}
        benefit['name'] = rb.name
        benefit['benefit_id']=rb.id
        benefit['state'] = 'available'
        benefit['partner_id'] = self.id
        try:
            self.env['loyalty.plan.partner_benefit'].create(benefit)
        except Exception as e:
            raise UserError('Error al crear beneficio: '+str(e))
    
    def action_show_points(self):
        self.ensure_one()
        ctx = {'default_partner_id':self.id}
        return{
            'name':_('Puntos acumulados'),
            'type': 'ir.actions.act_window',
            'view_mode':'form',
            'res_model':'loyalty.plan.resume_wizard',
            'target':'new',
            'view_id':self.env.ref('sv_loyalty.wizard_compute_point_form_view').id,
            'context':ctx
        }


class ProductPriceListPlan(models.Model):
    _inherit = 'product.pricelist'

    is_public = fields.Boolean("Es lista pública")

class ProductPriceListItemPlan(models.Model):
    _inherit = 'product.pricelist.item'
    
    prev_fixed_price = fields.Float("Precio anterior")

    def reset_fixed_price(self):
        self.ensure_one()
        self.fixed_price = self.prev_fixed_price
        self.prev_fixed_price = 0

class ProductCategoryPlan(models.Model):
    _inherit = 'product.category'

    available_in_plan = fields.Boolean("Disponible para plan de fidelización")