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
    'depends': ['base','hr_payroll_community','hr_attendance'],

    # always loaded
    'data': [
        'views/views.xml',
        'security/ir.model.access.csv',
        'data/data.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    'images':[],
    'license':'LGPL-3',
}
