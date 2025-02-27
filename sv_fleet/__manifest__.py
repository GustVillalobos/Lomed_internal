# -*- coding: utf-8 -*-
{
    'name': "Motocicletas para flota",

    'summary': """
        Adiciones al modulo de Flota
      """,

    'description': """
       Contiene las modificaciones necesarias para uso del modulo en El Salvador
    """,
    
    'author': "Gustavo Villalobos",
    'website': "",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '1.0',

    # any module necessary for this one to work correctly
    'depends': ['fleet','base','sv_dispatch_orders'],

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
     'images': [],
     'license':'LGPL-3',
}
