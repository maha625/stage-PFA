{
    'name': 'Connecteur GDS Amadeus',
    'version': '18.0.1.0.0',
    'category': 'Sales/Travel',
    'summary': 'Intégration GDS Amadeus en temps réel (Extraction PNR)',
    'depends': ['base', 'sale', 'api_gds'],
    'data': [
        'security/ir.model.access.csv',
        'views/amadeus_views.xml',
    ],
    'installable': True,
    'application': True,
}