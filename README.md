# 🌿 Celery Demo

A hands-on Django + Celery + RabbitMQ demo application that showcases all major Celery concepts — chains, groups, chords, retries, timeouts, scheduled tasks, and more. Everything runs in Docker; **no local Python installation required**.

---

## 📋 Prerequisites

| Requirement | Version |
|---|---|
| [Docker Desktop](https://www.docker.com/products/docker-desktop/) | 4.x or newer |
| Docker Compose | included with Docker Desktop |

That's it. No Python, no pip, no virtual environments needed.

---

## 🚀 Setup & Run

### 1 – Clone the repository

```bash
git clone https://github.com/peterjgithub/celery_demo.git
cd celery_demo
```

### 2 – Start all services

```bash
docker compose up --build
```

This builds the images and starts 5 services:

| Service | What it does |
|---|---|
| `rabbitmq` | Message broker (task queue transport) |
| `web` | Django app + runs migrations + creates admin user |
| `worker` | Celery worker (processes tasks, concurrency 4) |
| `beat` | Celery Beat (fires scheduled tasks every minute) |
| `flower` | Real-time Celery monitoring UI |

> ⏳ First boot takes ~30 seconds while Docker pulls images and pip installs packages.  
> Subsequent starts are instant (images are cached).

### 3 – Verify everything is running

```bash
docker compose ps
```

All 5 services should show `Up` / `healthy`.

---

## 🌐 Open in your browser

Once all services are up, open these URLs:

| Interface | URL | Credentials |
|---|---|---|
| **Dashboard** | http://localhost:8080 | – |
| **Django Admin** | http://localhost:8080/admin | `admin` / `admin` |
| **Flower** (Celery monitor) | http://localhost:5555 | – |
| **RabbitMQ Management** | http://localhost:15672 | `guest` / `guest` |

> � **Tip:** keep the Dashboard and Flower open side by side. Trigger a task on the Dashboard and watch it appear live in Flower.

---

## 🎯 How to use the demo

Every section on the Dashboard has an **ℹ info button** — click it for a step-by-step guide explaining what to do and what to look for in Flower.

The recommended order:

1. **Dummy Tasks** – run A, B, C individually; inspect results in Flower
2. **Chain** – see sequential task execution, result passing
3. **Group** – see parallel execution
4. **Chord (basic)** – parallel tasks with a single aggregating callback
5. **Chord (chained header)** – each parallel branch is itself a chain
6. **Incomplete Chord** – trigger a stuck chord, then use Delete or Force Start to resolve it
7. **Spawning Tasks** – a task that spawns child tasks at runtime
8. **Workflow** – full canvas pipeline combining chord + chain
9. **Timeout Demo** – `SoftTimeLimitExceeded` caught gracefully
10. **Retry Demo** – automatic retries visible in Flower
11. **Scheduled Task** – wait ~1 min; heartbeat appears automatically
12. **Audit Trail** – central log of every task execution (auto-refreshes every 5 s)

---

## 🛑 Stopping the app

```bash
# Stop containers (data is preserved)
docker compose down

# Stop and wipe all data (fresh start next time)
docker compose down -v
```

---

## 📦 What Celery concepts are covered?

| Concept | Where |
|---|---|
| `@shared_task` | All tasks |
| `chain` | Step ② |
| `group` | Steps ③, ⑥ |
| `chord` | Steps ④a, ④b |
| Incomplete chord + management | Steps ④c, ⑤ |
| Spawning tasks (one-shot, no infinite loop) | Step ⑥ |
| Canvas pipeline combination | Step ⑦ |
| `soft_time_limit` + `SoftTimeLimitExceeded` | Step ⑧ |
| `max_retries` + `self.retry()` | Step ⑨ |
| `django-celery-beat` periodic task | Step ⑩ |
| Central Audit Trail via signals | Step ⑪ |
| Flower remote control + Revoke | Step ⑫ |

---

## � Tech stack

| Layer | Technology |
|---|---|
| Web framework | Django 4.2 |
| Task queue | Celery 5.3 |
| Message broker | RabbitMQ 3 |
| Result backend | Redis |
| Database | SQLite (file-based, zero config) |
| Periodic tasks | django-celery-beat |
| Result storage | django-celery-results |
| Monitoring | Flower 2.0 |
| Server | Gunicorn |
| Infrastructure | Docker + Docker Compose |

---

## 🗂 Project structure

```
celery_demo/              Django project package
  settings.py
  celery.py               Celery app + signal hooks for Audit Trail
  urls.py

tasks_app/                Demo Django app
  models.py               AuditTrail + IncompleteChord models
  tasks.py                All Celery task definitions
  views.py                Dashboard view + trigger endpoints
  urls.py
  admin.py
  management/commands/
    setup_periodic_tasks.py

templates/
  tasks_app/index.html    Dashboard UI (vanilla HTML/CSS/JS)

Dockerfile
docker-compose.yml
requirements.txt
STAPPENPLAN.md            Detailed step-by-step guide
```

