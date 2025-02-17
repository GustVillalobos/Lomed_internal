# -*- coding: utf-8 -*-
{
    'name': "Gestión de rutas",

    'summary': """
        Gestión de rutas
      """,

    'description': """
       Adecuaciones para poder gestionar pedidos por ruta, asignando gestor de cobros, ruta y pedidos a colocar.
    """,
    
    'author': "Gustavo Villalobos",
    'website': "",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '16.0',

    # any module necessary for this one to work correctly
    'depends': ['base','account','sale_management','fleet'],

    # always loaded
    'data': [
        'views/views.xml',
        'security/ir.model.access.csv',
        'data/data.xml',
        'views/res_config_settings.xml',
        'views/templates.xml',
    ],
    'installable': True,
    'application': True,
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
     'images': [''],
}
