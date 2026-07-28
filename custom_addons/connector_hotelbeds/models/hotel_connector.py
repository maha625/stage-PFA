import hashlib
import time
import requests
from odoo import models, fields, api
from odoo.exceptions import UserError

class HotelConnector(models.Model):
    _name = 'hotel.connector'
    _description = 'Gestion Connecteur Hotelbeds'

    name = fields.Char(string='Nom de la liaison', required=True, default='Hotelbeds API')
    api_endpoint = fields.Char(string='URL API REST', required=True, default='https://api.test.hotelbeds.com/hotel-api/1.0')
    active = fields.Boolean(default=True)
    
    last_search_result = fields.Text(string='Dernier Résultat JSON / Disponibilités', readonly=True)

    def _get_headers(self):
        self.ensure_one()
        get_param = self.env['ir.config_parameter'].sudo().get_param
        api_key = (get_param('api_gds.hotelbeds_api_key') or '').strip()
        shared_secret = (get_param('api_gds.hotelbeds_shared_secret') or '').strip()

        if not api_key or not shared_secret:
            raise UserError("Veuillez renseigner l'API Key et le Shared Secret dans le menu de configuration GDS.")
        
        timestamp = str(int(time.time()))
        signature_string = api_key + shared_secret + timestamp
        signature = hashlib.sha256(signature_string.encode('utf-8')).hexdigest()

        return {
            'Api-key': api_key,
            'X-Signature': signature,
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }

    def action_check_availability(self):
        """ Interrogation directe des disponibilités, tarifs et affichage dans Odoo """
        self.ensure_one()
        url = f"{self.api_endpoint}/hotels"
        headers = self._get_headers()
        
        payload = {
            "stay": {
                "checkIn": "2026-09-01",
                "checkOut": "2026-09-05"
            },
            "occupancies": [
                {"rooms": 1, "adults": 2, "children": 0}
            ],
            "hotels": {
                "hotel": [10001, 10002]
            }
        }

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            if response.status_code == 200:
                data = response.json()
                self.last_search_result = str(data)
                
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'Succès',
                        'message': 'Disponibilités et tarifs récupérés et affichés dans la fiche !',
                        'type': 'success',
                        'sticky': False,
                    }
                }
            else:
                raise UserError(f"Erreur API Hotelbeds ({response.status_code}): {response.text}")
        except requests.exceptions.RequestException as e:
            raise UserError(f"Erreur de connexion réseau : {str(e)}")

    def action_book_room(self, booking_payload):
        """ Réservation instantanée et récupération du numéro de confirmation """
        self.ensure_one()
        url = f"{self.api_endpoint}/bookings"
        headers = self._get_headers()

        response = requests.post(url, json=booking_payload, headers=headers, timeout=30)
        if response.status_code == 200:
            booking_data = response.json()
            reference_code = booking_data.get('booking', {}).get('reference')
            return reference_code
        else:
            raise UserError(f"Échec de la réservation instantanée : {response.text}")