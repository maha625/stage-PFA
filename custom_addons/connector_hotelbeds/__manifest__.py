{
    'name': 'Connecteur Hotelbeds',
    'version': '18.0.1.0.0',
    'category': 'Sales/API',
    'summary': 'Interrogation directe via API REST Hotelbeds',
    'author': 'Maha El Allam',
    'depends': ['base', 'sale'],
    'data': [
        'security/ir.model.access.csv',
        'views/hotel_connector_views.xml',  # <-- Ajoutez cette ligne ici
        'views/hotel_search_wizard_views.xml',  # <-- Ajoutez cette ligne ici
    ],
    'installable': True,
    'application': True, # Passé à True pour afficher un menu principal dédié
    'auto_install': False,
    'license': 'LGPL-3',
}