# Generated by Django 5.0.7 on 2025-05-20 15:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core__c', '0022_alter_chatmessage_message_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='chatmessage',
            name='message_id',
            field=models.CharField(default='c0093313-f296-4c2f-8bbe-295223e11827', editable=False, max_length=100, unique=True),
        ),
    ]
