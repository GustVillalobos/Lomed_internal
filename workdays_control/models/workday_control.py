# -*- coding: utf-8 -*-
##############################################################################
#
#    Odoo
#
##############################################################################
import base64
import time
from datetime import datetime,date,timedelta,time
from odoo import api, fields, models,_
from odoo.exceptions import UserError,ValidationError
import pytz

class WorkdayControl(models.Model):
    _name = 'workday.control'
    _inherit = ['mail.thread']
    _description = 'Jornada visual'

    name = fields.Char("Titulo de jornada")
    partner_id = fields.Many2one(comodel_name='res.partner',string="Contacto")
    manager_id = fields.Many2one(comodel_name='res.users',string="Encargado")
    active = fields.Boolean("Activo",default=True)
    stage = fields.Selection(selection=[
        ('created','Creado'),
        ('required','Solicitado'),
        ('scheduled','Agendado'),
        ('approved','Aprobado'),
    ],default='created',string="Etapa")
    date_from = fields.Date("Inicia jornada")
    date_to = fields.Date("Finaliza jornada")
    days = fields.Integer("Días de jornada",compute='_compute_total_days', store=True)
    hour_from = fields.Float("Hora de salida")
    hour_to = fields.Float("Hora de retorno")
    order_ids = fields.One2many(comodel_name='sale.order',inverse_name='workday_id',string="Pedidos")
    order_count = fields.Integer("Total ordenes",compute='_compute_order_count')
    total_sale = fields.Float("Total vendido",compute='_compute_total_sale')
    actual_income = fields.Float("Ingresado a la fecha")
    team_member_ids = fields.One2many(comodel_name='workday.team.line',string="Equipo de trabajo",inverse_name='workday_id')
    fuel_cost = fields.Float("Costo de combustible")
    total_cost = fields.Float("Viaticos totales",compute='_compute_total_cost',store = True)
    calendar_event_ids = fields.One2many(string="Eventos agendados",comodel_name='calendar.event',inverse_name='workday_id')
    calendare_event_count = fields.Integer("Cantidad de eventos",compute='_compute_calendar_event_count')

    @api.depends('date_from','date_to')
    def _compute_total_days(self):
        for r in self:
            res = 1
            if r.date_from and r.date_to and r.date_from != r.date_to:
                res += (r.date_to - r.date_from).days
            r.days = res

    @api.depends('order_ids')
    def _compute_order_count(self):
        for r in self:
            res = 0
            if r.order_ids:
                res = len(r.order_ids)
            r.order_count = res

    @api.depends('fuel_cost','team_member_ids')
    def _compute_total_cost(self):
        for r in self:
            res = 0
            if r.team_member_ids:
                for tm in r.team_member_ids:
                    res += tm.total_expense
            if r.fuel_cost:
                res += r.fuel_cost
            r.total_cost = res
    
    @api.depends('order_ids')
    def _compute_total_sale(self):
        for r in self:
            res = 0
            if r.order_ids:
                for o in r.order_ids:
                    res += o.amount_untaxed
            r.total_sale = res

    def get_order_list(self):
        self.ensure_one()
        return{
            'type':'ir.actions.act_window'
            ,'name':'Ordenes de la jornada'
            ,'view_mode':'tree,form'
            ,'res_model':'sale.order'
            ,'domain':[('workday_id','=',self.id)]
            ,'context':"{'create':False}"
        }
    
    def update_income_field(self):
        self.ensure_one()
        income = 0
        if self.order_ids:
            for so in self.order_ids:
                for inv in so.invoice_ids:
                    var = inv.amount_total - inv.amount_residual
                    income += var
        self.actual_income = income

    def send_to_approve(self):
        self.ensure_one()
        #Validar campos - Al menos  contacto inicial, al menos  optometra.
        has_promoter = self.team_member_ids.filtered(lambda tm:tm.role=='promoter')
        has_optometrist = self.team_member_ids.filtered(lambda tm:tm.role=='optometrist')
        if not has_promoter:
            raise UserError('Debe agregar al miembro que realizó el primer contacto')
        if not has_optometrist:
            raise UserError('Debe agregar un optometrista para realizar los examenes')
        #Enviar correo a encargado.
        tmpl_id = self.env.ref('workdays_control.workday_mail_approve')
        if tmpl_id:
            tmpl_id.send_mail(self.id,force_send=True)
        #Cambiar estado.
        self.stage = 'required'
    
    def convert_to_time_format(self,time):
        t_int = int(time)
        t_res = int((time - t_int)*60)
        hour = ''
        minute = ''
        msj = ' am'
        if t_int < 10:
            hour = '0'+str(t_int)
        else:
            hour = str(t_int)
        if t_res < 10:
            minute = '0'+str(t_res)
        else:
            minute = str(t_res)
        if t_int >= 12:
            msj = ' pm'
        return hour+':'+minute+msj
    
    def get_minute(self,time):
        t_int = int(time)
        t_res = int((time - t_int)*60)
        return t_res
    
    def action_schedule(self):
        self.ensure_one()
        days = {'Sunday':'Domingo','Monday':'Lunes','Tuesday':'Martes','Wednesday':'Miércoles','Thursday':'Jueves','Friday':'Viernes','Saturday':'Sábado',}
        #Crear objeto calendario
        control_date = self.date_from
        while control_date <= self.date_to:
            start = self.get_utc_datetime(datetime.combine(control_date,time(int(self.hour_from),self.get_minute(self.hour_from),0)))
            stop = self.get_utc_datetime(datetime.combine(control_date,time(int(self.hour_to),self.get_minute(self.hour_to),0)))
            calendar_event = {}
            calendar_event['name'] = self.name+': '+days[control_date.strftime("%A")]
            calendar_event['start'] = start
            calendar_event['stop'] = stop
            calendar_event['user_id'] = self.create_uid.id
            calendar_event['privacy'] = 'confidential'
            calendar_event['workday_id'] = self.id
            try:
                ce = self.env['calendar.event'].create(calendar_event)
                partner_ids = []
                partner_ids.append(self.manager_id.partner_id.id)
                for e in self.team_member_ids:
                    if e.employee_id.work_contact_id:
                        partner_ids.append(e.employee_id.work_contact_id.id)
                ce.write({'partner_ids':[(6,0,partner_ids)]})
            except Exception as e:
                raise UserError('Error: '+str(e))
            control_date = control_date + timedelta(days=1)
        #Cambiar estado
        self.stage = 'scheduled'
    
    def action_authorize(self):
        self.ensure_one()
        self.stage = 'approved'

    def action_cancel_workday(self):
        for r in self:
            r.active = False
            if r.calendar_event_ids:
                for ce in r.calendar_event_ids:
                    ce.unlink()
                    
    @api.model
    def create(self,vals):
        date_from = False
        date_to = False
        hour_from = False
        hour_to = False
        if 'date_from' in vals:
            date_from = vals.get('date_from')
        if 'date_to' in vals:
            date_to = vals.get('date_to')
        if 'hour_from' in vals:
            hour_from = vals.get('hour_from')
        if 'hour_to' in vals:
            hour_to = vals.get('hour_to')
        if date_to < date_from:
            vals['date_from'] = date_to
            vals['date_to'] = date_from
        if hour_from > hour_to:
            vals['hour_from'] = hour_to
            vals['hour_to'] = hour_from
        workday = super(WorkdayControl,self).create(vals)
        return workday
    
    def get_role(self,role):
        role_list = {'promoter':'Contacto inicial',
        'business':'Asesor empresarial',
        'commercial':'Asesor de ventas',
        'optometrist':'Optometrista'}
        return role_list[role]
    
    def get_calendar_event_list(self):
        self.ensure_one()
        return{
            'type':'ir.actions.act_window'
            ,'name':'Programación de jornada'
            ,'view_mode':'calendar,tree,form'
            ,'res_model':'calendar.event'
            ,'domain':[('workday_id','=',self.id)]
            ,'context':"{'create':False}"
        }
    
    @api.depends('calendar_event_ids')
    def _compute_calendar_event_count(self):
        for r in self:
            res = 0
            if r.calendar_event_ids:
                res = len(r.calendar_event_ids)
            r.calendare_event_count = res
    
    def get_utc_datetime(self,convert_date):
        tz = pytz.timezone(self.env.user.tz or 'America/El_Salvador')
        date_local = tz.localize(convert_date)
        date_utc = date_local.astimezone(pytz.utc)
        return date_utc.replace(tzinfo=None)

