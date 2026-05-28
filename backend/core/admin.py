from django.contrib import admin

from .models import (
    AuditEvent,
    IngestionRun,
    NormalizedActivity,
    RawRecord,
    SourceSystem,
    Tenant,
)


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "created_at")
    search_fields = ("name", "slug")


@admin.register(SourceSystem)
class SourceSystemAdmin(admin.ModelAdmin):
    list_display = ("name", "tenant", "source_type", "is_active", "created_at")
    list_filter = ("source_type", "is_active", "tenant")
    search_fields = ("name", "tenant__name")


@admin.register(IngestionRun)
class IngestionRunAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "tenant",
        "source_system",
        "uploaded_file_name",
        "status",
        "total_rows",
        "success_rows",
        "failed_rows",
        "created_at",
    )
    list_filter = ("status", "source_system__source_type", "tenant")
    search_fields = ("uploaded_file_name", "source_system__name", "tenant__name")
    readonly_fields = ("created_at",)


@admin.register(RawRecord)
class RawRecordAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "tenant",
        "source_system",
        "ingestion_run",
        "source_row_number",
        "status",
        "created_at",
    )
    list_filter = ("status", "source_system__source_type", "tenant")
    search_fields = ("row_hash", "error_message")
    readonly_fields = ("raw_payload", "created_at")


@admin.register(NormalizedActivity)
class NormalizedActivityAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "tenant",
        "source_system",
        "activity_type",
        "scope_category",
        "facility_code",
        "original_quantity",
        "original_unit",
        "normalized_quantity",
        "normalized_unit",
        "status",
        "created_at",
    )
    list_filter = (
        "status",
        "scope_category",
        "source_system__source_type",
        "tenant",
    )
    search_fields = (
        "activity_type",
        "facility_code",
        "cost_center",
        "supplier_or_vendor",
    )
    readonly_fields = (
        "created_at",
        "updated_at",
        "approved_at",
        "locked_at",
    )


@admin.register(AuditEvent)
class AuditEventAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "tenant",
        "event_type",
        "normalized_activity",
        "actor",
        "created_at",
    )
    list_filter = ("event_type", "tenant")
    search_fields = ("message",)
    readonly_fields = (
        "before_payload",
        "after_payload",
        "created_at",
    )