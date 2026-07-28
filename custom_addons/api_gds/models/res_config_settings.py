from odoo import fields, models

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    gds_environment = fields.Selection([
        ('test', 'Test / Sandbox'),
        ('production', 'Production')
    ], string="Environnement GDS", default='test', config_parameter='api_gds.environment')
    
    gds_client_id = fields.Char(
        string="Client ID", 
        config_parameter='api_gds.client_id'
    )
    
    gds_client_secret = fields.Char(
        string="Client Secret", 
        config_parameter='api_gds.client_secret'
    )

    # Nouveaux champs pour Hotelbeds / Grossistes
    hotelbeds_api_key = fields.Char(
        string="API Key (Hotelbeds)", 
        config_parameter='api_gds.hotelbeds_api_key'
    )

    hotelbeds_shared_secret = fields.Char(
        string="Shared Secret (Hotelbeds)", 
        config_parameter='api_gds.hotelbeds_shared_secret'
    )