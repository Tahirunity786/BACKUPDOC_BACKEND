# Generated by Django 5.0.7 on 2025-05-15 12:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core__c', '0003_alter_chatmessage_message_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='chatmessage',
            name='message_id',
            field=models.CharField(default='13f83b1e-4854-4a3a-9457-43e74d3e397f', editable=False, max_length=100, unique=True),
        ),
    ]
