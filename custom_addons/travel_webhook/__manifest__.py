{
    'name': 'Travel Webhook & Real-Time Sync',
    'version': '1.0',
    'category': 'Sales/Travel',
    'summary': 'Réception de webhooks fournisseurs et synchronisation en temps réel',
    'description': """
        Ce module permet de recevoir instantanément des événements fournisseurs (annulation de vol, changement d’horaire, confirmation de transfert) afin d'alerter automatiquement l'agent.
        """,
    'author': 'Maha El Allam',
    'depends': ['base', 'base_automation', 'mail'],
    'data': [
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}