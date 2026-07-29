import hashlib
import time
import requests
from odoo import models, fields, api
from odoo.exceptions import UserError

class HotelSearchWizard(models.Model):
    _name = 'hotel.search.wizard'
    _description = 'Assistant de Recherche Hôtelière Global'
    _order = 'create_date desc'

    checkin_date = fields.Date(string='Date d\'Arrivée', required=True, default=fields.Date.context_today)
    checkout_date = fields.Date(string='Date de Départ', required=True)
    
    city = fields.Char(string='Ville', placeholder='ex: Marrakech, Paris')
    country = fields.Char(string='Pays', placeholder='ex: Morocco, Spain')
    destination_code = fields.Char(string='Code Destination API (Auto)', help="Généré automatiquement ou saisi manuellement.")
    
    rooms = fields.Integer(string='Chambres', default=1)
    adults = fields.Integer(string='Adultes', default=2)
    children = fields.Integer(string='Enfants', default=0)
    child_age = fields.Integer(string='Âge de l\'enfant', default=8, help="Âge requis par Hotelbeds si des enfants voyagent.")
    
    max_hotels = fields.Integer(string='Limite max. d\'hôtels', default=10)
    search_results = fields.Html(string='Résultats des Offres', readonly=True)

    @api.depends('city', 'destination_code', 'checkin_date')
    def _compute_display_name(self):
        for record in self:
            dest = record.city or record.destination_code or 'Inconnue'
            date_in = record.checkin_date or ''
            record.display_name = f"Recherche {dest} ({date_in})"

    def _get_api_headers(self):
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

    def _resolve_destination_code(self, headers):
        if self.destination_code:
            return self.destination_code

        if not self.city:
            raise UserError("Veuillez renseigner au moins une ville pour lancer la recherche.")

        url = f"https://api.test.hotelbeds.com/hotel-api/1.0/locations/destinations?codes={self.city.upper()}&from=1&to=5"
        
        try:
            response = requests.get(url, headers=headers, timeout=15)
            if response.status_code == 200:
                data = response.json()
                destinations = data.get('destinations', [])
                if destinations:
                    return destinations[0].get('code')
        except Exception:
            pass

        city_lower = (self.city or '').lower()
        mapping_secours = {
            'marrakech': 'RAK',
            'casablanca': 'CMN',
            'agadir': 'AGA',
            'tanger': 'TNG',
            'fes': 'FEZ',
            'rabat': 'RBA',
            'paris': 'PAR',
            'majorque': 'PMI',
            'palma': 'PMI'
        }
        
        return mapping_secours.get(city_lower, self.city.upper()[:3])

    def action_search_hotels(self):
        self.ensure_one()
        self.flush_recordset()
        headers = self._get_api_headers()
        
        resolved_code = self._resolve_destination_code(headers)
        self.destination_code = resolved_code

        url = "https://api.test.hotelbeds.com/hotel-api/1.0/hotels"

        occupancies_list = []
        for _ in range(self.rooms):
            paxes_list = []
            if self.children > 0:
                for _c in range(self.children):
                    paxes_list.append({
                        "type": "CH",
                        "age": self.child_age
                    })

            occupancies_list.append({
                "rooms": 1,
                "adults": self.adults,
                "children": self.children,
                "paxes": paxes_list
            })

        payload = {
            "stay": {
                "checkIn": str(self.checkin_date),
                "checkOut": str(self.checkout_date)
            },
            "occupancies": occupancies_list,
            "destination": {
                "code": resolved_code
            }
        }

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            if response.status_code == 200:
                data = response.json()
                hotels_data = data.get('hotels', {}).get('hotels', [])
                currency = data.get('hotels', {}).get('currency', 'EUR')

                if self.max_hotels > 0:
                    hotels_data = hotels_data[:self.max_hotels]

                lieu_str = f"{self.city or ''} {('(' + self.country + ')') if self.country else ''} [Code: {resolved_code}]".strip()

                if not hotels_data:
                    self.search_results = f"<div class='alert alert-warning'>Aucun hôtel trouvé pour <b>{lieu_str}</b> du {self.checkin_date} au {self.checkout_date}.</div>"
                else:
                    html_content = f"""
                    <div style="font-family: Arial, sans-serif; font-size: 13px;">
                        <div style="background: #e9ecef; padding: 10px; border-radius: 4px; margin-bottom: 15px;">
                            <strong>📍 Lieu :</strong> {lieu_str} <br/>
                            <strong>📅 Séjour :</strong> Du {self.checkin_date} au {self.checkout_date} | 
                            <strong>👥 Voyageurs :</strong> {self.adults} Adulte(s), {self.children} Enfant(s) | 
                            <strong>🏨 Affichés :</strong> {len(hotels_data)} hôtel(s) max
                        </div>
                    """
                    
                    for h in hotels_data:
                        hotel_name = h.get('name', 'Hôtel Inconnu')
                        category = h.get('categoryName', 'Standard')
                        code = h.get('code')
                        
                        html_content += f"""
                        <div style="border: 1px solid #ced4da; border-radius: 4px; padding: 10px; margin-bottom: 10px; background: #fff;">
                            <div style="font-weight: bold; color: #0056b3; font-size: 14px; border-bottom: 1px solid #eee; padding-bottom: 4px; margin-bottom: 6px;">
                                {hotel_name} <span style="color: #6c757d; font-weight: normal; font-size: 12px;">({category} - Code: {code})</span>
                            </div>
                        """
                        
                        rooms_list = h.get('rooms', [])
                        if rooms_list:
                            html_content += "<table style='width: 100%; border-collapse: collapse; font-size: 12px;'>"
                            html_content += "<tr style='background: #f8f9fa; text-align: left;'><th style='padding: 4px; border-bottom: 1px solid #ddd;'>Chambre</th><th style='padding: 4px; border-bottom: 1px solid #ddd;'>Régime / Pension</th><th style='padding: 4px; border-bottom: 1px solid #ddd; text-align: right;'>Prix Net</th></tr>"
                            
                            for room in rooms_list:
                                room_name = room.get('name', 'Chambre')
                                rates = room.get('rates', [])
                                for rate in rates:
                                    board = rate.get('boardName', 'Standard')
                                    net_price = rate.get('net', '0.00')
                                    html_content += f"""
                                    <tr>
                                        <td style='padding: 4px; border-bottom: 1px solid #f1f1f1;'>{room_name}</td>
                                        <td style='padding: 4px; border-bottom: 1px solid #f1f1f1;'>{board}</td>
                                        <td style='padding: 4px; border-bottom: 1px solid #f1f1f1; text-align: right; color: #28a745; font-weight: bold;'>{net_price} {currency}</td>
                                    </tr>
                                    """
                            html_content += "</table>"
                        else:
                            html_content += "<span style='color: #dc3545; font-style: italic;'>Pas de chambres disponibles.</span>"
                        
                        html_content += "</div>"
                    
                    html_content += "</div>"
                    self.search_results = html_content
            else:
                raise UserError(f"Erreur API Hotelbeds ({response.status_code}): {response.text}")
        except requests.exceptions.RequestException as e:
            raise UserError(f"Erreur réseau : {str(e)}")

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'hotel.search.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'current',
        }