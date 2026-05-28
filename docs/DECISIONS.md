# DECISIONS.md

## Product Scope

I built a prototype ingestion and analyst review system for ESG activity data.

The prototype focuses on:

- ingesting source files
- validating source-specific schemas
- preserving raw source rows
- normalizing activity data into a common model
- surfacing warnings and failed rows
- allowing analysts to approve or reject rows
- locking approved rows for audit traceability

I deliberately did not build a full carbon accounting engine.

---

## Why this scope

The assignment says the hard part is not computing carbon, but ingesting data that comes from different client systems in different shapes, with different gaps.

I therefore prioritized:

- realistic source shapes
- clear data model
- source traceability
- review workflow
- audit locking
- explicit tradeoffs

---

## Ingestion Mechanism Decision

I chose CSV upload for all three source types.

### Why

- file exports are realistic during early enterprise onboarding
- live SAP, utility, and travel platform integrations require credentials and client configuration
- CSV allows the prototype to focus on mapping, validation, normalization, and review
- the assignment does not provide mock APIs or sample files

I did not want to fake API integrations without real tenants or credentials.

---

## SAP Decision

### Chosen mode

CSV upload modeled after SAP procurement/material export.

### Why not live SAP API?

SAP APIs and OData services exist, but real integration requires:

- tenant credentials
- client-specific configuration
- authorization scopes
- source module decisions
- mapping to client master data

For a prototype, direct SAP integration would distract from the assignment’s core concern: messy source data normalization.

### SAP subset handled

The prototype handles rows with:

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

### SAP messiness represented

The sample data includes:

- inconsistent date formats
- mixed units
- missing cost center
- unknown plant code
- suspiciously large quantity
- unknown material/unit
- fuel vs procurement classification

### SAP scope mapping

- fuel-like material rows become Scope 1
- non-fuel purchased material rows become Scope 3

### SAP ignored

I ignored:

- IDoc parsing
- BAPI integration
- live OData integration
- SAP master data sync
- German column header translation
- custom SAP fields
- multi-company chart of accounts mapping

### Questions I would ask the PM

- Are fuel records coming from purchase orders, goods movements, invoices, or a custom SAP report?
- Will the client provide plant master data?
- Will the client provide material master data?
- Which units and countries should be supported first?
- Are German/localized column headers expected in the first client upload?

---

## Utility Electricity Decision

### Chosen mode

CSV upload modeled after a utility portal / Green Button-style export.

### Why not PDF bill OCR?

PDF bill OCR is noisy and time-consuming.

It would introduce:

- layout variability
- OCR errors
- utility-specific bill templates
- inconsistent extraction quality

For this prototype, a structured utility portal CSV better demonstrates ingestion, validation, period handling, and review.

### Why not utility API?

Utility APIs vary by provider and require account authorization.

For onboarding, facilities teams often begin with portal exports.

### Utility subset handled

The prototype handles:

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

### Utility messiness represented

The sample data includes:

- kWh and MWh
- billing periods that cross calendar months
- missing meter ID
- estimated bills
- negative correction bill
- very large usage outlier
- unknown facility code

### Utility scope mapping

Purchased electricity becomes Scope 2.

### Utility ignored

I ignored:

- PDF extraction
- interval meter readings
- live utility APIs
- tariff calculation
- demand charge allocation
- calendar-month proration
- grid emissions factor mapping

### Questions I would ask the PM

- Are facilities sending bills, interval data, or monthly summaries?
- Should billing periods be prorated into calendar months?
- Do we have meter-to-facility lookup tables?
- Which countries and electricity markets are in scope?
- Are estimated bills acceptable for audit, or should they always require review?

---

## Corporate Travel Decision

### Chosen mode

CSV upload modeled after Concur/Navan-style expense report exports.

### Why not live Concur/Navan API?

Travel APIs require OAuth, tenant access, and platform-specific configuration.

For this prototype, a CSV export is sufficient to model:

- travel categories
- transaction dates
- airport codes
- missing distances
- amount and currency
- vendor information

### Travel subset handled

The prototype handles:

- flights
- hotels
- taxi/rideshare/ground transport

Fields handled:

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

### Travel messiness represented

The sample data includes:

- flight with missing distance but airport codes available
- flight with explicit distance
- hotel with nights
- taxi with distance
- taxi missing distance
- unsupported meal expense

### Travel scope mapping

Business travel rows become Scope 3.

### Travel ignored

I ignored:

- live Concur API
- live Navan API
- OAuth
- multi-leg itinerary reconstruction
- rail
- meals
- per diem
- employee HR sync
- duplicate expense report detection

### Questions I would ask the PM

- Should travel data come from booked itineraries or expense reports?
- Are airport codes always available for flights?
- Should missing flight distances be calculated from airport pairs?
- Should hotels be calculated by nights, spend, location, or supplier data?
- Are personal expenses included in the export?
- Should meals be ignored or mapped to another Scope 3 category?

---

## CSV Validation Decision

The app validates source-specific CSV headers before ingestion.

Example:

If a SAP CSV is uploaded as a travel CSV, the upload is rejected.

Behavior:

- failed `IngestionRun` is created
- no raw rows are inserted
- no normalized activities are inserted
- error message is shown in the UI

### Why

This prevents bad data from entering the review workflow while still preserving evidence that an upload attempt occurred.

---

## Row-Level Malformation Decision

If a CSV row has more columns than the header, the row is treated as malformed.

Behavior:

- failed `RawRecord` is created
- failed `AuditEvent` is created
- no `NormalizedActivity` is created

### Why

This keeps the ingestion process auditable but prevents malformed rows from entering analyst review.

---

## Atomicity Decision

The main ingestion function is atomic.

Valid uploads create ingestion run, raw records, normalized activities, and audit events together.

Invalid upload-level failures are recorded separately as failed ingestion runs.

### Why

This avoids partial normalized data while still making failed upload attempts visible to analysts and reviewers.

---

## UI Decision

The review dashboard intentionally shows only the fields analysts need to scan:

- source
- date or period
- facility
- activity
- scope
- warnings
- status
- view action

Original and normalized quantities are shown inside the detail modal.

### Why

Showing too many columns made the table hard to use.

The dashboard should support quick triage, while the modal supports detailed review.

---

## Terminal Status Decision

`locked` and `rejected` are terminal states.

Locked rows cannot be edited because they are approved for audit.

Rejected rows cannot be approved later through the normal analyst workflow.

### Why

This prevents accidental changes to final review decisions.