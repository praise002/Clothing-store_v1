# Generated by Django 5.1 on 2024-11-13 21:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('general', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='social',
            name='name',
            field=models.CharField(default='site detail', max_length=255),
            preserve_default=False,
        ),
    ]
