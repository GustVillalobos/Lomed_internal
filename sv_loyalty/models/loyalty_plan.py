# -*- coding: utf-8 -*-
##############################################################################
#
#    Odoo
#
##############################################################################
import base64
import time
from datetime import datetime,date,time
from odoo import api, fields, models,_
from odoo.exceptions import UserError,ValidationError
import pytz
import logging
_logger = logging.getLogger(__name__)


class LoyaltyPlan(models.Model):
    _name='loyalty.plan'
    _inherit = ['mail.thread']
    _description = 'Plan de fidelización'

    name = fields.Char("Plan")
    active = fields.Boolean("Activo",default=True)
    code = fields.Char("Referencia")
    start = fields.Date("Inicia")
    end = fields.Date("Termina")
    partner_ids = fields.One2many(string="Participantes",comodel_name='res.partner',inverse_name='plan_id')
    rank_ids = fields.One2many(string="Rangos asociados",comodel_name='loyalty.plan.rank',inverse_name='plan_id')
    rank_count = fields.Integer(string="Total rangos",compute='_commpute_rank_count')
    partner_count = fields.Integer(string="Total participantes",compute='_commpute_partner_count')
    note = fields.Html("Notas")
    use_points = fields.Boolean(string="Usa sistema de puntos")
    mode = fields.Selection([
        ('none','Sin conteo'),
        ('point_pd','Punto por dolar'),
        ('point_pa','Punto por monto'),
        ('point_pp','Punto por producto'),
        ('point_po','Punto por orden'),
        ],default="none",string="Método de acumulación")
    config_line_ids = fields.One2many(comodel_name='loyalty.plan.point_system',string="Lineas de configuración",inverse_name='plan_id')

    @api.depends('rank_ids')
    def _commpute_rank_count(self):
        for r in self:
            res = 0
            if r.rank_ids:
                res = len(r.rank_ids)
            r.rank_count = res
    
    @api.depends('partner_ids')
    def _commpute_partner_count(self):
        for r in self:
            res = 0
            if r.partner_ids:
                res = len(r.partner_ids)
            r.partner_count = res

    def get_rank_list(self):
        self.ensure_one()
        ctx = {'default_plan_id':self.id}
        return{
            'type':'ir.actions.act_window'
            ,'name':'Rangos Asociados'
            ,'view_mode':'tree,form'
            ,'res_model':'loyalty.plan.rank'
            ,'domain':[('plan_id','=',self.id)]
            ,'context':ctx
        }

    def get_partner_list(self):
        ctx = {'create':False}
        return{
            'type':'ir.actions.act_window'
            ,'name':'Miembros del plan'
            ,'view_mode':'kanban,tree,form'
            ,'res_model':'res.partner'
            ,'domain':[('plan_id','=',self.id)]
            ,'context':ctx
        }
    
    @api.model
    def create(self,vals):
        try:
            plan = super(LoyaltyPlan,self).create(vals)
            plan.code = 'LP'+str(plan.id).zfill(6)
        except Exception as e:
            raise ValidationError('Error al crear código: '+str(e))
        return plan
    
    def enable_point_system(self):
        self.ensure_one()
        if self.config_line_ids:
            self.clean_config_line()
        if not self.use_points:
            self.use_points = True

    def diable_point_system(self):
        self.ensure_one()
        if self.config_line_ids:
            self.clean_config_line()
        if not self.use_points:
            self.use_points = True
    
    def clean_config_line(self):
        self.ensure_one()
        self.config_line_ids = [(5, 0, 0)]
    
class LoyaltyPlanRank(models.Model):
    _name = 'loyalty.plan.rank'
    _description = 'Rango'

    name = fields.Char("Rango")
    active = fields.Boolean("Activo",related='plan_id.active',store="True")
    plan_id = fields.Many2one(string="Plan de fidelización",comodel_name='loyalty.plan')
    benefit_ids = fields.One2many(string="Beneficios aplicables",comodel_name='loyalty.plan.benefit',inverse_name='rank_id')
    partner_ids = fields.One2many(string="Miembros",comodel_name='res.partner',inverse_name='rank_id')
    partner_count = fields.Integer(string="Total participantes",compute='_commpute_partner_count')

    @api.depends('partner_ids')
    def _commpute_partner_count(self):
        for r in self:
            res = 0
            if r.partner_ids:
                res = len(r.partner_ids)
            r.partner_count = res

    def get_partner_list(self):
        ctx = {'create':False}
        return{
            'type':'ir.actions.act_window'
            ,'name':'Clientes en rango'
            ,'view_mode':'kanban,tree,form'
            ,'res_model':'res.partner'
            ,'domain':[('rank_id','=',self.id)]
            ,'context':ctx
        }
    
class LoyaltyPlanBenefits(models.Model):
    _name = 'loyalty.plan.benefit'
    _decription = 'Beneficios'

    name = fields.Char("Beneficio")
    active=fields.Boolean("Activo",related="rank_id.plan_id.active",store=True)
    type = fields.Selection(selection=[
        ('expense','Inversion'),
        ('rectification','Rectificaciones'),
        ('courtesy','Cortesias'),
        ('price','Precios especiales'),
        ('event','Evento'),
        ('promo','Promoción')
    ],default='expense',string="Tipo")
    rank_id = fields.Many2one(string="Rango",comodel_name='loyalty.plan.rank')
    note = fields.Html("Nota")
    quantity = fields.Integer("Cantidad")
    requirement = fields.Float("Monto mínimo")
    aplicable_products = fields.Many2many(string="Cortesias",comodel_name='product.template',domain="[('categ_id.available_in_plan','=',True)]")
    optional_discount = fields.Float("Descuento opcional")
    price_list_ids = fields.One2many(string="Precios especiales",comodel_name='loyalty.plan.price_list',inverse_name='benefit_id')
    #promo_product_id = fields.Many2one(string="Producto promo",comodel_name='product.template')


