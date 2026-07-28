import requests
from odoo import models, api
from odoo.exceptions import UserError

class ApiGdsMixin(models.AbstractModel):
    _name = 'api.gds.mixin'
    _description = 'Mixin technique pour les appels API GDS'

    @api.model
    def _get_oauth_token(self, provider='amadeus'):
        """Gère l'obtention du token d'accès OAuth2 pour Amadeus ou Sabre"""
        get_param = self.env['ir.config_parameter'].sudo().get_param
        env_type = get_param('api_gds.environment', 'test')

        if provider == 'amadeus':
            client_id = get_param('api_gds.amadeus_client_id')
            client_secret = get_param('api_gds.amadeus_client_secret')
            # URLs de test vs production Amadeus
            url = "https://api.test.amadeus.com/v1/security/oauth2/token" if env_type == 'test' else "https://api.amadeus.com/v1/security/oauth2/token"
            payload = {
                'grant_type': 'client_credentials',
                'client_id': client_id,
                'client_secret': client_secret
            }
            headers = {'Content-Type': 'application/x-www-form-urlencoded'}

        elif provider == 'sabre':
            client_id = get_param('api_gds.sabre_client_id')
            client_secret = get_param('api_gds.sabre_client_secret')
            # URLs de test vs production Sabre (exemple simplifié)
            url = "https://api.cert.sabre.com/v2/auth/token" if env_type == 'test' else "https://api.sabre.com/v2/auth/token"
            # Sabre utilise souvent du Basic Auth pour le token
            payload = {'grant_type': 'client_credentials'}
            # Note: Encoder les credentials en Base64 selon les specs exactes de Sabre si requis
            headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        else:
            raise UserError(f"Fournisseur GDS inconnu : {provider}")

        try:
            response = requests.post(url, data=payload, headers=headers, timeout=10)
            if response.status_code == 200:
                res_data = response.json()
                return res_data.get('access_token')
            else:
                raise UserError(f"Erreur d'authentification {provider.capitalize()} : {response.text}")
        except requests.exceptions.RequestException as e:
            raise UserError(f"Impossible de joindre le serveur {provider.capitalize()} : {str(e)}")