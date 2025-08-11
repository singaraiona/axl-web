# AXL DB Documentation

Welcome to the AXL DB docs. This site is generated from Markdown files in the `docs/` folder and rendered to match the main website theme.

This page serves as a hub with quick links and longer paragraphs to test wrapping, lists, and tables.

## Quick links

- [Getting Started](./getting-started.html)
- [Architecture](./architecture.html)
- [C API Overview](./api.html)
- [Performance Tuning](./performance.html)
- [FAQ](./faq.html)

## Overview

AXL DB is a compact vector database engine focused on predictable latency and high throughput on commodity hardware. It is written in plain C with zero runtime dependencies, aiming for small binaries that are easy to audit and embed. This documentation explores the principles behind the engine, practical guidance for building and deploying it, and reference material for the public API.

The project optimizes for the realities of real workloads: cache-aware data layouts, SIMD-first kernels, and careful control over memory and I/O patterns. From embedded devices to high-density servers, AXL DB aims to deliver consistent performance.

## What to expect in these docs

1. Conceptual explanations of the storage engine and indexing structures
2. Practical setup guides for building from source and running sample programs
3. Performance tuning advice for different hardware profiles
4. Reference for public APIs with examples

## Sample table

| Topic          | Summary                                     |
|----------------|---------------------------------------------|
| Getting Started| Build and run your first queries             |
| Architecture   | Components, data layout, and query pipeline |
| C API          | Core types and functions                     |
| Performance    | Flags, sizing, and troubleshooting           |

## Code sample

```c
#include "axl.h"

int main(void) {
  axl_db *db = axl_open("data.axl", AXL_CREATE_IF_MISSING);
  axl_index_opts opts = axl_index_opts_default();
  float q[128] = {0};
  int results[10] = {0};
  axl_search(db, "users", (const float*)q, 128, 10, results);
  axl_close(db);
  return 0;
}
```
