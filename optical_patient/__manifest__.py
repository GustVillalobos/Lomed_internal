# -*- coding: utf-8 -*-
{
    'name': "Lentexpress",

    'summary': """
       Gestion de pacientes y examenes visuales""",

    'description': """
        Módulo para registro de pacientes, control de citas e historia clínica
    """,

    'author': "Gustavo Villalobos",
    'website': "",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '16.0',

    # any module necessary for this one to work correctly
    'depends': ['base','sale','account','product'],

    # always loaded
    'data': [
        'security/res_groups.xml',
        'data/op_disease.xml',
        'data/op_specialty.xml',
        'data/op_tags.xml',
        'views/op_reception.xml',
        'views/op_patient.xml',
        'views/op_tags.xml',
        'views/op_disease.xml',
        'views/op_physician.xml',
        'views/op_wizard_create_order.xml',
        'views/op_appointment.xml',
        'views/views.xml',
        'security/ir.model.access.csv',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    'images':[],
    'license':'LGPL-3',
}
