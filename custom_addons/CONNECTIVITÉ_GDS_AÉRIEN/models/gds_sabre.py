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

        # Sabre utilise les valeurs encodées
        # dans les credentials Basic Auth.
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

        # On considère la validation souple si au moins les adultes sont présents
        has_adults = returned.get("ADT", 0) > 0

        return {
            "valid": has_adults,  # Valide dès qu'on a un tarif de base adulte
            "requested": requested,
            "returned": returned,
            "missing": missing,
        }
    # ============================================================
    # CALCUL TARIF
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

        # Récupération du tarif unitaire Adulte de référence
        adt_fare = next(
            (f for f in passenger_fares if f["code"] == "ADT"),
            None
        )

        totals = {}

        # S'il y a un tarif adulte de base, on s'en sert pour extrapoler s'il manque des données
        base_unit_total = (adt_fare["total"] / adt_fare["quantity"]) if adt_fare and adt_fare["quantity"] > 0 else 0.0
        base_unit_base = (adt_fare["base"] / adt_fare["quantity"]) if adt_fare and adt_fare["quantity"] > 0 else 0.0
        base_unit_taxes = (adt_fare["taxes"] / adt_fare["quantity"]) if adt_fare and adt_fare["quantity"] > 0 else 0.0
        currency = adt_fare["currency"] if adt_fare else "USD"

        # Calcul pour les Adultes
        adt_qty = requested.get("ADT", 1)
        totals["ADT"] = {
            "quantity": adt_qty,
            "total": base_unit_total * adt_qty,
            "base": base_unit_base * adt_qty,
            "taxes": base_unit_taxes * adt_qty,
            "currency": currency,
        }

        # Calcul pour les Enfants (CNN) - Application d'un ratio de 75% si non retourné par Sabre
        cnn_qty = requested.get("CNN", 0)
        if cnn_qty > 0:
            totals["CNN"] = {
                "quantity": cnn_qty,
                "total": base_unit_total * 0.75 * cnn_qty,
                "base": base_unit_base * 0.75 * cnn_qty,
                "taxes": base_unit_taxes * cnn_qty,
                "currency": currency,
            }

        # Calcul pour les Bébés (INF) - Application d'un ratio de 10% si non retourné par Sabre
        inf_qty = requested.get("INF", 0)
        if inf_qty > 0:
            totals["INF"] = {
                "quantity": inf_qty,
                "total": base_unit_total * 0.10 * inf_qty,
                "base": base_unit_base * 0.10 * inf_qty,
                "taxes": 0.0,
                "currency": currency,
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
        # AUTHENTIFICATION
        # --------------------------------------------------------

        access_token = (
            self.get_auth_token()
        )

        config = self._get_sabre_config()

        endpoint = (
            f"{config['base_url']}/v2/shop/flights"
        )

        # --------------------------------------------------------
        # PASSAGERS
        # --------------------------------------------------------

        passengers = (
            self._get_requested_passengers(
                booking
            )
        )

        # --------------------------------------------------------
        # PARAMÈTRES
        # --------------------------------------------------------

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

        # --------------------------------------------------------
        # RETOUR
        # --------------------------------------------------------

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

        # --------------------------------------------------------
        # ENFANTS
        # --------------------------------------------------------

        if passengers["CNN"] > 0:
            params["cnn"] = passengers["CNN"]

        # --------------------------------------------------------
        # BÉBÉS
        # --------------------------------------------------------

        if passengers["INF"] > 0:
            params["inf"] = passengers["INF"]

        # --------------------------------------------------------
        # VENTILATION DES TARIFS PASSAGERS
        # --------------------------------------------------------

        params["includePassengerTypeBreakdown"] = "true"

        # --------------------------------------------------------
        # CABINE
        # --------------------------------------------------------

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

        # --------------------------------------------------------
        # APPEL API
        # --------------------------------------------------------

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

        # --------------------------------------------------------
        # ERREUR HTTP
        # --------------------------------------------------------

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

        # --------------------------------------------------------
        # JSON
        # --------------------------------------------------------

        try:

            raw_data = response.json()

        except ValueError:

            raise UserError(
                "Sabre a retourné un JSON invalide."
            )

        # --------------------------------------------------------
        # FILTRE CABINE
        # --------------------------------------------------------

        filtered_data = (
            self._apply_cabin_filter(
                raw_data,
                booking,
            )
        )

        # --------------------------------------------------------
        # FILTRE COMPAGNIE
        # --------------------------------------------------------

        filtered_data = (
            self._apply_airline_filter(
                filtered_data,
                booking,
            )
        )

        # --------------------------------------------------------
        # FORMATAGE
        # --------------------------------------------------------

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
    # FORMATAGE DES VOLS
    # ============================================================

    @api.model
    def _format_traveler_itinerary(
        self,
        data,
        booking,
    ):

        itineraries = data.get(
            "PricedItineraries",
            [],
        )

        passengers = (
            self._get_requested_passengers(
                booking
            )
        )

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
            f"• Adultes : {passengers['ADT']}"
        )

        lines.append(
            f"• Enfants : {passengers['CNN']}"
        )

        lines.append(
            f"• Bébés : {passengers['INF']}"
        )

        lines.append("")

        # --------------------------------------------------------
        # ITINÉRAIRES
        # --------------------------------------------------------

        for idx, itinerary in enumerate(
            itineraries,
            1,
        ):

            air_itin = itinerary.get(
                "AirItinerary",
                {},
            )

            pricing = itinerary.get(
                "AirItineraryPricingInfo",
                {},
            )

            itin_total_fare = (
                pricing.get(
                    "ItinTotalFare",
                    {},
                )
            )

            total_fare_info = (
                itin_total_fare.get(
                    "TotalFare",
                    {},
                )
            )

            base_fare_info = (
                itin_total_fare.get(
                    "BaseFare",
                    {},
                )
            )

            global_total = self._to_float(
                total_fare_info.get(
                    "Amount",
                    0,
                )
            )

            global_base = self._to_float(
                base_fare_info.get(
                    "Amount",
                    0,
                )
            )

            currency = (
                total_fare_info.get(
                    "CurrencyCode"
                )
                or base_fare_info.get(
                    "CurrencyCode"
                )
                or "USD"
            )

            # ----------------------------------------------------
            # SEGMENTS
            # ----------------------------------------------------

            options_dest = (
                air_itin
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
                options_dest,
                dict,
            ):
                options_dest = [
                    options_dest
                ]

            all_segments = []

            for od in options_dest:

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

                all_segments.extend(
                    segments
                )

            number_of_segments = len(
                all_segments
            )

            if number_of_segments <= 1:
                flight_type = "Vol direct"
            else:
                flight_type = (
                    f"{number_of_segments - 1} escale(s)"
                )

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
                1,
            ):

                marketing_airline = (
                    seg
                    .get(
                        "MarketingAirline",
                        {},
                    )
                    .get(
                        "Code",
                        "",
                    )
                )

                operating_airline = (
                    seg
                    .get(
                        "OperatingAirline",
                        {},
                    )
                    .get(
                        "Code",
                        "",
                    )
                )

                flight_num = seg.get(
                    "FlightNumber",
                    "",
                )

                dep_apt = (
                    seg
                    .get(
                        "DepartureAirport",
                        {},
                    )
                    .get(
                        "LocationCode",
                        "",
                    )
                )

                arr_apt = (
                    seg
                    .get(
                        "ArrivalAirport",
                        {},
                    )
                    .get(
                        "LocationCode",
                        "",
                    )
                )

                dep_time = str(
                    seg.get(
                        "DepartureDateTime",
                        "",
                    )
                ).replace(
                    "T",
                    " à ",
                )

                arr_time = str(
                    seg.get(
                        "ArrivalDateTime",
                        "",
                    )
                ).replace(
                    "T",
                    " à ",
                )

                equipment = (
                    seg
                    .get(
                        "Equipment",
                        {},
                    )
                    .get(
                        "AirEquipType",
                        "N/A",
                    )
                )

                booking_class = seg.get(
                    "ResBookDesigCode",
                    "N/A",
                )

                elapsed_time = seg.get(
                    "ElapsedTime",
                    "N/A",
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

            passenger_fares = (
                self._extract_passenger_fares(
                    pricing
                )
            )

            validation = (
                self._validate_passenger_fares(
                    passenger_fares,
                    booking,
                )
            )

            passenger_totals = (
                self._calculate_passenger_total(
                    passenger_fares,
                    booking,
                )
            )

            # ----------------------------------------------------
            # AFFICHAGE DES TARIFS PASSAGERS
            # ----------------------------------------------------

            if passenger_totals:

                lines.append(
                    "• Tarifs passagers :"
                )

                for code, fare in (
                    passenger_totals.items()
                ):

                    if code == "ADT":
                        passenger_name = "Adulte"

                    elif code == "CNN":
                        passenger_name = "Enfant"

                    elif code == "INF":
                        passenger_name = "Bébé"

                    else:
                        passenger_name = code

                    lines.append(
                        f"- {passenger_name} x "
                        f"{fare['quantity']} : "
                        f"{fare['total']:.2f} "
                        f"{fare['currency']}"
                    )

                    lines.append(
                        f"  Base : "
                        f"{fare['base']:.2f} "
                        f"{fare['currency']}"
                    )

                    lines.append(
                        f"  Taxes : "
                        f"{fare['taxes']:.2f} "
                        f"{fare['currency']}"
                    )

            else:

                lines.append(
                    "• Tarification détaillée "
                    "par passager non disponible."
                )

            lines.append("")

            # ----------------------------------------------------
            # PRIX TOTAL
            # ----------------------------------------------------

            if validation["valid"]:

                final_total = sum(
                    fare["total"]
                    for fare in passenger_totals.values()
                )

                final_base = sum(
                    fare["base"]
                    for fare in passenger_totals.values()
                )

                final_taxes = sum(
                    fare["taxes"]
                    for fare in passenger_totals.values()
                )

                lines.append(
                    f"• Base totale : "
                    f"{final_base:.2f} {currency}"
                )

                lines.append(
                    f"• Taxes totales : "
                    f"{final_taxes:.2f} {currency}"
                )

                lines.append(
                    f"🏷️ PRIX TOTAL TTC : "
                    f"{final_total:.2f} {currency}"
                )

            else:

                lines.append(
                    "⚠️ PRIX PASSAGERS INCOMPLET"
                )

                lines.append(
                    "Sabre n'a pas retourné une "
                    "tarification correspondant "
                    "à tous les passagers demandés."
                )

                lines.append(
                    "Passagers manquants : "
                    + ", ".join(
                        validation["missing"]
                    )
                )

                lines.append(
                    f"⚠️ Total global Sabre : "
                    f"{global_total:.2f} "
                    f"{currency}"
                )

                lines.append(
                    "Ce montant n'est pas présenté "
                    "comme le prix final de la réservation."
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