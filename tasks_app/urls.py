from django.urls import path
from . import views

app_name = 'tasks_app'

urlpatterns = [
    # Dashboard
    path('', views.index, name='index'),

    # Trigger endpoints
    path('trigger/dummy-a/', views.trigger_dummy_a, name='trigger_dummy_a'),
    path('trigger/dummy-b/', views.trigger_dummy_b, name='trigger_dummy_b'),
    path('trigger/dummy-c/', views.trigger_dummy_c, name='trigger_dummy_c'),
    path('trigger/chain/', views.trigger_chain, name='trigger_chain'),
    path('trigger/group/', views.trigger_group, name='trigger_group'),
    path('trigger/chord/', views.trigger_chord, name='trigger_chord'),
    path('trigger/chord-chained/', views.trigger_chord_chained, name='trigger_chord_chained'),
    path('trigger/incomplete-chord/', views.trigger_incomplete_chord, name='trigger_incomplete_chord'),
    path('trigger/spawning/', views.trigger_spawning, name='trigger_spawning'),
    path('trigger/dynamic-workflow/', views.trigger_dynamic_workflow, name='trigger_dynamic_workflow'),
    path('trigger/workflow/', views.trigger_workflow, name='trigger_workflow'),
    path('trigger/timeout/', views.trigger_timeout, name='trigger_timeout'),
    path('trigger/retry/', views.trigger_retry, name='trigger_retry'),

    # Chord management
    path('chord/<str:chord_id>/delete/', views.chord_force_delete, name='chord_force_delete'),
    path('chord/<str:chord_id>/force-start/', views.chord_force_start, name='chord_force_start'),

    # API
    path('api/task-status/<str:task_id>/', views.task_status, name='task_status'),
    path('api/audit-trail/', views.audit_trail_json, name='audit_trail_json'),
]
