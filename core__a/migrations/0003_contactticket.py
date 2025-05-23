# Generated by Django 5.0.7 on 2025-05-04 11:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core__a', '0002_alter_user_otp_delay'),
    ]

    operations = [
        migrations.CreateModel(
            name='ContactTicket',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('contact_id', models.CharField(db_index=True, default='', max_length=100, null=True, unique=True)),
                ('first_name', models.CharField(db_index=True, max_length=100)),
                ('last_name', models.CharField(db_index=True, max_length=100)),
                ('subject', models.CharField(max_length=255)),
                ('company_name', models.CharField(blank=True, max_length=255, null=True)),
                ('employee_number', models.CharField(blank=True, max_length=255, null=True)),
                ('message', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('is_resolved', models.BooleanField(default=False)),
            ],
        ),
    ]
