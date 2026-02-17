# Model Loading and Caching

- the sklearn pipeline is loaded via `PredictionService`
- service instance is memoized using `lru_cache` in API wiring
- model artifact path defaults to `model/vehicle_maintenance_pipeline.pkl`
- prediction requests reuse the in-memory pipeline for low latency

Operational expectation:
- cold start performs one model load
- steady-state requests should avoid per-request disk reads
