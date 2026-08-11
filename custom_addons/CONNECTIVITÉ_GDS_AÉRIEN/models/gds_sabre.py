import requests
import base64
import json
import logging

from odoo import models, api
from odoo.exceptions import UserError


_logger = logging.getLogger(__name__)


class GdsSabreService(models.AbstractModel):

    _name = 'gds.sabre.service'
    _description = 'Service technique Sabre'

    # ============================================================
    # DEBUG RÉPONSE SABRE
    # ============================================================

    @api.model
    def _log_sabre_response(
        self,
        response,
        title="RÉPONSE SABRE"
    ):

        _logger.warning("")
        _logger.warning(
            "============================================================"
        )
        _logger.warning(
            "                  %s",
            title
        )
        _logger.warning(
            "============================================================"
        )

        _logger.warning(
            "HTTP Status : %s",
            response.status_code
        )

        _logger.warning(
            "Reason      : %s",
            response.reason
        )

        _logger.warning(
            "URL finale  : %s",
            response.url
        )

        _logger.warning("")
        _logger.warning(
            "Contenu brut retourné par Sabre :"
        )

        if response.text:
            _logger.warning(
                "%s",
                response.text
            )
        else:
            _logger.warning(
                "(Réponse vide)"
            )

        try:

            json_data = response.json()

            _logger.warning("")
            _logger.warning(
                "JSON retourné par Sabre :"
            )

            _logger.warning(
                "%s",
                json.dumps(
                    json_data,
                    indent=4,
                    ensure_ascii=False
                )
            )

        except ValueError:

            _logger.warning(
                "La réponse Sabre n'est pas un JSON valide."
            )

        _logger.warning("")
        _logger.warning(
            "============================================================"
        )
        _logger.warning(
            "                    FIN RÉPONSE SABRE"
        )
        _logger.warning(
            "============================================================"
        )
        _logger.warning("")

    # ============================================================
    # AUTHENTIFICATION SABRE
    # ============================================================

    @api.model
    def get_auth_token(self):

        get_param = (
            self.env['ir.config_parameter']
            .sudo()
            .get_param
        )

        environment = get_param(
            'api_gds.sabre_environment',
            'test'
        )

        client_id = get_param(
            'api_gds.sabre_client_id'
        )

        client_secret = get_param(
            'api_gds.sabre_client_secret'
        )

        # ========================================================
        # VALIDATION
        # ========================================================

        if not client_id:
            raise UserError(
                "Le Client ID Sabre n'est pas configuré."
            )

        if not client_secret:
            raise UserError(
                "Le Client Secret Sabre n'est pas configuré."
            )

        # ========================================================
        # NETTOYAGE
        # ========================================================

        client_id = str(client_id).strip()
        client_secret = str(client_secret).strip()

        # ========================================================
        # URL AUTHENTIFICATION
        # ========================================================

        if environment == 'production':

            auth_url = (
                "https://api.platform.sabre.com"
                "/v2/auth/token"
            )

        else:

            auth_url = (
                "https://api.cert.platform.sabre.com"
                "/v2/auth/token"
            )

        # ========================================================
        # CONSTRUCTION BASIC AUTH
        #
        # Sabre utilise :
        #
        # Base64(
        #     Base64(client_id)
        #     :
        #     Base64(client_secret)
        # )
        # ========================================================

        client_id_b64 = base64.b64encode(
            client_id.encode("utf-8")
        ).decode("ascii")

        client_secret_b64 = base64.b64encode(
            client_secret.encode("utf-8")
        ).decode("ascii")

        credentials = (
            f"{client_id_b64}:{client_secret_b64}"
        )

        basic_credentials = base64.b64encode(
            credentials.encode("ascii")
        ).decode("ascii")

        # ========================================================
        # HEADERS
        # ========================================================

        headers = {
            "Authorization": (
                f"Basic {basic_credentials}"
            ),
            "Content-Type": (
                "application/x-www-form-urlencoded"
            ),
            "Accept": "application/json",
        }

        payload = {
            "grant_type": "client_credentials"
        }

        # ========================================================
        # LOG DEBUG
        # ========================================================

        _logger.warning("")
        _logger.warning(
            "============================================================"
        )
        _logger.warning(
            "              AUTHENTIFICATION SABRE"
        )
        _logger.warning(
            "============================================================"
        )

        _logger.warning(
            "Environnement : %s",
            environment
        )

        _logger.warning(
            "URL OAuth : %s",
            auth_url
        )

        _logger.warning(
            "Client ID présent : %s",
            bool(client_id)
        )

        _logger.warning(
            "Client Secret présent : %s",
            bool(client_secret)
        )

        # NE JAMAIS afficher les credentials
        _logger.warning(
            "Longueur Client ID : %s",
            len(client_id)
        )

        _logger.warning(
            "Longueur Client Secret : %s",
            len(client_secret)
        )

        _logger.warning(
            "Client ID commence par : %s",
            client_id[:4] if len(client_id) >= 4 else "***"
        )

        _logger.warning(
            "Client Secret commence par : %s",
            client_secret[:4] if len(client_secret) >= 4 else "***"
        )

        _logger.warning(
            "Grant type : %s",
            payload["grant_type"]
        )

        _logger.warning(
            "============================================================"
        )

        # ========================================================
        # APPEL OAUTH
        # ========================================================

        try:

            response = requests.post(
                auth_url,
                headers=headers,
                data=payload,
                timeout=30
            )

        except requests.exceptions.RequestException as e:

            _logger.exception(
                "Erreur réseau pendant l'authentification Sabre"
            )

            raise UserError(
                "Impossible de contacter Sabre : "
                f"{str(e)}"
            )

        # ========================================================
        # LOG RÉPONSE
        # ========================================================

        self._log_sabre_response(
            response,
            "RÉPONSE AUTHENTIFICATION SABRE"
        )

        # ========================================================
        # ERREUR HTTP
        # ========================================================

        if response.status_code != 200:

            _logger.error(
                "Authentification Sabre échouée."
            )

            _logger.error(
                "HTTP Status : %s",
                response.status_code
            )

            _logger.error(
                "Réponse Sabre : %s",
                response.text
            )

            # ----------------------------------------------------
            # 401
            # ----------------------------------------------------

            if response.status_code == 401:

                raise UserError(
                    "Authentification Sabre refusée (401).\n\n"
                    "Vérifiez :\n"
                    "• Client ID\n"
                    "• Client Secret\n"
                    "• environnement Sabre (test/production)\n"
                    "• credentials correspondant à l'environnement\n"
                    "• absence d'espaces ou retours à la ligne "
                    "dans les credentials."
                )

            raise UserError(
                "Erreur authentification Sabre "
                f"[{response.status_code}] :\n"
                f"{response.text}"
            )

        # ========================================================
        # JSON
        # ========================================================

        try:

            data = response.json()

        except ValueError:

            raise UserError(
                "Sabre a retourné une réponse qui "
                "n'est pas un JSON valide."
            )

        # ========================================================
        # TOKEN
        # ========================================================

        access_token = data.get(
            "access_token"
        )

        if not access_token:

            _logger.error(
                "Sabre n'a pas retourné access_token."
            )

            _logger.error(
                "JSON reçu : %s",
                json.dumps(
                    data,
                    indent=4,
                    ensure_ascii=False
                )
            )

            raise UserError(
                "Sabre n'a pas retourné de token "
                "d'authentification."
            )

        # ========================================================
        # INFORMATIONS TOKEN
        # ========================================================

        token_type = data.get(
            "token_type",
            "unknown"
        )

        expires_in = data.get(
            "expires_in",
            "unknown"
        )

        _logger.warning("")
        _logger.warning(
            "============================================================"
        )
        _logger.warning(
            "          AUTHENTIFICATION SABRE RÉUSSIE"
        )
        _logger.warning(
            "============================================================"
        )

        _logger.warning(
            "Token obtenu : OUI"
        )

        _logger.warning(
            "Type token : %s",
            token_type
        )

        _logger.warning(
            "Expiration : %s secondes",
            expires_in
        )

        # NE PAS afficher le token complet
        _logger.warning(
            "Longueur token : %s",
            len(access_token)
        )

        _logger.warning(
            "Token début : %s...",
            access_token[:15]
        )

        _logger.warning(
            "============================================================"
        )

        return access_token
    # ============================================================
    # CLASSE CABINE
    # ============================================================

    @api.model
    def _get_sabre_cabin_class(
        self,
        cabin_class
    ):

        if not cabin_class:
            return None

        value = (
            str(cabin_class)
            .strip()
            .upper()
        )

        mapping = {

            'ECONOMY': 'Y',
            'ECONOMIC': 'Y',
            'ECONOMIQUE': 'Y',
            'ÉCONOMIQUE': 'Y',
            'Y': 'Y',

            'PREMIUM_ECONOMY': 'S',
            'PREMIUM ECONOMY': 'S',
            'PREMIUM-ECONOMY': 'S',
            'PREMIUM': 'S',
            'PREMIUM_ECONOMIC': 'S',
            'PREMIUM ECONOMIC': 'S',
            'S': 'S',

            'BUSINESS': 'C',
            'BUSINESS CLASS': 'C',
            'BUSINESS_CLASS': 'C',
            'AFFAIRES': 'C',
            'C': 'C',

            'FIRST': 'F',
            'FIRST CLASS': 'F',
            'FIRST_CLASS': 'F',
            'PREMIERE': 'F',
            'PREMIÈRE': 'F',
            'PREMIERE CLASSE': 'F',
            'PREMIÈRE CLASSE': 'F',
            'F': 'F',
        }

        cabin_code = mapping.get(value)

        if not cabin_code:

            raise UserError(
                "Classe de cabine inconnue : "
                f"'{cabin_class}'."
            )

        return cabin_code

    # ============================================================
    # CLASSES DE RÉSERVATION
    # ============================================================

    @api.model
    def _get_booking_classes(
        self,
        cabin_class
    ):

        if not cabin_class:
            return []

        value = (
            str(cabin_class)
            .strip()
            .upper()
        )

        if value in (
            'ECONOMY',
            'ECONOMIC',
            'ECONOMIQUE',
            'ÉCONOMIQUE',
            'Y',
        ):

            return [
                'Y',
                'B',
                'M',
                'H',
                'K',
                'Q',
                'V',
                'W',
                'T',
                'L',
                'U',
                'G',
                'N',
                'O',
                'S',
                'E',
                'X',
            ]

        if value in (
            'PREMIUM_ECONOMY',
            'PREMIUM ECONOMY',
            'PREMIUM-ECONOMY',
            'PREMIUM',
            'PREMIUM_ECONOMIC',
            'PREMIUM ECONOMIC',
            'S',
        ):

            return [
                'S',
                'W',
                'E',
            ]

        if value in (
            'BUSINESS',
            'BUSINESS CLASS',
            'BUSINESS_CLASS',
            'AFFAIRES',
            'C',
        ):

            return [
                'C',
                'J',
                'D',
                'I',
                'Z',
            ]

        if value in (
            'FIRST',
            'FIRST CLASS',
            'FIRST_CLASS',
            'PREMIERE',
            'PREMIÈRE',
            'PREMIERE CLASSE',
            'PREMIÈRE CLASSE',
            'F',
        ):

            return [
                'F',
                'A',
                'P',
            ]

        return []

    # ============================================================
    # DEBUG TARIFICATION PASSAGERS
    # ============================================================

    @api.model
    def _debug_passenger_fares(
        self,
        data,
        booking
    ):

        _logger.warning("")
        _logger.warning(
            "============================================================"
        )
        _logger.warning(
            "             DEBUG TARIFICATION PASSAGERS"
        )
        _logger.warning(
            "============================================================"
        )

        _logger.warning(
            "PASSAGERS DEMANDÉS DANS ODOO"
        )

        _logger.warning(
            "Adultes : %s",
            booking.adults or 0
        )

        _logger.warning(
            "Enfants : %s",
            booking.children or 0
        )

        _logger.warning(
            "Bébés   : %s",
            booking.infants or 0
        )

        itineraries = data.get(
            'PricedItineraries',
            []
        )

        _logger.warning(
            "Nombre itinéraires : %s",
            len(itineraries)
        )

        for index, itinerary in enumerate(
            itineraries[:5],
            1
        ):

            pricing = itinerary.get(
                'AirItineraryPricingInfo',
                {}
            )

            _logger.warning("")
            _logger.warning(
                "---------------- ITINÉRAIRE %s ----------------",
                index
            )

            ptc = pricing.get(
                'PTC_FareBreakdowns',
                {}
            )

            _logger.warning(
                "PTC_FareBreakdowns :"
            )

            _logger.warning(
                "%s",
                json.dumps(
                    ptc,
                    indent=4,
                    ensure_ascii=False
                )
            )

        _logger.warning(
            "============================================================"
        )
        _logger.warning(
            "          FIN DEBUG TARIFICATION PASSAGERS"
        )
        _logger.warning(
            "============================================================"
        )

    # ============================================================
    # RECHERCHE VOLS
    # ============================================================

    @api.model
    def search_flights(
        self,
        booking
    ):

        # --------------------------------------------------------
        # AUTHENTIFICATION
        # --------------------------------------------------------

        access_token = (
            self.get_auth_token()
        )

        get_param = (
            self.env['ir.config_parameter']
            .sudo()
            .get_param
        )

        environment = get_param(
            'api_gds.sabre_environment',
            'test'
        )

        # --------------------------------------------------------
        # URL
        # --------------------------------------------------------

        if environment == 'production':

            base_url = (
                "https://api.platform.sabre.com"
            )

        else:

            base_url = (
                "https://api.cert.platform.sabre.com"
            )

        endpoint = (
            f"{base_url}/v2/shop/flights"
        )

        # --------------------------------------------------------
        # VALIDATION
        # --------------------------------------------------------

        if not booking.origin_code:

            raise UserError(
                "L'aéroport de départ est obligatoire."
            )

        if not booking.destination_code:

            raise UserError(
                "L'aéroport de destination est obligatoire."
            )

        if not booking.departure_date:

            raise UserError(
                "La date de départ est obligatoire."
            )

        # --------------------------------------------------------
        # PASSAGERS
        # --------------------------------------------------------

        adults = int(
            booking.adults or 0
        )

        children = int(
            booking.children or 0
        )

        infants = int(
            booking.infants or 0
        )

        if adults <= 0:

            adults = 1

        # --------------------------------------------------------
        # PARAMÈTRES SABRE
        # --------------------------------------------------------

        params = {

            'origin':
                booking.origin_code
                .strip()
                .upper(),

            'destination':
                booking.destination_code
                .strip()
                .upper(),

            'departuredate':
                str(booking.departure_date),

            'adt':
                adults,
        }

        # --------------------------------------------------------
        # ALLER RETOUR
        # --------------------------------------------------------

        if (
            booking.trip_type == 'round_trip'
            and booking.return_date
        ):

            if (
                booking.return_date
                <= booking.departure_date
            ):

                raise UserError(
                    "La date de retour doit être "
                    "postérieure à la date de départ."
                )

            params['returndate'] = (
                str(booking.return_date)
            )

        # --------------------------------------------------------
        # ENFANTS
        # --------------------------------------------------------

        if children > 0:

            params['cnn'] = children

        # --------------------------------------------------------
        # BÉBÉS
        # --------------------------------------------------------

        if infants > 0:

            params['inf'] = infants

        # --------------------------------------------------------
        # CLASSE
        # --------------------------------------------------------

        if booking.cabin_class:

            params['cabinclass'] = (
                self._get_sabre_cabin_class(
                    booking.cabin_class
                )
            )

        # --------------------------------------------------------
        # LOG PASSAGERS
        # --------------------------------------------------------

        _logger.warning("")
        _logger.warning(
            "============================================================"
        )
        _logger.warning(
            "                    REQUÊTE SABRE"
        )
        _logger.warning(
            "============================================================"
        )

        _logger.warning(
            "Origin      : %s",
            params.get('origin')
        )

        _logger.warning(
            "Destination : %s",
            params.get('destination')
        )

        _logger.warning(
            "Départ      : %s",
            params.get('departuredate')
        )

        _logger.warning(
            "Retour      : %s",
            params.get('returndate')
        )

        _logger.warning(
            "Adultes     : %s",
            params.get('adt')
        )

        _logger.warning(
            "Enfants     : %s",
            params.get('cnn', 0)
        )

        _logger.warning(
            "Bébés       : %s",
            params.get('inf', 0)
        )

        _logger.warning(
            "Cabine      : %s",
            params.get('cabinclass')
        )

        _logger.warning(
            "PARAMÈTRES COMPLETS : %s",
            params
        )

        _logger.warning(
            "============================================================"
        )

        headers = {

            'Authorization':
                f'Bearer {access_token}',

            'Accept':
                'application/json',
        }

        # --------------------------------------------------------
        # APPEL SABRE
        # --------------------------------------------------------

        try:

            response = requests.get(
                endpoint,
                headers=headers,
                params=params,
                timeout=30
            )

            self._log_sabre_response(
                response,
                "RÉPONSE RECHERCHE VOLS SABRE"
            )

            # ----------------------------------------------------
            # ERREURS
            # ----------------------------------------------------

            if response.status_code != 200:

                try:

                    error_json = (
                        response.json()
                    )

                    error_text = json.dumps(
                        error_json,
                        indent=4,
                        ensure_ascii=False
                    )

                except ValueError:

                    error_text = (
                        response.text
                    )

                _logger.error(
                    "Erreur API Sabre HTTP %s : %s",
                    response.status_code,
                    error_text
                )

                booking.flight_details = (
                    f"❌ Erreur API Sabre "
                    f"[{response.status_code}] :\n\n"
                    f"{error_text}"
                )

                return booking.flight_details

            # ----------------------------------------------------
            # JSON
            # ----------------------------------------------------

            try:

                raw_data = (
                    response.json()
                )

            except ValueError:

                raise UserError(
                    "Sabre a répondu avec un "
                    "JSON invalide."
                )

            # ----------------------------------------------------
            # JSON COMPLET
            # ----------------------------------------------------

            _logger.warning("")
            _logger.warning(
                "============================================================"
            )
            _logger.warning(
                "             JSON COMPLET RETOURNÉ PAR SABRE"
            )
            _logger.warning(
                "============================================================"
            )

            _logger.warning(
                "%s",
                json.dumps(
                    raw_data,
                    indent=4,
                    ensure_ascii=False
                )
            )

            _logger.warning(
                "============================================================"
            )

            # ----------------------------------------------------
            # DEBUG PASSAGERS
            # ----------------------------------------------------

            self._debug_passenger_fares(
                raw_data,
                booking
            )

            # ----------------------------------------------------
            # CLASSES
            # ----------------------------------------------------

            self._log_returned_classes(
                raw_data
            )

            # ----------------------------------------------------
            # FILTRE CABINE
            # ----------------------------------------------------

            filtered_data = (
                self._apply_cabin_filter(
                    raw_data,
                    booking
                )
            )

            # ----------------------------------------------------
            # FILTRE COMPAGNIE
            # ----------------------------------------------------

            filtered_data = (
                self._apply_airline_filter(
                    filtered_data,
                    booking
                )
            )

            # ----------------------------------------------------
            # FORMATAGE
            # ----------------------------------------------------

            formatted_output = (
                self._format_traveler_itinerary(
                    filtered_data,
                    booking
                )
            )

            booking.flight_details = (
                formatted_output
            )

            return formatted_output

        except UserError:

            raise

        except requests.exceptions.RequestException as e:

            _logger.exception(
                "Erreur réseau Sabre"
            )

            raise UserError(
                "Erreur réseau Sabre : "
                f"{str(e)}"
            )

        except Exception as e:

            _logger.exception(
                "Erreur inattendue Sabre"
            )

            raise UserError(
                "Erreur lors de la recherche Sabre : "
                f"{str(e)}"
            )

    # ============================================================
    # LOG CLASSES
    # ============================================================

    @api.model
    def _log_returned_classes(
        self,
        data
    ):

        itineraries = data.get(
            'PricedItineraries',
            []
        )

        classes_found = set()

        for itinerary in itineraries:

            air_itinerary = itinerary.get(
                'AirItinerary',
                {}
            )

            od_options = (
                air_itinerary
                .get(
                    'OriginDestinationOptions',
                    {}
                )
                .get(
                    'OriginDestinationOption',
                    []
                )
            )

            if isinstance(
                od_options,
                dict
            ):

                od_options = [
                    od_options
                ]

            for od in od_options:

                segments = od.get(
                    'FlightSegment',
                    []
                )

                if isinstance(
                    segments,
                    dict
                ):

                    segments = [
                        segments
                    ]

                for segment in segments:

                    booking_class = segment.get(
                        'ResBookDesigCode',
                        'N/A'
                    )

                    if booking_class:

                        classes_found.add(
                            str(
                                booking_class
                            )
                            .strip()
                            .upper()
                        )

        _logger.warning("")
        _logger.warning(
            "============================================================"
        )
        _logger.warning(
            "             CLASSES RETOURNÉES PAR SABRE"
        )
        _logger.warning(
            "============================================================"
        )

        _logger.warning(
            "Nombre itinéraires : %s",
            len(itineraries)
        )

        _logger.warning(
            "Classes trouvées : %s",
            sorted(classes_found)
        )

        _logger.warning(
            "============================================================"
        )

    # ============================================================
    # FILTRE CABINE
    # ============================================================

    @api.model
    def _apply_cabin_filter(
        self,
        data,
        booking
    ):

        requested_cabin = (
            booking.cabin_class
            if booking.cabin_class
            else None
        )

        if not requested_cabin:

            return data

        allowed_classes = (
            self._get_booking_classes(
                requested_cabin
            )
        )

        if not allowed_classes:

            return data

        itineraries = data.get(
            'PricedItineraries',
            []
        )

        if not itineraries:

            return data

        filtered_itineraries = []

        for itinerary in itineraries:

            air_itinerary = itinerary.get(
                'AirItinerary',
                {}
            )

            od_options = (
                air_itinerary
                .get(
                    'OriginDestinationOptions',
                    {}
                )
                .get(
                    'OriginDestinationOption',
                    []
                )
            )

            if isinstance(
                od_options,
                dict
            ):

                od_options = [
                    od_options
                ]

            itinerary_matches = True

            for od in od_options:

                segments = od.get(
                    'FlightSegment',
                    []
                )

                if isinstance(
                    segments,
                    dict
                ):

                    segments = [
                        segments
                    ]

                for segment in segments:

                    booking_class = (
                        str(
                            segment.get(
                                'ResBookDesigCode',
                                ''
                            )
                        )
                        .strip()
                        .upper()
                    )

                    if (
                        booking_class
                        not in allowed_classes
                    ):

                        itinerary_matches = False
                        break

                if not itinerary_matches:
                    break

            if itinerary_matches:

                filtered_itineraries.append(
                    itinerary
                )

        data['PricedItineraries'] = (
            filtered_itineraries
        )

        _logger.info(
            "FILTRE CLASSE | Avant=%s | Après=%s | Classe=%s",
            len(itineraries),
            len(filtered_itineraries),
            requested_cabin
        )

        return data

    # ============================================================
    # FILTRE COMPAGNIE
    # ============================================================

    @api.model
    def _apply_airline_filter(
        self,
        data,
        booking
    ):

        itineraries = data.get(
            'PricedItineraries',
            []
        )

        if not itineraries:

            return data

        preferred_airline = (
            booking.preferred_airline_code
            if booking.preferred_airline_code
            else None
        )

        if not preferred_airline:

            return data

        preferred_airline = (
            preferred_airline
            .strip()
            .upper()
        )

        filtered_itineraries = []

        for itinerary in itineraries:

            air_itinerary = itinerary.get(
                'AirItinerary',
                {}
            )

            od_options = (
                air_itinerary
                .get(
                    'OriginDestinationOptions',
                    {}
                )
                .get(
                    'OriginDestinationOption',
                    []
                )
            )

            if isinstance(
                od_options,
                dict
            ):

                od_options = [
                    od_options
                ]

            all_segments = []

            for od in od_options:

                segments = od.get(
                    'FlightSegment',
                    []
                )

                if isinstance(
                    segments,
                    dict
                ):

                    segments = [
                        segments
                    ]

                all_segments.extend(
                    segments
                )

            airline_found = False

            for segment in all_segments:

                marketing_airline = (
                    segment
                    .get(
                        'MarketingAirline',
                        {}
                    )
                    .get(
                        'Code',
                        ''
                    )
                    .strip()
                    .upper()
                )

                operating_airline = (
                    segment
                    .get(
                        'OperatingAirline',
                        {}
                    )
                    .get(
                        'Code',
                        ''
                    )
                    .strip()
                    .upper()
                )

                if (
                    marketing_airline
                    == preferred_airline
                    or
                    operating_airline
                    == preferred_airline
                ):

                    airline_found = True
                    break

            if airline_found:

                filtered_itineraries.append(
                    itinerary
                )

        data['PricedItineraries'] = (
            filtered_itineraries
        )

        _logger.info(
            "FILTRE COMPAGNIE | "
            "Demandée=%s | Avant=%s | Après=%s",
            preferred_airline,
            len(itineraries),
            len(filtered_itineraries)
        )

        return data

    # ============================================================
    # EXTRACTION TARIF PASSAGER
    # ============================================================

    @api.model
    def _extract_passenger_fares(
        self,
        pricing
    ):

        result = []

        breakdowns = pricing.get(
            'PTC_FareBreakdowns',
            {}
        )

        if not breakdowns:

            return result

        breakdown_list = breakdowns.get(
            'PTC_FareBreakdown',
            []
        )

        if isinstance(
            breakdown_list,
            dict
        ):

            breakdown_list = [
                breakdown_list
            ]

        for breakdown in breakdown_list:

            passenger_quantity = (
                breakdown.get(
                    'PassengerTypeQuantity',
                    {}
                )
            )

            if isinstance(
                passenger_quantity,
                list
            ):

                passenger_quantity = (
                    passenger_quantity[0]
                    if passenger_quantity
                    else {}
                )

            code = (
                passenger_quantity.get(
                    'Code',
                    'ADT'
                )
            )

            quantity = (
                passenger_quantity.get(
                    'Quantity',
                    1
                )
            )

            try:

                quantity = int(
                    quantity
                )

            except (
                TypeError,
                ValueError
            ):

                quantity = 1

            passenger_fare = (
                breakdown.get(
                    'PassengerFare',
                    {}
                )
            )

            total_fare = (
                passenger_fare.get(
                    'TotalFare',
                    {}
                )
            )

            base_fare = (
                passenger_fare.get(
                    'BaseFare',
                    {}
                )
            )

            taxes = (
                passenger_fare.get(
                    'Taxes',
                    {}
                )
            )

            total_amount = self._to_float(
                total_fare.get(
                    'Amount',
                    0
                )
            )

            base_amount = self._to_float(
                base_fare.get(
                    'Amount',
                    0
                )
            )

            tax_amount = self._to_float(
                taxes.get(
                    'Amount',
                    0
                )
            )

            currency = (
                total_fare.get(
                    'CurrencyCode',
                    base_fare.get(
                        'CurrencyCode',
                        'USD'
                    )
                )
            )

            result.append({

                'code': code,

                'quantity': quantity,

                'base': base_amount,

                'taxes': tax_amount,

                'total': total_amount,

                'currency': currency,
            })

        return result

    # ============================================================
    # CONVERSION FLOAT
    # ============================================================

    @api.model
    def _to_float(
        self,
        value
    ):

        try:

            return float(
                value or 0
            )

        except (
            TypeError,
            ValueError
        ):

            return 0.0

    # ============================================================
    # FORMATAGE
    # ============================================================

    @api.model
    def _format_traveler_itinerary(
        self,
        data,
        booking
    ):

        itineraries = data.get(
            'PricedItineraries',
            []
        )

        adults = int(
            booking.adults or 0
        )

        children = int(
            booking.children or 0
        )

        infants = int(
            booking.infants or 0
        )

        if adults <= 0:

            adults = 1

        # --------------------------------------------------------
        # AUCUN RÉSULTAT
        # --------------------------------------------------------

        if not itineraries:

            return (
                "✈️ Aucun vol ne correspond "
                "aux critères de recherche."
            )

        lines = []

        # --------------------------------------------------------
        # PASSAGERS
        # --------------------------------------------------------

        lines.append(
            "👥 PASSAGERS :"
        )

        lines.append(
            f"• Adultes : {adults}"
        )

        lines.append(
            f"• Enfants : {children}"
        )

        lines.append(
            f"• Bébés   : {infants}"
        )

        lines.append("")

        # --------------------------------------------------------
        # ITINÉRAIRES
        # --------------------------------------------------------

        for idx, itinerary in enumerate(
            itineraries,
            1
        ):

            air_itin = itinerary.get(
                'AirItinerary',
                {}
            )

            pricing = itinerary.get(
                'AirItineraryPricingInfo',
                {}
            )

            # ----------------------------------------------------
            # TARIF GLOBAL
            # ----------------------------------------------------

            itin_total_fare = (
                pricing
                .get(
                    'ItinTotalFare',
                    {}
                )
            )

            total_fare_info = (
                itin_total_fare
                .get(
                    'TotalFare',
                    {}
                )
            )

            base_fare_info = (
                itin_total_fare
                .get(
                    'BaseFare',
                    {}
                )
            )

            global_total = self._to_float(
                total_fare_info.get(
                    'Amount',
                    0
                )
            )

            global_base = self._to_float(
                base_fare_info.get(
                    'Amount',
                    0
                )
            )

            currency = (
                total_fare_info.get(
                    'CurrencyCode',
                    base_fare_info.get(
                        'CurrencyCode',
                        'USD'
                    )
                )
            )

            # ----------------------------------------------------
            # SEGMENTS
            # ----------------------------------------------------

            options_dest = (
                air_itin
                .get(
                    'OriginDestinationOptions',
                    {}
                )
                .get(
                    'OriginDestinationOption',
                    []
                )
            )

            if isinstance(
                options_dest,
                dict
            ):

                options_dest = [
                    options_dest
                ]

            all_segments = []

            for od in options_dest:

                segments = od.get(
                    'FlightSegment',
                    []
                )

                if isinstance(
                    segments,
                    dict
                ):

                    segments = [
                        segments
                    ]

                all_segments.extend(
                    segments
                )

            number_of_segments = len(
                all_segments
            )

            if number_of_segments <= 1:

                flight_type = (
                    "Vol Direct"
                )

            else:

                flight_type = (
                    f"{number_of_segments - 1} escale(s)"
                )

            # ----------------------------------------------------
            # TITRE
            # ----------------------------------------------------

            lines.append(
                f"## 🔹 OPTION DE VOL N° {idx}"
            )

            lines.append("")

            lines.append(
                f"✈️ Type de vol : {flight_type}"
            )

            lines.append("")

            # ----------------------------------------------------
            # SEGMENTS
            # ----------------------------------------------------

            for segment_counter, seg in enumerate(
                all_segments,
                1
            ):

                marketing_airline = (
                    seg
                    .get(
                        'MarketingAirline',
                        {}
                    )
                    .get(
                        'Code',
                        ''
                    )
                )

                operating_airline = (
                    seg
                    .get(
                        'OperatingAirline',
                        {}
                    )
                    .get(
                        'Code',
                        ''
                    )
                )

                flight_num = (
                    seg.get(
                        'FlightNumber',
                        ''
                    )
                )

                dep_apt = (
                    seg
                    .get(
                        'DepartureAirport',
                        {}
                    )
                    .get(
                        'LocationCode',
                        ''
                    )
                )

                arr_apt = (
                    seg
                    .get(
                        'ArrivalAirport',
                        {}
                    )
                    .get(
                        'LocationCode',
                        ''
                    )
                )

                dep_time = (
                    seg
                    .get(
                        'DepartureDateTime',
                        ''
                    )
                    .replace(
                        'T',
                        ' à '
                    )
                )

                arr_time = (
                    seg
                    .get(
                        'ArrivalDateTime',
                        ''
                    )
                    .replace(
                        'T',
                        ' à '
                    )
                )

                equipment = (
                    seg
                    .get(
                        'Equipment',
                        {}
                    )
                    .get(
                        'AirEquipType',
                        'N/A'
                    )
                )

                booking_class = (
                    seg.get(
                        'ResBookDesigCode',
                        'N/A'
                    )
                )

                elapsed_time = (
                    seg.get(
                        'ElapsedTime',
                        'N/A'
                    )
                )

                lines.append(
                    f"✈️ Segment {segment_counter} : "
                    f"{marketing_airline} {flight_num}"
                )

                if (
                    operating_airline
                    and
                    operating_airline
                    != marketing_airline
                ):

                    lines.append(
                        f"   Opéré par : "
                        f"{operating_airline}"
                    )

                lines.append(
                    f"   📍 Trajet : "
                    f"{dep_apt} ➔ {arr_apt}"
                )

                lines.append(
                    f"   🕒 Départ : "
                    f"{dep_time}"
                )

                lines.append(
                    f"   🕒 Arrivée : "
                    f"{arr_time}"
                )

                lines.append(
                    f"   ⏱️ Durée : "
                    f"{elapsed_time} minutes"
                )

                lines.append(
                    f"   💺 Classe : "
                    f"{booking_class}"
                )

                lines.append(
                    f"   ✈️ Appareil : "
                    f"{equipment}"
                )

                lines.append("")

            # ----------------------------------------------------
            # TARIFICATION
            # ----------------------------------------------------

            lines.append(
                "💵 DÉTAIL DU TARIF :"
            )

            lines.append("")

            lines.append(
                f"• Tarif de base global : "
                f"{global_base:.2f} {currency}"
            )

            lines.append(
                "• Tarifs passagers :"
            )

            passenger_fares = (
                self._extract_passenger_fares(
                    pricing
                )
            )

            calculated_total = 0.0

            calculated_base = 0.0

            calculated_taxes = 0.0

            if passenger_fares:

                for fare in passenger_fares:

                    code = fare['code']

                    quantity = fare['quantity']

                    base = fare['base']

                    taxes = fare['taxes']

                    total = fare['total']

                    # ------------------------------------------------
                    # NOM PASSAGER
                    # ------------------------------------------------

                    if code == 'ADT':

                        passenger_name = (
                            "Adulte"
                        )

                    elif code == 'CNN':

                        passenger_name = (
                            "Enfant"
                        )

                    elif code == 'INF':

                        passenger_name = (
                            "Bébé"
                        )

                    else:

                        passenger_name = (
                            code
                        )

                    lines.append(
                        f"- {passenger_name} x {quantity} : "
                        f"{total:.2f} {fare['currency']}"
                    )

                    lines.append(
                        f"  Base : "
                        f"{base:.2f} "
                        f"{fare['currency']}"
                    )

                    lines.append(
                        f"  Taxes : "
                        f"{taxes:.2f} "
                        f"{fare['currency']}"
                    )

                    # ------------------------------------------------
                    # TOTAL DU GROUPE DE PASSAGERS
                    # ------------------------------------------------

                    calculated_total += (
                        total * quantity
                    )

                    calculated_base += (
                        base * quantity
                    )

                    calculated_taxes += (
                        taxes * quantity
                    )

            else:

                # ----------------------------------------------------
                # PAS DE PTC
                # ----------------------------------------------------

                lines.append(
                    "- Tarification détaillée "
                    "par passager non fournie par Sabre."
                )

                calculated_total = (
                    global_total
                )

                calculated_base = (
                    global_base
                )

            lines.append("")

            # ----------------------------------------------------
            # TAXES GLOBALES
            # ----------------------------------------------------

            if calculated_taxes > 0:

                lines.append(
                    f"• Taxes et frais globaux : "
                    f"{calculated_taxes:.2f} "
                    f"{currency}"
                )

            else:

                lines.append(
                    "• Taxes et frais globaux : "
                    "0.00 "
                    f"{currency}"
                )

            lines.append("")

            # ----------------------------------------------------
            # TOTAL
            # ----------------------------------------------------

            # Si Sabre fournit plusieurs PTC,
            # on utilise le calcul par passager.
            #
            # Sinon on conserve le TotalFare de Sabre.

            if passenger_fares:

                final_total = (
                    calculated_total
                )

            else:

                final_total = (
                    global_total
                )

            lines.append(
                f"🏷️ PRIX TOTAL TTC : "
                f"{final_total:.2f} "
                f"{currency}"
            )

            lines.append("")

            lines.append(
                "--------------------------------------------------"
            )

            lines.append("")

        return "\n".join(lines)

    # ============================================================
    # RÉCUPÉRATION PNR
    # ============================================================

    @api.model
    def fetch_pnr(
        self,
        booking
    ):

        if not booking.pnr_code:

            raise UserError(
                "Le code PNR est obligatoire."
            )

        access_token = (
            self.get_auth_token()
        )

        get_param = (
            self.env['ir.config_parameter']
            .sudo()
            .get_param
        )

        environment = get_param(
            'api_gds.sabre_environment',
            'test'
        )

        if environment == 'production':

            base_url = (
                "https://api.platform.sabre.com"
            )

        else:

            base_url = (
                "https://api.cert.platform.sabre.com"
            )

        endpoint = (
            f"{base_url}/v1/trip/orders/getBooking/"
            f"{booking.pnr_code}"
        )

        headers = {

            'Authorization':
                f'Bearer {access_token}',

            'Accept':
                'application/json',
        }

        try:

            response = requests.get(
                endpoint,
                headers=headers,
                timeout=15
            )

            self._log_sabre_response(
                response,
                "RÉPONSE RÉCUPÉRATION PNR SABRE"
            )

            if response.status_code == 200:

                raw_data = (
                    response.json()
                )

                booking.flight_details = (
                    json.dumps(
                        raw_data,
                        indent=4,
                        ensure_ascii=False
                    )
                )

                booking.state = (
                    'confirmed'
                )

                return raw_data

            raise UserError(
                "Erreur GDS Sabre : "
                f"{response.text}"
            )

        except UserError:

            raise

        except requests.exceptions.RequestException as e:

            _logger.exception(
                "Erreur réseau Sabre"
            )

            raise UserError(
                "Erreur réseau Sabre : "
                f"{str(e)}"
            )

        except Exception as e:

            _logger.exception(
                "Erreur récupération PNR"
            )

            raise UserError(
                "Erreur récupération PNR : "
                f"{str(e)}"
            )
