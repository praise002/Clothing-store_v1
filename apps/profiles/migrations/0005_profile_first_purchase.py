# Generated by Django 5.1 on 2024-12-06 01:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('profiles', '0004_alter_profile_phone'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='first_purchase',
            field=models.BooleanField(default=True),
        ),
    ]