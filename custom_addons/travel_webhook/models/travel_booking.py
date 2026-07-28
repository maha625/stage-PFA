from odoo import models, fields, api

class TravelBooking(models.Model):
    _name = 'travel.booking'
    _description = 'Réservation de Voyage'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Référence / Dossier', required=True, tracking=True)
    flight_status = fields.Selection([
        ('confirmed', 'Confirmé'),
        ('schedule_change', 'Changement d’horaire'),
        ('flight_cancellation', 'Annulation de vol'),
        ('transfer_confirmed', 'Confirmation de transfert')
    ], string='Statut Fournisseur', default='confirmed', tracking=True)
    
    agent_id = fields.Many2one('res.users', string='Agent de voyage assigné', tracking=True)
    last_supplier_update = fields.Text(string='Dernières notes du fournisseur', tracking=True)

    def write(self, vals):
        res = super(TravelBooking, self).write(vals)
        # S'appuie sur la logique d'automatisation pour notifier l'agent en temps réel
        if 'flight_status' in vals or 'last_supplier_update' in vals:
            for record in self:
                if record.agent_id:
                    self.env['mail.activity'].create({
                        'res_model_id': self.env['ir.model']._get('travel.booking').id,
                        'res_id': record.id,
                        'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
                        'summary': 'Alerte Temps Réel : Événement Fournisseur',
                        'note': f'Mise à jour reçue. Statut actuel : {record.flight_status}. Détails : {record.last_supplier_update or "Aucun"}',
                        'user_id': record.agent_id.id,
                    })
        return res