# Generated by Django 5.0.6 on 2024-08-12 04:34

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('jobs', '0005_jobapplication_match_score'),
    ]

    operations = [
        migrations.RenameField(
            model_name='jobapplication',
            old_name='cv',
            new_name='resume',
        ),
    ]