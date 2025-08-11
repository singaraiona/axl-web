# Ingestion Pipelines

Ingesting data efficiently is essential for predictable performance.

## Batching

- Accumulate vectors into batches to minimize overhead
- Align batches to cache-line and SIMD-friendly sizes

## File formats

- Binary float32 arrays for vectors
- Optional sidecar files for IDs and attributes

## Example

```bash
./axl ingest --index users --dim 128 --vectors users.f32 --ids users.ids --batch 4096
```

## Backpressure

- Use bounded queues between producers and the database
- Shed load or drop to a slower path under sustained pressure
