# -*- coding: utf-8 -*-
##############################################################################
#
#    Odoo
#
##############################################################################
import logging
import time
from datetime import datetime,timedelta
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models,_
from odoo.exceptions import ValidationError,UserError
_logger = logging.getLogger(__name__)

class sv_route(models.Model):
    _name='sv.route'
    #_inherit=['mail.thread']
    _description='Rutas programadas'

    name = fields.Char("Nombre",copy=False)
    code = fields.Char("Código",copy=False)
    employee_id = fields.Many2one(comodel_name='hr.employee',string="Mensajero preferido",copy=False)
    route_dispatch_ids = fields.One2many(comodel_name='sv.route.dispatch',inverse_name='route_id',string="Todas las rutas asociadas")
    route_dispatch_count = fields.Integer("Rutas totales",copy=False,store=False,compute='compute_total_routes')
    active_routes = fields.Integer("Rutas activas",copy=False,store=False,compute='compute_active_routes')
    tour_date = fields.Date(string="Último recorrido",copy=False,store=True,compute='compute_tour_date')
    active = fields.Boolean("Activo",default=True)
    department_id = fields.Integer("Departamento",compute='compute_department_id')

    @api.depends('route_dispatch_ids')
    def compute_total_routes(self):
        for r in self:
            r.route_dispatch_count = len(r.route_dispatch_ids)

    @api.depends('route_dispatch_ids')
    def compute_active_routes(self):
        for r in self:
            active_routes = r.route_dispatch_ids.filtered(lambda r: r.state in ('confirm','progress'))
            if active_routes:
                r.active_routes = len(active_routes)
            else:
                r.active_routes = 0

    @api.depends('route_dispatch_ids')
    def compute_tour_date(self):
        for r in self:
            last_record = False
            if len(r.route_dispatch_ids)>=1:
                last_record = r.route_dispatch_ids[-1]
            if last_record:
                r.tour_date = last_record.dispatch_date
            else:
                r.tour_date = False
        
    def get_active_route_list(self):
        self.ensure_one()
        return{
            'type':'ir.actions.act_window'
            ,'name':'Despachos activos'
            ,'view_mode':'tree,form'
            ,'res_model':'sv.route.dispatch'
            ,'domain':[('state','in',('confirm','progress')),('route_id','=',self.id)]
            ,'context':"{'create':False}"
        }
    
    def get_route_list(self):
        self.ensure_one()
        return{
            'type':'ir.actions.act_window'
            ,'name':'Todos los despachos'
            ,'view_mode':'tree,form'
            ,'res_model':'sv.route.dispatch'
            ,'domain':[('route_id','=',self.id)]
            ,'context':"{'create':False}"
        }
    
    def compute_department_id(self):
        for r in self:
            depart_param = r.env['ir.config_parameter'].sudo().get_param('sv_route.deapartment_ref_id')
            r.department_id = int(depart_param) if depart_param else 0

