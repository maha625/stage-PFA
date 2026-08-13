from odoo import models
from odoo.exceptions import UserError

class HotelSearchWizardWebBeds(models.Model):
    _inherit = 'hotel.search.wizard'

    def _search_webbeds(self):
        # Logique spécifique WebBeds à implémenter ici
        raise UserError("La connexion à l'API WebBeds est en cours de développement.")