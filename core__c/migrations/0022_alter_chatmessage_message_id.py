# Generated by Django 5.0.7 on 2025-05-20 12:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core__c', '0021_alter_chatmessage_message_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='chatmessage',
            name='message_id',
            field=models.CharField(default='5b0d10e9-c6aa-4c57-b1d2-470a2728a27c', editable=False, max_length=100, unique=True),
        ),
    ]
