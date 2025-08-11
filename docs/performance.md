# Performance Tuning

This guide collects best practices for achieving consistent low latency and high throughput.

## Build flags

```bash
cc -O3 -march=native -ffast-math -fno-exceptions -o axl examples/main.c src/*.c
```

- Enable SIMD and unrolling where safe
- Consider profile-guided optimization (PGO) for hot paths

## Hardware notes

- Prefer CPUs with wide SIMD (AVX2/AVX-512) and high L3 bandwidth
- Bind processes to isolated cores for tail-latency sensitive workloads

## Index sizing

- Choose dimensions to match SIMD lanes (multiples of 8/16 floats help)
- Batch queries to keep pipelines full

## Example metrics

| Metric           | AXL DB         | Generic DB     |
|------------------|----------------|----------------|
| Queries/sec      | ~3.6M          | ~2.1M          |
| P99 latency      | ~1.8 ms        | ~4.2 ms        |
| Binary footprint | ~480 KB        | 5–20 MB        |

## Troubleshooting

- Check CPU flags (`cat /proc/cpuinfo`) to confirm SIMD availability
- Warm up the process to stabilize instruction cache
- Pin I/O and compute threads separately under heavy load
