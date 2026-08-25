{
    'name': 'Gestion des Blocs-Sièges et Rooming Lists',
    'version': '1.0',
    'category': 'Industries',
    'summary': 'Gestion des allotrements aériens, PNR blocs et rooming lists pour agence de voyage',
    'author': 'Maha El Allam',
    'depends': ['base', 'CONNECTIVITÉ_GDS_AÉRIEN'],
    'data': [
        'security/ir.model.access.csv',
        'views/airline_block_views.xml',
        'views/hotel_stay_views.xml',
    ],
    'installable': True,
    'application': True,
}