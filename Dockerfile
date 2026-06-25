# Stage 1: Build dependencies
FROM python:3.11-slim AS builder

WORKDIR /app
COPY pyproject.toml README.md ./
COPY src/bbc_aos/ ./src/bbc_aos/

RUN pip install --no-cache-dir --user .

# Stage 2: Production runtime
FROM python:3.11-slim AS runner

WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY src/bbc_aos/ ./src/bbc_aos/

ENV PATH=/root/.local/bin:$PATH
EXPOSE 8080

ENTRYPOINT ["bbc", "serve", "--port", "8080", "--host", "0.0.0.0"]
