# Generated by Django 5.1 on 2024-11-13 21:59

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('general', '0002_social_name'),
    ]

    operations = [
        migrations.DeleteModel(
            name='BusinessUnit',
        ),
        migrations.DeleteModel(
            name='HappyPartner',
        ),
        migrations.RenameField(
            model_name='message',
            old_name='message',
            new_name='text',
        ),
        migrations.RenameField(
            model_name='social',
            old_name='be',
            new_name='ig',
        ),
    ]
