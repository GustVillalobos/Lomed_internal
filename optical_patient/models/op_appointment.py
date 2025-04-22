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

class op_appointment(models.Model):
    _name = 'op.appointment'
    _inherit = ['mail.thread','barcodes.barcode_events_mixin']
    _description = 'Consulta optométrica'

    name = fields.Char("Número")
    patient_id = fields.Many2one(string="Paciente",comodel_name='op.patient')
    state = fields.Selection([
        ('draft','Borrador'),
        ('confirm','Confirmada'),
        ('done','Hecho'),
        ('cancel','Cancelado')
    ],default='draft',string="Estado",tracking=True)
    date = fields.Date("Fecha de examen")
    physician_id = fields.Many2one(string="Optometrista",comodel_name='op.physician',tracking=True)
    reception_id = fields.Many2one(string="Sala de recepción",comodel_name='op.reception')
    confirm_date = fields.Datetime("Fecha de confirmación",tracking=True)
    effective_date = fields.Datetime("Fin atención",tracking=True)
    time_service = fields.Float("Tiempo de atención")
    frame_id = fields.Many2one(string="Aro seleccionado",comodel_name='product.product')
    design_id = fields.Many2one(string="Producto seleccionado",comodel_name='product.product')
    order_id = fields.Many2one(string="Orden de venta",comodel_name='sale.order')
    comment = fields.Html("Comentario")
    '''Aclaración de sintaxis campos lensometria previa y receta por acrónimos:
    Estructura a seguir: etapa_ojo_valor
        -Etapa:
            -Lensometria previa: prv
            -Refracción final: fnl
        -Ojo:
            -Derecho: re
            -Izquierdo: le
        -Valor:
            -Esfera: sph
            -Cilindro: cyl
            -Eje: axis
            -Adicion: add
            -Prisma valor: prism
            -Prisma posicion: prism_pst
            -Curva Base: base
            -AV Lejos: avf
            -AV Cerca: avc
    '''
    prism_pst = [
        ("NA","Ｏ"),
        ("U","∇ U"),
        ("D","∆ D"),
        ("O","⊲ O"),
        ("I","⊳ I")
    ]
    #Lensometria previa
    prv_re_sph = fields.Char("Esfera ojo derecho(previo)")
    prv_le_sph = fields.Char("Esfera ojo izquierdo(previo)")
    prv_re_cyl = fields.Char("Cilindro ojo derecho(previo)")
    prv_le_cyl = fields.Char("Cilindro ojo izquierdo(previo)")
    prv_re_axis = fields.Char("Eje ojo derecho(previo)")
    prv_le_axis = fields.Char("Eje ojo izquierdo(previo)")
    prv_re_add = fields.Char("Adicion ojo derecho(previo)")
    prv_le_add = fields.Char("Adicion ojo izquierdo(previo)")
    prv_re_prism = fields.Char("Prisma ojo derecho(previo)")
    prv_le_prism = fields.Char("Prisma ojo izquierdo(previo)")
    prv_re_prism_pst = fields.Selection(prism_pst,default='NA',string="Posición prisma ojo derecho(previo)")
    prv_le_prism_pst = fields.Selection(prism_pst,default='NA',string="Posición prisma ojo izquierdo(previo)")
    prv_re_base = fields.Char("Curva base ojo derecho(previo)")
    prv_le_base = fields.Char("Curva base ojo izquierdo(previo)")
    prv_re_avf = fields.Char("AV lejos ojo derecho(previo)")
    prv_le_avf = fields.Char("AV lejos ojo izquierdo(previo)")
    prv_re_avc = fields.Char("AV cerca ojo derecho(previo)")
    prv_le_avc = fields.Char("AV cerca ojo izquierdo(previo)")
    prv_design = fields.Char("Diseño")
    usage_time = fields.Integer("Tiempo de uso")
    usage_unit = fields.Selection([
        ('year','Años'),
        ('month','Meses'),
        ('week','Semanas')
    ],default='year',string="Unidad de tiempo")
    from_lomed = fields.Boolean("Es diseño nuestro")

    #Refraccion final
    fnl_re_sph = fields.Char("Esfera ojo derecho")
    fnl_le_sph = fields.Char("Esfera ojo izquierdo")
    fnl_re_cyl = fields.Char("Cilindro ojo derecho")
    fnl_le_cyl = fields.Char("Cilindro ojo izquierdo")
    fnl_re_axis = fields.Char("Eje ojo derecho")
    fnl_le_axis = fields.Char("Eje ojo izquierdo")
    fnl_re_add = fields.Char("Adicion ojo derecho")
    fnl_le_add = fields.Char("Adicion ojo izquierdo")
    fnl_re_prism = fields.Char("Prisma ojo derecho")
    fnl_le_prism = fields.Char("Prisma ojo izquierdo")
    fnl_re_prism_pst = fields.Selection(prism_pst,default='NA',string="Posición prisma ojo derecho")
    fnl_le_prism_pst = fields.Selection(prism_pst,default='NA',string="Posición prisma ojo izquierdo")
    fnl_re_base = fields.Char("Curva base ojo derecho")
    fnl_le_base = fields.Char("Curva base ojo izquierdo")
    fnl_re_avf = fields.Char("AV lejos ojo derecho")
    fnl_le_avf = fields.Char("AV lejos ojo izquierdo")
    fnl_re_avc = fields.Char("AV cerca ojo derecho")
    fnl_le_avc = fields.Char("AV cerca ojo izquierdo")
    is_contact_lens = fields.Boolean("Es lente de contacto")

    #Medidas de aro
    dnp_re = fields.Char("DNP ojo derecho")
    dnp_le = fields.Char("DNP ojo izquierdo")
    dip = fields.Char("DIP")
    pupillary_height = fields.Char("Altura Pupilar")
    blaze_height = fields.Char("Altura de oblea")
    its_own_frame = fields.Boolean("Aro propio")
    frame_mark = fields.Char("Marca")
    frame_code = fields.Char("Código")
    frame_zise = fields.Char("Tamaño")
    frame_color = fields.Char("Color")

    #Regimenes para lentes de contacto
    replace_time = fields.Integer("Tiempo de reemplazo")
    replace_unit = fields.Selection([
        ('year','Años'),
        ('month','Meses'),
        ('week','Semana'),
        ('day','Dias')
    ],default = 'year',string="Unidades tiempo reemplazo")
    clean_time = fields.Integer("Tiempo de limpieza")
    clean_product_id = fields.Many2one(string="Producto para limpieza",comodel_name='product.product')
    

    def action_draft(self):
        self.ensure_one()
        if self.effective_date:
            self.effective_date = False
        if self.time_service > 0:
            self.time_service = 0
        self.state = 'draft'
    
    def action_confirm(self):
        self.ensure_one()
        if not self.confirm_date:
            self.confirm_date = datetime.now()
        self.state = 'confirm'

    def action_done(self):
        self.ensure_one()
        now = datetime.now()
        if not self.effective_date:
            self.effective_date = now
        if self.time_service <= 0:
            self.time_service = ((now - self.confirm_date).total_seconds()) / 60 #Calculando minutos transcurridos
        self.state = 'done'
    
    def action_cancel(self):
        self.ensure_one()
        self.state = 'cancel'
    
    @api.model
    def create(self,vals):
        appointment = super(op_appointment,self).create(vals)
        dic = {'name':'EV'+str(appointment.id).zfill(6)}
        if appointment.reception_id.sequence_id:
            dic = {'name':appointment.reception_id.sequence_id.next_by_id()}
        appointment.write(dic)
        return appointment
    
    def on_barcode_scanned(self,barcode):
        state = {'done':'Hecha','cancel':'Cancelada'}
        if self.state in ('done','cancel'):
            raise ValidationError(_('No puede agregar aro a una consulta que está %s',state[self.state]))
        frame = self.env['product.product'].search([('barcode','=',barcode)])
        if not frame:
            raise UserError('El producto que busca no está registrado en la base de datos.')
        if frame and not self.its_own_frame:
            self.its_own_frame = True
        self.frame_id = frame.id
        self.frame_mark = frame.x_brand_product_id.x_name
        self.frame_code = frame.x_provider_code
        self.frame_zise = frame.x_size_product_id.x_name
        self.frame_color = frame.x_product_color_id.x_name
    
    def new_order(self):
        self.ensure_one()
        ctx = {'default_partner_id':self.patient_id.partner_id.id,
               'default_appointment_id':self.id,
               'default_frame_id':self.frame_id.id,
               'default_design_id':self.design_id.id,
               }
        return{
            'name':_('Nueva orden de venta'),
            'type': 'ir.actions.act_window',
            'view_mode':'form',
            'res_model':'op.wizard.create_order',
            'target':'new',
            'view_id':self.env.ref('optical_patient.op_wizard_create_order_form_view').id,
            'context':ctx
        }
    
    def get_order(self):
        self.ensure_one()
        return{
            'type':'ir.actions.act_window'
            ,'name':'Orden relacionada'
            ,'view_mode':'tree,form'
            ,'res_model':'sale.order'
            ,'domain':[('appointment_ids','in',self.id)]
            ,'context':"{'create':False}"
        }
    
    def get_prior_lensometry(self):
        self.ensure_one()
        last_exam = self.env['op.appointment'].search([('patient_id','=',self.patient_id.id),('id','!=',self.id)],order = "id desc", limit=1)
        if last_exam:
            self.prv_re_sph = last_exam.fnl_re_sph
            self.prv_le_sph = last_exam.fnl_le_sph
            self.prv_re_cyl = last_exam.fnl_re_cyl
            self.prv_le_cyl = last_exam.fnl_le_cyl
            self.prv_re_axis = last_exam.fnl_re_axis
            self.prv_le_axis = last_exam.fnl_le_axis
            self.prv_re_add = last_exam.fnl_re_add
            self.prv_le_add = last_exam.fnl_le_add
            self.prv_re_prism = last_exam.fnl_re_prism
            self.prv_le_prism = last_exam.fnl_le_prism
            self.prv_re_prism_pst = last_exam.fnl_re_prism_pst
            self.prv_le_prism_pst = last_exam.fnl_le_prism_pst
            self.prv_re_base = last_exam.fnl_re_base
            self.prv_le_base = last_exam.fnl_le_base
            self.prv_re_avf = last_exam.fnl_re_avf
            self.prv_le_avf = last_exam.fnl_le_avf
            self.prv_le_avc = last_exam.fnl_le_avc
            self.prv_design = last_exam.design_id.name