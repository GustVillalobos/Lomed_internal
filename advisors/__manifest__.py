# -*- coding: utf-8 -*-
{
    'name': "Asesores",

    'summary': """
       Permite diferenciar asesores""",

    'description': """
        Añade campos y funciones para distinguir y controlar la actividad de los asesores
    """,

    'author': "Gustavo Villalobos",
    'website': "",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '16.0',

    # any module necessary for this one to work correctly
    'depends': ['base','account','sale'],

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
