# -*- coding: utf-8 -*-
{
    'name': "CRM - Perfil comercial",

    'summary': """
       Perfil Comercial""",

    'description': """
        Genera un resumen del comportamiento comercial del cliente, con el fin de realizar los analisis correspondientes para fidelización o ventas
    """,

    'author': "Gustavo Villalobos",
    'website': "",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '16.0',

    # any module necessary for this one to work correctly
    'depends': ['base','sale_management','crm'],

    # always loaded
    'data': [
        'security/res_groups.xml',
        'views/sale_summary.xml',
        'security/ir.model.access.csv',
        'data/data.xml',
        'report/report_summary_sale.xml'
    ],
    'images':[],
    'license':'LGPL-3',
}
