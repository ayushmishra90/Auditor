from datetime import date, datetime
from decimal import Decimal

from django.db import transaction

from .models import AuditEvent, IngestionRun, NormalizedActivity, RawRecord, SourceSystem, Tenant
from .parsers.common import (
    clean_row,
    has_extra_columns,
    read_csv_file,
    row_hash,
    validate_csv_headers,
)
from .parsers.sap import parse_sap_row
from .parsers.travel import parse_travel_row
from .parsers.utility import parse_utility_row


PARSER_BY_SOURCE_TYPE = {
    SourceSystem.SourceType.SAP: parse_sap_row,
    SourceSystem.SourceType.UTILITY: parse_utility_row,
    SourceSystem.SourceType.TRAVEL: parse_travel_row,
}


SOURCE_NAME_BY_TYPE = {
    SourceSystem.SourceType.SAP: "SAP Export",
    SourceSystem.SourceType.UTILITY: "Utility Portal Export",
    SourceSystem.SourceType.TRAVEL: "Corporate Travel Export",
}


def get_or_create_demo_tenant():
    tenant, _ = Tenant.objects.get_or_create(
        slug="demo-client",
        defaults={"name": "Demo Client"},
    )
    return tenant


def get_or_create_source_system(tenant, source_type):
    source_system, _ = SourceSystem.objects.get_or_create(
        tenant=tenant,
        source_type=source_type,
        name=SOURCE_NAME_BY_TYPE[source_type],
        defaults={
            "description": f"Demo {SOURCE_NAME_BY_TYPE[source_type]} source system.",
            "is_active": True,
        },
    )
    return source_system

def make_json_safe(value):
    """
    Converts Python objects like date and Decimal into JSON-safe values
    before storing them in AuditEvent JSON fields.
    """
    if isinstance(value, dict):
        return {key: make_json_safe(item) for key, item in value.items()}

    if isinstance(value, list):
        return [make_json_safe(item) for item in value]

    if isinstance(value, (date, datetime)):
        return value.isoformat()

    if isinstance(value, Decimal):
        return str(value)

    return value

@transaction.atomic
def ingest_csv_file(*, uploaded_file, source_type, user=None):
    if source_type not in PARSER_BY_SOURCE_TYPE:
        raise ValueError(f"Unsupported source_type: {source_type}")

    tenant = get_or_create_demo_tenant()
    source_system = get_or_create_source_system(tenant, source_type)
    parser = PARSER_BY_SOURCE_TYPE[source_type]

    ingestion_run = IngestionRun.objects.create(
        tenant=tenant,
        source_system=source_system,
        uploaded_file_name=uploaded_file.name,
        status=IngestionRun.Status.PROCESSING,
        created_by=user if user and user.is_authenticated else None,
    )

    rows = read_csv_file(uploaded_file)

    validate_csv_headers(rows, source_type)

    total_rows = len(rows)
    success_rows = 0
    failed_rows = 0

    for index, original_row in enumerate(rows, start=1):
        row_has_extra_columns = has_extra_columns(original_row)
        row = clean_row(original_row)

        raw_record = RawRecord.objects.create(
            tenant=tenant,
            ingestion_run=ingestion_run,
            source_system=source_system,
            source_row_number=index,
            raw_payload=row,
            row_hash=row_hash(row),
            status=RawRecord.Status.PARSED,
        )

        if row_has_extra_columns:
            raw_record.status = RawRecord.Status.FAILED
            raw_record.error_message = "Row has more columns than the CSV header."
            raw_record.save(update_fields=["status", "error_message"])

            AuditEvent.objects.create(
                tenant=tenant,
                normalized_activity=None,
                raw_record=raw_record,
                event_type=AuditEvent.EventType.FAILED,
                before_payload=None,
                after_payload=make_json_safe(row),
                actor=user if user and user.is_authenticated else None,
                message="Row rejected because it has more columns than the CSV header.",
            )

            failed_rows += 1
            continue

        try:
            normalized_payload = parser(row)

            activity = NormalizedActivity.objects.create(
                tenant=tenant,
                raw_record=raw_record,
                source_system=source_system,
                **normalized_payload,
            )

            AuditEvent.objects.create(
                tenant=tenant,
                normalized_activity=activity,
                raw_record=raw_record,
                event_type=AuditEvent.EventType.CREATED,
                before_payload=None,
                after_payload=make_json_safe(normalized_payload),
                actor=user if user and user.is_authenticated else None,
                message="Normalized activity created from raw source row.",
            )

            success_rows += 1

        except Exception as exc:
            raw_record.status = RawRecord.Status.FAILED
            raw_record.error_message = str(exc)
            raw_record.save(update_fields=["status", "error_message"])

            AuditEvent.objects.create(
                tenant=tenant,
                normalized_activity=None,
                raw_record=raw_record,
                event_type=AuditEvent.EventType.FAILED,
                before_payload=None,
                after_payload=make_json_safe(row),
                actor=user if user and user.is_authenticated else None,
                message=f"Failed to parse row: {exc}",
            )

            failed_rows += 1

    ingestion_run.total_rows = total_rows
    ingestion_run.success_rows = success_rows
    ingestion_run.failed_rows = failed_rows

    if failed_rows == 0:
        ingestion_run.status = IngestionRun.Status.COMPLETED
    elif success_rows > 0:
        ingestion_run.status = IngestionRun.Status.COMPLETED_WITH_ERRORS
    else:
        ingestion_run.status = IngestionRun.Status.FAILED

    ingestion_run.save(
        update_fields=[
            "total_rows",
            "success_rows",
            "failed_rows",
            "status",
        ]
    )

    return ingestion_run

def create_failed_ingestion_run(*, uploaded_file_name, source_type, error_message, user=None):
    """
    Records an upload-level ingestion failure.

    This is intentionally outside the main atomic ingestion path. If a CSV is
    structurally invalid, we still want analysts/engineers to see that an upload
    attempt happened, but we do not want partial raw or normalized rows.
    """
    tenant = get_or_create_demo_tenant()

    if source_type in SOURCE_NAME_BY_TYPE:
        source_system = get_or_create_source_system(tenant, source_type)
    else:
        source_system = SourceSystem.objects.create(
            tenant=tenant,
            source_type=SourceSystem.SourceType.SAP,
            name=f"Unsupported source: {source_type}",
            description="Failed upload with unsupported source type.",
            is_active=False,
        )

    return IngestionRun.objects.create(
        tenant=tenant,
        source_system=source_system,
        uploaded_file_name=uploaded_file_name,
        status=IngestionRun.Status.FAILED,
        total_rows=0,
        success_rows=0,
        failed_rows=0,
        error_message=error_message,
        created_by=user if user and user.is_authenticated else None,
    )