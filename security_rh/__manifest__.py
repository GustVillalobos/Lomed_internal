# -*- coding: utf-8 -*-
{
    'name': "Permisos sobre salarios",

    'summary': """
       Permite limitar el acceso a la funcion de edicion de salario""",

    'description': """
        Permite limitar el acceso a la funcion de edicion del campo salario en contratos
    """,

    'author': "Gustavo Villalobos",
    'website': "",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Technical',
    'version': '16.0',

    # any module necessary for this one to work correctly
    'depends': ['base','hr','hr_contract'],

    # always loaded
    'data': [
        'views/views.xml',
        'security/ir.model.access.csv',
        'data/data.xml',
    ],
    # only loaded in demonstration mode
    'demo': [],
    'images':[],
    'license':'LGPL-3',
}
