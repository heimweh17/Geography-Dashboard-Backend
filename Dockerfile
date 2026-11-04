FROM python:3.11-slim

# Refresh the system certificate store for outbound HTTPS.
RUN apt-get update \
    && apt-get install --no-install-recommends -y ca-certificates \
    && update-ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000 \
    APP_MODULE=app.main:app

RUN addgroup --system app && adduser --system --ingroup app app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY alembic.ini ./
COPY alembic ./alembic
COPY app ./app
RUN chown -R app:app /app

USER app
EXPOSE 8000

# APP_MODULE can be overridden with app.ai_main:app for the AI service.
CMD ["sh", "-c", "uvicorn ${APP_MODULE} --host 0.0.0.0 --port ${PORT}"]
