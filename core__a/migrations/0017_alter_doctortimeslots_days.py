# Generated by Django 5.0.7 on 2025-05-21 12:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core__a', '0016_alter_doctortimeslots_days'),
    ]

    operations = [
        migrations.AlterField(
            model_name='doctortimeslots',
            name='days',
            field=models.CharField(choices=[('monday', 'monday'), ('tuesday', 'tuesday'), ('wednesday', 'wednesday'), ('thursday', 'thursday'), ('friday', 'friday'), ('saturday', 'saturday'), ('sunday', 'sunday')], db_index=True, default='monday', max_length=100),
        ),
    ]
