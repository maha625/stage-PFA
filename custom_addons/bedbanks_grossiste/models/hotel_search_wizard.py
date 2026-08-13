from odoo import models, fields, api
from odoo.exceptions import UserError

class HotelSearchWizard(models.Model):
    _name = 'hotel.search.wizard'
    _description = 'Assistant de Recherche Hôtelière Global'
    _order = 'create_date desc'

    # Sélecteur d'API
    api_provider = fields.Selection([
        ('hotelbeds', 'Hotelbeds'),
        ('ratehawk', 'RateHawk'),
        ('webbeds', 'WebBeds')
    ], string='Grossiste / API', required=True, default='hotelbeds')

    checkin_date = fields.Date(string='Date d\'Arrivée', required=True, default=fields.Date.context_today)
    checkout_date = fields.Date(string='Date de Départ', required=True)
    
    city = fields.Char(string='Ville', placeholder='ex: Marrakech, Paris')
    country = fields.Char(string='Pays', placeholder='ex: Morocco, Spain')
    destination_code = fields.Char(string='Code Destination / Ville', help="Code spécifique au grossiste.")
    
    rooms = fields.Integer(string='Chambres', default=1)
    adults = fields.Integer(string='Adultes', default=2)
    children = fields.Integer(string='Enfants', default=0)
    child_age = fields.Integer(string='Âge de l\'enfant', default=8)
    
    max_hotels = fields.Integer(string='Limite max. d\'hôtels', default=10)
    search_results = fields.Html(string='Résultats des Offres', readonly=True)

    def action_search_hotels(self):
        self.ensure_one()
        self.flush_recordset()

        # Dispatcher vers le fichier / méthode du grossiste sélectionné
        if self.api_provider == 'hotelbeds':
            return self._search_hotelbeds()
        elif self.api_provider == 'ratehawk':
            return self._search_ratehawk()
        elif self.api_provider == 'webbeds':
            return self._search_webbeds()
        else:
            raise UserError("Veuillez sélectionner un grossiste valide.")