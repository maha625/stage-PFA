import requests
import logging
from odoo import models, fields, api
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

class HotelChannelManager(models.Model):
    _name = 'hotel.channel.manager'
    _description = 'Gestionnaire de Connexion Channel Manager'

    name = fields.Selection([
        ('siteminder', 'SiteMinder'),
        ('yieldplanet', 'YieldPlanet'),
        ('dedge', 'D-EDGE')
    ], string='Nom du Canal', required=True, default='siteminder')

    api_url = fields.Char(string='URL de l\'API Endpoint', required=True)
    api_token = fields.Char(string='Clé API / Token Bearer', required=True)
    hotel_id = fields.Char(string='ID de l\'Hôtel chez le Partenaire', required=True)
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('active', 'Actif'),
        ('inactive', 'Inactif')
    ], string='Statut', default='draft')

    def action_set_active(self):
            self.write({'state': 'active'})
    
    def action_set_inactive(self):
        self.write({'state': 'inactive'})

    def action_set_draft(self):
        self.write({'state': 'draft'})

    def action_push_availability_rates(self, inventory_data):
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
                _logger.error("Erreur API Channel Manager: %s", response.text)
                raise UserError(f"Échec de la synchronisation: {response.reason}")
        except requests.exceptions.RequestException as e:
            _logger.error("Erreur de connexion au Channel Manager: %s", e)
            raise UserError("Impossible de joindre le serveur du Channel Manager.")
    