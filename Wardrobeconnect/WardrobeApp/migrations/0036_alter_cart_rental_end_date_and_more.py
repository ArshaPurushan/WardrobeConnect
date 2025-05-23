# Generated by Django 5.1.6 on 2025-03-26 19:45

import WardrobeApp.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('WardrobeApp', '0035_alter_cart_rental_end_date_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cart',
            name='rental_end_date',
            field=models.DateField(default=WardrobeApp.models.default_rental_end_date),
        ),
        migrations.AlterField(
            model_name='employee',
            name='profile_picture',
            field=models.ImageField(blank=True, null=True, upload_to='profile_images/'),
        ),
    ]
