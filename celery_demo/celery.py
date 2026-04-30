import os
from celery import Celery
from celery.signals import task_prerun, task_postrun, task_failure, task_retry

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'celery_demo.settings')

app = Celery('celery_demo')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()


# -- Audit Trail signal hooks -------------------------------------------------

@task_prerun.connect
def on_task_prerun(task_id, task, args, kwargs, **extra):
    """Create or update AuditTrail record when a task starts."""
    try:
        from tasks_app.models import AuditTrail
        AuditTrail.objects.update_or_create(
            task_id=task_id,
            defaults={
                'task_name': task.name,
                'status': 'STARTED',
                'args': str(args),
                'kwargs': str(kwargs),
            },
        )
    except Exception:
        pass


@task_postrun.connect
def on_task_postrun(task_id, task, args, kwargs, retval, state, **extra):
    """Update AuditTrail record when a task finishes."""
    try:
        from tasks_app.models import AuditTrail
        AuditTrail.objects.filter(task_id=task_id).update(
            status=state,
            result=str(retval)[:500],
        )
    except Exception:
        pass


@task_failure.connect
def on_task_failure(task_id, exception, traceback, sender, **extra):
    """Update AuditTrail record on failure."""
    try:
        from tasks_app.models import AuditTrail
        AuditTrail.objects.filter(task_id=task_id).update(
            status='FAILURE',
            result=f'{type(exception).__name__}: {exception}'[:500],
        )
    except Exception:
        pass


@task_retry.connect
def on_task_retry(request, reason, einfo, **extra):
    """Mark AuditTrail record as RETRY."""
    try:
        from tasks_app.models import AuditTrail
        AuditTrail.objects.filter(task_id=request.id).update(
            status='RETRY',
            result=str(reason)[:500],
        )
    except Exception:
        pass
