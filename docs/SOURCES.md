# Sources

## SAP fuel and procurement

### Researched format

I used SAP purchase order/procurement exports as the reference shape.

SAP documents purchase order data export as CSV files such as:
- PurchaseOrderExport.csv
- PurchaseOrderDetailExport.csv
- PurchaseOrderSplitExport.csv

SAP also provides Purchase Order OData APIs, but direct API integration requires tenant access, credentials, and client-specific configuration.

### What I modeled

The sample SAP file includes:
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

### Realistic issues represented

- inconsistent date formats
- plant codes that require lookup
- material codes that require classification
- mixed units such as L, GAL, KG, BAG
- missing cost center
- suspiciously large quantity

### What would break in production

- custom SAP fields
- missing material master data
- unknown units
- localized column headers
- multiple SAP modules producing similar-looking rows

## Utility electricity

### Researched format

I used utility portal / Green Button-style exports as the reference shape.

Green Button allows customers to download utility usage data from utility websites. Some implementations provide billing data in CSV or XML format.

### What I modeled

The sample utility file includes:
- account number
- meter ID
- facility code
- bill start
- bill end
- usage
- usage unit
- demand kW
- tariff name
- total cost
- currency
- estimated flag

### Realistic issues represented

- billing periods that do not align with calendar months
- kWh and MWh normalization
- estimated bills
- missing meter ID
- negative correction bill
- large outlier usage

### What would break in production

- PDF-only bills
- interval meter data
- utility-specific export formats
- tariff-level calculations
- meter-to-facility mapping gaps

## Corporate travel

### Researched format

I used SAP Concur-style expense report data as the reference shape.

Concur expense data includes transaction date, transaction amount, currency, payment type, and expense entries. The Quick Expense API captures date, amount, and expense type.

### What I modeled

The sample travel file includes:
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

### Realistic issues represented

- flights with missing distance but airport codes available
- hotels with nights but no city
- taxis with amount but no distance
- unsupported expense categories

### What would break in production

- multi-leg itineraries
- missing airport codes
- spend-based-only travel records
- duplicate expense reports
- personal vs business expense classification