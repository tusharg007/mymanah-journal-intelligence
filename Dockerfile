FROM node:22-bookworm-slim AS web
WORKDIR /web
COPY web/package*.json ./
RUN npm ci --ignore-scripts
COPY web/ ./
RUN npm run build

FROM python:3.11-slim-bookworm
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 HF_HUB_DISABLE_TELEMETRY=1 ANONYMIZED_TELEMETRY=False
WORKDIR /app
COPY requirements.linux.lock ./
RUN pip install --no-cache-dir --require-hashes -r requirements.linux.lock
COPY pyproject.toml model_manifest.json ./
COPY mymanah/ ./mymanah/
COPY scripts/ ./scripts/
RUN pip install --no-deps . && useradd --create-home --uid 10001 app && mkdir -p /app/data /app/models && chown -R app:app /app
COPY --from=web /web/dist ./web/dist
USER app
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=180s CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health/ready',timeout=3)"
CMD ["python", "scripts/start.py"]
