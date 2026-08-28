from datetime import timedelta
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
    release_delay = fields.Integer(string="Délai Release (Jours)", default=21, help="Ex: 21 jours")
    release_date = fields.Datetime(string="Date de Release (Cut-Off)", compute='_compute_release_date', store=True)
    is_released = fields.Boolean(string="Rétrocédé", default=False, help="Indique si le stock non vendu a été restitué")

    @api.depends('departure_date', 'release_delay')
    def _compute_release_date(self):
        for record in self:
            if record.departure_date and record.release_delay:
                # Calcul : Date de départ + Délai release
                record.release_date = record.departure_date - timedelta(days=record.release_delay)
            else:
                record.release_date = False

    @api.depends('total_seats', 'passenger_line_ids.state')
    def _compute_seats_status(self):
        for record in self:
            sold = len(record.passenger_line_ids.filtered(lambda passenger: passenger.state == 'sold'))
            option = len(record.passenger_line_ids.filtered(lambda passenger: passenger.state == 'option'))
            record.seats_sold = sold
            record.seats_option = option
            record.seats_remaining = record.total_seats - sold - option

    def _cron_send_release_alerts(self):
        """Tâche planifiée : Envoie un e-mail d'alerte pour les blocs non rétrocédés"""
        print("--- DEBUT CRON AIRLINE ALERTS ---")
        
        # 1. Vérifions si le paramètre e-mail existe
        alert_email = self.env['ir.config_parameter'].sudo().get_param('api_gds.alert_email')
        print(f"1. Email de destination configuré : {alert_email}")
        if not alert_email:
            return

        # 2. Vérifions si le template existe en base
        template = self.env.ref('allotements_aeriens.email_template_airline_block_alert', raise_if_not_found=False)
        print(f"2. Template trouvé : {template}")
        if not template:
            return

        # 3. Récupérons les blocs
        blocks = self.search([('is_released', '=', False)])
        print(f"3. Nombre de blocs trouvés : {len(blocks)}")

        for block in blocks:
            print(f"-> Tentative d'envoi pour le bloc : {block.name}")
            template.send_mail(block.id, force_send=True, email_values={'email_to': alert_email})
            print(f"-> E-mail envoyé avec succès pour {block.name}")
        
        print("--- FIN CRON AIRLINE ALERTS ---")

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