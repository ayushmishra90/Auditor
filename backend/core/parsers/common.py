import csv
import hashlib
import io
from datetime import datetime
from decimal import Decimal, InvalidOperation

REQUIRED_HEADERS_BY_SOURCE_TYPE = {
    "sap": {
        "company_code",
        "plant_code",
        "material_code",
        "material_description",
        "posting_date",
        "quantity",
        "unit",
        "cost_center",
        "vendor",
        "document_number",
        "currency",
        "amount",
    },
    "utility": {
        "account_number",
        "meter_id",
        "facility_code",
        "bill_start",
        "bill_end",
        "usage",
        "usage_unit",
        "demand_kw",
        "tariff_name",
        "total_cost",
        "currency",
        "estimated",
    },
    "travel": {
        "report_id",
        "employee_id",
        "expense_type",
        "transaction_date",
        "origin_airport",
        "destination_airport",
        "distance_km",
        "hotel_nights",
        "ground_distance_km",
        "amount",
        "currency",
        "vendor",
    },
}

KNOWN_FACILITIES = {"DE01", "DE02", "IN01"}

AIRPORT_DISTANCE_KM = {
    ("BLR", "LHR"): 8050,
    ("LHR", "BLR"): 8050,
    ("DEL", "BOM"): 1150,
    ("BOM", "DEL"): 1150,
    ("BLR", "DEL"): 1740,
    ("DEL", "BLR"): 1740,
}


def read_csv_file(uploaded_file):
    """
    Reads a Django uploaded CSV file and returns rows as dictionaries.
    """
    decoded_file = uploaded_file.read().decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(decoded_file))
    return list(reader)

def normalize_header(header):
    if header is None:
        return ""
    return str(header).strip().lower()


def validate_csv_headers(rows, source_type):
    """
    Validates that an uploaded CSV matches the expected source type.

    This prevents a utility CSV from being uploaded as travel, or a random CSV
    from creating normalized records.
    """
    required_headers = REQUIRED_HEADERS_BY_SOURCE_TYPE.get(source_type)

    if not required_headers:
        raise ValueError(f"Unsupported source type: {source_type}")

    if not rows:
        raise ValueError("CSV file is empty.")

    actual_headers = set(normalize_header(key) for key in rows[0].keys() if key is not None)

    missing_headers = sorted(required_headers - actual_headers)

    if missing_headers:
        raise ValueError(
            "Invalid CSV for source_type="
            f"{source_type}. Missing required columns: {', '.join(missing_headers)}"
        )

    return True


def has_extra_columns(row):
    """
    csv.DictReader stores extra columns under None.
    That means the row has more values than the header.
    """
    return None in row

def row_hash(row):
    """
    Creates a stable hash for a raw source row.

    csv.DictReader creates a None key when a row has more values than headers.
    We stringify keys and values so malformed rows do not crash ingestion.
    """
    safe_items = []

    for key, value in row.items():
        safe_key = "_extra_columns" if key is None else str(key)
        safe_value = "" if value is None else str(value)
        safe_items.append((safe_key, safe_value))

    row_string = "|".join(
        f"{key}={value}" for key, value in sorted(safe_items, key=lambda item: item[0])
    )

    return hashlib.sha256(row_string.encode("utf-8")).hexdigest()


def clean_string(value):
    if value is None:
        return ""
    return str(value).strip()

def clean_row(row):
    """
    Cleans rows returned by csv.DictReader.

    If a row has more values than headers, DictReader stores the extra values
    under a None key. We preserve those under '_extra_columns' so the analyst can
    see the malformed source row instead of ingestion crashing.
    """
    cleaned = {}

    for key, value in row.items():
        if key is None:
            cleaned["_extra_columns"] = value
        else:
            cleaned[str(key)] = "" if value is None else value

    return cleaned

def parse_decimal(value):
    value = clean_string(value)

    if value == "":
        return None

    try:
        return Decimal(value)
    except (InvalidOperation, ValueError):
        return None


def parse_date(value):
    """
    Supports multiple date formats because source exports are inconsistent.
    """
    value = clean_string(value)

    if not value:
        return None

    formats = [
        "%Y-%m-%d",
        "%d.%m.%Y",
        "%Y/%m/%d",
        "%m/%d/%Y",
    ]

    for date_format in formats:
        try:
            return datetime.strptime(value, date_format).date()
        except ValueError:
            continue

    return None


def normalize_unit(quantity, unit):
    """
    Normalizes a small set of units for the prototype.
    Returns: normalized_quantity, normalized_unit, warning
    """
    if quantity is None:
        return None, "", "missing_quantity"

    unit_clean = clean_string(unit).upper()

    if unit_clean in ["L", "LTR", "LITER", "LITRE", "LITERS", "LITRES"]:
        return quantity, "L", None

    if unit_clean in ["GAL", "GALLON", "GALLONS"]:
        return quantity * Decimal("3.78541"), "L", None

    if unit_clean == "KWH":
        return quantity, "kWh", None

    if unit_clean == "MWH":
        return quantity * Decimal("1000"), "kWh", None

    if unit_clean in ["KM", "KMS", "KILOMETER", "KILOMETERS"]:
        return quantity, "km", None

    if unit_clean in ["MI", "MILE", "MILES"]:
        return quantity * Decimal("1.60934"), "km", None

    return quantity, unit_clean, "unknown_unit"


def warning_status(warnings):
    """
    Rows with warnings need analyst review.
    Clean rows can remain pending.
    """
    return "needs_review" if warnings else "pending"


def confidence_from_warnings(warnings):
    """
    Simple confidence score for prototype explainability.
    """
    if not warnings:
        return Decimal("1.00")

    score = Decimal("1.00") - (Decimal("0.15") * Decimal(len(warnings)))

    if score < Decimal("0.10"):
        return Decimal("0.10")

    return score


def is_cross_month(start_date, end_date):
    if not start_date or not end_date:
        return False

    return start_date.month != end_date.month or start_date.year != end_date.year


def airport_distance(origin, destination):
    origin = clean_string(origin).upper()
    destination = clean_string(destination).upper()

    if not origin or not destination:
        return None

    return AIRPORT_DISTANCE_KM.get((origin, destination))