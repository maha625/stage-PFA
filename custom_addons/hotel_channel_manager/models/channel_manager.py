import requests
import logging
from odoo import models, fields, api
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

class HotelChannelManager(models.Model):
    _name = 'hotel.channel.manager'
    _description = 'Gestionnaire de Connexion Channel Manager'

    name = fields.Char(string='Nom du Canal', required=True, help="Ex: SiteMinder, D-EDGE")
    api_url = fields.Char(string='URL de l\'API Endpoint', required=True)
    api_token = fields.Char(string='Clé API / Token Bearer', required=True)
    hotel_id = fields.Char(string='ID de l\'Hôtel chez le Partenaire', required=True)
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('active', 'Actif'),
        ('inactive', 'Inactif')
    ], string='Statut', default='draft')

    def action_push_availability_rates(self, inventory_data):
        """
        Méthode Push : Envoie les mises à jour de prix et de disponibilités 
        vers le Channel Manager externe via API REST.
        """
        self.ensure_one()
        headers = {
            'Authorization': f'Bearer {self.api_token}',
            'Content-Type': 'application/json'
        }
        endpoint = f"{self.api_url}/hotels/{self.hotel_id}/inventory"

        try:
            response = requests.post(endpoint, json=inventory_data, headers=headers, timeout=10)
            if response.status_code == 200:
                _logger.info("Synchronisation Channel Manager réussie.")
                return True
            else:
                _logger.error(f"Erreur API Channel Manager: {response.text}")
                raise UserError(f"Échec de la synchronisation: {response.reason}")
        except requests.exceptions.RequestException as e:
            _logger.error(f"Erreur de connexion au Channel Manager: {e}")
            raise UserError("Impossible de joindre le serveur du Channel Manager.")