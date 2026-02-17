# -*- coding: utf-8 -*-
{
    'name': "Reglas de descuento",

    'summary': """
       Reglas de descuento de cliente""",

    'description': """
        Te permite añadir, configurar y administrar reglas para aplicar descuentos visibles por cliente.
    """,

    'author': "Gustavo Villalobos",
    'website': "",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '16.0',

    # any module necessary for this one to work correctly
    'depends': ['base','sale'],

    # always loaded
    'data': [
        'data/data.xml',
        'views/views.xml',
        'views/discount_rule.xml',
        'security/ir.model.access.csv',
    ],
    'images':['static/description/icon.png'],
    'license':'LGPL-3',
}