class sv_dispatch_route(models.Model):
    _name='sv.route.dispatch'
    _inherit=['barcodes.barcode_events_mixin','mail.thread']
    _description = 'Despacho de rutas'

    name = fields.Char("Ruta",copy=False,compute="compute_name",readonly=True)
    dispatch_date = fields.Date("Fecha de ruta")
    confirm_date = fields.Datetime("Fecha de confirmación",copy=False,readonly=True)
    end_date = fields.Datetime("Fecha de finalizacion",copy=False,readonly=True)
    return_date = fields.Datetime("Fecha de retorno",copy=False,readonly=True)
    code = fields.Char("Código",copy=False,readonly=True,)
    employee_id = fields.Many2one(comodel_name='hr.employee',string="Mensajero asignado")
    state = fields.Selection([
        ('draft','Borrador')
        ,('confirm','Confirmada')
        ,('progress','En entrega')
        ,('close','Cerrada')
        ,('done','Recibida')
        ,('cancel','Cancelada')
        ],default='draft',string="Tipo de ruta")
    type_order = fields.Selection([
        ('Global','Global')
        ,('Lentexpress','Lentexpress')
        ,('Laboratorio','Laboratorio')
    ],default='Laboratorio',string="Tipo de orden")
    type = fields.Selection([
        ('AM','AM')
        ,('PM','PM')
        ,('Express','Express')
    ],default='AM',string="Tipo de ruta")
    route_id = fields.Many2one(comodel_name='sv.route',string="Ruta")
    order_count = fields.Integer("Cantidad de ordenes",compute='compute_order_qty',copy=False,store=True)
    client_count = fields.Integer("Cantidad de clientes",compute='compute_client_qty',copy=False,store=True)
    route_line_ids = fields.One2many(comodel_name='sv.route.dispatch.line',inverse_name='dispatch_route_id',string="Lineas de ruta")
    total_delivered = fields.Integer("Ordenes entregadas",copy=False,compute='compute_total_delivered')
    total_rejected = fields.Integer("Ordenes rechazadas",compute='compute_total_rejected',copy=False)
    total_pending = fields.Integer("Ordenes pendientes",compute='compute_total_pending',copy=False)
    total_devolution = fields.Integer("Devoluciones",compute='compute_total_devolution',copy=False)
    devolution_line_ids = fields.Many2many('sale.order','sv_route_dispath_sale_order_rel','route_disp_id','sale_order_id',string="Devoluciones")
    clear_fields = fields.Boolean(string="Limpiar Campos",compute='compute_clean_field',copy=False)
    department_id = fields.Integer("Departamento",compute='compute_department_id')
    color = fields.Integer(string="Color",compute='get_color')
    vehicle_id = fields.Many2one(comodel_name='fleet.vehicle',string="Vehiculo asignado",copy=False)

    @api.depends('dispatch_date','route_id','type','code','type_order')
    def compute_name(self):
        for r in self:
            type_order_name = r.type_order if r.type_order else ''
            route_name = r.route_id.name if r.route_id and r.route_id.name else 'RUTA_'
            disp_date = r.dispatch_date if r.dispatch_date else datetime.today()
            route_type = r.type if r.type and r.type else datetime.now().strftime('%p')
            display_name = '{0}[{1}] {2}/{3}'
            r.name = display_name.format(type_order_name.upper(),disp_date.strftime("%d/%m/%Y"),route_name.upper(),route_type)
    
    @api.depends('route_line_ids')
    def compute_order_qty(self):
        for r in self:
            r.order_count = len(r.route_line_ids)
    
    @api.depends('route_line_ids')
    def compute_client_qty(self):
        for r in self:
            client_list = r.route_line_ids.mapped('partner_id')
            r.client_count = len(client_list) if client_list else 0
    
    @api.depends('route_line_ids')
    def compute_total_delivered(self):
        for r in self:
            order_delivered = r.route_line_ids.filtered(lambda l:l.delivery_status == 'delivered')
            r.total_delivered = len(order_delivered)
            r.verify_state()

    @api.depends('route_line_ids')
    def compute_total_rejected(self):
        for r in self:
            order_rejected = r.route_line_ids.filtered(lambda l:l.delivery_status == 'rejected')
            r.total_rejected = len(order_rejected)
            r.verify_state()
    
    @api.depends('route_line_ids')
    def compute_total_pending(self):
        for r in self:
            order_pending = r.route_line_ids.filtered(lambda l:l.delivery_status in ('pending','forward'))
            r.total_pending = len(order_pending)
    
    @api.depends('devolution_line_ids')
    def compute_total_devolution(self):
        for r in self:
            r.total_devolution = len(r.devolution_line_ids)
    
    def compute_clean_field(self):
        for r in self:
            res = False
            clean_parameter = self.env['ir.config_parameter'].sudo().get_param('sv_route.clear_fields')
            if clean_parameter == 'True':
                res = True
            r.clear_fields = res

    def button_confirm_route(self):
        self.ensure_one()
        max_days = self.get_max_days()
        today = datetime.now()
        if not self.dispatch_date:
            self.dispatch_date = today.date()
        if len(self.route_line_ids) <= 0:
            raise UserError('Debe agregar por lo menos 1 pedido para entregar')
        if (self.dispatch_date - today.date()).days > max_days:
            raise ValidationError(f'No puedes confirmar rutas con mas de {max_days} días de anticipación')
        if not self.code:
            rec_id = str(self.id).zfill(6)
            self.code = today.strftime("%y%m")+rec_id
        if not self.confirm_date:
            self.confirm_date=datetime.now()
        if not self.employee_id:
            self.employee_id = self.route_id.employee_id.id
        self.state = 'confirm'
    
    def on_barcode_scanned(self,barcode):
        if not self.state or self.state == 'draft':
            exist = self.route_line_ids.filtered(lambda li: li.sale_order_id.name == barcode)
            if exist:
                raise UserError(f'La orden {exist.sale_order_id.name} ya esta agregada a esta ruta')
            order = self.env['sale.order'].search([('name','=',barcode)],limit=1)
            if order:
                if order.state == 'cancel':
                    raise UserError('La orden {order.name} está cancelada\nNo es posible agregar a ruta una orden cancelada')
                invoice = self.get_invoice(order)
                if self.type_order == 'Laboratorio' and not invoice:
                    raise ValidationError(f'La orden {order.name} no está facturada.\nLos despachos de tipo Laboratorio solo pueden contener ordenes facturadas')
                active_line = self.get_active_line(order)
                if active_line:
                    raise UserError(f'La orden {order.name} ya se encuentra pendiente de entrega en otra ruta')
                try:
                    dic={}
                    dic['dispatch_route_id'] = self.id
                    dic['sale_order_id']=order.id
                    #dic['date_order'] = order.date_order
                    dic['invoice_date'] = invoice.invoice_date if invoice else False
                    #dic['invoice_number'] = invoice.doc_numero if invoice else False
                    dic['invoice_number'] = invoice.name if invoice else False
                    self.env['sv.route.dispatch.line'].create(dic)
                except Exception as error:
                    raise ValidationError('Error al crear linea de ruta: '+str(error))
            else:
                raise UserError(f'La orden {barcode} no existe en la base de datos')
        else:
            raise UserError('No se puede añadir ordenes a un documento de ruta confirmado')
    
    def get_invoice(self,order):
        invoice_list = order.invoice_ids.filtered(lambda i:i.state=='posted' and i.move_type=='out_invoice' and i.payment_state != 'reversed')
        final_invoice = False
        deposit_id = self.get_deposit_id
        if invoice_list and len(invoice_list) > 1:
            for i in invoice_list:
                is_final = i.invoice_line_ids.filtered(lambda l: l.product_id.id == deposit_id and l.price_unit < 0)
                if is_final:
                    final_invoice = i
        elif invoice_list and len(invoice_list)==1:
            is_advance = invoice_list.invoice_line_ids.filtered(lambda l: l.product_id.id == deposit_id)
            if not is_advance:
                final_invoice = invoice_list
        
        return final_invoice
    
    def get_active_line(self,order_id):
        self.ensure_one()
        res = False
        active_line = self.env['sv.route.dispatch.line'].search([('sale_order_id','=',order_id.id),('delivery_status','=','pending'),('dispatch_route_id','!=',False)])
        if active_line:
            res = True
        return res
    
    def verify_state(self):
        self.ensure_one()
        not_pending  = self.route_line_ids.filtered(lambda l: l.delivery_status in ('delivered','rejected'))
        pending = self.route_line_ids.filtered(lambda l: l.delivery_status == 'pending')
        if self.state == 'confirm' and not_pending:
            self.state = 'progress'
        if self.state == 'progress' and not pending:
            self.state = 'close'
            self.end_date = datetime.now()

    def action_clear_fields(self):
        self.ensure_one()
        if self.route_line_ids:
            self.route_line_ids.unlink()
        if self.devolution_line_ids:
            self.write({'devolution_line_ids':[(6, 0, [])]})

    def button_cancel_route(self):
        self.ensure_one()
        if self.state == 'progress':
            raise UserError('Esta ruta ya posee entregas completadas no es posible cancelarla')
        if self.clear_fields:
            self.action_clear_fields()
        self.end_date = datetime.now()
        self.state = 'cancel'
    
    def button_draft_route(self):
        self.ensure_one()
        if self.state != 'confirm':
            raise UserError('Esta ruta ya posee entregas completadas no es posible cambiarla a borrador')
        if self.clear_fields:
            self.action_clear_fields()
        self.confirm_date = False
        self.state = 'draft'
    
    def button_complete_dispatch(self):
        self.ensure_one()
        if self.state != 'close':
            raise UserError('No se puede completar una ruta que no está cerrada')
        self.return_date = datetime.now()
        self.state = 'done'

    @api.depends('name')
    def compute_department_id(self):
        for r in self:
            depart_param = r.env['ir.config_parameter'].sudo().get_param('sv_route.deapartment_ref_id')
            r.department_id = int(depart_param) if depart_param else 0
    
    def print_dispatch_report(self):
        self.ensure_one()
        return self.env.ref('sv_dispatch_orders.dispatch_report_sv').report_action(self)
    
    def print_settlement_report(self):
        self.ensure_one()
        return self.env.ref('sv_dispatch_orders.settlement_report_sv').report_action(self)
    
    def get_employee_in_charge(self):
        self.ensure_one()
        r = self
        employee = False
        employee_param = r.env['ir.config_parameter'].sudo().get_param('sv_route.employee_in_charge')
        if employee_param:
            employee = r.env['hr.employee'].browse(int(employee_param))
        return employee 
    
    def get_max_days(self):
        res = 0
        parameter = self.env['ir.config_parameter'].sudo().get_param('sv_route.max_days')
        if parameter:
            res = int(parameter)
        return res
    
    def get_deposit_id(self):
        res = 123506
        param = self.env['ir.config_parameter'].sudo().get_param('sale.default_deposit_product_id')
        if param:
            res = int(param)
        return res
    
    def write(self,vals):
        if vals.get('type_order') == 'Laboratorio':
            not_invoice = self.route_line_ids.filtered(lambda lr:lr.invoice_number == False or lr.invoice_date==False)
            if not_invoice:
                raise UserError('Los despachos de tipo Laboratorio solo pueden contener ordenes facturadas')
        res = super(sv_dispatch_route, self).write(vals)
        return res
    
    def get_color(self):
        for r in self:
            res = 4
            if r.state in ('done','close'):
                res = 10
            elif r.state == 'cancel':
                res = 1
            elif r.state in ('confirm','progess'):
                res = 3
            r.color = res


