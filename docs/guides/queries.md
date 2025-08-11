# Query Patterns

This page explores common query patterns and how to optimize them.

## KNN search (top-k)

- Choose k based on application tolerance for recall/latency
- Use candidate heaps sized to k and batch across queries where possible

## Hybrid filters

- Combine vector similarity with scalar attributes
- Apply fast pre-filters to reduce the candidate set before scoring

## Streaming queries

- Maintain a small hot set of vectors in memory
- Periodically refresh with background merges to disk

## Example CLI

```bash
./axl search --index users --k 10 --vec-file query.vec --filter "country=US AND active=1"
```
