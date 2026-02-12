# `/predict` Usage Examples

## JSON request
```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "mileage": 64000,
    "engine_hours": 1200,
    "fault_codes": "P0171,P0420",
    "service_history": "average",
    "usage_patterns": "mixed city driving"
  }'
```

## CSV request
```bash
curl -X POST http://localhost:8000/predict \
  -F "file=@docs/data/vehicle_input_template.csv"
```

## Frontend fetch shape
```ts
const response = await fetch(`${API_BASE_URL}/predict`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify(payload),
});
```
