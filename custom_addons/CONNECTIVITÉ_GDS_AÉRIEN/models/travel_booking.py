import requests
import logging
from odoo import models, fields, api
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

class GdsApiService(models.AbstractModel):
    _name = 'gds.api.service'
    _description = 'Service technique centralisé pour les requêtes GDS'

    @api.model
    def get_auth_token(self):
        get_param = self.env['ir.config_parameter'].sudo().get_param
        environment = get_param('api_gds.environment', 'test')
        client_id = get_param('api_gds.client_id')
        client_secret = get_param('api_gds.client_secret')

        if not client_id or not client_secret:
            raise UserError("Les identifiants API GDS (Client ID / Client Secret) ne sont pas configurés.")

        auth_url = "https://api.amadeus.com/v1/security/oauth2/token" if environment == 'production' else "https://test.api.amadeus.com/v1/security/oauth2/token"
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        payload = {'grant_type': 'client_credentials', 'client_id': client_id, 'client_secret': client_secret}

        try:
            response = requests.post(auth_url, headers=headers, data=payload, timeout=10)
            response.raise_for_status()
            return response.json().get('access_token')
        except requests.exceptions.RequestException as e:
            raise UserError(f"Échec de l'authentification OAuth2 : {str(e)}")


class ResAirportCity(models.Model):
    _name = 'res.airport.city'
    _description = 'Référentiel Villes et Aéroports IATA'
    _rec_name = 'display_name'

    city_name = fields.Char(string='Ville', required=True, index=True)
    airport_name = fields.Char(string="Nom de l'Aéroport", required=True)
    iata_code = fields.Char(string='Code IATA', size=3, required=True, index=True)
    display_name = fields.Char(string='Libellé', compute='_compute_display_name', store=True)

    @api.depends('city_name', 'airport_name', 'iata_code')
    def _compute_display_name(self):
        for record in self:
            record.display_name = f"{record.city_name} ({record.iata_code}) - {record.airport_name}"


class ResAirline(models.Model):
    _name = 'res.airline'
    _description = 'Référentiel Compagnies Aériennes IATA'
    _rec_name = 'display_name'

    airline_name = fields.Char(string='Nom de la compagnie', required=True)
    iata_code = fields.Char(string='Code IATA', size=2, required=True, index=True)
    display_name = fields.Char(string='Libellé', compute='_compute_display_name', store=True)

    @api.depends('airline_name', 'iata_code')
    def _compute_display_name(self):
        for record in self:
            record.display_name = f"{record.airline_name} ({record.iata_code})"


class TravelBooking(models.Model):
    _name = 'travel.booking'
    _description = 'Dossier de Réservation GDS'

    name = fields.Char(string='Référence', readonly=True, default='Nouveau')
    type_api = fields.Selection([('amadeus', 'Amadeus'), ('sabre', 'Sabre')], default='amadeus')
    pnr_code = fields.Char(string='Code PNR')
    
    # --- CHAMP ÉTAT (STATE) ---
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('confirmed', 'Confirmé')
    ], string='État', default='draft', tracking=True)

    # --- SECTION DÉPART & ARRIVÉE ---
    origin_airport_id = fields.Many2one('res.airport.city', string='Départ (Aéroport)', required=True)
    origin_code = fields.Char(string='IATA Départ', related='origin_airport_id.iata_code', store=True, readonly=True)

    destination_airport_id = fields.Many2one('res.airport.city', string='Arrivée (Aéroport)', required=True)
    destination_code = fields.Char(string='IATA Arrivée', related='destination_airport_id.iata_code', store=True, readonly=True)

    # --- CHAMPS COMPLÉMENTAIRES DE RECHERCHE ---
    trip_type = fields.Selection([
        ('one_way', 'Aller simple'),
        ('round_trip', 'Aller-retour')
    ], string='Type de voyage', default='one_way', required=True)
    
    departure_date = fields.Date(string='Date de départ', default=fields.Date.context_today, required=True)
    return_date = fields.Date(string='Date de retour')
    
    adults = fields.Integer(string='Adultes', default=1, required=True)
    children = fields.Integer(string='Enfants', default=0)
    infants = fields.Integer(string='Bébés', default=0)
    
    cabin_class = fields.Selection([
        ('ECONOMY', 'Économique'),
        ('PREMIUM_ECONOMY', 'Économique Premium'),
        ('BUSINESS', 'Affaires'),
        ('FIRST', 'Première')
    ], string='Classe de cabine', default='ECONOMY')
    
    preferred_airline_id = fields.Many2one('res.airline', string='Compagnie aérienne préférée')
    preferred_airline_code = fields.Char(string='Code IATA Compagnie', related='preferred_airline_id.iata_code', store=True, readonly=True)
    
    flight_details = fields.Text(string='Détails du vol (JSON)')

    @api.model
    def create(self, vals):
        if vals.get('name', 'Nouveau') == 'Nouveau':
            vals['name'] = self.env['ir.sequence'].next_by_code('travel.booking') or 'NV'
        return super(TravelBooking, self).create(vals)

    def action_fetch_pnr(self):
        self.ensure_one()
        if not self.pnr_code:
            raise UserError("Veuillez saisir un code PNR.")

        access_token = self.env['gds.api.service'].get_auth_token()
        base_url = "https://test.api.amadeus.com" 
        endpoint = f"{base_url}/v2/booking/flight-orders/{self.pnr_code}"
        
        try:
            response = requests.get(endpoint, headers={'Authorization': f'Bearer {access_token}'}, timeout=10)
            if response.status_code == 200:
                self.flight_details = response.text
                self.state = 'confirmed'
            else:
                raise UserError(f"Erreur GDS : {response.text}")
        except Exception as e:
            raise UserError(f"Erreur réseau : {str(e)}")

    def action_realtime_flight_search(self):
        self.ensure_one()
        if not self.origin_code or not self.destination_code:
            raise UserError("Les codes IATA de départ et d'arrivée sont requis.")

        access_token = self.env['gds.api.service'].get_auth_token()
        base_url = "https://test.api.amadeus.com"
        endpoint = f"{base_url}/v2/shopping/flight-offers"
        
        params = {
            'originLocationCode': self.origin_code,
            'destinationLocationCode': self.destination_code,
            'departureDate': str(self.departure_date),
            'adults': self.adults,
        }

        if self.children and self.children > 0:
            params['children'] = self.children
        if self.infants and self.infants > 0:
            params['infants'] = self.infants

        if self.trip_type == 'round_trip' and self.return_date:
            params['returnDate'] = str(self.return_date)

        if self.cabin_class:
            params['travelClass'] = self.cabin_class

        # Si une compagnie spécifique est choisie, on l'ajoute. Si le champ est vide, l'API cherchera sur toutes les compagnies.
        if self.preferred_airline_code:
            params['includedAirlineCodes'] = self.preferred_airline_code

        try:
            response = requests.get(endpoint, headers={'Authorization': f'Bearer {access_token}'}, params=params, timeout=10)
            if response.status_code == 200:
                self.flight_details = response.text
            else:
                raise UserError(f"Erreur API : {response.text}")
        except Exception as e:
            raise UserError(f"Erreur réseau : {str(e)}")