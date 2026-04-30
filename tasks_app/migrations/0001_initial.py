from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='AuditTrail',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('task_id', models.CharField(db_index=True, max_length=255, unique=True)),
                ('task_name', models.CharField(db_index=True, max_length=255)),
                ('status', models.CharField(
                    choices=[
                        ('PENDING', 'Pending'), ('RECEIVED', 'Received'), ('STARTED', 'Started'),
                        ('SUCCESS', 'Success'), ('FAILURE', 'Failure'), ('RETRY', 'Retry'), ('REVOKED', 'Revoked'),
                    ],
                    default='PENDING', max_length=50,
                )),
                ('args', models.TextField(blank=True, default='')),
                ('kwargs', models.TextField(blank=True, default='')),
                ('result', models.TextField(blank=True, default='')),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={'ordering': ['-created_at'], 'verbose_name': 'Audit Trail', 'verbose_name_plural': 'Audit Trail'},
        ),
        migrations.CreateModel(
            name='IncompleteChord',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('chord_id', models.CharField(db_index=True, max_length=255, unique=True)),
                ('description', models.CharField(max_length=255)),
                ('header_task_ids', models.JSONField(default=list)),
                ('callback_task_id', models.CharField(blank=True, default='', max_length=255)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('resolved', models.BooleanField(default=False)),
            ],
            options={'ordering': ['-created_at']},
        ),
    ]
