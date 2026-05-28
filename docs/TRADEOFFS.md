# TRADEOFFS.md

## 1. No Live API Integrations

I did not implement live SAP, utility, Concur, or Navan API integrations.

### Why

Real API integrations require:

- tenant credentials
- authentication flows
- client-specific configuration
- permissions
- data mapping workshops
- error handling for external systems

For a prototype, implementing fake API clients would not prove much.

Instead, I used realistic CSV exports and focused on:

- source-specific schema validation
- raw data preservation
- normalization
- warning flags
- analyst review
- audit trail

### What would be needed in production

A production version would need:

- SAP OData/IDoc/BAPI integration depending on client environment
- utility API or Green Button integration where available
- Concur/Navan OAuth app setup
- retry logic
- connector health monitoring
- background jobs
- credential storage
- integration-specific mapping configuration

---

## 2. No PDF Utility Bill OCR

I did not implement PDF bill extraction.

### Why

PDF extraction is a separate hard problem.

It would require:

- OCR
- template detection
- layout parsing
- confidence scoring
- manual correction UI
- per-utility parser maintenance

The assignment emphasizes messy data ingestion and analyst review.

A utility portal CSV better demonstrates this within the prototype timebox.

### What would be needed in production

A production PDF ingestion system would need:

- OCR pipeline
- document classification
- bill template extraction
- human-in-the-loop correction
- original document storage
- extraction confidence scores
- page-level audit references

---

## 3. No Full Emissions Factor Engine

I did not build a full emissions calculation engine.

### Why

The assignment says the hard part is not computing carbon; it is ingesting and normalizing messy client data.

This prototype prepares clean, reviewed activity data that could later be passed into a calculation engine.

Adding a shallow emissions factor system would distract from the data model and review workflow.

### What would be needed in production

A production emissions engine would need:

- emission factor datasets
- factor versioning
- geography-specific factors
- time-specific factors
- unit compatibility checks
- calculation methodology tracking
- audit references for each factor used

---

## Summary

I deliberately left these three areas out because they would expand the prototype in the wrong direction.

The prototype instead focuses on the assignment’s core evaluation areas:

- realistic ingestion choices
- strong data model
- source traceability
- unit normalization
- analyst review
- audit trail
- explicit tradeoffs