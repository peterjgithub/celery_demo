from django.contrib import admin
from .models import AuditTrail, IncompleteChord


@admin.register(AuditTrail)
class AuditTrailAdmin(admin.ModelAdmin):
    list_display = ('task_name', 'status', 'task_id', 'created_at', 'updated_at')
    list_filter = ('status', 'task_name')
    search_fields = ('task_id', 'task_name', 'result')
    readonly_fields = ('task_id', 'task_name', 'status', 'args', 'kwargs', 'result', 'created_at', 'updated_at')
    ordering = ('-created_at',)

    def has_add_permission(self, request):
        return False


@admin.register(IncompleteChord)
class IncompleteChordAdmin(admin.ModelAdmin):
    list_display = ('chord_id', 'description', 'resolved', 'created_at')
    list_filter = ('resolved',)
    readonly_fields = ('chord_id', 'header_task_ids', 'callback_task_id', 'created_at')
