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

class sv_attendance(models.Model):
    _inherit = 'resource.calendar'

    tolerance = fields.Float("Tolerancia",help="Tiempo de gracia semanal para llegadas luego de la hora")

class sv_resource_calendar_attendance(models.Model):
    _inherit = 'resource.calendar.attendance'

    enable_rep_time = fields.Boolean("Repone tiempo")
    '''type = fields.Selection(selection=[
        ('work','Trabajar'),
        ('rest','Fin de semana'),
        ('reposition','Compensatorio'),
        ('leave','Permiso')
    ],default = 'work',string="Tipo")'''

class sv_employee_calendar(models.Model):
    _inherit = 'hr.employee'

    remaining = fields.Float("Toleracia restante",readonly="1")
    ignore_attendance = fields.Boolean("Ignorar marcación")

    def _reset_remaining(self):
        employee = self.env['hr.employee'].search([('active','=',True)])
        for e in employee:
            e.remaining = e.resource_calendar_id.tolerance

class sv_hr_attendance(models.Model):
    _inherit = 'hr.attendance'

    unworked_time = fields.Float("Tiempo no trabajado")
    replacement_time = fields.Float("Tiempo de reposición")
    type_close = fields.Selection(selection=[
        ('normal','Normal'),
        ('automatic','Automático'),
        ('manual','Manual')
    ],default='normal',string="Tipo salida")

    @api.model
    def create(self,vals):
        if 'check_in' in vals:
            res = 0
            rem = 0
            #capture info
            tz = pytz.timezone(self.env.user.tz or 'UTC')
            check_in = datetime.strptime(vals.get('check_in'),'%Y-%m-%d %H:%M:%S')
            check_in_utc = pytz.utc.localize(check_in)
            check_in_locale = check_in_utc.astimezone(tz)
            day = check_in_locale.weekday()
            hour = check_in_locale.hour + (check_in_locale.minute/60)
            employee = self.env['hr.employee'].browse(vals.get('employee_id'))
            sh_d = employee.resource_calendar_id.attendance_ids.filtered(lambda t:t.dayofweek == str(day) and t.day_period == 'morning')
            if hour > sh_d.hour_from and self.is_check_in(check_in,employee.id):
                _logger.info('Inicia calculo de llegada tarde')
                res = hour - sh_d.hour_from
                if employee.remaining >= res:
                    rem = employee.remaining - res
                    employee.remaining = rem
                    _logger.info(f'Menos de 10 minutos: {res}, Sobrante: {rem}')
                    res = 0
                elif employee.remaining < res:
                    res = res - employee.remaining
                    employee.remaining = rem
                    _logger.info(f'Más de 10 minutos: {res}, Sobrante: {rem}')
            vals['unworked_time'] = res
            try:
                _logger.info(str(vals))
                attendance = super(sv_hr_attendance,self).create(vals)
            except Exception as e:
                raise ValidationError("Error encontrado: "+str(e))
            return attendance

    def is_check_in(self,check_in,employee):
        tz = pytz.timezone(self.env.user.tz)
        ref = check_in.astimezone(tz)
        begin = ref.replace(hour=0,minute=0,second=0)
        end = ref.replace(hour=23,minute=59,second=59)
        attendance = self.env['hr.attendance'].search([('check_in','>=',begin.astimezone(pytz.timezone('UTC'))),('check_in','<=',end.astimezone(pytz.timezone('UTC'))),('employee_id','=',employee)])
        res = True
        if len(attendance) >= 1:
            res = False
        return res
    
    @api.onchange('check_out')
    def compute_replacement_time(self):
        for r in self:
            res = 0
            if r.check_out:
                tz = pytz.timezone(self.env.user.tz or 'UTC')
                check_out_utc = pytz.utc.localize(r.check_out)
                check_out_locale = check_out_utc.astimezone(tz)
                day = check_out_locale.weekday()
                hour = check_out_locale.hour + (check_out_locale.minute/60)
                applicable = r.employee_id.resource_calendar_id.attendance_ids.filtered(lambda t:t.dayofweek == str(day) and t.day_period == 'afternoon')
                if applicable.enable_rep_time:
                    res = hour - applicable.hour_to
                    if res < 0:
                        res = 0
            r.replacement_time = res
    
    def _close_attendance(self):
        attendance = self.env['hr.attendance'].search([('check_out','=',False)])
        if attendance:
            for att in attendance:
                att.check_out = att.check_in
                att.type_close = 'automatic'

