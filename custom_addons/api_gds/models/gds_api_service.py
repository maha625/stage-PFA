import requests
from odoo import models, fields, api
from odoo.exceptions import UserError

class GdsApiService(models.AbstractModel):
    _name = 'gds.api.service'
    _description = 'Service technique centralisé pour les requêtes GDS'

    @api.model
    def get_auth_token(self):
        """Récupère dynamiquement le Token OAuth2 auprès du fournisseur GDS."""
        get_param = self.env['ir.config_parameter'].sudo().get_param
        environment = get_param('api_gds.environment', 'test')
        client_id = get_param('api_gds.client_id')
        client_secret = get_param('api_gds.client_secret')

        if not client_id or not client_secret:
            raise UserError("Les identifiants API GDS (Client ID / Client Secret) ne sont pas configurés dans les Paramètres.")

        # URL de l'API selon l'environnement (exemple type Amadeus Self-Service)
        if environment == 'production':
            auth_url = "https://api.amadeus.com/v1/security/oauth2/token"
        else:
            auth_url = "https://test.api.amadeus.com/v1/security/oauth2/token"

        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        payload = {
            'grant_type': 'client_credentials',
            'client_id': client_id,
            'client_secret': client_secret
        }

        try:
            response = requests.post(auth_url, headers=headers, data=payload, timeout=10)
            response.raise_for_status()
            token_data = response.json()
            return token_data.get('access_token')
        except requests.exceptions.RequestException as e:
            raise UserError(f"Échec de l'authentification OAuth2 auprès du GDS : {str(e)}")