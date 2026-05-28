# Tradeoffs

## 1. File upload instead of live integrations

I used CSV upload instead of live SAP, utility, or travel API integrations.

Why:
- API access requires tenant credentials and configuration.
- File exports are realistic during early enterprise onboarding.
- This keeps the prototype focused on normalization, review, and auditability.

## 2. No PDF utility bill OCR

I did not implement PDF bill extraction.

Why:
- OCR introduces high noise and edge cases.
- Utility portal CSV / Green Button-style exports are more structured.
- The assignment is better served by showing a strong ingestion and review model.

## 3. No full emissions calculation engine

I did not implement a full emissions factor engine.

Why:
- The assignment says the hard part is messy ingestion, not carbon math.
- This prototype prepares normalized, approved activity data for downstream emissions calculations.
- Adding incomplete factor logic would distract from source traceability and review quality.