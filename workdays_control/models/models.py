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

class Wdc_SaleOrder(models.Model):
    _inherit = 'sale.order'

    workday_id = fields.Many2one(comodel_name='workday.control',string="Jornada")
    _allowed_employees = fields.Many2many(comodel_name='hr.employee',string="Empleados permitidos",compute='_get_allowed_employees')
    optometrist_id = fields.Many2one(comodel_name="hr.employee",string="Optometra")

    @api.depends('workday_id')
    def _get_allowed_employees(self):
        for r in self:
            res = []
            if r.workday_id:
                employees = r.workday_id.team_member_ids.filtered(lambda e: e.role == 'optometrist')
                for em in employees:
                    res.append(em.employee_id.id)
            r.write({'_allowed_employees':[(6,0,res)]})

class Wdc_HrEmployee(models.Model):
    _inherit = 'hr.employee'

    campaign_employee = fields.Boolean("Participa en jornada")

class Wdc_CalendarEvent(models.Model):
    _inherit = 'calendar.event'

    workday_id = fields.Many2one(comodel_name='workday.control',string="Jornada")