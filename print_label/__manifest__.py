# -*- coding: utf-8 -*-
{
    'name': "Imprimir etiqueta",

    'summary': """
       Función para imprimir etiquetas""",

    'description': """
        Funcion que integra ZebraBrowserPrint con Odoo para poder enviar impresiones de código ZPL directo al impresor
    """,

    'author': "Gustavo Villalobos",
    'website': "",

    # Categories can be used to filter modules in modules listing
    'category': 'Uncategorized',
    'version': '16.0',

    # any module necessary for this one to work correctly
    'depends': ['base'],

    # always loaded
    'data': [],
    'assets':{
        'web.assets_backend':[
            '/print_label/static/src/js/BrowserPrint-3.0.216.min.js',
            '/print_label/static/src/js/BrowserPrint-Zebra-1.0.216.min.js',
            '/print_label/static/src/js/label.js',
            ]
    },
    # only loaded in demonstration mode
    'demo': [],

    'images':[],
    'license':'LGPL-3',
}
