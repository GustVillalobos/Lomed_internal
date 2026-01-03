# -*- coding: utf-8 -*-
{
    'name': "Categorias Servicio de asistencia",

    'summary': """
       Añade la posibilidad de gestionar las categorias por una categoría padre""",

    'description': """
        Añade la posibilidad de gestionar las categorias por una categoría padre
    """,

    'author': "Gustavo Villalobos",
    'website': "",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '16.0',

    # any module necessary for this one to work correctly
    'depends': ['base','helpdesk'],

    # always loaded
    'data': [
        'views/views.xml',
        'data/data.xml',
    ],
    'images':['static/description/icon.png'],
    'license':'LGPL-3',
}
