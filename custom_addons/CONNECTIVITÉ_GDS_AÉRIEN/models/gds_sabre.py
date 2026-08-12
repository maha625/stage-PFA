import base64
import json
import logging

import requests

from odoo import api, models
from odoo.exceptions import UserError


_logger = logging.getLogger(__name__)


class GdsSabreService(models.AbstractModel):

    _name = "gds.sabre.service"
    _description = "Service technique Sabre"

    # ============================================================
    # CONFIGURATION SABRE
    # ============================================================

    @api.model
    def _get_sabre_config(self):
        get_param = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param
        )

        environment = get_param(
            "api_gds.sabre_environment",
            "test",
        )

        client_id = get_param(
            "api_gds.sabre_client_id"
        )

        client_secret = get_param(
            "api_gds.sabre_client_secret"
        )

        if not client_id:
            raise UserError(
                "Le Client ID Sabre n'est pas configuré."
            )

        if not client_secret:
            raise UserError(
                "Le Client Secret Sabre n'est pas configuré."
            )

        client_id = str(client_id).strip()
        client_secret = str(client_secret).strip()

        if environment == "production":
            base_url = (
                "https://api.platform.sabre.com"
            )
        else:
            base_url = (
                "https://api.cert.platform.sabre.com"
            )

        return {
            "environment": environment,
            "client_id": client_id,
            "client_secret": client_secret,
            "base_url": base_url,
        }

    # ============================================================
    # CONVERSION FLOAT
    # ============================================================

    @api.model
    def _to_float(self, value):

        try:
            return float(value or 0)

        except (TypeError, ValueError):
            return 0.0

    # ============================================================
    # AUTHENTIFICATION
    # ============================================================

    @api.model
    def get_auth_token(self):

        config = self._get_sabre_config()

        client_id = config["client_id"]
        client_secret = config["client_secret"]
        base_url = config["base_url"]

        auth_url = (
            f"{base_url}/v2/auth/token"
        )

        client_id_b64 = (
            base64.b64encode(
                client_id.encode("utf-8")
            )
            .decode("ascii")
        )

        client_secret_b64 = (
            base64.b64encode(
                client_secret.encode("utf-8")
            )
            .decode("ascii")
        )

        credentials = (
            f"{client_id_b64}:{client_secret_b64}"
        )

        basic_credentials = (
            base64.b64encode(
                credentials.encode("ascii")
            )
            .decode("ascii")
        )

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

        try:
            response = requests.post(
                auth_url,
                headers=headers,
                data=payload,
                timeout=30,
            )

        except requests.exceptions.RequestException as error:
            _logger.exception(
                "Erreur réseau pendant "
                "l'authentification Sabre."
            )

            raise UserError(
                "Impossible de contacter Sabre : "
                f"{error}"
            )

        if response.status_code != 200:

            _logger.error(
                "Authentification Sabre échouée "
                "(HTTP %s).",
                response.status_code,
            )

            try:
                error_data = response.json()
                error_text = json.dumps(
                    error_data,
                    ensure_ascii=False,
                )
            except ValueError:
                error_text = response.text

            raise UserError(
                "Erreur d'authentification Sabre "
                f"[HTTP {response.status_code}] :\n"
                f"{error_text}"
            )

        try:
            data = response.json()

        except ValueError:
            raise UserError(
                "Sabre a retourné une réponse "
                "d'authentification invalide."
            )

        access_token = data.get(
            "access_token"
        )

        if not access_token:
            raise UserError(
                "Sabre n'a pas retourné de "
                "token d'authentification."
            )

        return access_token

    # ============================================================
    # CLASSE CABINE
    # ============================================================

    @api.model
    def _get_sabre_cabin_class(
        self,
        cabin_class,
    ):

        if not cabin_class:
            return None

        value = (
            str(cabin_class)
            .strip()
            .upper()
        )

        mapping = {
            "ECONOMY": "Y",
            "ECONOMIC": "Y",
            "ECONOMIQUE": "Y",
            "ÉCONOMIQUE": "Y",
            "Y": "Y",
            "PREMIUM_ECONOMY": "S",
            "PREMIUM ECONOMY": "S",
            "PREMIUM-ECONOMY": "S",
            "PREMIUM": "S",
            "PREMIUM_ECONOMIC": "S",
            "PREMIUM ECONOMIC": "S",
            "S": "S",
            "BUSINESS": "C",
            "BUSINESS CLASS": "C",
            "BUSINESS_CLASS": "C",
            "AFFAIRES": "C",
            "C": "C",
            "FIRST": "F",
            "FIRST CLASS": "F",
            "FIRST_CLASS": "F",
            "PREMIERE": "F",
            "PREMIÈRE": "F",
            "PREMIERE CLASSE": "F",
            "PREMIÈRE CLASSE": "F",
            "F": "F",
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
        cabin_class,
    ):

        if not cabin_class:
            return []

        value = (
            str(cabin_class)
            .strip()
            .upper()
        )

        if value in (
            "ECONOMY",
            "ECONOMIC",
            "ECONOMIQUE",
            "ÉCONOMIQUE",
            "Y",
        ):
            return [
                "Y",
                "B",
                "M",
                "H",
                "K",
                "Q",
                "V",
                "W",
                "T",
                "L",
                "U",
                "G",
                "N",
                "O",
                "S",
                "E",
                "X",
            ]

        if value in (
            "PREMIUM_ECONOMY",
            "PREMIUM ECONOMY",
            "PREMIUM-ECONOMY",
            "PREMIUM",
            "PREMIUM_ECONOMIC",
            "PREMIUM ECONOMIC",
            "S",
        ):
            return [
                "S",
                "W",
                "E",
            ]

        if value in (
            "BUSINESS",
            "BUSINESS CLASS",
            "BUSINESS_CLASS",
            "AFFAIRES",
            "C",
        ):
            return [
                "C",
                "J",
                "D",
                "I",
                "Z",
            ]

        if value in (
            "FIRST",
            "FIRST CLASS",
            "FIRST_CLASS",
            "PREMIERE",
            "PREMIÈRE",
            "PREMIERE CLASSE",
            "PREMIÈRE CLASSE",
            "F",
        ):
            return [
                "F",
                "A",
                "P",
            ]

        return []

    # ============================================================
    # EXTRACTION DES PASSAGERS DEMANDÉS
    # ============================================================

    @api.model
    def _get_requested_passengers(
        self,
        booking,
    ):

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

        return {
            "ADT": adults,
            "CNN": children,
            "INF": infants,
        }

    # ============================================================
    # EXTRACTION DES TARIFS PASSAGERS
    # ============================================================

    @api.model
    def _extract_passenger_fares(
        self,
        pricing,
    ):

        result = []

        breakdowns = pricing.get(
            "PTC_FareBreakdowns",
            {},
        )

        if not breakdowns:
            return result

        breakdown_list = breakdowns.get(
            "PTC_FareBreakdown",
            [],
        )

        if isinstance(
            breakdown_list,
            dict,
        ):
            breakdown_list = [
                breakdown_list
            ]

        for breakdown in breakdown_list:

            passenger_quantity = (
                breakdown.get(
                    "PassengerTypeQuantity",
                    {},
                )
            )

            if isinstance(
                passenger_quantity,
                list,
            ):
                passenger_quantity = (
                    passenger_quantity[0]
                    if passenger_quantity
                    else {}
                )

            code = str(
                passenger_quantity.get(
                    "Code",
                    "",
                )
            ).strip().upper()

            if not code:
                continue

            raw_quantity = (
                passenger_quantity.get(
                    "Quantity",
                    0,
                )
            )

            try:
                quantity = int(
                    raw_quantity
                )
            except (
                TypeError,
                ValueError,
            ):
                quantity = 0

            passenger_fare = (
                breakdown.get(
                    "PassengerFare",
                    {},
                )
            )

            total_fare = (
                passenger_fare.get(
                    "TotalFare",
                    {},
                )
            )

            base_fare = (
                passenger_fare.get(
                    "BaseFare",
                    {},
                )
            )

            taxes = (
                passenger_fare.get(
                    "Taxes",
                    {},
                )
            )

            total_amount = self._to_float(
                total_fare.get(
                    "Amount",
                    0,
                )
            )

            base_amount = self._to_float(
                base_fare.get(
                    "Amount",
                    0,
                )
            )

            tax_amount = self._to_float(
                taxes.get(
                    "Amount",
                    0,
                )
            )

            currency = (
                total_fare.get(
                    "CurrencyCode"
                )
                or base_fare.get(
                    "CurrencyCode"
                )
                or "USD"
            )

            result.append({
                "code": code,
                "quantity": quantity,
                "base": base_amount,
                "taxes": tax_amount,
                "total": total_amount,
                "currency": currency,
            })

        return result

    # ============================================================
    # VALIDATION TARIFICATION PASSAGERS
    # ============================================================

    @api.model
    def _validate_passenger_fares(
        self,
        passenger_fares,
        booking,
    ):
        requested = (
            self._get_requested_passengers(
                booking
            )
        )

        returned = {}

        for fare in passenger_fares:
            code = fare["code"]
            quantity = fare["quantity"]
            returned[code] = (
                returned.get(code, 0)
                + quantity
            )

        missing = []

        for code, requested_quantity in requested.items():
            if requested_quantity <= 0:
                continue

            returned_quantity = returned.get(code, 0)

            if returned_quantity < requested_quantity:
                missing.append(
                    f"{code}: demandé {requested_quantity}, "
                    f"retourné {returned_quantity}"
                )

        has_adults = returned.get("ADT", 0) > 0

        return {
            "valid": has_adults,
            "requested": requested,
            "returned": returned,
            "missing": missing,
        }

    # ============================================================
    # CALCUL TARIF (MODIFIÉ POUR ENFANTS ET BÉBÉS)
    # ============================================================

    @api.model
    def _calculate_passenger_total(
        self,
        passenger_fares,
        booking,
    ):
        requested = (
            self._get_requested_passengers(
                booking
            )
        )

        fare_by_code = {f["code"]: f for f in passenger_fares}
        
        adt_fare = fare_by_code.get("ADT")
        cnn_fare = fare_by_code.get("CNN")
        inf_fare = fare_by_code.get("INF")

        base_unit_total = (adt_fare["total"] / adt_fare["quantity"]) if adt_fare and adt_fare["quantity"] > 0 else 0.0
        base_unit_base = (adt_fare["base"] / adt_fare["quantity"]) if adt_fare and adt_fare["quantity"] > 0 else 0.0
        base_unit_taxes = (adt_fare["taxes"] / adt_fare["quantity"]) if adt_fare and adt_fare["quantity"] > 0 else 0.0
        currency = adt_fare["currency"] if adt_fare else "USD"

        totals = {}

        # Calcul Adultes (ADT)
        adt_qty = requested.get("ADT", 1)
        if adt_fare and adt_fare["quantity"] > 0:
            unit_t = adt_fare["total"] / adt_fare["quantity"]
            unit_b = adt_fare["base"] / adt_fare["quantity"]
            unit_x = adt_fare["taxes"] / adt_fare["quantity"]
            curr = adt_fare["currency"]
        else:
            unit_t, unit_b, unit_x, curr = base_unit_total, base_unit_base, base_unit_taxes, currency

        totals["ADT"] = {
            "quantity": adt_qty,
            "total": unit_t * adt_qty,
            "base": unit_b * adt_qty,
            "taxes": unit_x * adt_qty,
            "currency": curr,
        }

        # Calcul Enfants (CNN)
        cnn_qty = requested.get("CNN", 0)
        if cnn_qty > 0:
            if cnn_fare and cnn_fare["quantity"] > 0:
                cnn_t = cnn_fare["total"] / cnn_fare["quantity"]
                cnn_b = cnn_fare["base"] / cnn_fare["quantity"]
                cnn_x = cnn_fare["taxes"] / cnn_fare["quantity"]
                cnn_curr = cnn_fare["currency"]
            else:
                cnn_t = base_unit_total * 0.75
                cnn_b = base_unit_base * 0.75
                cnn_x = base_unit_taxes
                cnn_curr = currency

            totals["CNN"] = {
                "quantity": cnn_qty,
                "total": cnn_t * cnn_qty,
                "base": cnn_b * cnn_qty,
                "taxes": cnn_x * cnn_qty,
                "currency": cnn_curr,
            }

        # Calcul Bébés (INF)
        inf_qty = requested.get("INF", 0)
        if inf_qty > 0:
            if inf_fare and inf_fare["quantity"] > 0:
                inf_t = inf_fare["total"] / inf_fare["quantity"]
                inf_b = inf_fare["base"] / inf_fare["quantity"]
                inf_x = inf_fare["taxes"] / inf_fare["quantity"]
                inf_curr = inf_fare["currency"]
            else:
                inf_t = base_unit_total * 0.10
                inf_b = base_unit_base * 0.10
                inf_x = 0.0
                inf_curr = currency

            totals["INF"] = {
                "quantity": inf_qty,
                "total": inf_t * inf_qty,
                "base": inf_b * inf_qty,
                "taxes": inf_x * inf_qty,
                "currency": inf_curr,
            }

        return totals

    # ============================================================
    # RECHERCHE VOLS
    # ============================================================

    @api.model
    def search_flights(
        self,
        booking,
    ):

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

        access_token = (
            self.get_auth_token()
        )

        config = self._get_sabre_config()

        endpoint = (
            f"{config['base_url']}/v2/shop/flights"
        )

        passengers = (
            self._get_requested_passengers(
                booking
            )
        )

        params = {
            "origin": (
                booking.origin_code
                .strip()
                .upper()
            ),
            "destination": (
                booking.destination_code
                .strip()
                .upper()
            ),
            "departuredate": str(
                booking.departure_date
            ),
            "adt": passengers["ADT"],
        }

        if (
            booking.trip_type == "round_trip"
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

            params["returndate"] = str(
                booking.return_date
            )

        if passengers["CNN"] > 0:
            params["cnn"] = passengers["CNN"]

        if passengers["INF"] > 0:
            params["inf"] = passengers["INF"]

        params["includePassengerTypeBreakdown"] = "true"

        if booking.cabin_class:

            params["cabinclass"] = (
                self._get_sabre_cabin_class(
                    booking.cabin_class
                )
            )

        _logger.info(
            "Recherche Sabre : "
            "%s -> %s | départ=%s | "
            "ADT=%s CNN=%s INF=%s",
            params["origin"],
            params["destination"],
            params["departuredate"],
            passengers["ADT"],
            passengers["CNN"],
            passengers["INF"],
        )

        headers = {
            "Authorization": (
                f"Bearer {access_token}"
            ),
            "Accept": "application/json",
        }

        try:

            response = requests.get(
                endpoint,
                headers=headers,
                params=params,
                timeout=30,
            )

        except requests.exceptions.RequestException as error:

            _logger.exception(
                "Erreur réseau Sabre."
            )

            raise UserError(
                "Erreur réseau Sabre : "
                f"{error}"
            )

        if response.status_code != 200:

            try:
                error_data = response.json()

                error_text = json.dumps(
                    error_data,
                    indent=2,
                    ensure_ascii=False,
                )

            except ValueError:

                error_text = response.text

            _logger.error(
                "Erreur Sabre HTTP %s : %s",
                response.status_code,
                error_text,
            )

            booking.flight_details = (
                "❌ Erreur API Sabre "
                f"[HTTP {response.status_code}] :\n\n"
                f"{error_text}"
            )

            return booking.flight_details

        try:

            raw_data = response.json()

        except ValueError:

            raise UserError(
                "Sabre a retourné un JSON invalide."
            )

        filtered_data = (
            self._apply_cabin_filter(
                raw_data,
                booking,
            )
        )

        filtered_data = (
            self._apply_airline_filter(
                filtered_data,
                booking,
            )
        )

        formatted_output = (
            self._format_traveler_itinerary(
                filtered_data,
                booking,
            )
        )

        booking.flight_details = (
            formatted_output
        )

        return formatted_output

    # ============================================================
    # FILTRE CABINE
    # ============================================================

    @api.model
    def _apply_cabin_filter(
        self,
        data,
        booking,
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
            "PricedItineraries",
            [],
        )

        if not itineraries:
            return data

        filtered_itineraries = []

        for itinerary in itineraries:

            air_itinerary = itinerary.get(
                "AirItinerary",
                {},
            )

            od_options = (
                air_itinerary
                .get(
                    "OriginDestinationOptions",
                    {},
                )
                .get(
                    "OriginDestinationOption",
                    [],
                )
            )

            if isinstance(
                od_options,
                dict,
            ):
                od_options = [
                    od_options
                ]

            itinerary_matches = True

            for od in od_options:

                segments = od.get(
                    "FlightSegment",
                    [],
                )

                if isinstance(
                    segments,
                    dict,
                ):
                    segments = [
                        segments
                    ]

                for segment in segments:

                    booking_class = str(
                        segment.get(
                            "ResBookDesigCode",
                            "",
                        )
                    ).strip().upper()

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

        data["PricedItineraries"] = (
            filtered_itineraries
        )

        return data

    # ============================================================
    # FILTRE COMPAGNIE
    # ============================================================

    @api.model
    def _apply_airline_filter(
        self,
        data,
        booking,
    ):

        itineraries = data.get(
            "PricedItineraries",
            [],
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
                "AirItinerary",
                {},
            )

            od_options = (
                air_itinerary
                .get(
                    "OriginDestinationOptions",
                    {},
                )
                .get(
                    "OriginDestinationOption",
                    [],
                )
            )

            if isinstance(
                od_options,
                dict,
            ):
                od_options = [
                    od_options
                ]

            for od in od_options:

                segments = od.get(
                    "FlightSegment",
                    [],
                )

                if isinstance(
                    segments,
                    dict,
                ):
                    segments = [
                        segments
                    ]

                for segment in segments:

                    marketing_airline = (
                        segment
                        .get(
                            "MarketingAirline",
                            {},
                        )
                        .get(
                            "Code",
                            "",
                        )
                        .strip()
                        .upper()
                    )

                    operating_airline = (
                        segment
                        .get(
                            "OperatingAirline",
                            {},
                        )
                        .get(
                            "Code",
                            "",
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
                        filtered_itineraries.append(
                            itinerary
                        )

                        break

                else:
                    continue

                break

        data["PricedItineraries"] = (
            filtered_itineraries
        )

        return data

    # ============================================================
    # FORMATAGE DES VOLS - AFFICHAGE PLEINE LARGEUR
    # ============================================================

    @api.model
    def _format_traveler_itinerary(
        self,
        data,
        booking,
    ):
        itineraries = data.get("PricedItineraries", [])
        passengers = self._get_requested_passengers(booking)

        # ============================================================
        # AUCUN VOL
        # ============================================================

        if not itineraries:
            return """
                <div style="
                    width: 100%;
                    box-sizing: border-box;
                    padding: 20px;
                    text-align: center;
                    background-color: #fff3cd;
                    color: #856404;
                    border-radius: 8px;
                    border: 1px solid #ffeeba;
                ">
                    <p style="
                        margin: 0;
                        font-size: 1.1em;
                    ">
                        ✈️ Aucun vol ne correspond aux critères de recherche.
                    </p>
                </div>
            """

        # ============================================================
        # CONTENEUR PRINCIPAL
        # ============================================================

        html = ["""
            <div style="
                font-family: -apple-system, BlinkMacSystemFont,
                            'Segoe UI', Roboto, 'Helvetica Neue',
                            Arial, sans-serif;
                color: #333;
                width: 100%;
                max-width: none;
                box-sizing: border-box;
                margin: 0;
                padding: 0;
            ">
        """]

        # ============================================================
        # RÉSUMÉ DES PASSAGERS
        # ============================================================

        html.append("""
            <div style="
                background: #f1f3f5;
                padding: 15px 20px;
                border-radius: 6px;
                margin-bottom: 25px;
                display: flex;
                align-items: center;
                justify-content: space-between;
                width: 100%;
                box-sizing: border-box;
            ">

                <h3 style="
                    margin: 0;
                    font-size: 1.1em;
                    color: #495057;
                ">
                    👥 Passagers recherchés
                </h3>

                <div style="
                    font-size: 1em;
                    color: #212529;
                ">
        """)

        pass_summary = []

        if passengers["ADT"] > 0:
            pass_summary.append(
                f"<strong>{passengers['ADT']}</strong> Adulte(s)"
            )

        if passengers["CNN"] > 0:
            pass_summary.append(
                f"<strong>{passengers['CNN']}</strong> Enfant(s)"
            )

        if passengers["INF"] > 0:
            pass_summary.append(
                f"<strong>{passengers['INF']}</strong> Bébé(s)"
            )

        html.append(" &nbsp; | &nbsp; ".join(pass_summary))

        html.append("""
                </div>
            </div>
        """)

        # ============================================================
        # OPTIONS DE VOL
        # ============================================================

        for idx, itinerary in enumerate(itineraries, 1):

            air_itin = itinerary.get(
                "AirItinerary",
                {}
            )

            pricing = itinerary.get(
                "AirItineraryPricingInfo",
                {}
            )

            # ========================================================
            # PRIX GLOBAL
            # ========================================================

            itin_total = pricing.get(
                "ItinTotalFare",
                {}
            )

            global_total = itin_total.get(
                "TotalFare",
                {}
            )

            global_base = itin_total.get(
                "BaseFare",
                {}
            )

            global_taxes = itin_total.get(
                "Taxes",
                {}
            )

            global_total_amount = self._to_float(
                global_total.get("Amount", 0)
            )

            global_base_amount = self._to_float(
                global_base.get("Amount", 0)
            )

            global_tax_amount = self._to_float(
                global_taxes.get("Amount", 0)
            )

            global_currency = (
                global_total.get("CurrencyCode")
                or global_base.get("CurrencyCode")
                or "USD"
            )

            # ========================================================
            # SEGMENTS
            # ========================================================

            options_dest = air_itin.get(
                "OriginDestinationOptions",
                {}
            ).get(
                "OriginDestinationOption",
                []
            )

            if isinstance(options_dest, dict):
                options_dest = [options_dest]

            all_segments = []

            for od in options_dest:

                segs = od.get(
                    "FlightSegment",
                    []
                )

                if isinstance(segs, dict):
                    all_segments.append(segs)
                else:
                    all_segments.extend(segs)

            nb_escales = len(all_segments) - 1

            escale_text = (
                "Vol direct"
                if nb_escales == 0
                else f"{nb_escales} escale(s)"
            )

            # ========================================================
            # CARTE OPTION
            # ========================================================

            html.append("""
                <div style="
                    background: #ffffff;
                    border: 1px solid #e0e0e0;
                    padding: 25px;
                    margin-bottom: 30px;
                    border-radius: 8px;
                    box-shadow: 0 2px 6px rgba(0,0,0,0.05);
                    width: 100%;
                    max-width: none;
                    box-sizing: border-box;
                ">
            """)

            # ========================================================
            # TITRE OPTION
            # ========================================================

            html.append(f"""
                <div style="
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    border-bottom: 2px solid #f1f3f5;
                    padding-bottom: 12px;
                    margin-bottom: 20px;
                ">

                    <h2 style="
                        margin: 0;
                        font-size: 1.3em;
                        color: #1a73e8;
                    ">
                        ✈️ Option de vol N° {idx}
                    </h2>

                    <span style="
                        background: #e8f0fe;
                        color: #1a73e8;
                        padding: 5px 12px;
                        border-radius: 12px;
                        font-size: 0.9em;
                        font-weight: 600;
                    ">
                        {escale_text}
                    </span>

                </div>
            """)

            # ========================================================
            # TABLEAU DES SEGMENTS - 8 COLONNES
            # ========================================================

            html.append("""
                <div style="
                    width: 100%;
                    overflow-x: auto;
                    margin-bottom: 20px;
                ">

                    <table style="
                        width: 100%;
                        min-width: 1100px;
                        border-collapse: collapse;
                        font-size: 0.90em;
                        table-layout: auto;
                    ">

                        <thead>

                            <tr style="
                                background-color: #f8f9fa;
                                color: #495057;
                                text-align: left;
                            ">

                                <th style="
                                    padding: 12px;
                                    white-space: nowrap;
                                ">
                                    Vol
                                </th>

                                <th style="
                                    padding: 12px;
                                    white-space: nowrap;
                                ">
                                    Trajet
                                </th>

                                <th style="
                                    padding: 12px;
                                    white-space: nowrap;
                                ">
                                    Départ
                                </th>

                                <th style="
                                    padding: 12px;
                                    white-space: nowrap;
                                ">
                                    Arrivée
                                </th>

                                <th style="
                                    padding: 12px;
                                    white-space: nowrap;
                                ">
                                    Classe
                                </th>

                                <th style="
                                    padding: 12px;
                                    white-space: nowrap;
                                ">
                                    Appareil
                                </th>

                                <th style="
                                    padding: 12px;
                                    white-space: nowrap;
                                ">
                                    Durée
                                </th>

                                <th style="
                                    padding: 12px;
                                    white-space: nowrap;
                                ">
                                    Opéré par
                                </th>

                            </tr>

                        </thead>

                        <tbody>
            """)

            # ========================================================
            # LIGNES DES SEGMENTS
            # ========================================================

            for seg in all_segments:

                marketing_airline = seg.get(
                    "MarketingAirline",
                    {}
                ).get(
                    "Code",
                    ""
                )

                operating_airline = seg.get(
                    "OperatingAirline",
                    {}
                ).get(
                    "Code",
                    ""
                )

                flight_number = seg.get(
                    "FlightNumber",
                    ""
                )

                departure = seg.get(
                    "DepartureAirport",
                    {}
                ).get(
                    "LocationCode",
                    ""
                )

                arrival = seg.get(
                    "ArrivalAirport",
                    {}
                ).get(
                    "LocationCode",
                    ""
                )

                departure_datetime = str(
                    seg.get(
                        "DepartureDateTime",
                        ""
                    )
                ).replace(
                    "T",
                    " "
                )

                arrival_datetime = str(
                    seg.get(
                        "ArrivalDateTime",
                        ""
                    )
                ).replace(
                    "T",
                    " "
                )

                booking_class = seg.get(
                    "ResBookDesigCode",
                    ""
                )

                equipment = (
                    seg.get(
                        "Equipment",
                        {}
                    ).get(
                        "AirEquipType",
                        ""
                    )
                    or
                    seg.get(
                        "Equipment",
                        {}
                    ).get(
                        "Code",
                        ""
                    )
                )

                duration = seg.get(
                    "JourneyDuration",
                    seg.get(
                        "ElapsedTime",
                        ""
                    )
                )

                # ====================================================
                # UNE SEULE LIGNE / 8 COLONNES
                # ====================================================

                html.append(f"""
                    <tr style="
                        border-bottom: 1px solid #f1f3f5;
                        vertical-align: middle;
                    ">

                        <!-- 1. VOL -->
                        <td style="
                            padding: 14px 12px;
                            white-space: nowrap;
                        ">
                            <strong>
                                {marketing_airline} {flight_number}
                            </strong>
                        </td>

                        <!-- 2. TRAJET -->
                        <td style="
                            padding: 14px 12px;
                            white-space: nowrap;
                        ">
                            
                            <strong>{departure}</strong>
                            &nbsp;➜&nbsp;
                            <strong>{arrival}</strong>
                        </td>

                        <!-- 3. DÉPART -->
                        <td style="
                            padding: 14px 12px;
                            color: #495057;
                            white-space: nowrap;
                        ">
                             {departure_datetime}
                        </td>

                        <!-- 4. ARRIVÉE -->
                        <td style="
                            padding: 14px 12px;
                            color: #495057;
                            white-space: nowrap;
                        ">
                             {arrival_datetime}
                        </td>

                        <!-- 5. CLASSE -->
                        <td style="
                            padding: 14px 12px;
                            white-space: nowrap;
                        ">
                            
                            <strong>
                                {booking_class or 'N/A'}
                            </strong>
                        </td>

                        <!-- 6. APPAREIL -->
                        <td style="
                            padding: 14px 12px;
                            white-space: nowrap;
                        ">
                            
                        {equipment or 'N/A'}
                        </td>

                        <!-- 7. DURÉE -->
                        <td style="
                            padding: 14px 12px;
                            white-space: nowrap;
                        ">
                        {duration or 'N/A'} min
                        </td>

                        <!-- 8. OPÉRÉ PAR -->
                        <td style="
                            padding: 14px 12px;
                            white-space: nowrap;
                        ">
                            
                            {operating_airline or 'N/A'}
                        </td>

                    </tr>
                """)

            html.append("""
                        </tbody>

                    </table>

                </div>
            """)

            # ========================================================
            # CALCUL DES TARIFS
            # ========================================================

            passenger_fares = self._extract_passenger_fares(
                pricing
            )

            passenger_totals = self._calculate_passenger_total(
                passenger_fares,
                booking
            )

            validation = self._validate_passenger_fares(
                passenger_fares,
                booking
            )

            # ========================================================
            # CONTRÔLE PASSAGERS + RÉCAPITULATIF
            # ========================================================

            html.append("""
                <div style="
                    display: flex;
                    gap: 20px;
                    margin-bottom: 20px;
                    width: 100%;
                    box-sizing: border-box;
                ">
            """)

            # --------------------------------------------------------
            # CONTRÔLE PASSAGERS
            # --------------------------------------------------------

            html.append("""
                <div style="
                    flex: 1;
                    background: #f8f9fa;
                    padding: 15px;
                    border-radius: 6px;
                    border-left: 4px solid #17a2b8;
                    font-size: 0.95em;
                    box-sizing: border-box;
                ">

                    <strong style="
                        color: #17a2b8;
                    ">
                        👥 Contrôle des passagers
                    </strong>

                    <br/><br/>
            """)

            for code in ["ADT", "CNN", "INF"]:

                requested_qty = validation[
                    "requested"
                ].get(
                    code,
                    0
                )

                if requested_qty <= 0:
                    continue

                returned_qty = validation[
                    "returned"
                ].get(
                    code,
                    0
                )

                passenger_name = {
                    "ADT": "Adultes",
                    "CNN": "Enfants",
                    "INF": "Bébés",
                }.get(
                    code,
                    code
                )

                html.append(
                    f"""
                        • {passenger_name} :
                        demandé <strong>{requested_qty}</strong>
                        |
                        tarifé <strong>{returned_qty}</strong>
                        <br/>
                    """
                )

            html.append("""
                </div>
            """)

            # --------------------------------------------------------
            # RÉCAPITULATIF GLOBAL SABRE
            # --------------------------------------------------------

            html.append(f"""
                <div style="
                    flex: 1;
                    background: #f8f9fa;
                    padding: 15px;
                    border-radius: 6px;
                    border-left: 4px solid #6c757d;
                    font-size: 0.95em;
                    box-sizing: border-box;
                ">

                    <strong style="
                        color: #495057;
                    ">
                        💰 Récapitulatif Global Sabre
                    </strong>

                    <br/><br/>

                    • Base globale :
                    <strong>
                        {global_base_amount:.2f}
                        {global_currency}
                    </strong>

                    <br/>

                    • Taxes globales :
                    <strong>
                        {global_tax_amount:.2f}
                        {global_currency}
                    </strong>

                    <br/>

                    • Total global :
                    <strong>
                        {global_total_amount:.2f}
                        {global_currency}
                    </strong>

                </div>
            """)

            html.append("""
                </div>
            """)

            # ========================================================
            # DÉTAIL PAR TYPE DE PASSAGER
            # ========================================================

            if passenger_totals:

                html.append("""
                    <h4 style="
                        margin: 20px 0 10px 0;
                        font-size: 1.05em;
                        color: #495057;
                    ">
                        💵 Détail par type de passager
                    </h4>

                    <div style="
                        width: 100%;
                        overflow-x: auto;
                    ">

                        <table style="
                            width: 100%;
                            border-collapse: collapse;
                            font-size: 0.95em;
                        ">

                            <thead>

                                <tr style="
                                    background-color: #f1f3f5;
                                    color: #495057;
                                    text-align: left;
                                ">

                                    <th style="padding: 10px;">
                                        Type
                                    </th>

                                    <th style="
                                        padding: 10px;
                                        text-align: center;
                                    ">
                                        Qté
                                    </th>

                                    <th style="
                                        padding: 10px;
                                        text-align: right;
                                    ">
                                        Base unitaire
                                    </th>

                                    <th style="
                                        padding: 10px;
                                        text-align: right;
                                    ">
                                        Taxes unitaires
                                    </th>

                                    <th style="
                                        padding: 10px;
                                        text-align: right;
                                    ">
                                        Total
                                    </th>

                                </tr>

                            </thead>

                            <tbody>
                """)

                for code, fare in passenger_totals.items():

                    name = {
                        "ADT": "Adulte",
                        "CNN": "Enfant",
                        "INF": "Bébé",
                    }.get(
                        code,
                        code
                    )

                    quantity = fare["quantity"]

                    html.append(f"""
                        <tr style="
                            border-bottom: 1px solid #f1f3f5;
                        ">

                            <td style="padding: 10px;">
                                {name}
                            </td>

                            <td style="
                                padding: 10px;
                                text-align: center;
                            ">
                                {quantity}
                            </td>

                            <td style="
                                padding: 10px;
                                text-align: right;
                            ">
                                {fare['base'] / quantity:.2f}
                            </td>

                            <td style="
                                padding: 10px;
                                text-align: right;
                            ">
                                {fare['taxes'] / quantity:.2f}
                            </td>

                            <td style="
                                padding: 10px;
                                text-align: right;
                            ">
                                <strong>
                                    {fare['total']:.2f}
                                    {fare['currency']}
                                </strong>
                            </td>

                        </tr>
                    """)

                html.append("""
                            </tbody>

                        </table>

                    </div>
                """)

            # ========================================================
            # PRIX TOTAL FINAL
            # ========================================================

            if validation["valid"]:

                final_total = sum(
                    f["total"]
                    for f in passenger_totals.values()
                )

                curr = passenger_totals.get(
                    "ADT",
                    {}
                ).get(
                    "currency",
                    "USD"
                )

                html.append(f"""
                    <div style="
                        background: #e6f4ea;
                        border: 1px solid #ceead6;
                        padding: 15px 20px;
                        border-radius: 6px;
                        display: flex;
                        justify-content: space-between;
                        align-items: center;
                        margin-top: 20px;
                        width: 100%;
                        box-sizing: border-box;
                    ">

                        <span style="
                            color: #137333;
                            font-weight: 600;
                            font-size: 1.1em;
                        ">
                            🏷️ PRIX TOTAL TTC
                        </span>

                        <span style="
                            color: #137333;
                            font-size: 1.3em;
                            font-weight: bold;
                        ">
                            {final_total:.2f} {curr}
                        </span>

                    </div>
                """)

            else:

                html.append(f"""
                    <div style="
                        background: #fce8e6;
                        border: 1px solid #fad2cf;
                        padding: 15px 20px;
                        border-radius: 6px;
                        color: #c5221f;
                        margin-top: 20px;
                        width: 100%;
                        box-sizing: border-box;
                    ">

                        ⚠️ Prix incomplet.

                        Manquants :
                        {", ".join(validation["missing"])}

                    </div>
                """)

            # ========================================================
            # FIN CARTE OPTION
            # ========================================================

            html.append("""
                </div>
            """)

        # ============================================================
        # FIN CONTENEUR
        # ============================================================

        html.append("""
            </div>
        """)

        return "".join(html)

    #======================================================
    # RÉCUPÉRATION PNR
    # ============================================================

    @api.model
    def fetch_pnr(
        self,
        booking,
    ):

        if not booking.pnr_code:
            raise UserError(
                "Le code PNR est obligatoire."
            )

        access_token = (
            self.get_auth_token()
        )

        config = self._get_sabre_config()

        endpoint = (
            f"{config['base_url']}"
            f"/v1/trip/orders/getBooking/"
            f"{booking.pnr_code}"
        )

        headers = {
            "Authorization": (
                f"Bearer {access_token}"
            ),
            "Accept": "application/json",
        }

        try:

            response = requests.get(
                endpoint,
                headers=headers,
                timeout=15,
            )

        except requests.exceptions.RequestException as error:

            _logger.exception(
                "Erreur réseau pendant "
                "la récupération du PNR."
            )

            raise UserError(
                "Erreur réseau Sabre : "
                f"{error}"
            )

        if response.status_code != 200:

            try:
                error_data = response.json()

                error_text = json.dumps(
                    error_data,
                    indent=2,
                    ensure_ascii=False,
                )

            except ValueError:

                error_text = response.text

            _logger.error(
                "Erreur récupération PNR "
                "HTTP %s : %s",
                response.status_code,
                error_text,
            )

            raise UserError(
                "Erreur GDS Sabre :\n"
                f"{error_text}"
            )

        try:

            raw_data = response.json()

        except ValueError:

            raise UserError(
                "Sabre a retourné un JSON "
                "invalide pour le PNR."
            )

        booking.flight_details = (
            json.dumps(
                raw_data,
                indent=2,
                ensure_ascii=False,
            )
        )

        booking.state = "confirmed"

        return raw_data