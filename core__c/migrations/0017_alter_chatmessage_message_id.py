# Generated by Django 5.0.7 on 2025-05-19 15:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core__c', '0016_alter_chatmessage_message_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='chatmessage',
            name='message_id',
            field=models.CharField(default='7373e3b2-ac42-499b-ab17-1db9f8e0a27c', editable=False, max_length=100, unique=True),
        ),
    ]
