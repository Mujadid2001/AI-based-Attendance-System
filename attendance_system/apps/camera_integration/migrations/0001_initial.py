"""
Initial migration for camera_integration app.
"""
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('authentication', '0001_initial'),
        ('attendance', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ExternalCameraSource',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(help_text='Name for this camera source', max_length=255)),
                ('device_id', models.CharField(help_text='Unique device identifier', max_length=255, unique=True)),
                ('device_type', models.CharField(choices=[('mobile', 'Mobile Device'), ('tablet', 'Tablet'), ('webcam', 'External Webcam'), ('other', 'Other')], default='mobile', max_length=50)),
                ('access_token', models.CharField(db_index=True, max_length=64, unique=True)),
                ('status', models.CharField(choices=[('active', 'Active'), ('inactive', 'Inactive'), ('disconnected', 'Disconnected')], default='inactive', max_length=20)),
                ('last_connected', models.DateTimeField(blank=True, null=True)),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True)),
                ('user_agent', models.TextField(blank=True)),
                ('is_enabled', models.BooleanField(default=True)),
                ('auto_mark_attendance', models.BooleanField(default=False, help_text='Automatically mark attendance when face is recognized')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='camera_sources', to='authentication.user')),
            ],
            options={
                'verbose_name': 'External Camera Source',
                'verbose_name_plural': 'External Camera Sources',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='CameraStreamSession',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('started_at', models.DateTimeField(auto_now_add=True)),
                ('ended_at', models.DateTimeField(blank=True, null=True)),
                ('frames_received', models.IntegerField(default=0)),
                ('faces_detected', models.IntegerField(default=0)),
                ('faces_recognized', models.IntegerField(default=0)),
                ('attendance_marked', models.IntegerField(default=0)),
                ('attendance_session', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='camera_sessions', to='attendance.attendancesession')),
                ('camera_source', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='stream_sessions', to='camera_integration.externalcamerasource')),
            ],
            options={
                'verbose_name': 'Camera Stream Session',
                'verbose_name_plural': 'Camera Stream Sessions',
                'ordering': ['-started_at'],
            },
        ),
    ]
