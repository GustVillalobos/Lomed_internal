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

class create_sale_order(models.TransientModel):
    _name='op.wizard.create_order'
    _description = 'Crear Orden de venta'

    appointment_id = fields.Many2one(string="Examen visual",comodel_name='op.appointment')
    include_ar = fields.Boolean("Incluir antirreflejo")
    accessories = fields.Boolean("Incluir accesorios",help="Agregar franela y estuche al pedido")
    partner_id = fields.Many2one(string="Contacto",comodel_name='res.partner')
    frame_id = fields.Many2one(string="Aro seleccionado",comodel_name='product.product')
    design_id = fields.Many2one(string="Producto",comodel_name='product.product')
    component_ar = fields.Many2one(string="Componente AR",comodel_name='product.product',domain="[('type_optic','=','ar_component')]")

    def create_sale_order(self):
        self.ensure_one()
        sale_order = {}
        ppst = {'U':'Arriba','D':'Abajo','I':'Adentro','O':'Afuera','NA':False,'False':False}
        #Llenando encabezado de orden
        sale_order['partner_id'] = self.partner_id.id
        sale_order['paciente'] = self.appointment_id.patient_id.name
        sale_order['date_order'] = datetime.now()
        #llenando receta optica
        sale_order['x_sphere_eye_right'] = self.appointment_id.fnl_re_sph
        sale_order['x_sphere_eye_left'] = self.appointment_id.fnl_le_sph
        sale_order['x_cilinder_eye_right'] = self.appointment_id.fnl_re_cyl
        sale_order['x_cilinder_eye_left'] = self.appointment_id.fnl_le_cyl
        sale_order['x_eje_eye_right'] = self.appointment_id.fnl_re_axis
        sale_order['x_eje_eye_left'] = self.appointment_id.fnl_le_axis
        sale_order['x_adition_eye_right'] = self.appointment_id.fnl_re_add
        sale_order['x_adition_eye_left'] = self.appointment_id.fnl_le_add
        sale_order['x_prism_eye_right'] = self.appointment_id.fnl_re_prism
        sale_order['x_prism_eye_left'] = self.appointment_id.fnl_le_prism
        sale_order['x_prism_eye_right_location'] = ppst.get(self.appointment_id.fnl_re_prism_pst)
        sale_order['x_prism_eye_left_location'] = ppst.get(self.appointment_id.fnl_le_prism_pst)
        if self.appointment_id.its_own_frame:
            sale_order['x_aro_propio'] = self.appointment_id.frame_mark+'/'+self.appointment_id.frame_code
        else:
            sale_order['x_aro'] = self.appointment_id.frame_mark+'/'+self.appointment_id.frame_code
        sale_order['x_distance_pupilar'] = self.appointment_id.dnp_re+'/'+self.appointment_id.dnp_le
        sale_order['x_heigh_wafer_eye'] = self.appointment_id.blaze_height
        sale_order['x_heigh_pupilar_eye'] = self.appointment_id.pupillary_height
        sale_order['x_size_aro'] = self.appointment_id.frame_zise
        sale_order['x_color_aro'] = self.appointment_id.frame_color
        try:
            order = self.env['sale.order'].create(sale_order)
        except Exception as error:
            raise ValidationError('Error: '+str(error))
        #Creando lineas de pedido
        product_list = self.get_product_list()
        for pl in product_list:
            line = {}
            usr_lang = self.env.user.lang
            line['name'] = pl.with_context(lang = usr_lang).name
            line['product_id'] = pl.id
            line['product_uom_qty'] = 1 if pl.id != self.design_id.id else 2
            line['order_id'] = order.id
            try:
                self.env['sale.order.line'].create(line)
            except Exception as e:
                raise ValidationError('Error: '+str(e))
        self.appointment_id.order_id = order.id
        return{
            'type':'ir.actions.act_window',
            'res_model':'sale.order',
            'res_id':order.id,
            'view_mode':'form',
            'target':'current'
        }

    def get_product_list(self):
        self.ensure_one()
        list = []
        list.append(self.design_id.id)
        if self.include_ar:
            list.append(self.component_ar.id)
        if self.frame_id:
            list.append(self.frame_id.id)
        if self.accessories:
            accesories = self.get_accessories()
            for p in accesories:
                list.append(p.id)
        if self.appointment_id.clean_product_id:
            list.append(self.appointment_id.clean_product_id.id)
        product_ids = self.env['product.product'].search([('id','in',list)])
        if product_ids:
            return product_ids
        else:
            return False
    
    def get_accessories(self):
        accesories = self.env['product.product'].search([('active','=',True),('type_optic','=','accesories')])
        if accesories:
            return accesories
        else:
            return False
    

