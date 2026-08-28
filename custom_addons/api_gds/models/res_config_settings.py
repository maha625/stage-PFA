from odoo import fields, models

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    # --- Amadeus ---
    amadeus_environment = fields.Selection([
        ('test', 'Test / Sandbox'),
        ('production', 'Production')
    ], string="Environnement Amadeus", default='test', config_parameter='api_gds.amadeus_environment')
    
    amadeus_client_id = fields.Char(string="Client ID (Amadeus)", config_parameter='api_gds.amadeus_client_id')
    amadeus_client_secret = fields.Char(string="Client Secret (Amadeus)", config_parameter='api_gds.amadeus_client_secret')

    # --- Sabre ---
    sabre_environment = fields.Selection([
        ('test', 'Test / Sandbox'),
        ('production', 'Production')
    ], string="Environnement Sabre", default='test', config_parameter='api_gds.sabre_environment')
    
    sabre_client_id = fields.Char(string="Client ID (Sabre)", config_parameter='api_gds.sabre_client_id')
    sabre_client_secret = fields.Char(string="Client Secret (Sabre)", config_parameter='api_gds.sabre_client_secret')
    sabre_pcc = fields.Char(string="PCC (Sabre)", config_parameter='api_gds.sabre_pcc', help="Pseudo City Code ou iPCC Sabre")

    # --- Galileo ---
    galileo_environment = fields.Selection([
        ('test', 'Test / Sandbox'),
        ('production', 'Production')
    ], string="Environnement Galileo", default='test', config_parameter='api_gds.galileo_environment')
    
    galileo_client_id = fields.Char(string="Client ID (Galileo)", config_parameter='api_gds.galileo_client_id')
    galileo_client_secret = fields.Char(string="Client Secret (Galileo)", config_parameter='api_gds.galileo_client_secret')

    # --- Hotelbeds & Autres ---
    hotelbeds_api_key = fields.Char(string="API Key (Hotelbeds)", config_parameter='api_gds.hotelbeds_api_key')
    hotelbeds_shared_secret = fields.Char(string="Shared Secret (Hotelbeds)", config_parameter='api_gds.hotelbeds_shared_secret')

    api_ninjas_key = fields.Char(
        string="API Key (API Ninjas)", 
        config_parameter='api_gds.api_ninjas_key',
        help="Clé API utilisée pour la recherche d'aéroports externes"
    )
    siteminder_api_token = fields.Char(string="Token API SiteMinder", config_parameter='api_gds.siteminder_api_token')

    # --- YieldPlanet ---
    yieldplanet_api_token = fields.Char(string="Token API YieldPlanet", config_parameter='api_gds.yieldplanet_api_token')

    # --- D-EDGE ---
    dedge_api_token = fields.Char(string="Token API D-EDGE", config_parameter='api_gds.dedge_api_token')
    # --- Paramètre d'alerte e-mail global ---
    alert_email = fields.Char(
        string="E-mail d'alerte par défaut (Rétrocession)", 
        config_parameter='api_gds.alert_email',
        help="Adresse e-mail utilisée par défaut pour les alertes automatiques de stock"
    )