# Generated by Django 5.0.7 on 2025-05-15 14:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core__c', '0005_alter_chatmessage_message_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='chatmessage',
            name='message_id',
            field=models.CharField(default='125183be-e0b4-4775-9c41-bd91d962b3b1', editable=False, max_length=100, unique=True),
        ),
    ]
