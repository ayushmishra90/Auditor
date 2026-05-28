from rest_framework import serializers

from .models import (
    AuditEvent,
    IngestionRun,
    NormalizedActivity,
    RawRecord,
    SourceSystem,
    Tenant,
)


class TenantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tenant
        fields = [
            "id",
            "name",
            "slug",
            "created_at",
        ]


class SourceSystemSerializer(serializers.ModelSerializer):
    tenant_name = serializers.CharField(source="tenant.name", read_only=True)

    class Meta:
        model = SourceSystem
        fields = [
            "id",
            "tenant",
            "tenant_name",
            "name",
            "source_type",
            "description",
            "is_active",
            "created_at",
        ]


class IngestionRunSerializer(serializers.ModelSerializer):
    tenant_name = serializers.CharField(source="tenant.name", read_only=True)
    source_system_name = serializers.CharField(source="source_system.name", read_only=True)
    source_type = serializers.CharField(source="source_system.source_type", read_only=True)

    class Meta:
        model = IngestionRun
        fields = [
            "id",
            "tenant",
            "tenant_name",
            "source_system",
            "source_system_name",
            "source_type",
            "uploaded_file_name",
            "status",
            "total_rows",
            "success_rows",
            "failed_rows",
            "error_message",
            "created_by",
            "created_at",
        ]
        read_only_fields = [
            "status",
            "total_rows",
            "success_rows",
            "failed_rows",
            "error_message",
            "created_by",
            "created_at",
        ]


class RawRecordSerializer(serializers.ModelSerializer):
    source_system_name = serializers.CharField(source="source_system.name", read_only=True)

    class Meta:
        model = RawRecord
        fields = [
            "id",
            "tenant",
            "ingestion_run",
            "source_system",
            "source_system_name",
            "source_row_number",
            "raw_payload",
            "row_hash",
            "status",
            "error_message",
            "created_at",
        ]


class AuditEventSerializer(serializers.ModelSerializer):
    actor_username = serializers.CharField(source="actor.username", read_only=True)

    class Meta:
        model = AuditEvent
        fields = [
            "id",
            "tenant",
            "normalized_activity",
            "raw_record",
            "event_type",
            "before_payload",
            "after_payload",
            "actor",
            "actor_username",
            "message",
            "created_at",
        ]


class NormalizedActivitySerializer(serializers.ModelSerializer):
    tenant_name = serializers.CharField(source="tenant.name", read_only=True)
    source_system_name = serializers.CharField(source="source_system.name", read_only=True)
    source_type = serializers.CharField(source="source_system.source_type", read_only=True)
    raw_record_payload = serializers.JSONField(source="raw_record.raw_payload", read_only=True)
    audit_events = AuditEventSerializer(many=True, read_only=True)
    approved_by_username = serializers.CharField(source="approved_by.username", read_only=True)
    edited_by_username = serializers.CharField(source="edited_by.username", read_only=True)

    class Meta:
        model = NormalizedActivity
        fields = [
            "id",
            "tenant",
            "tenant_name",
            "raw_record",
            "raw_record_payload",
            "source_system",
            "source_system_name",
            "source_type",
            "activity_date",
            "period_start",
            "period_end",
            "facility_code",
            "cost_center",
            "activity_type",
            "scope_category",
            "original_quantity",
            "original_unit",
            "normalized_quantity",
            "normalized_unit",
            "amount",
            "currency",
            "supplier_or_vendor",
            "confidence_score",
            "warning_flags",
            "status",
            "edited_by",
            "edited_by_username",
            "approved_by",
            "approved_by_username",
            "approved_at",
            "locked_at",
            "created_at",
            "updated_at",
            "audit_events",
        ]
        read_only_fields = [
            "tenant",
            "raw_record",
            "source_system",
            "original_quantity",
            "original_unit",
            "created_at",
            "updated_at",
            "approved_by",
            "approved_at",
            "locked_at",
            "audit_events",
        ]

    def validate(self, attrs):
        instance = self.instance

        if instance and instance.is_locked:
            raise serializers.ValidationError(
                "Locked activities cannot be edited through the analyst workflow."
            )
        
        if instance and instance.status == NormalizedActivity.Status.REJECTED:
            raise serializers.ValidationError(
                "Rejected activities cannot be edited through the analyst workflow."
            )

        return attrs

class IngestionUploadSerializer(serializers.Serializer):
    source_type = serializers.ChoiceField(
        choices=SourceSystem.SourceType.choices,
    )
    file = serializers.FileField()

    def validate_file(self, value):
        if not value.name.lower().endswith(".csv"):
            raise serializers.ValidationError("Only CSV files are supported.")

        return value