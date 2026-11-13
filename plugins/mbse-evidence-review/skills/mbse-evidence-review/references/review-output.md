# Human-readable review result contract

## Scope and evidence ledger

System, lifecycle stage, configuration baseline and review scope. List every inspected source with its locator and version. Distinguish supplied-but-uninspected material and missing material.

## Traceability matrix

| Requirement / claim ID | Source + revision | Architecture allocation | Verification method | Result record + baseline | Assessment |
|---|---|---|---|---|---|
| User-provided ID, or provisional review ID | Exact inspected locator or not provided | ID and reciprocal link, or gap | Tested / planned / absent | Actual supplied evidence or not provided | Observed / asserted / missing / contradictory / N/A with rationale |

## Findings

For each finding provide: stable review ID; type (`contradiction`, `evidence_gap`, `tradeoff`, `not_assessable`); severity and rationale; affected IDs; evidence locator; bounded mechanism; corrective action; closure evidence; owner if assigned; unresolved assumptions.

## Non-claims

Never use "compliant", "certified", "approved", "verified", or "safe" as an overall result merely because this review ran or links are present. Source content authenticity, technical adequacy, lifecycle process compliance, authority acceptance, and operational suitability require separate evidence and review.
