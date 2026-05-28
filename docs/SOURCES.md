# SOURCES.md

## Purpose

This document explains what real-world source formats I researched, what I learned, why the sample files look the way they do, and what would break in a real deployment.

The assignment did not provide sample files. I therefore researched realistic source formats and created sample data that reflects common enterprise ingestion issues.

---

# 1. SAP Fuel and Procurement

## Researched format

I used SAP procurement / purchase-order style exports as the reference shape.

SAP procurement exports are often available as flat files or CSV exports. SAP systems can also expose procurement data through OData APIs or other integration mechanisms, but direct integration depends heavily on client environment, credentials, and configuration.

For this prototype, I chose a CSV upload modeled after SAP procurement/material export.

---

## What I learned

Important SAP-style concepts include:

- company code
- plant code
- material code
- material description
- quantity
- unit
- posting date
- vendor
- purchase document number
- currency
- amount

The hard part is not simply reading the file. The hard part is interpreting the row:

- plant codes require lookup tables
- material codes require classification
- units can vary
- date formats can vary
- localized column headers may exist
- cost centers may be missing
- fuel and procurement data may come from different SAP modules

---

## Sample data file

```text
sample_data/sap_fuel_procurement.csv
```

Columns:

```text
company_code,
plant_code,
material_code,
material_description,
posting_date,
quantity,
unit,
cost_center,
vendor,
document_number,
currency,
amount
```

---

## Why the sample data looks this way

The sample contains:

- diesel rows
- petrol rows
- LPG row
- unknown material row
- German-style date
- slash-formatted date
- missing cost center
- unknown plant code
- very large outlier quantity
- unknown unit

These rows were chosen to demonstrate:

- unit normalization
- warning flags
- plant-code uncertainty
- fuel vs procurement classification
- analyst review needs

---

## Current prototype handling

The prototype maps:

- fuel-like rows to Scope 1
- non-fuel procurement-like rows to Scope 3

It normalizes:

- gallons to litres
- litres to litres

It flags:

- missing cost center
- unknown plant code
- unknown unit
- large quantity outlier
- invalid date
- uncertain material classification

---

## What would break in real deployment

A real client SAP deployment could break this prototype if:

- column names are localized
- custom SAP fields are used
- material master data is missing
- plant master data is missing
- fuel is recorded through goods movements instead of purchase exports
- units are not in the small supported set
- multiple SAP modules produce similar rows
- procurement rows need invoice matching
- SAP data arrives through IDoc or OData instead of flat export

---

## What I would add next

- configurable column mapping
- plant lookup table upload
- material classification table
- localized header mapping
- support for IDoc/OData ingestion
- richer procurement category mapping

---

# 2. Utility Electricity

## Researched format

I used utility portal / Green Button-style exports as the reference shape.

Facilities teams often download electricity usage reports from utility portals. Green Button-style exports and utility portal data commonly include billing or usage information in structured formats such as CSV or XML.

For this prototype, I chose a CSV export instead of PDF bill extraction or live utility API integration.

---

## What I learned

Utility data is period-based.

Important concepts include:

- account number
- meter ID
- facility mapping
- billing start date
- billing end date
- usage
- usage unit
- demand
- tariff
- total cost
- estimated bill flag

Billing periods often do not align with calendar months. Meter readings and billing summaries are related but not identical.

---

## Sample data file

```text
sample_data/utility_electricity.csv
```

Columns:

```text
account_number,
meter_id,
facility_code,
bill_start,
bill_end,
usage,
usage_unit,
demand_kw,
tariff_name,
total_cost,
currency,
estimated
```

---

## Why the sample data looks this way

The sample contains:

- kWh row
- MWh row
- billing period crossing month boundary
- missing meter ID
- estimated bill
- negative correction bill
- large usage outlier
- unknown facility code

These rows were chosen to demonstrate:

- kWh/MWh normalization
- billing-period review
- estimated data review
- meter mapping problems
- suspicious quantity detection

---

## Current prototype handling

The prototype maps utility electricity to Scope 2.

It normalizes:

- MWh to kWh
- kWh to kWh

It flags:

- missing meter ID
- unknown facility code
- billing period crossing month
- estimated bill
- negative quantity
- large quantity outlier
- invalid billing period

---

## What would break in real deployment

A real utility deployment could break this prototype if:

- the client only has PDF bills
- the export contains interval readings instead of monthly summaries
- the utility uses XML Green Button files
- meter IDs do not map cleanly to facilities
- tariffs need detailed calculation
- bill corrections span multiple periods
- currency and tax treatment varies by country
- electricity factor mapping depends on grid region

---

## What I would add next

- Green Button XML parser
- PDF bill extraction pipeline
- meter-to-facility lookup table
- billing-period proration
- interval data support
- grid-region mapping
- estimated bill policy configuration

---

# 3. Corporate Travel

## Researched format

I used SAP Concur/Navan-style expense report data as the reference shape.

Travel and expense systems commonly expose report-level and entry-level data. Expense entries often include transaction date, amount, currency, vendor, and expense type.

For travel emissions, the important issue is that different travel categories need different activity data. Flights, hotels, and ground transport cannot be normalized in exactly the same way.

---

## What I learned

Travel emissions depend heavily on category.

Flights may need:

- origin airport
- destination airport
- distance
- cabin class, if available

Hotels may need:

- number of nights
- city or country
- hotel vendor

Ground transport may need:

- distance
- vehicle type
- spend
- vendor

Distances are not always available. Sometimes only airport codes are present.

Expense reports may also contain categories that are not useful for this prototype, such as meals.

---

## Sample data file

```text
sample_data/concur_travel.csv
```

Columns:

```text
report_id,
employee_id,
expense_type,
transaction_date,
origin_airport,
destination_airport,
distance_km,
hotel_nights,
ground_distance_km,
amount,
currency,
vendor
```

---

## Why the sample data looks this way

The sample contains:

- flight missing distance but with airport codes
- flight with explicit distance
- hotel with nights
- taxi with distance
- taxi missing distance
- unsupported meal expense

These rows were chosen to demonstrate:

- category-specific parsing
- airport-code distance fallback
- missing distance warnings
- unsupported expense category handling
- Scope 3 mapping

---

## Current prototype handling

The prototype maps all handled business travel rows to Scope 3.

It handles:

- airfare
- hotel
- taxi/rideshare/ground transport

It flags:

- distance calculated from airport codes
- missing flight distance
- missing hotel nights
- missing ground distance
- unsupported expense type
- invalid date

---

## What would break in real deployment

A real travel deployment could break this prototype if:

- flight itineraries are multi-leg
- airport codes are missing
- travel data comes from bookings instead of expense reports
- expenses are duplicated
- personal and business expenses are mixed
- hotel location is needed but not present
- distance is only available via external lookup
- supplier-provided emissions are present and should override calculations

---

## What I would add next

- airport distance lookup service
- multi-leg itinerary model
- rail support
- booking-vs-expense reconciliation
- duplicate expense detection
- hotel location mapping
- spend-based fallback method
- Concur/Navan API connector

---

# Source Summary

| Source | Researched shape | Prototype mode |
|---|---|---|
| SAP | Procurement / purchase-order style export, OData patterns | CSV upload |
| Utility | Utility portal / Green Button-style billing export | CSV upload |
| Travel | Concur/Navan-style expense report data | CSV upload |

---

## Why file upload is acceptable for this prototype

File upload is realistic for first enterprise onboarding because clients often provide exports before integration credentials are ready.

It also makes the prototype focus on the assignment’s core evaluation areas:

- data model quality
- decision quality
- realistic source handling
- analyst UX
- tradeoffs