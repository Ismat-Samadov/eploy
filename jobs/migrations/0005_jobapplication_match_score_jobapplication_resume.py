# Generated by Django 5.0.6 on 2024-08-11 10:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('jobs', '0004_alter_jobpost_posted_by'),
    ]

    operations = [
        migrations.AddField(
            model_name='jobapplication',
            name='match_score',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='jobapplication',
            name='resume',
            field=models.FileField(blank=True, null=True, upload_to='resumes/'),
        ),
    ]
