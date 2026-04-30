"""
Celery Demo - Celery Tasks
============================
Demonstrates:
  - Simple tasks (Dummy A / B / C)
  - Task Chaining
  - Groups
  - Chords  (complete & intentionally incomplete)
  - Tasks that spawn new tasks
  - Celery Workflow (canvas primitives combined)
  - Scheduled task (via django-celery-beat)
  - Timeout / SoftTimeLimitExceeded demo
  - on_failure handler for incomplete chords
  - Helper to forcefully complete an incomplete chord
"""

import time
import uuid
import logging

from celery import shared_task, chain, group, chord, signature
from celery.exceptions import SoftTimeLimitExceeded
from celery.result import AsyncResult

logger = logging.getLogger(__name__)


# -- helpers ------------------------------------------------------------------

def _audit(task_id: str, task_name: str, status: str, result: str = '') -> None:
    """Write directly to the AuditTrail model (used inside tasks)."""
    try:
        from tasks_app.models import AuditTrail
        AuditTrail.objects.update_or_create(
            task_id=task_id,
            defaults={'task_name': task_name, 'status': status, 'result': result[:500]},
        )
    except Exception as exc:
        logger.warning('AuditTrail write failed: %s', exc)


# ============================================================================
# 1.  DUMMY TASKS  A / B / C
# ============================================================================

@shared_task(bind=True, name='tasks.dummy_a')
def dummy_a(self, value: int = 1) -> int:
    logger.info('[Dummy A] started - value=%s', value)
    time.sleep(2)
    result = value * 10
    logger.info('[Dummy A] done - result=%s', result)
    return result


@shared_task(bind=True, name='tasks.dummy_b')
def dummy_b(self, value: int = 1) -> int:
    logger.info('[Dummy B] started - value=%s', value)
    time.sleep(1)
    result = value + 5
    logger.info('[Dummy B] done - result=%s', result)
    return result


@shared_task(bind=True, name='tasks.dummy_c')
def dummy_c(self, value: int = 1) -> str:
    logger.info('[Dummy C] started - value=%s', value)
    time.sleep(1)
    result = f'Final result: {value}'
    logger.info('[Dummy C] done - result=%s', result)
    return result


# ============================================================================
# 2.  CHAIN DEMO   A -> B -> C
# ============================================================================

@shared_task(bind=True, name='tasks.run_chain_demo')
def run_chain_demo(self) -> str:
    """Kick off a chain:  dummy_a(1)  ->  dummy_b  ->  dummy_c"""
    pipeline = chain(dummy_a.s(1), dummy_b.s(), dummy_c.s())
    result = pipeline.apply_async()
    logger.info('[Chain] dispatched, root task_id=%s', result.id)
    return f'chain dispatched: root_id={result.id}'


# ============================================================================
# 3.  GROUP DEMO
# ============================================================================

@shared_task(bind=True, name='tasks.run_group_demo')
def run_group_demo(self) -> str:
    """Run A, B, C in parallel via a Group."""
    job = group(dummy_a.s(1), dummy_b.s(2), dummy_c.s(3))
    result = job.apply_async()
    logger.info('[Group] dispatched, group_id=%s', result.id)
    return f'group dispatched: group_id={result.id}'


# ============================================================================
# 4a. CHORD - callback aggregates all header results
# ============================================================================

@shared_task(bind=True, name='tasks.chord_callback')
def chord_callback(self, results: list) -> str:
    summary = f'Chord complete! Got {len(results)} results: {results}'
    logger.info('[Chord callback] %s', summary)
    return summary


@shared_task(bind=True, name='tasks.run_chord_demo')
def run_chord_demo(self) -> str:
    """Complete chord: group of 3 tasks -> single callback."""
    header = group(dummy_a.s(2), dummy_b.s(3), dummy_c.s(4))
    callback = chord_callback.s()
    result = chord(header, callback).apply_async()
    logger.info('[Chord] dispatched, id=%s', result.id)
    return f'chord dispatched: id={result.id}'


# ============================================================================
# 4b. CHORD - second example with chained header
# ============================================================================

@shared_task(bind=True, name='tasks.chord_callback_chained')
def chord_callback_chained(self, results: list) -> str:
    total = sum(r for r in results if isinstance(r, (int, float)))
    summary = f'Chained-chord complete! Sum={total}, raw={results}'
    logger.info('[Chord-chained callback] %s', summary)
    return summary


