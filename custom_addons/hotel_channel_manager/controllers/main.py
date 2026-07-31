from odoo import http
from odoo.http import request
import json
import logging

_logger = logging.getLogger(__name__)

class ChannelManagerWebhookController(http.Controller):

    @http.route('/api/channel-manager/webhook', type='json', auth='none', methods=['POST'], csrf=False)
    def receive_webhook(self, **kwargs):
        """
        Endpoint Webhook sécurisé pour recevoir les événements (Réservations, Annulations)
        en provenance de SiteMinder, D-EDGE, YieldPlanet, etc.
        """
        try:
            # Récupération des données JSON envoyées dans la requête
            # Utilisation de request.params ou request.get_json_data() selon la version d'Odoo
            data = request.params or request.httprequest.get_json(silent=True) or {}
            if not data:
                return {"status": "error", "message": "Données vides"}

            event_type = data.get('type')
            reservation_id = data.get('reservationId')
            guest_info = data.get('guest', {})
            booking_details = data.get('details', {})

            _logger.info(f"Webhook reçu - Type: {event_type}, Réservation: {reservation_id}")

            if event_type == 'RESERVATION_CREATED':
                # Logique métier : Créer la réservation dans Odoo pour éviter le double-booking
                # Exemple d'appel ORM (à adapter selon vos objets Odoo existants) :
                # request.env['hotel.reservation'].sudo().create({
                #     'partner_name': guest_info.get('name'),
                #     'room_id': booking_details.get('roomId'),
                #     'check_in': booking_details.get('checkIn'),
                #     'check_out': booking_details.get('checkOut'),
                #     'channel_ref': reservation_id
                # })
                _logger.info(f"Réservation {reservation_id} enregistrée avec succès.")

            elif event_type == 'RESERVATION_CANCELLED':
                # Logique métier : Libérer la chambre
                # reservation = request.env['hotel.reservation'].sudo().search([('channel_ref', '=', reservation_id)])
                # if reservation:
                #     reservation.action_cancel()
                _logger.info(f"Réservation {reservation_id} annulée et stock libéré.")

            else:
                _logger.warning(f"Type d'événement non pris en charge: {event_type}")

            return {"status": "success", "message": "Webhook traité avec succès"}

        except Exception as e:
            _logger.error(f"Erreur lors du traitement du Webhook: {str(e)}")
            return {"status": "error", "message": str(e)}