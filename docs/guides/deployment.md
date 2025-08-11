# Deployment

AXL DB can be deployed in embedded scenarios, as a local service, or packaged into containers. This guide outlines options and tradeoffs.

## Embedded library

- Link statically into your process
- Control lifecycle and I/O directly from your code

## Local service

- Run as a background process reachable over a local IPC or HTTP interface
- Good for multi-language environments

## Containers

```bash
docker build -t axl-db:latest .
docker run --rm -p 8080:8080 axl-db:latest
```

## Configuration

| Setting      | Description                         |
|--------------|-------------------------------------|
| index_dir    | Path to on-disk indexes             |
| wal_dir      | Path to write-ahead log             |
| compaction   | Background compaction policy        |
| threads      | Worker thread count                 |

## Rolling updates

- Use blue/green or canary strategies
- Keep cold-start times minimal with small binaries
