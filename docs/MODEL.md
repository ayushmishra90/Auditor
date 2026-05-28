# MODEL.md

## Overview

This prototype models an ESG data ingestion and analyst review workflow.

The model is designed to support:

- multi-tenancy
- source-of-truth tracking
- unit normalization
- Scope 1, Scope 2, and Scope 3 categorization
- analyst review
- edit history
- failed upload visibility
- audit trail
- audit locking

The most important design decision is separating raw source data from normalized review data.

Raw source data is preserved in `RawRecord`.

Analyst-reviewable standardized data is stored in `NormalizedActivity`.

This gives the system both:

- source-of-truth traceability
- analyst-editable normalized data

---

## Core Relationship

```text
Tenant
  -> SourceSystem
  -> IngestionRun
  -> RawRecord
  -> NormalizedActivity
  -> AuditEvent
```

---

## Implemented Django Models

The backend implements these core models:

- `Tenant`
- `SourceSystem`
- `IngestionRun`
- `RawRecord`
- `NormalizedActivity`
- `AuditEvent`

---

## Tenant

`Tenant` represents a client company.

Important fields:

- `name`
- `slug`
- `created_at`

### Why this model exists

The assignment requires multi-tenancy. Every source system, ingestion run, raw record, normalized activity, and audit event belongs to a tenant.

In this prototype, a demo tenant is automatically created. In production, tenants would be created and managed through an onboarding or admin workflow.

---

## SourceSystem

`SourceSystem` represents where uploaded data came from.

Examples:

- SAP Export
- Utility Portal Export
- Corporate Travel Export

Important fields:

- `tenant`
- `name`
- `source_type`
- `description`
- `is_active`
- `created_at`

### Why this model exists

Analysts and auditors need to know which system produced a row.

A normalized activity row is not enough by itself. The system should also answer:

- Did this row come from SAP?
- Did it come from a utility portal?
- Did it come from a corporate travel platform?
- Which tenant owns it?

---

## IngestionRun

`IngestionRun` represents one upload/import attempt.

Important fields:

- `tenant`
- `source_system`
- `uploaded_file_name`
- `status`
- `total_rows`
- `success_rows`
- `failed_rows`
- `error_message`
- `created_by`
- `created_at`

Possible statuses:

- `pending`
- `processing`
- `completed`
- `completed_with_errors`
- `failed`

### Why this model exists

An ingestion run lets analysts and engineers trace every file upload.

It records:

- which file was uploaded
- which source system it belonged to
- when it was uploaded
- whether it succeeded
- how many rows succeeded
- how many rows failed
- whether upload-level validation failed

### Upload-level failures

If a wrong CSV is uploaded, for example a SAP file uploaded as corporate travel, the app creates a failed `IngestionRun` but does not create raw or normalized rows.

This keeps failed upload attempts visible without inserting bad data.

---

## RawRecord

`RawRecord` stores one source row as received from the uploaded file.

Important fields:

- `tenant`
- `ingestion_run`
- `source_system`
- `source_row_number`
- `raw_payload`
- `row_hash`
- `status`
- `error_message`
- `created_at`

Possible statuses:

- `parsed`
- `failed`

### Why this model exists

`RawRecord` is the source-of-truth layer.

Even if an analyst edits the normalized version of a row, the original source row remains preserved.

This is important for auditability.

### Row-level failures

If a row has structural problems, such as more columns than the CSV header, the system can preserve it as a failed `RawRecord` without creating a `NormalizedActivity`.

This keeps bad source data visible while preventing malformed rows from entering the review queue.

---

## NormalizedActivity

`NormalizedActivity` is the standardized activity row reviewed by analysts.

Important fields:

- `tenant`
- `raw_record`
- `source_system`
- `activity_date`
- `period_start`
- `period_end`
- `facility_code`
- `cost_center`
- `activity_type`
- `scope_category`
- `original_quantity`
- `original_unit`
- `normalized_quantity`
- `normalized_unit`
- `amount`
- `currency`
- `supplier_or_vendor`
- `confidence_score`
- `warning_flags`
- `status`
- `edited_by`
- `approved_by`
- `approved_at`
- `locked_at`
- `created_at`
- `updated_at`

Primary statuses used in the analyst workflow:

- `pending`
- `needs_review`
- `locked`
- `rejected`

The model also contains a defensive `failed` status, but row-level parse failures are generally represented as failed `RawRecord`s rather than failed normalized activities.

### Why this model exists

The three source types have different shapes:

- SAP fuel/procurement rows
- utility electricity rows
- corporate travel rows

The analyst should not need to review three completely different tables.

`NormalizedActivity` gives all source types one common review model.

---

## AuditEvent

`AuditEvent` records lifecycle events.

Important fields:

- `tenant`
- `normalized_activity`
- `raw_record`
- `event_type`
- `before_payload`
- `after_payload`
- `actor`
- `message`
- `created_at`

Event types:

- `created`
- `edited`
- `approved`
- `rejected`
- `locked`
- `failed`

