# -*- coding: utf-8 -*-
{
    'name': "Referencia medica",

    'summary': """
       Permite generar una referencia médica""",

    'description': """
        Permite generar una referencia médica y verificar su validez
    """,

    'author': "Gustavo Villalobos",
    'website': "",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '16.0',

    # any module necessary for this one to work correctly
    'depends': ['base'],

    # always loaded
    'data': [
        'security/res_groups.xml',
        'report/referrals_document.xml',
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
