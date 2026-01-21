# Generated migration for wireless camera support

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('camera_integration', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='externalcamerasource',
            name='device_type',
            field=models.CharField(
                choices=[
                    ('mobile', 'Mobile Device'),
                    ('tablet', 'Tablet'),
                    ('webcam', 'External Webcam'),
                    ('ip_camera', 'IP Camera / Wireless Camera'),
                    ('rtsp', 'RTSP Stream'),
                    ('http_stream', 'HTTP/MJPEG Stream'),
                    ('other', 'Other')
                ],
                default='mobile',
                max_length=50
            ),
        ),
        migrations.AddField(
            model_name='externalcamerasource',
            name='stream_url',
            field=models.URLField(
                blank=True,
                help_text='Stream URL for IP cameras (rtsp://, http://, etc.)',
                max_length=512,
                null=True
            ),
        ),
        migrations.AddField(
            model_name='externalcamerasource',
            name='stream_username',
            field=models.CharField(
                blank=True,
                help_text='Username for authenticated streams',
                max_length=255
            ),
        ),
        migrations.AddField(
            model_name='externalcamerasource',
            name='stream_password',
            field=models.CharField(
                blank=True,
                help_text='Password for authenticated streams',
                max_length=255
            ),
        ),
        migrations.AddField(
            model_name='externalcamerasource',
            name='stream_protocol',
            field=models.CharField(
                choices=[
                    ('rtsp', 'RTSP'),
                    ('http', 'HTTP/MJPEG'),
                    ('https', 'HTTPS'),
                    ('upload', 'Manual Upload')
                ],
                default='upload',
                help_text='Protocol used for streaming',
                max_length=20
            ),
        ),
        migrations.AddField(
            model_name='externalcamerasource',
            name='stream_quality',
            field=models.CharField(
                choices=[
                    ('high', 'High Quality'),
                    ('medium', 'Medium Quality'),
                    ('low', 'Low Quality')
                ],
                default='medium',
                help_text='Stream quality/resolution preference',
                max_length=20
            ),
        ),
        migrations.AddField(
            model_name='externalcamerasource',
            name='fps_limit',
            field=models.IntegerField(
                default=5,
                help_text='Frames per second limit for processing (1-30)'
            ),
        ),
    ]
