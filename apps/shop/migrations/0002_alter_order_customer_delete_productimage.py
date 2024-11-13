# Generated by Django 5.1 on 2024-11-13 21:59

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('profiles', '0002_alter_profile_phone_alter_profile_shipping_address'),
        ('shop', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='customer',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='orders', to='profiles.profile'),
        ),
        migrations.DeleteModel(
            name='ProductImage',
        ),
    ]
