# Zebra Label Gateway web app.
# PyMuPDF and Pillow ship manylinux wheels, so no system build tools are needed.
FROM python:3.12-slim

# Faster, quieter Python in containers.
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    ZLG_CONFIG_DIR=/app/config \
    ZLG_DATA_DIR=/app/data \
    ZLG_PRINTER_PORT=9100

WORKDIR /app

# Install dependencies first (better layer caching) then the package itself.
COPY pyproject.toml requirements.txt ./
COPY src ./src
COPY config ./config
RUN pip install --upgrade pip && pip install ".[web]"

# Run as a non-root user; give it a writable data dir for history + trained profiles.
RUN useradd --create-home --uid 10001 appuser \
    && mkdir -p /app/data \
    && chown -R appuser /app/data
USER appuser

# Persist saved-label history and trained profiles across container restarts.
VOLUME ["/app/data"]

EXPOSE 8000

# The printer host is provided at runtime, e.g. -e ZLG_PRINTER_HOST=10.10.100.107
ENV ZLG_PRINTER_HOST=""

HEALTHCHECK --interval=30s --timeout=4s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/api/profiles',timeout=3).status==200 else 1)"

CMD ["uvicorn", "zebra_label_gateway.webapp.server:app", "--host", "0.0.0.0", "--port", "8000"]
