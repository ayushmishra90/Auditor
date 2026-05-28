# Breathe ESG Tech Intern Assignment

A Django REST + React prototype for ingesting messy ESG activity data from multiple enterprise source systems, normalizing it into a common activity model, and giving analysts a review workflow before rows are locked for audit.

## Live App

Frontend: `https://auditor-dusky.vercel.app/`

Backend API: `https://auditor-dmbn.onrender.com/api/`


## Problem Framing

Breathe ESG’s assignment emphasizes that the hard part is not carbon calculation itself, but ingesting client data that arrives from different systems, in different shapes, with missing fields, inconsistent units, and unclear source-of-truth boundaries.

This prototype focuses on:

- ingesting three realistic source types
- preserving raw source rows
- normalizing rows into a common activity model
- surfacing suspicious or failed rows
- allowing analysts to approve or reject rows
- locking approved rows for audit traceability
- recording audit events for lifecycle actions

The app deliberately does not attempt to become a full emissions calculation engine. It prepares reviewed activity data for downstream emissions calculation.

## Tech Stack

### Backend

- Django
- Django REST Framework
- PostgreSQL for deployment
- SQLite for local development
- Gunicorn for production serving
- WhiteNoise for static files

### Frontend

- React
- Vite
- Axios
- React Router
- Tailwind CSS

### Deployment

- Backend: Render
- Database: Render PostgreSQL
- Frontend: Vercel

## Core Workflow

1. Analyst uploads a CSV for one of three source types:
   - SAP fuel/procurement
   - utility electricity
   - corporate travel
2. Backend validates source-specific CSV headers.
3. Backend creates an `IngestionRun`.
4. Each valid row becomes:
   - a `RawRecord`
   - a `NormalizedActivity`
   - an `AuditEvent`
5. Rows with warnings are marked `needs_review`.
6. Rows without warnings are marked `pending`.
7. Analyst reviews rows in the dashboard.
8. Analyst can view:
   - raw source row
   - normalized fields
   - warning flags
   - audit events
9. Analyst approves or rejects rows.
10. Approved rows are locked for audit.

## Main Features

### Upload

The upload page has three cards:

- SAP Fuel / Procurement
- Utility Electricity
- Corporate Travel

Each card validates that the uploaded CSV matches the expected source type.

A SAP file uploaded as a travel file is rejected and recorded as a failed ingestion run.

### Ingestion Runs

The ingestion run page shows:

- source system
- uploaded file name
- status
- total rows
- successful rows
- failed rows
- error message

Upload-level failures are recorded as failed ingestion runs without inserting partial row data.

### Review Dashboard

The review dashboard shows:

- source
- date or billing period
- facility
- activity type
- scope category
- warning flags
- review status
- view action

Detailed values are intentionally moved into the row detail modal to keep the table readable for analysts.

### Row Detail Modal

The detail modal shows:

- raw source row JSON
- normalized activity fields
- original quantity and unit
- normalized quantity and unit
- warning flags
- audit events
- approve/reject actions

Approved and rejected rows are terminal states. They cannot be edited or re-approved from the normal analyst workflow.

## Source Types

### 1. SAP Fuel and Procurement

Chosen ingestion mode: CSV upload modeled after SAP procurement/material export.

Handled fields include:

- company code
- plant code
- material code
- material description
- posting date
- quantity
- unit
- cost center
- vendor
- document number
- currency
- amount

Realistic issues represented:

- inconsistent date formats
- mixed units
- unknown plant codes
- missing cost centers
- suspiciously large quantities
- unknown material classification

### 2. Utility Electricity

Chosen ingestion mode: utility portal CSV / Green Button-style export.

Handled fields include:

- account number
- meter ID
- facility code
- bill start date
- bill end date
- usage
- usage unit
- demand kW
- tariff name
- total cost
- currency
- estimated flag

Realistic issues represented:

- billing periods crossing calendar months
- kWh and MWh normalization
- estimated bills
- missing meter IDs
- negative correction bills
- large outlier usage

### 3. Corporate Travel

Chosen ingestion mode: Concur/Navan-style travel expense CSV.

Handled categories:

- flights
- hotels
- taxi/rideshare or ground transport

Handled fields include:

- report ID
- employee ID
- expense type
- transaction date
- origin airport
- destination airport
- distance km
- hotel nights
- ground distance km
- amount
- currency
- vendor

Realistic issues represented:

- flight distance missing but airport codes available
- hotel rows using nights instead of distance
- taxi rows sometimes missing distance
- unsupported expense categories

## Scope Mapping

- SAP fuel activity → Scope 1
- Utility electricity → Scope 2
- Corporate travel → Scope 3
- SAP purchased goods/material rows → Scope 3

## Unit Normalization

The app preserves both original and normalized values.

Examples:

- gallons → litres
- MWh → kWh
- miles → km

Original source values remain visible for audit traceability.

## Validation Behavior

The app distinguishes between two failure types:

### Upload-level failure

Example: uploading a SAP CSV into the travel upload card.

Behavior:

- creates failed `IngestionRun`
- does not create `RawRecord`
- does not create `NormalizedActivity`
- stores an error message

### Row-level failure

Example: row has extra columns or malformed structure.

Behavior:

- preserves failed `RawRecord`
- creates failed `AuditEvent`
- does not create `NormalizedActivity`

This keeps the ingestion pipeline auditable while avoiding bad normalized rows.

## Local Setup

### Backend

```bash
cd backend
python -m venv venv
venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver