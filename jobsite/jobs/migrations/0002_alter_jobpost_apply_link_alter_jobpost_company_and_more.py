# Generated by Django 5.0.6 on 2024-07-11 06:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('jobs', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='jobpost',
            name='apply_link',
            field=models.URLField(default='', max_length=1000),
        ),
        migrations.AlterField(
            model_name='jobpost',
            name='company',
            field=models.CharField(max_length=500),
        ),
        migrations.AlterField(
            model_name='jobpost',
            name='location',
            field=models.CharField(max_length=500),
        ),
        migrations.AlterField(
            model_name='jobpost',
            name='title',
            field=models.CharField(max_length=500),
        ),
    ]