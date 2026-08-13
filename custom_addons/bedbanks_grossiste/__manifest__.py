{
    'name': 'BEDBANKS & GROSSISTES',
    'version': '18.0.1.0.0',
    'category': 'Sales/API',
    'summary': 'Connecteur APIs Grossistes Hôteliers (Hotelbeds, RateHawk, WebBeds)',
    'author': 'Maha El Allam',
    'depends': ['base', 'sale'],
    'data': [
        'security/ir.model.access.csv',
        'views/hotel_search_wizard_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}