# -*- coding: utf-8 -*-
{
    'name': "Impresión de contrato",

    'summary': """
       Permite imprimir un contrato individual de trabajo""",

    'description': """
        Te proporciona las herramientas para imprimir un formato de contrato individual de trabajo, esto ajustado a la normativa legal de El Salvador.
    """,

    'author': "Gustavo Villalobos",
    'website': "",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Human Resources',
    'version': '16.0',

    # any module necessary for this one to work correctly
    'depends': ['base','hr','hr_contract'],

    # always loaded
    'data': [
        'views/views.xml',
        'security/ir.model.access.csv',
        'data/data.xml',
        'reports/contract_report.xml',
    ],
    'images':[],
    'license':'LGPL-3',
}
