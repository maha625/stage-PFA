from odoo import http
from odoo.http import request

class SaleOrderWebhookController(http.Controller):

    @http.route('/api/v1/webhook/purchase', type='json', auth='public', methods=['POST'], csrf=False)
    def receive_sale_webhook(self, order_ref=None, event_type=None, details='', **kwargs):
        
        # Si order_ref n'est pas capturé directement, on essaie de le lire depuis request.params
        if not order_ref:
            params = request.params
            order_ref = params.get('order_ref')
            event_type = params.get('event_type')
            details = params.get('details', '')

        if not order_ref:
            return {"status": "error", "message": "Aucun order_ref reçu dans la requête."}

        # Recherche de la commande de vente
        sale_order = request.env['sale.order'].sudo().search([('name', '=', str(order_ref))], limit=1)
        
        if not sale_order:
            return {"status": "error", "message": f"Devis introuvable pour la valeur : '{order_ref}'"}

        # Si trouvé, on ajoute le message dans le Chatter
        sale_order.message_post(
            body=f"<b>Alerte Fournisseur :</b> Le fournisseur a refusé. Détails : {details} (Événement : {event_type})"
        )

        return {"status": "success", "message": f"Devis {order_ref} mis à jour avec succès."}