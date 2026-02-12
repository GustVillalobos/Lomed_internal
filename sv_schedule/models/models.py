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

class sv_employee_calendar(models.Model):
    _inherit = 'hr.employee'

    remaining = fields.Float("Toleracia restante",readonly="1")
    ignore_attendance = fields.Boolean("Ignorar marcación")
    schedule_template_id = fields.Many2one(string="Siguiente horario",comodel_name="resource.calendar")

    def _update_employee_schedule(self):
        employee = self.env['hr.employee'].search([('active','=',True),('schedule_template_id','!=',False)])
        for e in employee:
            e.remaining = e.resource_calendar_id.tolerance
            if e.schedule_template_id:
                for att in e.resource_calendar_id.attendance_ids:
                    new_att = e.schedule_template_id.attendance_ids.filtered(lambda at:at.dayofweek == att.dayofweek and at.day_period == att.day_period)
                    if new_att:
                        att.hour_from = new_att.hour_from
                        att.hour_to = new_att.hour_to
                        att.work_entry_type_id = new_att.work_entry_type_id.id
    
    def _verify_attendance(self):
        employees = self.env['hr.employee'].search([('active','=',True)])
        ref = datetime.now()
        begin = ref.replace(hour=0,minute=0,second=0)
        end = ref.replace(hour=23,minute=59,second=59)
        is_holyday = self.env['resource.calendar.leaves'].search([('date_from','>=',ref.replace(hour=0,minute=0,second=0)),('date_from','<=',ref.replace(hour=23,minute=59,second=59)),('resource_id','=',False)])
        leave_type = self.env.ref('sv_schedule.unjustify_absence_leavetype')
        for emp in employees:
            abs_already_reg = self.env['hr.leave'].search([('employee_id','=',emp.id),('request_date_from','=',ref.date())])
            is_present = emp.attendance_ids.filtered(lambda att:att.check_in >= begin and att.check_in <= end)
            is_work_day = emp.resource_calendar_id.attendance_ids.filtered(lambda att:att.dayofweek == str(begin.weekday()) and att.work_entry_type_id.is_leave == False)
            if not is_present and is_work_day and not is_holyday:
                #Crear objeto ausencia injustificada
                if not abs_already_reg and not emp.ignore_attendance:
                    absence={}
                    absence['name'] = f"{emp.name} en {leave_type.name}: {ref.strftime('%d/%m/%Y')}"
                    absence['holiday_type'] = 'employee'
                    absence['employee_id'] = emp.id
                    absence['holiday_status_id'] = leave_type.id
                    absence['request_date_from'] = ref.date()
                    absence['request_date_to'] = ref.date()
                    date_from = self.compute_date(ref.date(),self.compute_hour(lines=is_work_day))
                    absence['date_from'] = self.get_utc_date(date_from,emp)
                    date_to = self.compute_date(ref.date(),self.compute_hour(lines=is_work_day,mode='check_out'))
                    absence['date_to'] = self.get_utc_date(date_to,emp)
                    absence['leave_type_request_unit'] = leave_type.leave_validation_type
                    absence['state'] = 'confirm'
                    try:
                        new_absence = self.env['hr.leave'].create(absence)
                    except Exception:
                        _logger.info(str(absence))
                        _logger.exception(f"Error al crear ausencia")
            elif not is_present and is_holyday and is_work_day:
                #Crear asistencia normal
                for sch in is_work_day:
                    attendance = {}
                    attendance['employee_id']=emp.id
                    check_in = self.compute_date(ref.date(),sch.hour_from)
                    attendance['check_in'] = self.get_utc_date(check_in,emp)
                    check_out = self.compute_date(ref.date(),sch.hour_to)
                    attendance['check_out'] = self.get_utc_date(check_out,emp)
                    try:
                        new_attendance = self.env['hr.attendance'].create(attendance)
                    except Exception as e:
                        _logger.warning("Error al crear asistencia: "+str(e))
            elif is_present and is_holyday:
                #Marcar como asueto pagado la asistencia
                for a in is_present:
                    a.is_holiday = True
    
    def compute_date(self,date,hour_float):
        hour, minute = divmod(int(hour_float * 60),60)
        return datetime.combine(date,time(hour,minute))
    
    def compute_hour(self,lines,mode='check_in'):
        period = 'morning' if mode == 'check_in' else 'afternoon'
        res_line = lines.filtered(lambda p:p.day_period==period)
        if res_line and mode == 'check_in':
            return res_line[0].hour_from
        elif res_line and mode != 'check_in':
            return res_line[0].hour_to
        else:
            return 0

    def get_utc_date(self,date,employee):
        tz = pytz.timezone(employee.tz or 'UTC')
        if not date:
            return date
        local = tz.localize(date)
        date_utc = local.astimezone(pytz.utc)
        return date_utc.replace(tzinfo=None)

