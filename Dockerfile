FROM python:3.11-alpine3.21

# Upgrade all packages to pick up security patches, then add runtime deps
RUN apk upgrade --no-cache && apk add --no-cache curl

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Collect static files (ignore errors – db not available at build time)
RUN python manage.py collectstatic --noinput || true

EXPOSE 8000

CMD ["gunicorn", "celery_demo.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "2", "--timeout", "120"]
