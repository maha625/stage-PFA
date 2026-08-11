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