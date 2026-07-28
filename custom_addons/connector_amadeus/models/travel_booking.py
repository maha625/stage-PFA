import requests
from odoo import models, fields, api
from odoo.exceptions import UserError

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

    @api.model
    def create(self, vals):
        if vals.get('name', 'Nouveau') == 'Nouveau':
            vals['name'] = self.env['ir.sequence'].next_by_code('travel.booking') or 'NV'
        return super(TravelBooking, self.create, vals)

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