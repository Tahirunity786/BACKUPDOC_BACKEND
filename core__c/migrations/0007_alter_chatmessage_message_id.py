# Generated by Django 5.0.7 on 2025-05-16 07:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core__c', '0006_alter_chatmessage_message_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='chatmessage',
            name='message_id',
            field=models.CharField(default='c5d743e6-2c2e-4e21-bcd2-ba681e4aecac', editable=False, max_length=100, unique=True),
        ),
    ]
