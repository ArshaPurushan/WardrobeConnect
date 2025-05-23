# Generated by Django 5.1.6 on 2025-03-07 09:21

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('WardrobeApp', '0006_alter_booking_rental_end_date'),
    ]

    operations = [
        migrations.RenameField(
            model_name='admin',
            old_name='name',
            new_name='password',
        ),
        migrations.RemoveField(
            model_name='admin',
            name='logid',
        ),
        migrations.AddField(
            model_name='admin',
            name='username',
            field=models.CharField(default='admin', max_length=150, unique=True),
        ),
        migrations.AlterField(
            model_name='booking',
            name='rental_end_date',
            field=models.DateTimeField(default=datetime.datetime(2025, 3, 14, 9, 20, 57, 809973, tzinfo=datetime.timezone.utc)),
        ),
    ]
