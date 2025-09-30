# -*- coding: utf-8 -*-
{
    'name': "Plan de fidelización",

    'summary': """
       Añade modelos y campos necesarios para crear y controlar un plan de fidelización""",

    'description': """
        Añade modelos y campos necesarios para crear y controlar un plan de fidelización
    """,

    'author': "Gustavo Villalobos",
    'website': "",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '16.0',

    # any module necessary for this one to work correctly
    'depends': ['base','product','sale','account','advisors'],

    # always loaded
    'data': [
        'data/data.xml',
        'views/loyalty_plan.xml',
        'views/lomed_point_system.xml',
        'security/ir.model.access.csv',
        'views/views.xml',
        'report/point_system_report.xml',   
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    'images':[],
    'license':'LGPL-3',
}
