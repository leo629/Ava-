# Generated by Django 5.1.7 on 2025-03-24 03:57

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0002_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='message',
            old_name='content',
            new_name='message',
        ),
    ]
