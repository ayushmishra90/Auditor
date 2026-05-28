from .common import (
    KNOWN_FACILITIES,
    clean_string,
    confidence_from_warnings,
    is_cross_month,
    normalize_unit,
    parse_date,
    parse_decimal,
    warning_status,
)


def parse_utility_row(row):
    warnings = []

    meter_id = clean_string(row.get("meter_id"))
    facility_code = clean_string(row.get("facility_code"))
    bill_start = parse_date(row.get("bill_start"))
    bill_end = parse_date(row.get("bill_end"))
    usage = parse_decimal(row.get("usage"))
    usage_unit = clean_string(row.get("usage_unit"))
    demand_kw = parse_decimal(row.get("demand_kw"))
    tariff_name = clean_string(row.get("tariff_name"))
    total_cost = parse_decimal(row.get("total_cost"))
    currency = clean_string(row.get("currency"))
    estimated = clean_string(row.get("estimated")).lower()

    if not meter_id:
        warnings.append("missing_meter_id")

    if not facility_code:
        warnings.append("missing_facility")
    elif facility_code not in KNOWN_FACILITIES:
        warnings.append("unknown_facility_code")

    if not bill_start or not bill_end:
        warnings.append("invalid_or_missing_billing_period")

    if is_cross_month(bill_start, bill_end):
        warnings.append("billing_period_crosses_month")

    normalized_quantity, normalized_unit, unit_warning = normalize_unit(usage, usage_unit)

    if unit_warning:
        warnings.append(unit_warning)

    if usage is not None and usage < 0:
        warnings.append("negative_quantity")

    if usage is not None and usage > 500000:
        warnings.append("large_quantity_outlier")

    if estimated in ["true", "yes", "1", "y"]:
        warnings.append("estimated_bill")

    return {
        "activity_date": None,
        "period_start": bill_start,
        "period_end": bill_end,
        "facility_code": facility_code,
        "cost_center": "",
        "activity_type": "purchased_electricity",
        "scope_category": "scope_2",
        "original_quantity": usage,
        "original_unit": usage_unit,
        "normalized_quantity": normalized_quantity,
        "normalized_unit": normalized_unit,
        "amount": total_cost,
        "currency": currency,
        "supplier_or_vendor": tariff_name,
        "confidence_score": confidence_from_warnings(warnings),
        "warning_flags": warnings,
        "status": warning_status(warnings),
    }