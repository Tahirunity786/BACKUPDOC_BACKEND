# Generated by Django 5.0.7 on 2025-05-15 12:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core__p', '0005_alter_patients_patient_xrays'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='patients',
            name='date_of_birth',
        ),
        migrations.RemoveField(
            model_name='patients',
            name='patient_ssn',
        ),
        migrations.AddField(
            model_name='patients',
            name='age',
            field=models.PositiveIntegerField(db_index=True, default=0),
        ),
    ]
