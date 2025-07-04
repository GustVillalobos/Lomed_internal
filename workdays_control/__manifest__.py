# -*- coding: utf-8 -*-
{
    'name': "Control de jornadas visuales",

    'summary': """
       Perimite registrar los datos relacionados a jornadas visuales""",

    'description': """
        Para registrar los datos de jornadas visuales incluyendo participantes, costos, viaticos y ventas
    """,

    'author': "Gustavo Villalobos",
    'website': "",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '16.0',

    # any module necessary for this one to work correctly
    'depends': ['base','sale','hr'],

    # always loaded
    'data': [
        'data/data.xml',
        'report/expense_report.xml',
        'views/workday_control.xml',
        'views/views.xml',
        'security/ir.model.access.csv',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    'images':[],
    'license':'LGPL-3',
}