class sv_hr_attendance(models.Model):
    _inherit = 'hr.attendance'

    unworked_time = fields.Float("Tiempo no trabajado")
    replacement_time = fields.Float("Tiempo de reposición")
    type_close = fields.Selection(selection=[
        ('normal','Normal'),
        ('automatic','Automático'),
        ('manual','Manual')
    ],default='normal',string="Tipo salida")
    is_holiday = fields.Boolean("Es asueto")

    @api.model_create_multi
    def create(self,vals_list):
        for vals in vals_list:
            if 'check_in' in vals:
                res = 0
                rem = 0
                #capture info
                tz = pytz.timezone(self.env.user.tz or 'UTC')
                check_in = False
                if isinstance(vals.get('check_in'),datetime):
                    check_in = vals.get('check_in')
                else:
                    check_in = datetime.strptime(vals.get('check_in'),'%Y-%m-%d %H:%M:%S')
                check_in_utc = pytz.utc.localize(check_in)
                check_in_locale = check_in_utc.astimezone(tz)
                day = check_in_locale.weekday()
                hour = check_in_locale.hour + (check_in_locale.minute/60)
                employee = self.env['hr.employee'].browse(vals.get('employee_id'))
                sh_d = employee.resource_calendar_id.attendance_ids.filtered(lambda t:t.dayofweek == str(day) and t.day_period == 'morning')
                if sh_d and hour > sh_d.hour_from and self.is_check_in(check_in,employee.id):
                    #_logger.info('Inicia calculo de llegada tarde')
                    res = hour - sh_d.hour_from
                    if employee.remaining >= res:
                        rem = employee.remaining - res
                        employee.remaining = rem
                        #_logger.info(f'Menos de 10 minutos: {res}, Sobrante: {rem}')
                        res = 0
                    elif employee.remaining < res:
                        res = res - employee.remaining
                        employee.remaining = rem
                        #_logger.info(f'Más de 10 minutos: {res}, Sobrante: {rem}')
                vals['unworked_time'] = res

        attendance = super().create(vals_list)
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

    start_cut = fields.Date("Inicia corte")
    end_cut = fields.Date("Finaliza corte")

    #computed = fields.Boolean("Test")

    def action_compute_unworked_time(self):
        self.ensure_one()
        date_start = datetime.combine(self.start_cut,time(0,0,0))#x_inicia_corte
        date_end = datetime.combine(self.end_cut,time(23,59,59))#x_fin_corte
        mid_date = date_start + timedelta(days=7)
        weeks={date_start.strftime("%U"):0,date_end.strftime("%U"):0,mid_date.strftime("%U"):0}
        injustify_type = self.env.ref('sv_schedule.unjustify_absence_leavetype')
        justify_type = self.env.ref('sv_schedule.justify_absence_leavetype')
        sickness_type = self.env.ref('sv_schedule.sickness_leavetype')
        if self.slip_ids:
            for p in self.slip_ids:
                absense = 0
                unworked_time = 0
                holiday = 0
                sunday = 0
                attendance = self.env['hr.attendance'].search([('employee_id','=',p.employee_id.id),('check_in','>=',date_start),('check_in','<=',date_end)])
                leaves = self.env['hr.leave'].search([('employee_id','=',p.employee_id.id),('request_date_from','>=',self.start_cut),('request_date_to','<=',self.end_cut)])
                #Calculando tiempo no trabajado y asuetos
                if attendance and not p.employee_id.ignore_attendance:
                    for a in attendance:
                        if a.unworked_time > 0:
                            unworked_time += a.unworked_time
                        if a.replacement_time > 0:
                            unworked_time -= a.replacement_time
                        if a.is_holiday:
                            holiday += a.worked_hours
                    #_logger.info(f"Tiempo no trabajado calculado {unworked_time}")
                #Calculando ausencias
                if leaves and not p.employee_id.ignore_attendance:
                    inj_leave = leaves.filtered(lambda ij:ij.holiday_status_id.id == injustify_type.id)
                    injustify = len(inj_leave)
                    sic_leave = leaves.filtered(lambda ij:ij.holiday_status_id.id == sickness_type.id)
                    sickness = 0
                    for s in sic_leave:
                        if s.inability_type == 'first':
                            sickness += (s.number_of_days - 3) if (s.number_of_days - 3) > 0 else 0
                        elif s.inability_type == 'extend':
                            sickness += s.number_of_days if s.number_of_days > 0 else 0
                    just_leave = leaves.filtered(lambda ij:ij.holiday_status_id.id == justify_type.id)
                    justify =  len(just_leave)
                    if inj_leave:
                        for i in inj_leave:
                            if weeks[i.request_date_from.strftime("%U")] < 1:
                                weeks[i.request_date_from.strftime("%U")] = 1
                    sunday = sum(weeks.values()) if sum(weeks.values()) <= 2 else 2
                    absense = injustify+justify+sickness

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
                    msg = 'Ausencias calculo automático'
                    input = self.get_input_id('rrhh_sv_cm.input_type_absence')
                    exist = p.input_line_ids.filtered(lambda ili:ili.input_type_id.id == input)
                    if not exist:
                        self.create_input_lines(input=input,msg=msg,amount=absense,slip_id=p.id)
                    else:
                        exist.name = msg
                        exist.amount= absense
                if holiday > 0:
                    input = self.get_input_id('rrhh_sv_cm.input_type_holiday')
                    exist = p.input_line_ids.filtered(lambda ili:ili.input_type_id.id == input)
                    if not exist:
                        msg = 'Asueto calculo automático'
                        self.create_input_lines(input=input,msg=msg,amount=holiday,slip_id=p.id)
                    else:
                        exist.amount = holiday
                if sunday > 0:
                    input = self.get_input_id('sv_schedule.input_other_absence')
                    exist = p.input_line_ids.filtered(lambda ili:ili.input_type_id.id == input)
                    if not exist:
                        msg = 'Descuento de 7mo por ausencia injustificada'
                        self.create_input_lines(input=input,msg=msg,amount=sunday,slip_id=p.id)
                    else:
                        exist.amount = sunday
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

class ScheduleHrLeave(models.Model):
    _inherit = 'hr.leave'

    inability_type = fields.Selection([
        ('first','Inicial'),
        ('extend','Prorroga'),
        ('permanent','Permanente')
    ],string="Tipo de incapacidad")