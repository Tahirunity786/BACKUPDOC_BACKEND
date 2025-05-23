# Generated by Django 5.0.7 on 2025-05-18 06:45

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core__p', '0007_appointments'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='appointments',
            name='doctor',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='doctor_appoint', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='appointments',
            name='patient',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='patient_appoint', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='appointments',
            name='status',
            field=models.CharField(choices=[('pending', 'pending'), ('resolved', 'resolved')], db_index=True, default='NA', max_length=100),
        ),
        migrations.AlterField(
            model_name='appointments',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, db_index=True),
        ),
        migrations.AlterField(
            model_name='appointments',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, db_index=True),
        ),
    ]
