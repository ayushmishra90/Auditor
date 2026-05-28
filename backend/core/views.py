from django.db.models import Count
from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from .ingestion import create_failed_ingestion_run, ingest_csv_file

from .models import AuditEvent, IngestionRun, NormalizedActivity, SourceSystem, Tenant
from .serializers import (
    AuditEventSerializer,
    IngestionRunSerializer,
    IngestionUploadSerializer,
    NormalizedActivitySerializer,
    SourceSystemSerializer,
    TenantSerializer,
)


class TenantViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tenant.objects.all()
    serializer_class = TenantSerializer


class SourceSystemViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = SourceSystem.objects.select_related("tenant").all()
    serializer_class = SourceSystemSerializer


class IngestionRunViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = (
        IngestionRun.objects.select_related("tenant", "source_system", "created_by")
        .all()
    )
    serializer_class = IngestionRunSerializer


class AuditEventViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = (
        AuditEvent.objects.select_related(
            "tenant",
            "normalized_activity",
            "raw_record",
            "actor",
        )
        .all()
    )
    serializer_class = AuditEventSerializer


class NormalizedActivityViewSet(viewsets.ModelViewSet):
    queryset = (
        NormalizedActivity.objects.select_related(
            "tenant",
            "raw_record",
            "source_system",
            "edited_by",
            "approved_by",
        )
        .prefetch_related("audit_events")
        .all()
    )
    serializer_class = NormalizedActivitySerializer

    def get_queryset(self):
        queryset = super().get_queryset()

        source_type = self.request.query_params.get("source_type")
        scope_category = self.request.query_params.get("scope_category")
        status_value = self.request.query_params.get("status")
        facility_code = self.request.query_params.get("facility_code")
        warning = self.request.query_params.get("warning")

        if source_type:
            queryset = queryset.filter(source_system__source_type=source_type)

        if scope_category:
            queryset = queryset.filter(scope_category=scope_category)

        if status_value:
            queryset = queryset.filter(status=status_value)

        if facility_code:
            queryset = queryset.filter(facility_code__icontains=facility_code)

        if warning:
            matching_ids = [
                activity.id
                for activity in queryset
                if warning in (activity.warning_flags or [])
            ]
            queryset = queryset.filter(id__in=matching_ids)
        
        return queryset

    def partial_update(self, request, *args, **kwargs):
        activity = self.get_object()

        if activity.is_locked:
            return Response(
                {"detail": "Locked activities cannot be edited."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if activity.status == NormalizedActivity.Status.REJECTED:
            return Response(
                {"detail": "Rejected activities cannot be edited."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        before_payload = NormalizedActivitySerializer(activity).data

        response = super().partial_update(request, *args, **kwargs)

        activity.refresh_from_db()
        activity.edited_by = request.user if request.user.is_authenticated else None
        activity.save(update_fields=["edited_by", "updated_at"])

        after_payload = NormalizedActivitySerializer(activity).data

        AuditEvent.objects.create(
            tenant=activity.tenant,
            normalized_activity=activity,
            raw_record=activity.raw_record,
            event_type=AuditEvent.EventType.EDITED,
            before_payload=before_payload,
            after_payload=after_payload,
            actor=request.user if request.user.is_authenticated else None,
            message="Normalized activity edited by analyst.",
        )

        return response

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        activity = self.get_object()

        if activity.is_locked:
            return Response(
                {"detail": "Activity is already locked."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        if activity.status == NormalizedActivity.Status.REJECTED:
            return Response(
                {"detail": "Rejected activities cannot be approved."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        before_payload = NormalizedActivitySerializer(activity).data

        activity.approve_and_lock(
            user=request.user if request.user.is_authenticated else None
        )

        after_payload = NormalizedActivitySerializer(activity).data

        AuditEvent.objects.create(
            tenant=activity.tenant,
            normalized_activity=activity,
            raw_record=activity.raw_record,
            event_type=AuditEvent.EventType.APPROVED,
            before_payload=before_payload,
            after_payload=after_payload,
            actor=request.user if request.user.is_authenticated else None,
            message="Activity approved and locked for audit.",
        )

        AuditEvent.objects.create(
            tenant=activity.tenant,
            normalized_activity=activity,
            raw_record=activity.raw_record,
            event_type=AuditEvent.EventType.LOCKED,
            before_payload=before_payload,
            after_payload=after_payload,
            actor=request.user if request.user.is_authenticated else None,
            message="Activity locked after approval.",
        )

        return Response(NormalizedActivitySerializer(activity).data)

    @action(detail=True, methods=["post"])
    def reject(self, request, pk=None):
        activity = self.get_object()

        if activity.is_locked:
            return Response(
                {"detail": "Locked activities cannot be rejected."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        if activity.status == NormalizedActivity.Status.REJECTED:
            return Response(
                {"detail": "Activity is already rejected."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        before_payload = NormalizedActivitySerializer(activity).data

        activity.reject(user=request.user if request.user.is_authenticated else None)

        after_payload = NormalizedActivitySerializer(activity).data

        AuditEvent.objects.create(
            tenant=activity.tenant,
            normalized_activity=activity,
            raw_record=activity.raw_record,
            event_type=AuditEvent.EventType.REJECTED,
            before_payload=before_payload,
            after_payload=after_payload,
            actor=request.user if request.user.is_authenticated else None,
            message="Activity rejected by analyst.",
        )

        return Response(NormalizedActivitySerializer(activity).data)


@api_view(["POST"])
def ingest(request):
    serializer = IngestionUploadSerializer(data=request.data)

    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    uploaded_file = serializer.validated_data["file"]
    source_type = serializer.validated_data["source_type"]

    try:
        ingestion_run = ingest_csv_file(
            uploaded_file=uploaded_file,
            source_type=source_type,
            user=request.user,
        )
    except ValueError as exc:
        failed_run = create_failed_ingestion_run(
            uploaded_file_name=uploaded_file.name,
            source_type=source_type,
            error_message=str(exc),
            user=request.user,
        )

        return Response(
            {
                "detail": str(exc),
                "ingestion_run": IngestionRunSerializer(failed_run).data,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )
    except Exception as exc:
        failed_run = create_failed_ingestion_run(
            uploaded_file_name=uploaded_file.name,
            source_type=source_type,
            error_message=f"Unexpected ingestion error: {str(exc)}",
            user=request.user,
        )

        return Response(
            {
                "detail": f"Unexpected ingestion error: {str(exc)}",
                "ingestion_run": IngestionRunSerializer(failed_run).data,
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
    return Response(
        IngestionRunSerializer(ingestion_run).data,
        status=status.HTTP_201_CREATED,
    )
    
@api_view(["GET"])
def dashboard_summary(request):
    total_activities = NormalizedActivity.objects.count()
    pending_count = NormalizedActivity.objects.filter(
        status=NormalizedActivity.Status.PENDING
    ).count()
    needs_review_count = NormalizedActivity.objects.filter(
        status=NormalizedActivity.Status.NEEDS_REVIEW
    ).count()
    locked_count = NormalizedActivity.objects.filter(
        status=NormalizedActivity.Status.LOCKED
    ).count()
    rejected_count = NormalizedActivity.objects.filter(
        status=NormalizedActivity.Status.REJECTED
    ).count()

    by_scope = (
        NormalizedActivity.objects.values("scope_category")
        .annotate(count=Count("id"))
        .order_by("scope_category")
    )

    by_source = (
        NormalizedActivity.objects.values("source_system__source_type")
        .annotate(count=Count("id"))
        .order_by("source_system__source_type")
    )

    recent_runs = IngestionRun.objects.select_related("source_system").order_by(
        "-created_at"
    )[:5]

    return Response(
        {
            "total_activities": total_activities,
            "pending_count": pending_count,
            "needs_review_count": needs_review_count,
            "locked_count": locked_count,
            "rejected_count": rejected_count,
            "by_scope": list(by_scope),
            "by_source": list(by_source),
            "recent_runs": IngestionRunSerializer(recent_runs, many=True).data,
        }
    )