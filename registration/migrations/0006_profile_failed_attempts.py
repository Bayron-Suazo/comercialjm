# Generated by Django 5.1.2 on 2025-05-14 21:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('registration', '0005_remove_profile_is_active'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='failed_attempts',
            field=models.IntegerField(default=0),
        ),
    ]
