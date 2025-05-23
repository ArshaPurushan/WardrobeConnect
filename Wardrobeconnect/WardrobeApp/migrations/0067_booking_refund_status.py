# Generated by Django 5.1.6 on 2025-04-10 07:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('WardrobeApp', '0066_booking_inspection_note_booking_late_fee_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='booking',
            name='refund_status',
            field=models.CharField(choices=[('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected'), ('processed', 'Processed')], default='pending', max_length=10),
        ),
    ]
