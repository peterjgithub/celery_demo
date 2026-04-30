from django.db import models
from django.utils import timezone


class AuditTrail(models.Model):
    """Central audit log - every Celery task writes a record here."""

    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('RECEIVED', 'Received'),
        ('STARTED', 'Started'),
        ('SUCCESS', 'Success'),
        ('FAILURE', 'Failure'),
        ('RETRY', 'Retry'),
        ('REVOKED', 'Revoked'),
    ]

    task_id = models.CharField(max_length=255, unique=True, db_index=True)
    task_name = models.CharField(max_length=255, db_index=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='PENDING')
    args = models.TextField(blank=True, default='')
    kwargs = models.TextField(blank=True, default='')
    result = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Audit Trail'
        verbose_name_plural = 'Audit Trail'

    def __str__(self):
        return f'[{self.status}] {self.task_name} - {self.task_id[:8]}'


class IncompleteChord(models.Model):
    """Tracks chord header task-IDs so we can manage incomplete chords."""

    chord_id = models.CharField(max_length=255, unique=True, db_index=True)
    description = models.CharField(max_length=255)
    header_task_ids = models.JSONField(default=list)
    callback_task_id = models.CharField(max_length=255, blank=True, default='')
    created_at = models.DateTimeField(default=timezone.now)
    resolved = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        status = 'resolved' if self.resolved else 'incomplete'
        return f'Chord {self.chord_id[:8]} ({status})'
