# Generated by Django 5.1.6 on 2025-05-13 18:47

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('WardrobeApp', '0071_product_created_at'),
    ]

    operations = [
        migrations.AlterField(
            model_name='booking',
            name='return_by',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AlterField(
            model_name='report',
            name='description',
            field=models.TextField(blank=True, null=True),
        ),
    ]
