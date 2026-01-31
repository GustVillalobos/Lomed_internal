# -*- coding: utf-8 -*-
##############################################################################
#
#    Odoo
#
##############################################################################
import base64
import time
import pytz
from datetime import datetime,date,time,timedelta
from odoo import api, fields, models,_
from odoo.exceptions import UserError,ValidationError
import logging
_logger = logging.getLogger(__name__)

class ReportWizardAttendance(models.TransientModel):
    _name = 'report.wizard.attendance'
    _description = 'Reporte de asistencia'

    name = fields.Char("Report name")
    employee_ids = fields.Many2many(comodel_name='hr.employee',string="Empleados")
    date_from = fields.Datetime("Desde")
    date_to = fields.Datetime("Hasta")
    report_type = fields.Selection([
        ('late','Llegadas tarde'),
        ('attendance','Asistencia'),
        ('holiday','Asueto')
    ],default='late',string="Tipo")

    def action_print_report(self):
        self.ensure_one()
        return self.env.ref('sv_schedule.attendance_report_action').report_action(self)
    
    def get_attendance_data(self):
        self.ensure_one()
        user_tz = pytz.timezone(self.env.user.tz or 'UTC')

        date_from = user_tz.localize(datetime.combine(self.date_from,time.min)).astimezone(pytz.UTC)
        date_to = user_tz.localize(datetime.combine(self.date_to,time.max)).astimezone(pytz.UTC)

        search_domain = [
            ('check_in','>=',date_from),
            ('check_in','<=',date_to)
        ]

        if self.employee_ids:
            search_domain.append(('employee_id','in',self.employee_ids.ids))
        
        if self.report_type == 'late':
            search_domain += [
                '|',
                ('unworked_time','>',0),
                ('replacement_time','>',0)
            ]
        elif self.report_type == 'holiday':
            search_domain.append(('is_holiday','=',True))
        
        attendance_list = self.env['hr.attendance'].search(search_domain,order='check_in desc')
        employee_map = {}

        for att in attendance_list:
            emp = att.employee_id
            if emp.id not in employee_map:
                employee_map[emp.id]={
                    "employee_id":emp.id,
                    "name":emp.name,
                    "code":emp.barcode,
                    "total_late_records":0,
                    "total_worked_time":0,
                    "total_unworked_time":0,
                    "total_replacement_time":0,
                    "attendance":[],
                }
            check_in_local = att.check_in.astimezone(user_tz) if att.check_in else False
            check_out_local = att.check_out.astimezone(user_tz) if att.check_out else False
            
            if att.unworked_time > 0:
                employee_map[emp.id]['total_late_records'] += 1
            
            employee_map[emp.id]['total_unworked_time'] += att.unworked_time or 0.0
            employee_map[emp.id]['total_replacement_time'] += att.replacement_time or 0.0
            employee_map[emp.id]['total_worked_time'] += att.worked_hours or 0.0

            employee_map[emp.id]['attendance'].append({
                "attendance_date":check_in_local.strftime("%d-%m-%Y") if check_in_local else '',
                "check_in":check_in_local.strftime("%d-%m-%Y %H:%M:%S") if check_in_local else '',
                "check_out":check_out_local.strftime("%d-%m-%Y %H:%M:%S") if check_out_local else '',
                "worked_hours":self._format_hours(att.worked_hours),
                "unworked_time":self._format_hours(att.unworked_time),
                "replacement_time":self._format_hours(att.replacement_time),
            })
        
        for emp_data in employee_map.values():
            emp_data['total_unworked_time'] = self._format_hours(emp_data['total_unworked_time'])
            emp_data['total_replacement_time'] = self._format_hours(emp_data['total_replacement_time'])
            overtime = emp_data['total_worked_time'] - 96 if (emp_data['total_worked_time'] - 96) > 0 else 0
            emp_data['overtime_calculated'] = self._format_hours(overtime)
            emp_data['total_worked_time'] = self._format_hours(emp_data['total_worked_time'])

        json_data = {"employee_list":list(employee_map.values())}
        #_logger.info(str(json_data))
        return json_data
    
    def _format_hours(self,hours):
        if not hours:
            return "00:00 (0.0)"
        
        total_minutes = int(round(hours * 60))
        hh = total_minutes // 60
        mm = total_minutes % 60

        return f"{hh:02d}:{mm:02d} ({hours:.2f})"
    
    @api.onchange('date_from')
    def _onchange_date_from(self):
        if self.date_from:
            tz = pytz.timezone(self.env.user.tz or 'UTC')
            date_res = tz.localize(datetime.combine(self.date_from.date(),time.min)).astimezone(pytz.UTC)
            self.date_from = date_res.replace(tzinfo=None)

    @api.onchange('date_to')
    def _onchange_date_to(self):
        if self.date_to:
            tz = pytz.timezone(self.env.user.tz or 'UTC')
            date_res = tz.localize(datetime.combine(self.date_to.date(),time.max)).astimezone(pytz.UTC)
            self.date_to = date_res.replace(tzinfo=None)
