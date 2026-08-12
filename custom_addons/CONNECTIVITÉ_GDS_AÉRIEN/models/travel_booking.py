import logging
from odoo import models, fields, api
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

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
    type_api = fields.Selection([
        ('amadeus', 'Amadeus'), 
        ('sabre', 'Sabre'),
        ('galileo', 'Galileo')
    ], string='Fournisseur GDS', default='amadeus', required=True)
    
    pnr_code = fields.Char(string='Code PNR')
    
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('confirmed', 'Confirmé')
    ], string='État', default='draft', tracking=True)

    origin_airport_id = fields.Many2one('res.airport.city', string='Départ (Aéroport)', required=True)
    origin_code = fields.Char(string='IATA Départ', related='origin_airport_id.iata_code', store=True, readonly=True)

    destination_airport_id = fields.Many2one('res.airport.city', string='Arrivée (Aéroport)', required=True)
    destination_code = fields.Char(string='IATA Arrivée', related='destination_airport_id.iata_code', store=True, readonly=True)

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
    

    flight_details = fields.Html(string='Détails du vol', sanitize=False)
    @api.model
    def create(self, vals):
        if vals.get('name', 'Nouveau') == 'Nouveau':
            vals['name'] = self.env['ir.sequence'].next_by_code('travel.booking') or 'NV'
        return super(TravelBooking, self).create(vals)

    def action_fetch_pnr(self):
        self.ensure_one()
        if not self.pnr_code:
            raise UserError("Veuillez saisir un code PNR.")

        # Routage PNR selon l'API sélectionnée
        if self.type_api == 'amadeus':
            return self.env['gds.amadeus.service'].fetch_pnr(self)
        elif self.type_api == 'sabre':
            return self.env['gds.sabre.service'].fetch_pnr(self)
        elif self.type_api == 'galileo':
            return self.env['gds.galileo.service'].fetch_pnr(self)
        else:
            raise UserError("Fournisseur GDS non pris en charge.")

    def action_realtime_flight_search(self):
        self.ensure_one()
        if not self.origin_code or not self.destination_code:
            raise UserError("Les codes IATA de départ et d'arrivée sont requis.")

        # Routage dynamique vers le service GDS sélectionné
        if self.type_api == 'amadeus':
            return self.env['gds.amadeus.service'].search_flights(self)
        elif self.type_api == 'sabre':
            return self.env['gds.sabre.service'].search_flights(self)
        elif self.type_api == 'galileo':
            return self.env['gds.galileo.service'].search_flights(self)
        else:
            raise UserError("Fournisseur GDS non pris en charge.")