# Generated migration for teacher admin approval

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0001_initial'),  # Adjust to your latest migration
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='is_approved',
            field=models.BooleanField(default=True, help_text='Account approved by admin (for teachers)'),
        ),
    ]
