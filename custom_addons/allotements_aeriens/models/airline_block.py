from odoo import api, fields, models


class TravelAirlineBlock(models.Model):
    _name = 'travel.airline.block'
    _description = 'Gestion des Blocs-Sièges et Rooming Lists'

    name = fields.Char(string='Référence du Bloc', required=True)
    airline_id = fields.Many2one('res.airline', string='Compagnie Aérienne')
    flight_number = fields.Char(string='Numéro de Vol')
    departure_date = fields.Datetime(string='Date de Départ')

    total_seats = fields.Integer(string='Sièges Achetés (Total)', required=True)
    seats_sold = fields.Integer(string='Sièges Vendus', compute='_compute_seats_status', store=True)
    seats_option = fields.Integer(string='Sièges en Option', compute='_compute_seats_status', store=True)
    seats_remaining = fields.Integer(string='Sièges Restants', compute='_compute_seats_status', store=True)

    pnr_block = fields.Char(string='Numéro PNR Bloc')
    rooming_deadline = fields.Datetime(string="Date d'émission de la Rooming List")

    passenger_line_ids = fields.One2many(
        'travel.rooming.line', 'block_id', string='Rooming List (Passagers)'
    )

    @api.depends('total_seats', 'passenger_line_ids.state')
    def _compute_seats_status(self):
        for record in self:
            sold = len(record.passenger_line_ids.filtered(lambda passenger: passenger.state == 'sold'))
            option = len(record.passenger_line_ids.filtered(lambda passenger: passenger.state == 'option'))
            record.seats_sold = sold
            record.seats_option = option
            record.seats_remaining = record.total_seats - sold - option


class TravelRoomingLine(models.Model):
    _name = 'travel.rooming.line'
    _description = 'Ligne Rooming List Passager'

    block_id = fields.Many2one('travel.airline.block', string='Bloc Aérien', ondelete='cascade')
    passenger_name = fields.Char(string='Nom complet du Passager', required=True)
    passport_number = fields.Char(string='Numéro de Passeport')
    state = fields.Selection(
        [('option', 'En Option'), ('sold', 'Vendu / Confirmé')],
        string='Statut Siège',
        default='option',
        required=True,
    )