class WorkdayTeamLine(models.Model):
    _name = 'workday.team.line'
    _description = 'Miembro de equipo'

    name = fields.Char("Nombre",compute='_compute_name')
    employee_id = fields.Many2one(comodel_name='hr.employee',string="Empleado")
    role = fields.Selection(selection=[
        ('promoter','Contacto inicial'),
        ('business','Asesor empresarial'),
        ('commercial','Asesor de ventas'),
        ('optometrist','Optometrista')
    ],string="Rol",required=True)
    food_expense = fields.Float("Viaticos alimentos")
    days = fields.Integer("Días")
    total_expense = fields.Float("Total viaticos",compute='_compute_total_expense')
    workday_id = fields.Many2one(comodel_name='workday.control',string="Jornada")

    @api.depends('employee_id')
    def _compute_name(self):
        for r in self:
            res = 'Nuevo miembro'
            if r.employee_id:
                res = 'Miembro: '+r.employee_id.name
            r.name=res
    
    def write(self,vals):
        if 'days' in vals:
            workday = self.env['workday.control'].browse(vals.get('workday_id'))
            if workday.days < vals.get('days'):
                raise UserError(f"No puede asignar más días de viaticos de los que durará la jornada\njornada: {workday.days}\nDias: {vals.get('days')}")
        team_line = super(WorkdayTeamLine,self).write(vals)
        return team_line

    @api.model
    def create(self,vals):
        if 'days' in vals:
            workday = self.env['workday.control'].browse(vals.get('workday_id'))
            if workday.days < vals.get('days'):
                raise UserError(f"No puede asignar más días de viaticos de los que durará la jornada\njornada: {workday.days}\nDias: {vals.get('days')}")
        team_line = super(WorkdayTeamLine,self).create(vals)
        return team_line
    
    @api.depends('food_expense','days')
    def _compute_total_expense(self):
        for r in self:
            r.total_expense = r.food_expense * r.days