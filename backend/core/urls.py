from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    AuditEventViewSet,
    IngestionRunViewSet,
    NormalizedActivityViewSet,
    SourceSystemViewSet,
    TenantViewSet,
    dashboard_summary,
    ingest,
)

router = DefaultRouter()
router.register("tenants", TenantViewSet, basename="tenant")
router.register("source-systems", SourceSystemViewSet, basename="source-system")
router.register("ingestion-runs", IngestionRunViewSet, basename="ingestion-run")
router.register("activities", NormalizedActivityViewSet, basename="activity")
router.register("audit-events", AuditEventViewSet, basename="audit-event")

urlpatterns = [
    path("", include(router.urls)),
    path("ingest/", ingest, name="ingest"),
    path("dashboard-summary/", dashboard_summary, name="dashboard-summary"),
]