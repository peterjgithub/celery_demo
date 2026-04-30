"""
Management command: setup_periodic_tasks
Registers all django-celery-beat periodic tasks for the demo.
Run automatically in docker-compose startup.
"""
import json
from django.core.management.base import BaseCommand
from django_celery_beat.models import PeriodicTask, IntervalSchedule, CrontabSchedule


class Command(BaseCommand):
    help = 'Register Celery demo periodic tasks in django-celery-beat'

    def handle(self, *args, **options):
        # Every-minute heartbeat
        interval, _ = IntervalSchedule.objects.get_or_create(
            every=1, period=IntervalSchedule.MINUTES
        )
        task, created = PeriodicTask.objects.get_or_create(
            name='Celery - Scheduled Heartbeat',
            defaults={
                'interval': interval,
                'task': 'tasks.scheduled_heartbeat',
                'args': json.dumps([]),
                'enabled': True,
            },
        )
        if created:
            self.stdout.write(self.style.SUCCESS('[OK] Heartbeat periodic task created (every 1 min)'))
        else:
            self.stdout.write('  Heartbeat task already exists - skipped.')
