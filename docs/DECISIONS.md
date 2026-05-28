# Decisions

## Product scope

I am building a prototype ingestion and review system for ESG activity data.

The app focuses on:
- ingesting source files from SAP, utility electricity exports, and corporate travel exports
- preserving raw source rows
- normalizing activity data into one common model
- surfacing failed or suspicious rows for analyst review
- allowing analysts to approve/reject rows
- locking approved rows for audit traceability

I am deliberately not building a full carbon accounting engine. The prototype prepares normalized, reviewed activity data for downstream emissions calculation.

## Why this scope

The assignment emphasizes that the hard part is not carbon math, but ingesting messy client data from different systems, normalizing it, and allowing analysts to review it before audit signoff.

## Source ingestion choices

### SAP fuel and procurement

I chose file upload using a CSV export modeled after SAP procurement/material movement exports.

Why:
- Enterprise onboarding often starts with exports before direct integrations are available.
- SAP integrations require tenant access, credentials, and configuration that are unrealistic for this prototype.
- CSV lets the prototype focus on the actual assignment risks: field mapping, unit normalization, missing master data, validation, and review.

Subset handled:
- fuel purchase/activity rows
- plant code
- material code
- quantity
- unit
- posting date
- cost center
- vendor
- document number

Ignored:
- live OData integration
- BAPI integration
- IDoc parsing
- full SAP master data sync
- custom client-specific fields

Questions for PM:
- Are fuel records coming from purchase orders, goods movements, invoices, or a custom SAP report?
- Will the client provide plant and material master lookup tables?
- Which units and countries must be supported first?

### Utility electricity

I chose file upload using a CSV export from a utility portal or Green Button-style data export.

Why:
- Facilities teams commonly download utility usage reports from portals.
- Structured CSV is more reliable for a prototype than PDF bill extraction.
- Electricity bills often have billing periods that do not align with calendar months, which the model should support.

Subset handled:
- account number
- meter ID
- facility code
- billing start and end date
- usage
- usage unit
- demand kW
- tariff name
- cost
- estimated bill flag

Ignored:
- PDF bill OCR
- utility API authentication
- interval meter readings
- tariff calculation
- demand charge modeling

Questions for PM:
- Are we receiving bills, interval data, or monthly summary exports?
- Do analysts need to allocate billing periods into calendar months?
- Which grid region or location data is available?

### Corporate travel

I chose file upload using a CSV export modeled after Concur/Navan-style expense or travel reports.

Why:
- Travel platforms expose report and expense-entry data, but live OAuth/API setup is outside this prototype.
- CSV lets the app handle realistic travel issues like missing distance, airport codes, and different travel categories.

Subset handled:
- flights
- hotels
- ground transport
- transaction date
- amount
- currency
- vendor
- airport codes
- distance where available

Ignored:
- live Concur/Navan API integration
- OAuth
- multi-leg itinerary reconstruction
- rail
- meals
- per diem
- employee HR sync

Questions for PM:
- Should travel data come from expense reports or booked itineraries?
- Should emissions be based on spend, distance, or supplier-provided data?
- Are airport codes always available for flights?