class sv_payslip_run(models.Model):
    _inherit = 'hr.payslip.run'

    #computed = fields.Boolean("Test")

    def action_compute_unworked_time(self):
        self.ensure_one()
        date_start = datetime.combine(self.x_inicia_corte,time(0,0,0))#x_inicia_corte
        date_end = datetime.combine(self.x_fin_corte,time(23,59,59))#x_fin_corte
        if self.slip_ids:
            for p in self.slip_ids:
                schedule = p.employee_id.resource_calendar_id
                absense = 0
                unworked_time = 0
                holiday = 0
                attendance = self.env['hr.attendance'].search([('employee_id','=',p.employee_id.id),('check_in','>=',date_start),('check_in','<=',date_end)])
                #Calculando tiempo no trabajado
                if attendance:
                    for a in attendance:
                        if a.unworked_time > 0:
                            unworked_time += a.unworked_time
                        if a.replacement_time > 0:
                            unworked_time -= a.replacement_time
                        _logger.info('Tiempo no trabajado calculado')
                #Calculando ausencias y asuetos
                if not p.employee_id.ignore_attendance:
                    control_date = date_start
                    msj = ''
                    if not schedule.two_weeks_calendar:
                        while control_date.date() <= date_end.date():
                            is_work_day = schedule.attendance_ids.filtered(lambda att:att.dayofweek == str(control_date.weekday()) and att.work_entry_type_id.is_leave == False and att.day_period == 'morning')
                            is_holyday = self.env['resource.calendar.leaves'].search([('date_from','>=',control_date),('date_from','<=',control_date.replace(hour=23,minute=59,second=59)),('resource_id','=',False)])
                            is_present = attendance.filtered(lambda at:at.check_in.date() == control_date.date())
                            if is_work_day and len(is_present)<= 0 and not is_holyday:
                                absense +=1
                                msj = msj + control_date.strftime("[%d-%m-%Y],")
                                _logger.info(f'Ausencias calculadas {absense}')
                            if is_holyday and is_present:
                                for att in is_present:
                                    holiday += att.worked_hours
                            control_date = control_date + timedelta(days=1)
                if unworked_time > 0:
                    input = self.get_input_id('rrhh_sv_cm.input_type_unwork_time')
                    exist = p.input_line_ids.filtered(lambda ili:ili.input_type_id.id == input)
                    if not exist:
                        msg = 'Tiempo no trabajado calculo automático'
                        ut = self.get_amount_minutes(unworked_time)
                        self.create_input_lines(input=input,msg=msg,amount=ut,slip_id=p.id)
                    else:
                        exist.amount = self.get_amount_minutes(unworked_time)
                if absense > 0:
                    input = self.get_input_id('rrhh_sv_cm.input_type_absence')
                    exist = p.input_line_ids.filtered(lambda ili:ili.input_type_id.id == input)
                    if not exist:
                        self.create_input_lines(input=input,msg=msj,amount=absense,slip_id=p.id)
                    else:
                        exist.name = msj
                        exist.amount= absense
                if holiday > 0:
                    input = self.get_input_id('rrhh_sv_cm.input_type_holiday')
                    exist = p.input_line_ids.filtered(lambda ili:ili.input_type_id.id == input)
                    if not exist:
                        msg = 'Asueto calculo automático'
                        self.create_input_lines(input=input,msg=msg,amount=holiday,slip_id=p.id)
                    else:
                        exist.amount = holiday
                p.compute_sheet()
    
    def get_amount_minutes(self,minutes):
        res = 0
        if minutes >= 1.0:
            res += (int(minutes)*60)        
        res += ((minutes - int(minutes))*60)
        return res
    
    def get_input_id(self,ref):
        input_type = self.env.ref(ref)
        return input_type.id
    
    def create_input_lines(self,input,msg,amount,slip_id):
        dic={}
        dic['input_type_id'] = input
        dic['name'] = msg
        dic['amount'] = amount
        dic['payslip_id'] = slip_id
        try:
            self.env['hr.payslip.input'].create(dic)
        except Exception as e:
            raise UserError('Error: '+str(e))
