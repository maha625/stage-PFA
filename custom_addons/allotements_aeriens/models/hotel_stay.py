from odoo import models, fields, api

class TravelHotelStay(models.Model):
    _name = 'travel.hotel.stay'
    _description = 'Gestion des Séjours et Blocs Hôtels'

    name = fields.Char(string='Référence du Séjour / Contrat', required=True)
    hotel_name = fields.Char(string="Nom de l'Hôtel", required=True)
    destination = fields.Char(string='Destination / Ville')
    checkin_date = fields.Date(string="Date d'Arrivée (Check-in)", required=True)
    checkout_date = fields.Date(string="Date de Départ (Check-out)", required=True)
    
    board_basis = fields.Selection([
        ('room_only', 'Logement Seul'),
        ('bb', 'Petit-déjeuner (BB)'),
        ('hb', 'Demi-pension (HB)'),
        ('fb', 'Pension complète (FB)'),
        ('all_inclusive', 'All Inclusive')
    ], string='Régime', default='bb', required=True)

    # Relation One2many vers les lignes de types de chambres
    room_line_ids = fields.One2many('travel.hotel.room.line', 'stay_id', string='Détail des Chambres & Quotas')
    guest_line_ids = fields.One2many('travel.hotel.guest', 'stay_id', string='Rooming List / Occupants')

    # Champs calculés globaux pour tout le séjour
    total_rooms_allotted = fields.Integer(string='Total Chambres Allouées', compute='_compute_global_totals', store=True)
    total_rooms_sold = fields.Integer(string='Total Chambres Vendues', compute='_compute_global_totals', store=True)
    total_rooms_remaining = fields.Integer(string='Total Chambres Restantes', compute='_compute_global_totals', store=True)

    @api.depends('room_line_ids.total_allotted', 'room_line_ids.rooms_sold')
    def _compute_global_totals(self):
        for record in self:
            allotted = sum(record.room_line_ids.mapped('total_allotted'))
            sold = sum(record.room_line_ids.mapped('rooms_sold'))
            record.total_rooms_allotted = allotted
            record.total_rooms_sold = sold
            record.total_rooms_remaining = allotted - sold


class TravelHotelRoomLine(models.Model):
    _name = 'travel.hotel.room.line'
    _description = "Ligne de Type de Chambre (Allotment Hôtel)"

    stay_id = fields.Many2one('travel.hotel.stay', string='Séjour Hôtel', ondelete='cascade')
    
    room_type = fields.Selection([
        ('single', 'Single'),
        ('double', 'Double'),
        ('triple', 'Triple'),
        ('quadruple', 'Quadruple'),
        ('suite', 'Suite')
    ], string='Type de Chambre', default='double', required=True)
    
    total_allotted = fields.Integer(string='Allotment (Acheté)', required=True, default=1)
    rooms_sold = fields.Integer(
        string='Vendues', compute='_compute_rooms_sold', store=True
    )
    rooms_remaining = fields.Integer(string='Restantes', compute='_compute_room_line_remaining', store=True)
    
    price_unit = fields.Float(string='Prix Achat / Nuit')

    @api.depends('room_type', 'stay_id.guest_line_ids.room_type')
    def _compute_rooms_sold(self):
        room_capacity = {
            'single': 1,
            'double': 2,
            'triple': 3,
            'quadruple': 4,
            'suite': 2,
        }
        for line in self:
            capacity = room_capacity.get(line.room_type, 1)
            guest_count = len(
                line.stay_id.guest_line_ids.filtered(
                    lambda guest: guest.room_type == line.room_type
                )
            )
            line.rooms_sold = (guest_count + capacity - 1) // capacity

    @api.depends('total_allotted', 'rooms_sold')
    def _compute_room_line_remaining(self):
        for line in self:
            line.rooms_remaining = line.total_allotted - line.rooms_sold


class TravelHotelGuest(models.Model):
    _name = 'travel.hotel.guest'
    _description = 'Ligne Client / Rooming List'

    stay_id = fields.Many2one('travel.hotel.stay', string='Séjour Hôtel', ondelete='cascade')
    guest_name = fields.Char(string='Nom complet du Passager', required=True)
    room_type = fields.Selection([
        ('single', 'Single'),
        ('double', 'Double'),
        ('triple', 'Triple'),
        ('quadruple', 'Quadruple'),
        ('suite', 'Suite')
    ], string='Type de Chambre Occupé', default='double', required=True)
    room_number = fields.Char(string='N° de Chambre')
    phone = fields.Char(string='Téléphone')