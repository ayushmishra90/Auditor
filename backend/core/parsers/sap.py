from .common import (
    KNOWN_FACILITIES,
    clean_string,
    confidence_from_warnings,
    normalize_unit,
    parse_date,
    parse_decimal,
    warning_status,
)


FUEL_MATERIAL_KEYWORDS = ["DIESEL", "PETROL", "GASOLINE", "LPG", "NATURAL GAS"]


def parse_sap_row(row):
    warnings = []

    plant_code = clean_string(row.get("plant_code"))
    material_code = clean_string(row.get("material_code"))
    material_description = clean_string(row.get("material_description"))
    posting_date = parse_date(row.get("posting_date"))
    quantity = parse_decimal(row.get("quantity"))
    unit = clean_string(row.get("unit"))
    cost_center = clean_string(row.get("cost_center"))
    vendor = clean_string(row.get("vendor"))
    amount = parse_decimal(row.get("amount"))
    currency = clean_string(row.get("currency"))

    if not posting_date:
        warnings.append("invalid_or_missing_date")

    if not plant_code:
        warnings.append("missing_facility")
    elif plant_code not in KNOWN_FACILITIES:
        warnings.append("unknown_plant_code")

    if not cost_center:
        warnings.append("missing_cost_center")

    normalized_quantity, normalized_unit, unit_warning = normalize_unit(quantity, unit)

    if unit_warning:
        warnings.append(unit_warning)

    if quantity is not None and quantity < 0:
        warnings.append("negative_quantity")

    if quantity is not None and quantity > 100000:
        warnings.append("large_quantity_outlier")

    material_text = f"{material_code} {material_description}".upper()

    if any(keyword in material_text for keyword in FUEL_MATERIAL_KEYWORDS):
        activity_type = "stationary_or_mobile_fuel_combustion"
        scope_category = "scope_1"
    else:
        activity_type = "purchased_goods_or_material"
        scope_category = "scope_3"
        warnings.append("uncertain_material_classification")

    return {
        "activity_date": posting_date,
        "period_start": None,
        "period_end": None,
        "facility_code": plant_code,
        "cost_center": cost_center,
        "activity_type": activity_type,
        "scope_category": scope_category,
        "original_quantity": quantity,
        "original_unit": unit,
        "normalized_quantity": normalized_quantity,
        "normalized_unit": normalized_unit,
        "amount": amount,
        "currency": currency,
        "supplier_or_vendor": vendor,
        "confidence_score": confidence_from_warnings(warnings),
        "warning_flags": warnings,
        "status": warning_status(warnings),
    }