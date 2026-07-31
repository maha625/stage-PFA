{
    'name': 'Hotel Channel Manager',
    'version': '1.0',
    'category': 'Hospitality',
    'summary': 'Synchronisation Channel Manager (SiteMinder, D-EDGE, YieldPlanet)',
    'description': """
        Module de synchronisation en temps réel pour Channel Manager hôtelier :
        - Envoi des tarifs et disponibilités (Push)
        - Réception des réservations et annulations via Webhooks (Pull)
    """,
    'author': 'Maha El Allam',
    'depends': ['base'],
    'data': [
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}