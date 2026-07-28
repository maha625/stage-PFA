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
class TravelBooking(models.Model):
    _name = 'travel.booking'
    _description = 'Dossier de Réservation GDS'

    name = fields.Char(string='Référence Dossier', required=True, copy=False, readonly=True, default='Nouveau')
    pnr_code = fields.Char(string='Code PNR GDS', required=True, help='Code de réservation Amadeus / Sabre')
    flight_details = fields.Text(string='Détails du Vol (JSON Brut)', readonly=True)
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('confirmed', 'Confirmé / Émis'),
        ('cancelled', 'Annulé')
    ], string='Statut', default='draft', tracking=True)
    gds_provider = fields.Selection([
    ('amadeus', 'Amadeus'),
    ('sabre', 'Sabre')
], string="Fournisseur GDS", default='amadeus', required=True)
    @api.model
    def create(self, vals):
        if vals.get('name', 'Nouveau') == 'Nouveau':
            vals['name'] = self.env['ir.sequence'].next_by_code('travel.booking') or 'NV'
        return super(TravelBooking, self).create(vals)
    def action_fetch_pnr(self):
        """Action déclenchée par le bouton pour interroger l'API GDS et importer le PNR."""
        self.ensure_one()
        if not self.pnr_code:
            raise UserError("Veuillez saisir un code PNR valide avant de lancer l'extraction.")

        # 1. Obtenir le token via le socle api_gds
        access_token = self.env['gds.api.service'].get_auth_token()

        # 2. Déterminer l'URL (Test ou Prod)
        get_param = self.env['ir.config_parameter'].sudo().get_param
        environment = get_param('api_gds.environment', 'test')
        
        base_url = "https://test.api.amadeus.com" if environment == 'test' else "https://api.amadeus.com"
        endpoint = f"{base_url}/v2/booking/flight-orders/{self.pnr_code}"

        headers = {
            'Authorization': f'Bearer {access_token}',
            'Accept': 'application/vnd.amadeus+json'
        }

        try:
            response = requests.get(endpoint, headers=headers, timeout=10)
            
            if response.status_code == 200:
                self.flight_details = response.text
                self.state = 'confirmed'
            else:
                raise UserError(f"Erreur GDS (Code {response.status_code}) : {response.text}")

        except requests.exceptions.RequestException as e:
            raise UserError(f"Erreur de connexion réseau avec l'API GDS : {str(e)}")
    def action_search_flights(self):
        """Recherche de vols et vérification des disponibilités via Amadeus"""
        self.ensure_one()
        access_token = self.env['gds.api.service'].get_auth_token()
        get_param = self.env['ir.config_parameter'].sudo().get_param
        base_url = "https://test.api.amadeus.com" if get_param('api_gds.environment', 'test') == 'test' else "https://api.amadeus.com"
        
        endpoint = f"{base_url}/v2/shopping/flight-offers"
        headers = {'Authorization': f'Bearer {access_token}'}
        
        # Exemple de paramètres de recherche (à adapter selon vos champs de saisie)
        params = {
            'originLocationCode': 'PAR',
            'destinationLocationCode': 'NYC',
            'departureDate': '2026-10-15',
            'adults': 1
        }

        try:
            response = requests.get(endpoint, headers=headers, params=params, timeout=10)
            if response.status_code == 200:
                self.flight_details = response.text
            else:
                raise UserError(f"Erreur Recherche Vol : {response.text}")
        except requests.exceptions.RequestException as e:
            raise UserError(f"Erreur réseau : {str(e)}")

    def action_create_pnr(self):
        """Création d'un PNR (Flight Creation / Order)"""
        self.ensure_one()
        access_token = self.env['gds.api.service'].get_auth_token()
        get_param = self.env['ir.config_parameter'].sudo().get_param
        base_url = "https://test.api.amadeus.com" if get_param('api_gds.environment', 'test') == 'test' else "https://api.amadeus.com"
        
        endpoint = f"{base_url}/v1/booking/flight-orders"
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        # Corps de la requête JSON pour créer le PNR (structure type Amadeus)
        payload = {
            "data": {
                "type": "flight-order",
                # Ajoutez ici la structure des passagers et des offres choisies
            }
        }

        try:
            response = requests.post(endpoint, json=payload, headers=headers, timeout=10)
            if response.status_code in [200, 201]:
                self.flight_details = response.text
                self.state = 'confirmed'
            else:
                raise UserError(f"Erreur Création PNR : {response.text}")
        except requests.exceptions.RequestException as e:
            raise UserError(f"Erreur réseau : {str(e)}")

    def action_realtime_flight_search(self):
        """Recherche de vols en temps réel via l'API Amadeus Flight Offers Search"""
        self.ensure_one()
        
        # 1. Obtenir le token d'accès via le socle api_gds
        access_token = self.env['gds.api.service'].get_auth_token()

        # 2. Déterminer l'URL selon l'environnement (Test ou Production)
        get_param = self.env['ir.config_parameter'].sudo().get_param
        environment = get_param('api_gds.environment', 'test')
        base_url = "https://test.api.amadeus.com" if environment == 'test' else "https://api.amadeus.com"
        
        # Endpoint officiel Amadeus pour la recherche d'offres de vol
        endpoint = f"{base_url}/v2/shopping/flight-offers"

        headers = {
            'Authorization': f'Bearer {access_token}',
            'Accept': 'application/vnd.amadeus+json'
        }

        # Paramètres de recherche en temps réel (vous pouvez les rendre dynamiques via des champs Odoo)
        params = {
            'originLocationCode': 'CMN',      # Exemple : Casablanca (ou un champ de votre choix)
            'destinationLocationCode': 'PAR', # Exemple : Paris
            'departureDate': '2026-09-15',    # Date de départ souhaitée
            'adults': 1                       # Nombre de passagers
        }

        try:
            response = requests.get(endpoint, headers=headers, params=params, timeout=10)
            
            if response.status_code == 200:
                # Affichage direct du résultat JSON en temps réel dans l'onglet de la vue
                self.flight_details = response.text
            else:
                raise UserError(f"Erreur API Amadeus en temps réel (Code {response.status_code}) : {response.text}")

        except requests.exceptions.RequestException as e:
            raise UserError(f"Erreur de connexion réseau avec l'API Amadeus : {str(e)}")
