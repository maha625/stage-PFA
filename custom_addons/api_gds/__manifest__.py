{
    'name': 'API GDS Socle Technique',
    'version': '18.0.1.0.0',
    'category': 'Sales/Travel',
    'summary': 'Socle technique de gestion des configurations et tokens GDS (Amadeus/Sabre)',
    'depends': ['base', 'base_setup'],
    'data': [
        'security/ir.model.access.csv',
        'views/res_config_settings_views.xml',
    ],
    'installable': True,
    'application': False,
}