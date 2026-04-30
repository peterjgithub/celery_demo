FROM python:3.11-slim-bookworm

# System deps – upgrade first to pick up OS security patches
RUN apt-get update && apt-get upgrade -y && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Collect static files (ignore errors – db not available at build time)
RUN python manage.py collectstatic --noinput || true

EXPOSE 8000

CMD ["gunicorn", "celery_demo.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "2", "--timeout", "120"]