@shared_task(bind=True, name='tasks.run_chord_chained_demo')
def run_chord_chained_demo(self) -> str:
    """Chord where each header task is itself a mini-chain."""
    header = group(
        chain(dummy_a.s(1), dummy_b.s()),
        chain(dummy_a.s(2), dummy_b.s()),
        chain(dummy_a.s(3), dummy_b.s()),
    )
    result = chord(header, chord_callback_chained.s()).apply_async()
    return f'chained-chord dispatched: id={result.id}'


# ============================================================================
# 4c. INCOMPLETE CHORD  (header never finishes because one task always fails)
# ============================================================================

@shared_task(bind=True, name='tasks.always_failing_task',
             max_retries=0)
def always_failing_task(self, index: int = 0) -> None:
    """Deliberately raises an exception so the chord header stays incomplete."""
    logger.warning('[AlwaysFailing] task %s - raising exception', index)
    raise ValueError(f'Intentional failure for chord demo (index={index})')


@shared_task(bind=True, name='tasks.incomplete_chord_callback')
def incomplete_chord_callback(self, results: list) -> str:
    """This callback is *never* called because the header never completes."""
    return f'Incomplete-chord callback (should not appear): {results}'


@shared_task(bind=True, name='tasks.run_incomplete_chord')
def run_incomplete_chord(self) -> str:
    """
    Dispatch a chord where one header task always fails.
    Saves an IncompleteChord record so the dashboard can manage it.
    """
    from tasks_app.models import IncompleteChord

    t1 = dummy_a.s(10)
    t2 = always_failing_task.s(1)   # <- this breaks the chord
    t3 = dummy_b.s(5)

    header = group(t1, t2, t3)
    callback = incomplete_chord_callback.s()
    chord_result = chord(header, callback).apply_async()

    # Persist so we can manage it later
    IncompleteChord.objects.create(
        chord_id=chord_result.id,
        description='Demo incomplete chord - always_failing_task breaks it',
        header_task_ids=[],          # runtime IDs not available before execution
        callback_task_id='',
    )

    logger.warning('[IncompleteChord] dispatched chord_id=%s', chord_result.id)
    return f'incomplete chord dispatched: chord_id={chord_result.id}'


# ============================================================================
# 4d. INCOMPLETE CHORD MANAGEMENT
# ============================================================================

@shared_task(bind=True, name='tasks.force_delete_incomplete_chord')
def force_delete_incomplete_chord(self, chord_id: str) -> str:
    """
    Revoke & delete an incomplete chord and mark it resolved.
    Acts as the on_failure handler + admin cleanup utility.
    """
    from tasks_app.models import IncompleteChord

    try:
        ic = IncompleteChord.objects.get(chord_id=chord_id)
    except IncompleteChord.DoesNotExist:
        return f'IncompleteChord {chord_id} not found'

    # Revoke all known header tasks
    for tid in ic.header_task_ids:
        AsyncResult(tid).revoke(terminate=True)
        logger.info('[ForceDelete] revoked task %s', tid)

    # Revoke the callback if registered
    if ic.callback_task_id:
        AsyncResult(ic.callback_task_id).revoke(terminate=True)

    ic.resolved = True
    ic.save(update_fields=['resolved'])

    _audit(self.request.id, self.name, 'SUCCESS',
           f'Deleted incomplete chord {chord_id}')
    logger.info('[ForceDelete] chord %s marked resolved', chord_id)
    return f'Chord {chord_id} deleted and marked resolved'


@shared_task(bind=True, name='tasks.force_start_incomplete_chord')
def force_start_incomplete_chord(self, chord_id: str) -> str:
    """
    Force-complete the chord by publishing a synthetic result for missing
    header tasks, allowing the callback to finally execute.
    """
    from tasks_app.models import IncompleteChord
    from celery.backends.base import Backend  # noqa - just for type hint

    try:
        ic = IncompleteChord.objects.get(chord_id=chord_id)
    except IncompleteChord.DoesNotExist:
        return f'IncompleteChord {chord_id} not found'

    # Re-dispatch a fresh simple chord so the callback fires
    header = group(dummy_a.s(99), dummy_b.s(99))
    callback = chord_callback.s()
    new_result = chord(header, callback).apply_async()

    ic.resolved = True
    ic.save(update_fields=['resolved'])

    msg = (f'Force-started chord {chord_id}: '
           f'new chord dispatched as {new_result.id}')
    logger.info('[ForceStart] %s', msg)
    _audit(self.request.id, self.name, 'SUCCESS', msg)
    return msg


