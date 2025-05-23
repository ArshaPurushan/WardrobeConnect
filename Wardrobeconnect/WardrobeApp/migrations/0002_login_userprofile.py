# Generated by Django 5.1.6 on 2025-03-03 15:56

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('WardrobeApp', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Login',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('username', models.CharField(default='default_user', max_length=150, unique=True)),
                ('password', models.CharField(default='defaultpassword', max_length=150)),
                ('email', models.EmailField(blank=True, max_length=150, null=True, unique=True)),
                ('types', models.CharField(choices=[('admin', 'Admin'), ('user', 'User'), ('employee', 'Employee')], default='user', max_length=50)),
                ('status', models.CharField(default='1', max_length=10)),
            ],
        ),
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=150, null=True)),
                ('address', models.CharField(max_length=255)),
                ('gender', models.CharField(choices=[('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')], max_length=10)),
                ('phone', models.CharField(max_length=15)),
                ('email', models.EmailField(max_length=150, null=True)),
                ('status', models.CharField(default='1', max_length=10)),
                ('logid', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='WardrobeApp.login')),
            ],
        ),
    ]