class sv_route_dispatch_line(models.Model):
    _name = 'sv.route.dispatch.line'
    _description='Lineas de despacho de ruta'

    sale_order_id = fields.Many2one(comodel_name='sale.order',string="Order de venta",copy=False)
    date_order = fields.Datetime("Fecha de pedido",copy=False,related='sale_order_id.date_order')
    invoice_date = fields.Date("Fecha factura",copy=False)
    invoice_number = fields.Char("Número de factura",copy=False)
    partner_id = fields.Many2one(string="Cliente",related='sale_order_id.partner_id')
    #patient = fields.Char(string="Paciente",related='sale_order_id.paciente')
    delivery_status = fields.Selection([
        ('pending','Esperando entrega')
        ,('delivered','Entregada')
        ,('rejected','Rechazada')
        ,('forward','Reenvio')
    ],default='pending',string="Estado")
    employee_code=fields.Char(string="Codigo de empleado",copy=False)
    employee_id=fields.Many2one(comodel_name='hr.employee',string="Empleado encargado",copy=False,compute='compute_employee_id')
    note = fields.Text("Comentarios",copy=False)
    dispatch_route_id = fields.Many2one(comodel_name='sv.route.dispatch',string="Ruta de despacho")
    effective_date = fields.Datetime("Fecha de entrega")
    use_employee_code = fields.Boolean("Codigo de empleado",compute='compute_use_employee_code')
    comment_required = fields.Boolean("Comentario requerido",compute='compute_comment_required')
    parent_state = fields.Selection(string="Estado de ruta",related='dispatch_route_id.state')
    color = fields.Integer(string="Color",compute='get_color')

    @api.depends('employee_code')
    def compute_employee_id(self):
        self.ensure_one()
        department_id = self.get_department_id()
        employee = False
        if self.employee_code:
            employee = self.env['hr.employee'].search(['|',('barcode','=',self.employee_code),('pin','=',self.employee_code)],limit=1)
        if not employee and self.employee_code:
            raise UserError(f'El código {self.employee_code} no existe o no está asociado a ningun empleado')
        if employee and employee.active == False:
            raise UserError(f'El empleado {employee.name} no está activo en la empresa')
        if employee and employee.department_id.id != department_id.id:
            raise UserError(f'El empleado {employee.name} no pertenece al departamento {department_id.name}, no tiene permitido cambiar de estado las ordenes de ruta')
        if employee:
            self.employee_id = employee.id
        else:
            self.employee_id = False

    def action_end_process(self):
        for r in self:
            compose_form = self.env.ref('sv_dispatch_orders.sv_route_comment_form_view',False)
            #self.delivery_status = 'delivered'
            #self.effective_date = datetime.now()
            ctx = {'default_delivery_status':'delivered','default_effective_date':datetime.now()}
            return{
                'name':'Comentarios adicionales',
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'sv.route.dispatch.line',
                'views': [(compose_form.id, 'form')],
                'res_id':r.id,
                'target': 'new',
                'view_id': 'compose_form.id',
                'flags': {'action_buttons': False},
                'context': ctx
            }
        
    def get_department_id(self):
        self.ensure_one()
        department_id = False
        depart_param = self.env['ir.config_parameter'].sudo().get_param('sv_route.deapartment_ref_id')
        try:
            department_id = self.env['hr.department'].browse(int(depart_param))
        except Exception as error:
            raise UserError('Error al obtener configuración de departamento autorizado:\n'+str(error))
        return department_id if department_id else False
    
    def compute_use_employee_code(self):
        self.ensure_one()
        req_emp_code = False
        req_emp_param = self.env['ir.config_parameter'].sudo().get_param('sv_route.use_employee_code')
        if req_emp_param == 'True':
            req_emp_code = True
        self.use_employee_code = req_emp_code
    
    def compute_comment_required(self):
        self.ensure_one()
        comment_req = False
        comment_req_param = self.env['ir.config_parameter'].sudo().get_param('sv_route.coment_required')
        if comment_req_param == 'True':
            comment_req = True
        self.comment_required = comment_req
    
    def write(self, vals):
        text = str(vals)
        if 'delivery_status' in text:
            if vals.get('delivery_status') != 'pending':
                vals['effective_date'] = datetime.now()
                #msj = vals
                #raise UserError(str(msj))
        res = super(sv_route_dispatch_line, self).write(vals)
        return res
    
    def get_color(self):
        for r in self:
            res = 4
            if r.delivery_status == 'delivered':
                res = 10
            elif r.delivery_status == 'rejected':
                res = 1
            elif r.delivery_status == 'forward':
                res = 3
            r.color = res
    