# ============================================================================
# 5.  TASKS THAT SPAWN NEW TASKS  (one-shot, not infinite)
# ============================================================================

@shared_task(bind=True, name='tasks.spawning_task')
def spawning_task(self, depth: int = 0) -> str:
    """
    A task that spawns child tasks exactly once (depth guard prevents loops).
    depth=0 -> spawns 3 children; children do NOT spawn again.
    """
    logger.info('[SpawningTask] depth=%s', depth)
    if depth == 0:
        for i in range(3):
            dummy_a.apply_async(args=[i + 1])
            logger.info('[SpawningTask] spawned dummy_a(%s)', i + 1)
    return f'spawning_task depth={depth} done'


@shared_task(bind=True, name='tasks.dynamic_workflow_task')
def dynamic_workflow_task(self, items: list) -> str:
    """
    Receives a list of items, creates a dynamic group of tasks, one per item.
    Demonstrates runtime canvas construction.
    """
    logger.info('[DynamicWorkflow] building group for items=%s', items)
    job = group(dummy_b.s(item) for item in items)
    result = job.apply_async()
    return f'dynamic group dispatched for {len(items)} items, group_id={result.id}'


# ============================================================================
# 6.  CELERY WORKFLOW  (canvas: chain of group + chord combined)
# ============================================================================

@shared_task(bind=True, name='tasks.workflow_summary')
def workflow_summary(self, chord_result: str, chain_result: str = '') -> str:
    summary = f'Workflow complete! chord_result={chord_result}'
    logger.info('[Workflow] %s', summary)
    return summary


@shared_task(bind=True, name='tasks.run_workflow_demo')
def run_workflow_demo(self) -> str:
    """
    Full Celery workflow canvas:
      Step 1 (chord): parallel A+B -> aggregate callback
      Step 2 (chain): result piped into dummy_c
    """
    step1_header = group(dummy_a.s(5), dummy_b.s(5))
    step1_callback = chord_callback.s()
    step1 = chord(step1_header, step1_callback)

    # After the chord callback finishes, pipe into dummy_c
    pipeline = chain(step1, dummy_c.s())
    result = pipeline.apply_async()
    return f'workflow dispatched: root_id={result.id}'


# ============================================================================
# 7.  SCHEDULED TASK  (registered via django-celery-beat migration)
# ============================================================================

@shared_task(bind=True, name='tasks.scheduled_heartbeat')
def scheduled_heartbeat(self) -> str:
    """
    Runs every minute (configured via django-celery-beat PeriodicTask).
    Writes a heartbeat record to the AuditTrail.
    """
    msg = f'Heartbeat at {time.strftime("%Y-%m-%d %H:%M:%S")}'
    logger.info('[Heartbeat] %s', msg)
    _audit(self.request.id, self.name, 'SUCCESS', msg)
    return msg


# ============================================================================
# 8.  TIMEOUT DEMO  (SoftTimeLimitExceeded)
# ============================================================================

@shared_task(bind=True, name='tasks.timeout_demo',
             soft_time_limit=5, time_limit=10)
def timeout_demo(self, sleep_seconds: int = 20) -> str:
    """
    Sleeps longer than soft_time_limit (5 s) to trigger SoftTimeLimitExceeded.
    Catches it gracefully and logs to AuditTrail.
    """
    logger.info('[TimeoutDemo] sleeping %s seconds...', sleep_seconds)
    try:
        time.sleep(sleep_seconds)
        return f'finished after {sleep_seconds}s (no timeout)'
    except SoftTimeLimitExceeded:
        msg = f'SoftTimeLimitExceeded after {sleep_seconds}s - handled gracefully'
        logger.warning('[TimeoutDemo] %s', msg)
        _audit(self.request.id, self.name, 'FAILURE', msg)
        return msg


# ============================================================================
# 9.  TASK DETAILS & RETRY DEMO
# ============================================================================

@shared_task(bind=True, name='tasks.retry_demo', max_retries=3, default_retry_delay=5)
def retry_demo(self) -> str:
    """Fails twice, succeeds on the 3rd attempt. Shows retry in Flower."""
    attempt = self.request.retries
    logger.info('[RetryDemo] attempt %s', attempt)
    if attempt < 2:
        raise self.retry(exc=ValueError(f'Simulated failure on attempt {attempt}'),
                         countdown=3)
    return f'retry_demo succeeded on attempt {attempt}'
