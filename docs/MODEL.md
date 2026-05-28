# Data Model

## Design goals

The model is designed to support:

- multi-tenancy
- source-of-truth tracking
- unit normalization
- Scope 1, Scope 2, and Scope 3 categorization
- analyst review
- edit history
- audit locking

## Core model

```text
Tenant
  -> SourceSystem
  -> IngestionRun
  -> RawRecord
  -> NormalizedActivity
  -> AuditEvent

  ## Implemented Django models

The backend implements the following core models:

- Tenant
- SourceSystem
- IngestionRun
- RawRecord
- NormalizedActivity
- AuditEvent

The most important design choice is separating RawRecord from NormalizedActivity.

RawRecord stores the original source row exactly as received. NormalizedActivity stores the standardized representation used for analyst review.

This gives the system both:
- source-of-truth traceability
- analyst-editable normalized data

Approved rows are locked by setting status to `locked` and storing `approved_at`, `approved_by`, and `locked_at`.

Every important lifecycle action is represented as an AuditEvent.

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

Approval immediately locks the row in this prototype. This is a deliberate simplification to make the audit boundary clear.