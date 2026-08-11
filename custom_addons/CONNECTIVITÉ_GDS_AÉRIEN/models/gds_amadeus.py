import requests
import logging
from odoo import models, api
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

class GdsAmadeusService(models.AbstractModel):
    _name = 'gds.amadeus.service'
    _description = 'Service technique Amadeus'

    @api.model
    def get_auth_token(self):
        get_param = self.env['ir.config_parameter'].sudo().get_param
        environment = get_param('api_gds.amadeus_environment', 'test')
        client_id = get_param('api_gds.amadeus_client_id')
        client_secret = get_param('api_gds.amadeus_client_secret')

        if not client_id or not client_secret:
            raise UserError("Les identifiants API Amadeus (Client ID / Client Secret) ne sont pas configurés.")

        auth_url = "https://api.amadeus.com/v1/security/oauth2/token" if environment == 'production' else "https://test.api.amadeus.com/v1/security/oauth2/token"
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        payload = {'grant_type': 'client_credentials', 'client_id': client_id, 'client_secret': client_secret}

        try:
            response = requests.post(auth_url, headers=headers, data=payload, timeout=10)
            response.raise_for_status()
            return response.json().get('access_token')
        except requests.exceptions.RequestException as e:
            raise UserError(f"Échec de l'authentification OAuth2 Amadeus : {str(e)}")

    @api.model
    def search_flights(self, booking):
        access_token = self.get_auth_token()
        environment = self.env['ir.config_parameter'].sudo().get_param('api_gds.amadeus_environment', 'test')
        base_url = "https://api.amadeus.com" if environment == 'production' else "https://test.api.amadeus.com"
        endpoint = f"{base_url}/v2/shopping/flight-offers"
        
        params = {
            'originLocationCode': booking.origin_code,
            'destinationLocationCode': booking.destination_code,
            'departureDate': str(booking.departure_date),
            'adults': booking.adults,
        }

        if booking.children and booking.children > 0:
            params['children'] = booking.children
        if booking.infants and booking.infants > 0:
            params['infants'] = booking.infants
        if booking.trip_type == 'round_trip' and booking.return_date:
            params['returnDate'] = str(booking.return_date)
        if booking.cabin_class:
            params['travelClass'] = booking.cabin_class
        if booking.preferred_airline_code:
            params['includedAirlineCodes'] = booking.preferred_airline_code

        try:
            response = requests.get(endpoint, headers={'Authorization': f'Bearer {access_token}'}, params=params, timeout=10)
            if response.status_code == 200:
                booking.flight_details = response.text
            else:
                raise UserError(f"Erreur API Amadeus : {response.text}")
        except Exception as e:
            raise UserError(f"Erreur réseau Amadeus : {str(e)}")

    @api.model
    def fetch_pnr(self, booking):
        access_token = self.get_auth_token()
        environment = self.env['ir.config_parameter'].sudo().get_param('api_gds.amadeus_environment', 'test')
        base_url = "https://api.amadeus.com" if environment == 'production' else "https://test.api.amadeus.com"
        endpoint = f"{base_url}/v2/booking/flight-orders/{booking.pnr_code}"
        
        try:
            response = requests.get(endpoint, headers={'Authorization': f'Bearer {access_token}'}, timeout=10)
            if response.status_code == 200:
                booking.flight_details = response.text
                booking.state = 'confirmed'
            else:
                raise UserError(f"Erreur GDS Amadeus : {response.text}")
        except Exception as e:
            raise UserError(f"Erreur réseau Amadeus : {str(e)}")