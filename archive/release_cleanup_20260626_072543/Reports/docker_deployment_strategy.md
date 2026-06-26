# Phase 13A - Docker Deployment Strategy

This document details the containerization and micro-orchestration design for deploying the BBC-AOS sidecar API server.

---

## 1. Multi-Stage Dockerfile Layout

The deployment uses a multi-stage Dockerfile to minimize image sizes:

```dockerfile
# Stage 1: Build dependencies
FROM python:3.11-slim AS builder

WORKDIR /app
COPY pyproject.toml README.md ./
COPY bbc_aos/ ./bbc_aos/

RUN pip install --no-cache-dir --user .

# Stage 2: Production runtime
FROM python:3.11-slim AS runner

WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY bbc_aos/ ./bbc_aos/

ENV PATH=/root/.local/bin:$PATH
EXPOSE 8080

ENTRYPOINT ["bbc", "serve", "--port", "8080", "--host", "0.0.0.0"]
```

---

## 2. Docker Compose Configuration

For local development workflows:

```yaml
version: '3.8'

services:
  bbc-sidecar:
    build: .
    ports:
      - "8080:8080"
    volumes:
      - ./:/workspace
    environment:
      - BBC_WORKSPACE_ROOT=/workspace
      - BBC_ENV=production
    restart: always
```
