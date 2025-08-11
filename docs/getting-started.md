# Getting Started

Welcome to AXL DB. This guide helps you install, build, and run your first queries.

## Prerequisites

- A modern C toolchain (GCC or Clang)
- SIMD-capable CPU (AVX2 on x86_64, NEON on ARM is recommended)
- Make (optional, but convenient)

## Build from source

```bash
git clone https://github.com/hetoku/axl-db
cd axl-db
make            # or: cc -O3 -march=native -o axl examples/main.c src/*.c
./axl --help
```

## Minimal example in C

```c
#include "axl.h"

int main(void) {
  axl_db *db = axl_open("data.axl", AXL_CREATE_IF_MISSING);
  axl_index_opts opts = axl_index_opts_default();

  float vec[128] = {0};
  for (int i = 0; i < 128; i++) vec[i] = (float)i;

  axl_add_vector(db, "users", (const float*)vec, 128, 42, &opts);

  float query[128] = {0};
  int results[10] = {0};
  axl_search(db, "users", (const float*)query, 128, 10, results);

  axl_close(db);
  return 0;
}
```

## CLI basics

```bash
./axl create --index users --dim 128
./axl add --index users --id 42 --vec-file sample.vec
./axl search --index users --k 10 --vec-file query.vec
```

## Next steps

- Read the [Architecture](./architecture.html) overview
- Browse the [C API](./api.html)
- See [Performance](./performance.html) tuning tips
