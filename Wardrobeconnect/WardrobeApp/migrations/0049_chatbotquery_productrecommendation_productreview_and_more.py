# Generated by Django 5.1.6 on 2025-03-30 07:19

import WardrobeApp.models
import django.core.validators
import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('WardrobeApp', '0048_alter_cart_rental_end_date'),
    ]

    operations = [
        migrations.CreateModel(
            name='ChatbotQuery',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('query', models.TextField()),
                ('response', models.TextField()),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='ProductRecommendation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ],
        ),
        migrations.CreateModel(
            name='ProductReview',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rating', models.IntegerField(default=5)),
                ('review', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='ProductSize',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('size', models.IntegerField(choices=[(0, 'S'), (1, 'M'), (2, 'L'), (3, 'XL'), (4, 'XXL')])),
                ('stock', models.PositiveIntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='Return',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('returned_at', models.DateTimeField(auto_now_add=True)),
                ('condition', models.CharField(default='Good', max_length=255)),
                ('late_fee', models.DecimalField(decimal_places=2, default=0.0, max_digits=10)),
            ],
        ),
        migrations.RemoveField(
            model_name='cart',
            name='product',
        ),
        migrations.RemoveField(
            model_name='cart',
            name='user',
        ),
        migrations.DeleteModel(
            name='ChatbotResponse',
        ),
        migrations.RemoveField(
            model_name='notification',
            name='user',
        ),
        migrations.RemoveField(
            model_name='rentalproduct',
            name='product',
        ),
        migrations.RemoveField(
            model_name='review',
            name='product',
        ),
        migrations.RemoveField(
            model_name='review',
            name='user',
        ),
        migrations.DeleteModel(
            name='SalesReport',
        ),
        migrations.RemoveField(
            model_name='wishlist',
            name='product',
        ),
        migrations.RemoveField(
            model_name='wishlist',
            name='user',
        ),
        migrations.RenameField(
            model_name='booking',
            old_name='user',
            new_name='customer',
        ),
        migrations.RenameField(
            model_name='complaint',
            old_name='complaint_text',
            new_name='message',
        ),
        migrations.RenameField(
            model_name='complaint',
            old_name='created_at',
            new_name='submitted_at',
        ),
        migrations.RenameField(
            model_name='feedback',
            old_name='created_at',
            new_name='submitted_at',
        ),
        migrations.RemoveField(
            model_name='booking',
            name='address',
        ),
        migrations.RemoveField(
            model_name='booking',
            name='damage_fee',
        ),
        migrations.RemoveField(
            model_name='booking',
            name='late_fee',
        ),
        migrations.RemoveField(
            model_name='booking',
            name='product',
        ),
        migrations.RemoveField(
            model_name='booking',
            name='quantity',
        ),
        migrations.RemoveField(
            model_name='booking',
            name='refund_status',
        ),
        migrations.RemoveField(
            model_name='booking',
            name='rental_duration',
        ),
        migrations.RemoveField(
            model_name='booking',
            name='rental_end_date',
        ),
        migrations.RemoveField(
            model_name='booking',
            name='rental_start_date',
        ),
        migrations.RemoveField(
            model_name='booking',
            name='size',
        ),
        migrations.RemoveField(
            model_name='booking',
            name='total_price',
        ),
        migrations.RemoveField(
            model_name='employee',
            name='contact_number',
        ),
        migrations.RemoveField(
            model_name='employee',
            name='email',
        ),
        migrations.RemoveField(
            model_name='employee',
            name='name',
        ),
        migrations.RemoveField(
            model_name='employee',
            name='password',
        ),
        migrations.RemoveField(
            model_name='employee',
            name='status',
        ),
        migrations.RemoveField(
            model_name='employee',
            name='username',
        ),
        migrations.RemoveField(
            model_name='login',
            name='username',
        ),
        migrations.RemoveField(
            model_name='payment',
            name='razorpay_order_id',
        ),
        migrations.RemoveField(
            model_name='payment',
            name='razorpay_payment_id',
        ),
        migrations.RemoveField(
            model_name='payment',
            name='refund_amount',
        ),
        migrations.RemoveField(
            model_name='payment',
            name='security_deposit',
        ),
        migrations.RemoveField(
            model_name='product',
            name='size',
        ),
        migrations.RemoveField(
            model_name='product',
            name='status',
        ),
        migrations.RemoveField(
            model_name='rental',
            name='duration_days',
        ),
        migrations.RemoveField(
            model_name='rental',
            name='product',
        ),
        migrations.RemoveField(
            model_name='rental',
            name='status',
        ),
        migrations.RemoveField(
            model_name='userprofile',
            name='email',
        ),
        migrations.RemoveField(
            model_name='userprofile',
            name='password',
        ),
        migrations.AddField(
            model_name='booking',
            name='booked_at',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AddField(
            model_name='booking',
            name='booking_address',
            field=models.TextField(default='Unknown Address'),
        ),
        migrations.AddField(
            model_name='booking',
            name='booking_name',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name='booking',
            name='booking_phone',
            field=models.CharField(blank=True, max_length=15),
        ),
        migrations.AddField(
            model_name='booking',
            name='is_active',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='booking',
            name='return_by',
            field=models.DateTimeField(default=WardrobeApp.models.default_rental_end_date),
        ),
        migrations.AddField(
            model_name='complaint',
            name='booking',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='WardrobeApp.booking'),
        ),
        migrations.AddField(
            model_name='employee',
            name='user',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='WardrobeApp.login'),
        ),
        migrations.AddField(
            model_name='login',
            name='last_login',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AddField(
            model_name='payment',
            name='security_deposit_refunded',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='product',
            name='added_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='products', to='WardrobeApp.employee'),
        ),
        migrations.AddField(
            model_name='product',
            name='is_verified',
            field=models.IntegerField(choices=[(0, 'Pending'), (1, 'Verified')], default=0),
        ),
        migrations.AddField(
            model_name='product',
            name='subcategory',
            field=models.IntegerField(choices=[(0, 'Casual'), (1, 'Formal'), (2, 'Party Wear'), (3, 'Traditional'), (4, 'Sportswear'), (5, 'Winter Wear'), (6, 'Jewelry'), (7, 'Watches'), (8, 'Bags'), (9, 'Shoes')], default=0),
        ),
        migrations.AddField(
            model_name='rental',
            name='booking',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='WardrobeApp.booking'),
        ),
        migrations.AddField(
            model_name='rental',
            name='is_active',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='profile_picture',
            field=models.ImageField(blank=True, null=True, upload_to='profile_images/'),
        ),
        migrations.AlterField(
            model_name='booking',
            name='security_deposit',
            field=models.DecimalField(decimal_places=2, default=0.0, max_digits=10),
        ),
        migrations.AlterField(
            model_name='booking',
            name='status',
            field=models.IntegerField(choices=[(0, 'Booked'), (1, 'Completed'), (2, 'Canceled')], default=0),
        ),
        migrations.AlterField(
            model_name='complaint',
            name='status',
            field=models.IntegerField(choices=[(0, 'Pending'), (1, 'Resolved'), (2, 'Rejected')], default=0),
        ),
        migrations.AlterField(
            model_name='login',
            name='email',
            field=models.EmailField(max_length=254, unique=True),
        ),
        migrations.AlterField(
            model_name='login',
            name='types',
            field=models.IntegerField(choices=[(0, 'Admin'), (1, 'User'), (2, 'Employee')], default=1),
        ),
        migrations.AlterField(
            model_name='payment',
            name='payment_method',
            field=models.IntegerField(choices=[(0, 'Credit Card'), (1, 'UPI')]),
        ),
        migrations.AlterField(
            model_name='payment',
            name='status',
            field=models.IntegerField(choices=[(0, 'Pending'), (1, 'Successful'), (2, 'Failed')], default=0),
        ),
        migrations.AlterField(
            model_name='product',
            name='availability',
            field=models.IntegerField(choices=[(0, 'Available'), (1, 'Rented'), (2, 'Returned'), (3, 'Damaged'), (4, 'Pending Approval')], default=0),
        ),
        migrations.AlterField(
            model_name='product',
            name='category',
            field=models.IntegerField(choices=[(0, 'Clothing'), (1, 'Accessories'), (2, 'Footwear')], default=0),
        ),
        migrations.AlterField(
            model_name='product',
            name='gender',
            field=models.IntegerField(choices=[(0, 'Male'), (1, 'Female'), (2, 'Unisex'), (3, 'Boys'), (4, 'Girls')], default=2),
        ),
        migrations.AlterField(
            model_name='product',
            name='stock',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='rental',
            name='return_by',
            field=models.DateTimeField(),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='phone',
            field=models.CharField(max_length=15, unique=True, validators=[django.core.validators.RegexValidator(message='Invalid phone format', regex='^\\+?1?\\d{9,15}$')]),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='status',
            field=models.IntegerField(choices=[(0, 'Active'), (1, 'Reported'), (2, 'Blocked')], default=0),
        ),
        migrations.AddField(
            model_name='chatbotquery',
            name='user',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='WardrobeApp.login'),
        ),
        migrations.AddField(
            model_name='productrecommendation',
            name='product',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='recommended_for', to='WardrobeApp.product'),
        ),
        migrations.AddField(
            model_name='productrecommendation',
            name='recommended_product',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='recommended_products', to='WardrobeApp.product'),
        ),
        migrations.AddField(
            model_name='productreview',
            name='product',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='WardrobeApp.product'),
        ),
        migrations.AddField(
            model_name='productreview',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='WardrobeApp.login'),
        ),
        migrations.AddField(
            model_name='productsize',
            name='product',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sizes', to='WardrobeApp.product'),
        ),
        migrations.AddField(
            model_name='booking',
            name='product_size',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='WardrobeApp.productsize'),
        ),
        migrations.AddField(
            model_name='rental',
            name='product_size',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='WardrobeApp.productsize'),
        ),
        migrations.AddField(
            model_name='return',
            name='booking',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='WardrobeApp.booking'),
        ),
        migrations.AddField(
            model_name='return',
            name='handled_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='WardrobeApp.employee'),
        ),
        migrations.DeleteModel(
            name='Cart',
        ),
        migrations.DeleteModel(
            name='Notification',
        ),
        migrations.DeleteModel(
            name='RentalProduct',
        ),
        migrations.DeleteModel(
            name='Review',
        ),
        migrations.DeleteModel(
            name='Wishlist',
        ),
    ]
