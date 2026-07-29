from odoo import http
from odoo.http import request

class TravelWebhookController(http.Controller):

    @http.route('/api/v1/webhook/purchase', type='json', auth='public', methods=['POST'], csrf=False)
    def receive_purchase_webhook(self, **kwargs):
        params = request.params
        
        # Récupération des paramètres envoyés depuis l'extérieur (Postman, etc.)
        doc_type = params.get('doc_type', 'sale.order')
        doc_ref = params.get('doc_ref') or params.get('order_ref')
        action = params.get('action', 'update')
        details = params.get('details', '')

        if not doc_ref:
            return {"status": "error", "message": "Référence du document manquante (doc_ref ou order_ref)."}

        # Modèles autorisés dans Odoo (adaptés à votre contexte)
        allowed_models = {
            'sale.order': 'Devis / Commande client',
            'purchase.order': 'Commande fournisseur',
            'account.move': 'Facture',
        }

        if doc_type not in allowed_models:
            return {"status": "error", "message": f"Type de document '{doc_type}' non géré."}

        # 1. Recherche dynamique du document dans Odoo
        record = request.env[doc_type].sudo().search([('name', '=', str(doc_ref))], limit=1)

        if not record:
            return {"status": "error", "message": f"Document '{doc_ref}' introuvable dans le modèle {doc_type}."}

        # 2. Traitement des actions basées sur les événements fournisseurs
        if action in ['flight_cancellation', 'cancel']:
            if hasattr(record, 'action_cancel'):
                record.action_cancel()
            message = f"🚨 Annulation Fournisseur : {details}"
        elif action == 'schedule_change':
            message = f"⏰ Changement d'horaire Fournisseur : {details}"
        elif action == 'transfer_confirmed':
            message = f"✅ Confirmation de transfert : {details}"
        else:
            message = f"ℹ️ Mise à jour Fournisseur : {details}"

        # 3. Publication automatique dans le Chatter du document
        record.message_post(body=message)

        return {"status": "success", "message": f"Le document {doc_ref} a été mis à jour avec succès."}