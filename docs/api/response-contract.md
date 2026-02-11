# Prediction API Response Contract

## Endpoint
`POST /predict`

## Top-level response fields
- `risk_level`: one of `LOW`, `MEDIUM`, `HIGH`
- `confidence`: float in `[0, 1]`
- `feature_importance`: key-value map

## Batch CSV additions
- `total_records`: number of parsed rows
- `predictions`: per-row predictions list
- `metadata.summary_strategy`: currently `highest_risk`

## Validation expectations
- reject empty CSV uploads
- reject malformed CSV payloads
- return clear HTTP detail messages
