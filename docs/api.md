# C API Overview

AXL DB ships a small, focused C API. Below are the core calls with typical usage.

## Handles and options

```c
#include "axl.h"

typedef struct axl_db axl_db;

typedef enum {
  AXL_OK = 0,
  AXL_ERR_INVALID_ARG = -1,
  AXL_ERR_IO = -2,
  AXL_ERR_NOT_FOUND = -3
} axl_status;

typedef struct {
  int reserved;
} axl_index_opts;

axl_index_opts axl_index_opts_default(void);
```

## Open / close

```c
axl_db* axl_open(const char* path, int flags);
void axl_close(axl_db* db);
```

- `AXL_CREATE_IF_MISSING`: create the database file if necessary

## Ingest vectors

```c
axl_status axl_add_vector(
  axl_db* db,
  const char* index_name,
  const float* vector,
  int dim,
  int id,
  const axl_index_opts* opts
);
```

## Search

```c
axl_status axl_search(
  axl_db* db,
  const char* index_name,
  const float* query,
  int dim,
  int k,
  int* out_ids
);
```

## Errors

- Returns `AXL_OK` on success, negative codes on error
- Use defensive checks for dimensions and null pointers

## Versioning

- The ABI is stable within a minor version line
- Functions may gain new optional parameters guarded by flags
