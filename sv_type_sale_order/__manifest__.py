# -*- coding: utf-8 -*-
{
    'name': "Confirmar detalles de pedido",

    'summary': """Pantalla de confirmación de datos
      """,

    'description': """
       Agrega un pantalla adicional antes de confirmar para poder registrar reclamos, rectificaciones, garantias y cortesias en las ordenes de venta
    """,
    
    'author': "Gustavo Villalobos",
    'website': "",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '16.0.1.0',

    # any module necessary for this one to work correctly
    'depends': ['sale_management'],

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
}
