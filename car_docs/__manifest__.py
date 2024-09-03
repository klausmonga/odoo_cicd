# -*- coding: utf-8 -*-
{
    'name': "Car Docs",

    'summary': "MEMOIRE UDBL",

    'description': """
            
    """,

    'author': "",
    'website': "https://www.yourcompany.com",

    'category': 'Uncategorized',
    'version': '17.0',

    'depends': ['base', 'mail', 'project', 'web'],

    'data': [
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'data/ir_minister_data.xml',
        'data/ir_nature_data.xml',
        'data/ir_action_data.xml',
        'data/activity_document.xml',
        'data/email_document.xml',
        'data/ir_project_task_type_data.xml',
        'views/menu.xml',
        'views/control_nature.xml',
        'views/control_minister.xml',
        'views/control_document.xml',
        'views/control_action.xml',
        'views/project_task.xml',
    ],
    'images': ['car_docs/static/description/icon.png'],
    'assets': {
        'web.assets_backend': [
            'car_docs/static/src/js/dashboard.js',
            'car_docs/static/src/xml/dashboard.xml',
        ],
    },
    'application': True,
    'installable': True,
}
