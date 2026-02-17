# -*- coding: utf-8 -*-
{
    'name': "Mapeo de impuestos",

    'summary': """
        Permite mapear los impuestos de venta """,

    'description': """
        Permite seleccionar y configurar los impuestos a partir de los documentos fiscales
    """,

    'author': "Gustavo Villalobos",
    'website': "",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '16.0',

    # any module necessary for this one to work correctly
    'depends': ['base','sv_location','base_accounting_kit','account'],
    #Cambiar: 'base','account','account_accountant','sv_accounting'

    # always loaded
    'data': [
        'views/views.xml',
        'security/ir.model.access.csv',
        'data/data.xml',
    ],
    'images':[],
    'license':'LGPL-3',
}
