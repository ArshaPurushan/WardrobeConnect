# Generated by Django 5.1.6 on 2025-03-21 10:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('WardrobeApp', '0029_cart_wishlist'),
    ]

    operations = [
        migrations.AddField(
            model_name='salesreport',
            name='report_status',
            field=models.CharField(choices=[('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected')], default='pending', max_length=10),
        ),
    ]
