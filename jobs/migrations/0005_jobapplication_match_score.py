# Generated by Django 5.0.6 on 2024-08-12 04:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('jobs', '0004_rename_resume_jobapplication_cv'),
    ]

    operations = [
        migrations.AddField(
            model_name='jobapplication',
            name='match_score',
            field=models.FloatField(blank=True, null=True),
        ),
    ]