from decimal import Decimal

from .common import (
    airport_distance,
    clean_string,
    confidence_from_warnings,
    normalize_unit,
    parse_date,
    parse_decimal,
    warning_status,
)


def parse_travel_row(row):
    warnings = []

    expense_type = clean_string(row.get("expense_type"))
    transaction_date = parse_date(row.get("transaction_date"))
    origin_airport = clean_string(row.get("origin_airport"))
    destination_airport = clean_string(row.get("destination_airport"))
    distance_km = parse_decimal(row.get("distance_km"))
    hotel_nights = parse_decimal(row.get("hotel_nights"))
    ground_distance_km = parse_decimal(row.get("ground_distance_km"))
    amount = parse_decimal(row.get("amount"))
    currency = clean_string(row.get("currency"))
    vendor = clean_string(row.get("vendor"))

    if not transaction_date:
        warnings.append("invalid_or_missing_date")

    expense_type_lower = expense_type.lower()

    original_quantity = None
    original_unit = ""
    normalized_quantity = None
    normalized_unit = ""
    activity_type = "unknown_travel_activity"

    if expense_type_lower in ["airfare", "flight", "flights"]:
        activity_type = "business_travel_flight"

        if distance_km is not None:
            original_quantity = distance_km
            original_unit = "km"
            normalized_quantity, normalized_unit, unit_warning = normalize_unit(
                distance_km,
                "km",
            )
            if unit_warning:
                warnings.append(unit_warning)
        else:
            calculated_distance = airport_distance(origin_airport, destination_airport)

            if calculated_distance:
                original_quantity = Decimal(str(calculated_distance))
                original_unit = "km"
                normalized_quantity = Decimal(str(calculated_distance))
                normalized_unit = "km"
                warnings.append("distance_calculated_from_airport_codes")
            else:
                warnings.append("missing_distance")
                normalized_unit = "passenger_km"

    elif expense_type_lower in ["hotel", "lodging"]:
        activity_type = "business_travel_hotel"

        if hotel_nights is not None:
            original_quantity = hotel_nights
            original_unit = "nights"
            normalized_quantity = hotel_nights
            normalized_unit = "nights"
        else:
            warnings.append("missing_hotel_nights")
            normalized_unit = "nights"

    elif expense_type_lower in ["taxi", "rideshare", "ground transport", "ground_transport"]:
        activity_type = "business_travel_ground_transport"

        if ground_distance_km is not None:
            original_quantity = ground_distance_km
            original_unit = "km"
            normalized_quantity, normalized_unit, unit_warning = normalize_unit(
                ground_distance_km,
                "km",
            )
            if unit_warning:
                warnings.append(unit_warning)
        else:
            warnings.append("missing_ground_distance")
            normalized_unit = "km"

    else:
        warnings.append("unsupported_expense_type")

    return {
        "activity_date": transaction_date,
        "period_start": None,
        "period_end": None,
        "facility_code": "",
        "cost_center": "",
        "activity_type": activity_type,
        "scope_category": "scope_3",
        "original_quantity": original_quantity,
        "original_unit": original_unit,
        "normalized_quantity": normalized_quantity,
        "normalized_unit": normalized_unit,
        "amount": amount,
        "currency": currency,
        "supplier_or_vendor": vendor,
        "confidence_score": confidence_from_warnings(warnings),
        "warning_flags": warnings,
        "status": warning_status(warnings),
    }