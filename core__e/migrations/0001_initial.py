# Generated by Django 5.0.7 on 2025-05-09 15:18

import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Analysis',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('raw_image', models.CharField(blank=True, db_index=True, max_length=200, null=True)),
                ('analyzed_image', models.CharField(blank=True, db_index=True, max_length=200, null=True)),
                ('note', models.TextField(blank=True, null=True)),
                ('report_analysis', models.TextField(blank=True, null=True)),
                ('date_time', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='Predictions',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('result_prediction', models.CharField(max_length=100, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='AnalysisResult',
            fields=[
                ('analysis_id', models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('analysis', models.ManyToManyField(blank=True, related_name='analysis_results', to='core__e.analysis')),
            ],
        ),
        migrations.AddField(
            model_name='analysis',
            name='predictions',
            field=models.ManyToManyField(related_name='analyses', to='core__e.predictions'),
        ),
    ]