### Why this model exists

The assignment requires an audit trail.

The audit trail records:

- when a normalized activity was created
- when a raw row failed
- when an analyst edited a row
- when an analyst approved a row
- when a row was locked
- when a row was rejected

---

## Why RawRecord and NormalizedActivity are separate

This is the most important model choice.

`RawRecord` stores the original row exactly as received.

`NormalizedActivity` stores the cleaned, standardized representation used for analyst review.

This separation matters because:

- analysts may edit normalized fields
- raw source data should remain unchanged
- failed raw rows should not necessarily become normalized rows
- auditors need traceability from final reviewed data back to source data

---

## Multi-Tenancy

Every core model is tenant-scoped.

Tenant-owned models:

- `SourceSystem`
- `IngestionRun`
- `RawRecord`
- `NormalizedActivity`
- `AuditEvent`

This prevents data from different client companies from mixing.

The prototype uses one demo tenant, but the model supports multiple tenants.

---

## Source-of-Truth Tracking

Each normalized activity can be traced back to:

- tenant
- source system
- ingestion run
- uploaded file name
- source row number
- raw source payload
- audit events

This answers:

- which source produced this row?
- when did it come in?
- what did the original row look like?
- was it edited?
- who approved it?
- when was it locked?

---

## Scope Mapping

The prototype maps source data to emissions scopes as follows:

| Source | Activity | Scope |
|---|---|---|
| SAP | Fuel-like material rows | Scope 1 |
| SAP | Non-fuel purchased material rows | Scope 3 |
| Utility | Purchased electricity | Scope 2 |
| Travel | Flights, hotels, ground transport | Scope 3 |

---

## Unit Normalization

The system preserves both original and normalized values.

Examples:

| Original Unit | Normalized Unit |
|---|---|
| GAL | L |
| L | L |
| MWh | kWh |
| kWh | kWh |
| miles | km |
| km | km |

### Why both values are stored

The original quantity and unit preserve source truth.

The normalized quantity and unit allow consistent review and downstream calculation.

---

## Warning Flags

Rows can receive warning flags during ingestion.

Examples:

- `missing_cost_center`
- `unknown_plant_code`
- `unknown_unit`
- `large_quantity_outlier`
- `billing_period_crosses_month`
- `estimated_bill`
- `missing_meter_id`
- `distance_calculated_from_airport_codes`
- `missing_distance`
- `unsupported_expense_type`

Rows with warning flags are marked `needs_review`.

Rows without warning flags are marked `pending`.

---

## Approval and Audit Locking

Approval immediately locks the row in this prototype.

When a row is approved:

- `status` becomes `locked`
- `approved_by` is set
- `approved_at` is set
- `locked_at` is set
- audit events are created

Locked rows cannot be edited through the normal analyst workflow.

This is a deliberate simplification to make the audit boundary clear.

---

## Rejection

Rejected rows are terminal.

When a row is rejected:

- `status` becomes `rejected`
- an audit event is created
- approve/reject actions disappear in the UI
- backend blocks re-approval

This prevents accidental approval of a row that an analyst has already rejected.

---

## Review API

The prototype exposes API endpoints for the analyst workflow:

- list normalized activities
- filter by source, scope, status, facility, or warning flag
- inspect raw source payload
- edit normalized activity fields
- approve and lock rows
- reject rows
- inspect audit events
- view dashboard summary counts

Key endpoints:

```text
POST /api/ingest/
GET /api/activities/
GET /api/activities/:id/
PATCH /api/activities/:id/
POST /api/activities/:id/approve/
POST /api/activities/:id/reject/
GET /api/ingestion-runs/
GET /api/audit-events/
GET /api/dashboard-summary/
```

---

## Ingestion Pipeline

The backend implements CSV ingestion through:

```text
POST /api/ingest/
```

The endpoint accepts:

- `source_type`: `sap`, `utility`, or `travel`
- `file`: CSV upload

For each valid uploaded row, the system creates:

- `IngestionRun`
- `RawRecord`
- `NormalizedActivity`
- `AuditEvent`

Rows with warnings are marked `needs_review`.

Rows without warnings are marked `pending`.

The current prototype supports:

- SAP fuel/procurement-like CSV exports
- utility electricity CSV exports
- Concur/Navan-style travel CSV exports

---

## Upload-Level Failure vs Row-Level Failure

### Upload-Level Failure

Example:

A SAP CSV is uploaded as corporate travel.

Behavior:

- failed `IngestionRun` is created
- no `RawRecord` is created
- no `NormalizedActivity` is created
- error message is stored

### Row-Level Failure

Example:

A row has more columns than the CSV header.

Behavior:

- failed `RawRecord` is created
- failed `AuditEvent` is created
- no `NormalizedActivity` is created

---

## Why this model fits the assignment

The assignment specifically requires:

- multi-tenancy
- Scope 1/2/3 categorization
- source-of-truth tracking
- unit normalization
- audit trail

This model directly addresses each requirement while keeping the prototype small, understandable, and defensible.