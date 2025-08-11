# FAQ

## Why plain C?

Portability, auditability, and minimal runtime overhead. It embeds cleanly into diverse systems.

## Does it require libc at runtime?

No. The core has no runtime dependencies; static linking is supported.

## How big is the binary?

Typical builds are a few hundred kilobytes with SIMD enabled and stripped symbols.

## Is there a query language?

The focus is on vector similarity and simple filters. Bindings or higher-level query layers can be built on top.

## How do I report an issue?

Open an issue on GitHub and include your CPU flags, compiler versions, and a minimal repro.
