# Architecture

AXL DB is designed for predictable performance with a compact core. This page explains the main components and how they work together.

## Components

- Storage engine: append-only segments with compact headers and checksums
- Indexes: vector-optimized structures designed for SIMD scanning and cache locality
- Query pipeline: batching, early termination, and score aggregation
- Durability: crash-safe metadata commits and background compaction

## Data layout

The storage layer uses cache-friendly layouts:

- Header block with schema and index descriptors
- Contiguous vector blocks aligned to SIMD register width
- Sparse attribute columns (optional) for scalar filtering

```text
+------------------+
| Header (schema)  |
+------------------+
| Vector block 0   | 128-d floats (aligned)
+------------------+
| Vector block 1   |
+------------------+
| ...              |
```

## Query pipeline

1. Parse request and resolve target index
2. Prepare SIMD kernel based on dimension and hardware flags
3. Scan batches with prefetch and tight inner loops
4. Maintain a small candidate heap for top-k
5. Return final results with optional metadata fetch

## Concurrency model

- Reader/writer coordination with fine-grained latches
- Batched writes; queries proceed concurrently
- Background compaction avoids long pauses

## Error handling

- Clear error codes from all public APIs
- Bounds checks at ingestion and query boundaries
