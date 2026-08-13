import requests
import logging
from odoo import models, fields, api
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

class HotelChannelManager(models.Model):
    _name = 'hotel.channel.manager'
    _description = 'Gestionnaire de Connexion Channel Manager par Hôtel'

    name = fields.Selection([
        ('siteminder', 'SiteMinder'),
        ('yieldplanet', 'YieldPlanet'),
        ('dedge', 'D-EDGE')
    ], string='Nom du Canal', required=True, default='siteminder')

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
        
        # URLs de base fixes pour chaque canal (à adapter selon les documentations officielles)
        base_urls = {
            'siteminder': 'https://api.siteminder.com/v1',
            'yieldplanet': 'https://api.yieldplanet.com/v1',
            'dedge': 'https://api.d-edge.com/v1'
        }

        base_url = base_urls.get(self.name)
        if not base_url:
            raise UserError(f"Aucune URL définie pour le canal '{self.name}'.")

        # Récupération du Token global depuis la configuration
        get_param = self.env['ir.config_parameter'].sudo().get_param
        token_keys = {
            'siteminder': 'api_gds.siteminder_api_token',
            'yieldplanet': 'api_gds.yieldplanet_api_token',
            'dedge': 'api_gds.dedge_api_token'
        }
        
        api_token = get_param(token_keys.get(self.name))
        if not api_token:
            raise UserError(f"Le Token API pour '{self.name}' n'est pas configuré dans les réglages globaux.")

        headers = {
            'Authorization': f"Bearer {api_token}",
            'Content-Type': 'application/json'
        }
        endpoint = f"{base_url}/hotels/{self.hotel_id}/inventory"

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