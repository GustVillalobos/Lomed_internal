# -*- coding: utf-8 -*-
##############################################################################
#
#    Odoo
#
##############################################################################

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = ['res.config.settings']

    department_ref_id = fields.Many2one(comodel_name='hr.department',string="Departamento autorizado",config_parameter='sv_route.deapartment_ref_id')
    use_employee_code = fields.Boolean(string="Registrar empleado en cada entrega",config_parameter='sv_route.use_employee_code')
    comment_required = fields.Boolean(string="Comentario requerido",config_parameter='sv_route.coment_required')
    clear_fields = fields.Boolean(string="Limpiar campos",config_parameter='sv_route.clear_fields')
    emp_in_charge = fields.Many2one(comodel_name='hr.employee',string="Encargado de despacho",config_parameter="sv_route.employee_in_charge")
    max_days = fields.Integer("Dias de anticipación",config_parameter="sv_route.max_days")
