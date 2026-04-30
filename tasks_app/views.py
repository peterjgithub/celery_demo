import json
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from celery.result import AsyncResult

from .models import AuditTrail, IncompleteChord
from .tasks import (
    dummy_a, dummy_b, dummy_c,
    run_chain_demo,
    run_group_demo,
    run_chord_demo,
    run_chord_chained_demo,
    run_incomplete_chord,
    force_delete_incomplete_chord,
    force_start_incomplete_chord,
    spawning_task,
    dynamic_workflow_task,
    run_workflow_demo,
    timeout_demo,
    retry_demo,
)


# -- Dashboard ----------------------------------------------------------------

def index(request):
    audit_entries = AuditTrail.objects.all()[:50]
    incomplete_chords = IncompleteChord.objects.filter(resolved=False)
    context = {
        'audit_entries': audit_entries,
        'incomplete_chords': incomplete_chords,
    }
    return render(request, 'tasks_app/index.html', context)


# -- Individual task triggers -------------------------------------------------

@require_POST
def trigger_dummy_a(request):
    result = dummy_a.apply_async(args=[1])
    return JsonResponse({'task_id': result.id, 'task': 'dummy_a'})


@require_POST
def trigger_dummy_b(request):
    result = dummy_b.apply_async(args=[1])
    return JsonResponse({'task_id': result.id, 'task': 'dummy_b'})


@require_POST
def trigger_dummy_c(request):
    result = dummy_c.apply_async(args=[1])
    return JsonResponse({'task_id': result.id, 'task': 'dummy_c'})


@require_POST
def trigger_chain(request):
    result = run_chain_demo.apply_async()
    return JsonResponse({'task_id': result.id, 'task': 'chain A->B->C'})


@require_POST
def trigger_group(request):
    result = run_group_demo.apply_async()
    return JsonResponse({'task_id': result.id, 'task': 'group A+B+C'})


@require_POST
def trigger_chord(request):
    result = run_chord_demo.apply_async()
    return JsonResponse({'task_id': result.id, 'task': 'chord demo'})


@require_POST
def trigger_chord_chained(request):
    result = run_chord_chained_demo.apply_async()
    return JsonResponse({'task_id': result.id, 'task': 'chord chained'})


@require_POST
def trigger_incomplete_chord(request):
    result = run_incomplete_chord.apply_async()
    return JsonResponse({'task_id': result.id, 'task': 'incomplete chord'})


@require_POST
def trigger_spawning(request):
    result = spawning_task.apply_async(args=[0])
    return JsonResponse({'task_id': result.id, 'task': 'spawning_task'})


@require_POST
def trigger_dynamic_workflow(request):
    items = [1, 2, 3, 4, 5]
    result = dynamic_workflow_task.apply_async(args=[items])
    return JsonResponse({'task_id': result.id, 'task': 'dynamic_workflow'})


@require_POST
def trigger_workflow(request):
    result = run_workflow_demo.apply_async()
    return JsonResponse({'task_id': result.id, 'task': 'full workflow'})


@require_POST
def trigger_timeout(request):
    result = timeout_demo.apply_async(args=[20])
    return JsonResponse({'task_id': result.id, 'task': 'timeout_demo'})


@require_POST
def trigger_retry(request):
    result = retry_demo.apply_async()
    return JsonResponse({'task_id': result.id, 'task': 'retry_demo'})


# -- Incomplete chord management ----------------------------------------------

@require_POST
def chord_force_delete(request, chord_id):
    result = force_delete_incomplete_chord.apply_async(args=[chord_id])
    return JsonResponse({'task_id': result.id, 'action': 'force_delete', 'chord_id': chord_id})


@require_POST
def chord_force_start(request, chord_id):
    result = force_start_incomplete_chord.apply_async(args=[chord_id])
    return JsonResponse({'task_id': result.id, 'action': 'force_start', 'chord_id': chord_id})


# -- Task status API ----------------------------------------------------------

def task_status(request, task_id):
    result = AsyncResult(task_id)
    return JsonResponse({
        'task_id': task_id,
        'status': result.status,
        'result': str(result.result) if result.ready() else None,
    })


# -- Audit trail API ----------------------------------------------------------

def audit_trail_json(request):
    entries = list(
        AuditTrail.objects.values(
            'task_id', 'task_name', 'status', 'result', 'created_at', 'updated_at'
        )[:100]
    )
    # Convert datetimes to strings for JSON
    for e in entries:
        e['created_at'] = e['created_at'].isoformat()
        e['updated_at'] = e['updated_at'].isoformat()
    return JsonResponse({'entries': entries})