class LoyaltyPlanPriceList(models.Model):
    _name = 'loyalty.plan.price_list'
    _description = 'Plan de precios'

    name = fields.Char("Descripción",related='product_tmpl_id.name',store=True)
    active = fields.Boolean("Activo",related='benefit_id.rank_id.plan_id.active',store=True)
    product_tmpl_id = fields.Many2one(string="Producto",comodel_name='product.template',domain="[('categ_id.available_in_plan','=',True)]")
    fixed_price = fields.Float("Precio especial")
    benefit_id = fields.Many2one(string="Beneficio",comodel_name='loyalty.plan.benefit')
    start = fields.Date(string="Desde")
    end = fields.Date(string="Hasta")

class LoyaltyPlanPartnerBenefit(models.Model):
    _name = 'loyalty.plan.partner_benefit'
    _description = 'Beneficios de cliente'

    name = fields.Char("Beneficio",related='benefit_id.name',store=True)
    active = fields.Boolean("Activo",default=True)
    parent_active = fields.Boolean("Estado del beneficio",related='benefit_id.rank_id.plan_id.active',store="True")
    benefit_id = fields.Many2one(string="Beneficio",comodel_name='loyalty.plan.benefit')
    benefit_type = fields.Selection(string="Tipo de beneficio",related='benefit_id.type')
    state = fields.Selection(selection=[
        ('available','Disponible'),
        ('assigned','Asignado'),
        ('done','Consumido'),
        ('cancel','Cancelado')
    ],default="available",string="Estado")
    partner_id = fields.Many2one(string="Contacto",comodel_name='res.partner')
    document = fields.Binary(string="Documento",attachment=True)
    file_name = fields.Char("Nombre archivo")
    event_id = fields.Many2one(string="Evento",comodel_name='calendar.event')
    product_tmpl_id = fields.Many2one(string="Producto",comodel_name='product.template',domain="[('categ_id.available_in_plan','=',True)]")
    min_qty = fields.Integer("Cantidad minima")
    pricelist_rule_id = fields.Many2one(string="Regla de precio",comodel_name='product.pricelist.item')

    def action_assign_benefit(self):
        self.ensure_one()
        date_start = self.benefit_id.rank_id.plan_id.start
        date_end = self.benefit_id.rank_id.plan_id.end
        if self.state == 'done':
            raise UserError("No se puede habilitar un beneficio ya consumido")
        if date_start > date.today():
            raise UserError(f"No es posible asignar los beneficios hasta el día {date_start.strftime('%d-%m-%Y')}")
        if date_end < date.today():
            raise UserError(f"La fecha limite para asignar beneficios fue {date_end.strftime('%d-%m-%Y')}")
        self.state = 'assigned'
    
    def action_complete_benefit(self):
        self.ensure_one()
        if self.benefit_id and self.benefit_id.type == 'expense':
            if not self.document:
                raise UserError("No ha subido comprobante del consumo del beneficio")
        elif self.benefit_id and self.benefit_id.type == 'event':
            if not self.event_id:
                raise UserError('No ha programado evento para dar por consumido el beneficio')
        if self.benefit_id and self.benefit_id.type == 'price':
            if not self.benefit_id.price_list_ids:
                raise UserError("No ha configurado los precios de beneficio")
            if not self.partner_id.property_product_pricelist:
                raise ValidationError(f"El contacto {self.partner_id.name} no posee una lista de precios configurada")
            if not self.partner_id.property_product_pricelist.is_public:
                for sp in self.benefit_id.price_list_ids:
                    exist = self.partner_id.property_product_pricelist.item_ids.filtered(lambda ppi:ppi.compute_price == 'fixed' and ppi.applied_on == '1_product' and ppi.product_tmpl_id.id == sp.product_tmpl_id.id)
                    if not exist:
                        ppi = {}
                        ppi['pricelist_id'] = self.partner_id.property_product_pricelist.id
                        ppi['compute_price'] = 'fixed'
                        ppi['fixed_price'] = sp.fixed_price
                        ppi['applied_on'] = '1_product'
                        ppi['product_tmpl_id'] = sp.product_tmpl_id.id
                        if sp.start:
                            ppi['date_start'] = self.get_utc_date(sp.start,time(0,0,0))
                        if sp.end:
                            ppi['end'] = self.get_utc_date(sp.end,time(23,59,59))
                        try:
                            prod_pricelist_item = self.env['product.pricelist.item'].create(ppi)
                            self.pricelist_rule_id = prod_pricelist_item.id
                        except Exception as e:
                            raise ValidationError("Error al crear item: "+str(e))
                    else:
                        exist.prev_fixed_price = exist.fixed_price
                        exist.fixed_price = sp.fixed_price
                        if sp.start:
                            exist.date_start = self.get_utc_date(sp.start,time(0,0,0))
                        if sp.end:
                            exist.date_end = self.get_utc_date(sp.end,time(23,59,59))
                        self.pricelist_rule_id = exist.id
        self.state = 'done'

    def get_utc_date(self,date,time_set):
        self.ensure_one()
        tz = pytz.timezone(self.env.user.tz)
        source = datetime.combine(date,time_set)
        local = tz.localize(source)
        utc_date = local.astimezone(pytz.utc)
        return utc_date.replace(tzinfo=None)

    def action_cancel_benefit(self):
        self.ensure_one()
        if self.state == 'done':
            raise UserError("No se puede cancelar un beneficio ya consumido")
        self.state = 'cancel'
    
    @api.onchange('parent_active')
    def verify_state(self):
        for r in self:
            res = True
            if r.state != 'done':
                res = False
            r.active = res