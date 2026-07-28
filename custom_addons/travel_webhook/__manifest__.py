{
    'name': 'Travel Webhook & Real-Time Sync',
    'version': '1.0',
    'category': 'Sales/Travel',
    'summary': 'Réception de webhooks fournisseurs et synchronisation en temps réel',
    'description': """
        Ce module permet de :
        - Recevoir des webhooks externes (annulations de vol, changements d'horaires).
        - Mettre à jour automatiquement les réservations.
        - Alerter instantanément l'agent de voyage en temps réel.
    """,
    'author': 'Votre Nom',
    'depends': ['base', 'base_automation', 'mail'],
    'data': [
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}