# Request Normalization Rules

## Manual input aliases
- `mileage` can map to odometer-derived defaults
- `fault_codes` accepts comma, pipe, or semicolon separators
- `service_history` accepts qualitative values: good, average, poor

## CSV normalization
- trim leading/trailing whitespace from headers and values
- convert empty strings to null-like values before model row mapping
- preserve row ordering for predictable batch output
