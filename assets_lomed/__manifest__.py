# -*- coding: utf-8 -*-
{
    'name': "Activos fijos Lomed",

    'summary': """
       Adecuaciones y cambios para Activos fijos para Lomed""",

    'description': """
        Adecuaciones y cambios para Activos fijos para Lomed
    """,

    'author': "Gustavo Villalobos",
    'website': "",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '16.0',

    # any module necessary for this one to work correctly
    'depends': ['base','account_asset','print_label'],
    #account_asset,base_accounting_kit

    # always loaded
    'data': [
        'views/views.xml',
        'report/template.xml',
        'security/ir.model.access.csv',
    ],
    # only loaded in demonstration mode
    'demo': [],
    'images':[],
    'license':'LGPL-3',
}
