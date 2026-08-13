from odoo import models
from odoo.exceptions import UserError

class HotelSearchWizardRateHawk(models.Model):
    _inherit = 'hotel.search.wizard'

    def _search_ratehawk(self):
        # Logique spécifique RateHawk à implémenter ici
        raise UserError("La connexion à l'API RateHawk est en cours de développement.")