from django.conf import settings
from django.db import models
from django.utils import timezone


class Tenant(models.Model):
    """
    Represents a client company.

    Multi-tenancy is modeled explicitly so all source systems, ingestion runs,
    raw records, normalized activities, and audit events can be tied back to
    the client that owns the data.
    """

    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class SourceSystem(models.Model):
    """
    Represents the origin of uploaded data.

    Example source systems:
    - SAP
    - Utility Portal
    - Corporate Travel Platform
    """

    class SourceType(models.TextChoices):
        SAP = "sap", "SAP"
        UTILITY = "utility", "Utility Electricity"
        TRAVEL = "travel", "Corporate Travel"

    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name="source_systems",
    )
    name = models.CharField(max_length=255)
    source_type = models.CharField(
        max_length=50,
        choices=SourceType.choices,
    )
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ["tenant", "name"]
        ordering = ["tenant__name", "source_type", "name"]

    def __str__(self):
        return f"{self.tenant.name} - {self.name}"


class IngestionRun(models.Model):
    """
    Represents one upload/import attempt.

    This lets analysts and engineers trace what happened during ingestion:
    which file was uploaded, which source it came from, how many rows succeeded,
    and how many failed.
    """

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PROCESSING = "processing", "Processing"
        COMPLETED = "completed", "Completed"
        COMPLETED_WITH_ERRORS = "completed_with_errors", "Completed with Errors"
        FAILED = "failed", "Failed"

    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name="ingestion_runs",
    )
    source_system = models.ForeignKey(
        SourceSystem,
        on_delete=models.PROTECT,
        related_name="ingestion_runs",
    )
    uploaded_file_name = models.CharField(max_length=255)
    status = models.CharField(
        max_length=50,
        choices=Status.choices,
        default=Status.PENDING,
    )
    total_rows = models.PositiveIntegerField(default=0)
    success_rows = models.PositiveIntegerField(default=0)
    failed_rows = models.PositiveIntegerField(default=0)
    error_message = models.TextField(blank=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_ingestion_runs",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.source_system.name} - {self.uploaded_file_name}"


class RawRecord(models.Model):
    """
    Stores the source row exactly as received.

    This is the source-of-truth layer. Even if an analyst later edits the
    normalized activity, the raw source payload remains unchanged.
    """

    class Status(models.TextChoices):
        PARSED = "parsed", "Parsed"
        FAILED = "failed", "Failed"

    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name="raw_records",
    )
    ingestion_run = models.ForeignKey(
        IngestionRun,
        on_delete=models.CASCADE,
        related_name="raw_records",
    )
    source_system = models.ForeignKey(
        SourceSystem,
        on_delete=models.PROTECT,
        related_name="raw_records",
    )
    source_row_number = models.PositiveIntegerField()
    raw_payload = models.JSONField()
    row_hash = models.CharField(max_length=64, db_index=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PARSED,
    )
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["ingestion_run", "source_row_number"]
        unique_together = ["ingestion_run", "source_row_number"]

    def __str__(self):
        return f"{self.ingestion_run_id} row {self.source_row_number}"


class NormalizedActivity(models.Model):
    """
    Standardized activity row that analysts review.

    This model is intentionally source-agnostic. SAP fuel, utility electricity,
    and business travel rows all become NormalizedActivity records.
    """

    class ScopeCategory(models.TextChoices):
        SCOPE_1 = "scope_1", "Scope 1"
        SCOPE_2 = "scope_2", "Scope 2"
        SCOPE_3 = "scope_3", "Scope 3"
        UNKNOWN = "unknown", "Unknown"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        NEEDS_REVIEW = "needs_review", "Needs Review"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"
        LOCKED = "locked", "Locked"
        FAILED = "failed", "Failed"

    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name="normalized_activities",
    )
    raw_record = models.OneToOneField(
        RawRecord,
        on_delete=models.CASCADE,
        related_name="normalized_activity",
        null=True,
        blank=True,
    )
    source_system = models.ForeignKey(
        SourceSystem,
        on_delete=models.PROTECT,
        related_name="normalized_activities",
    )

    activity_date = models.DateField(null=True, blank=True)
    period_start = models.DateField(null=True, blank=True)
    period_end = models.DateField(null=True, blank=True)

    facility_code = models.CharField(max_length=100, blank=True)
    cost_center = models.CharField(max_length=100, blank=True)

    activity_type = models.CharField(max_length=100)
    scope_category = models.CharField(
        max_length=20,
        choices=ScopeCategory.choices,
        default=ScopeCategory.UNKNOWN,
    )

    original_quantity = models.DecimalField(
        max_digits=18,
        decimal_places=4,
        null=True,
        blank=True,
    )
    original_unit = models.CharField(max_length=50, blank=True)

    normalized_quantity = models.DecimalField(
        max_digits=18,
        decimal_places=4,
        null=True,
        blank=True,
    )
    normalized_unit = models.CharField(max_length=50, blank=True)

    amount = models.DecimalField(
        max_digits=18,
        decimal_places=4,
        null=True,
        blank=True,
    )
    currency = models.CharField(max_length=10, blank=True)

    supplier_or_vendor = models.CharField(max_length=255, blank=True)

    confidence_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=1.00,
        help_text="Simple prototype confidence score between 0 and 1.",
    )
    warning_flags = models.JSONField(default=list, blank=True)

    status = models.CharField(
        max_length=30,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )

    edited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="edited_activities",
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_activities",
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    locked_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["tenant", "status"]),
            models.Index(fields=["tenant", "scope_category"]),
            models.Index(fields=["tenant", "source_system"]),
            models.Index(fields=["facility_code"]),
        ]

    def __str__(self):
        return f"{self.source_system.name} - {self.activity_type} - {self.status}"

    @property
    def is_locked(self):
        return self.status == self.Status.LOCKED or self.locked_at is not None

    def approve_and_lock(self, user=None):
        """
        Approve and lock the row for audit.

        For this prototype, approval immediately locks the row.
        """
        self.status = self.Status.LOCKED
        self.approved_by = user
        self.approved_at = timezone.now()
        self.locked_at = timezone.now()
        self.save(
            update_fields=[
                "status",
                "approved_by",
                "approved_at",
                "locked_at",
                "updated_at",
            ]
        )

    def reject(self, user=None):
        self.status = self.Status.REJECTED
        self.edited_by = user
        self.save(update_fields=["status", "edited_by", "updated_at"])


class AuditEvent(models.Model):
    """
    Tracks important lifecycle events for normalized activities.

    Examples:
    - activity created from raw record
    - analyst edited normalized fields
    - analyst approved row
    - analyst rejected row
    - row locked for audit
    """

    class EventType(models.TextChoices):
        CREATED = "created", "Created"
        EDITED = "edited", "Edited"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"
        LOCKED = "locked", "Locked"
        FAILED = "failed", "Failed"

    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name="audit_events",
    )
    normalized_activity = models.ForeignKey(
        NormalizedActivity,
        on_delete=models.CASCADE,
        related_name="audit_events",
        null=True,
        blank=True,
    )
    raw_record = models.ForeignKey(
        RawRecord,
        on_delete=models.CASCADE,
        related_name="audit_events",
        null=True,
        blank=True,
    )
    event_type = models.CharField(
        max_length=30,
        choices=EventType.choices,
    )
    before_payload = models.JSONField(null=True, blank=True)
    after_payload = models.JSONField(null=True, blank=True)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_events",
    )
    message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["tenant", "event_type"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"{self.event_type} - {self.created_at}"