# -*- coding: utf-8 -*-
{
    'name': "Manejo de horario",

    'summary': """
       Funciones y campos para control y politicas de horario""",

    'description': """
        Funciones y campos para control y politicas de horario
    """,

    'author': "Gustavo Villalobos",
    'website': "",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '16.0',

    # any module necessary for this one to work correctly
    'depends': ['base','hr_payroll','hr_attendance','hr_holidays'],

    # always loaded
    'data': [
        'views/views.xml',
        'security/ir.model.access.csv',
        'report/report_wizard_attendance.xml',
        'data/data.xml',
    ],
    'images':[],
    'license':'LGPL-3',
}
