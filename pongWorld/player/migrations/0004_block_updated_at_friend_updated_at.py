# Generated by Django 4.2.10 on 2024-02-17 21:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('player', '0003_rename_blocked_id_block_blocked_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='block',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AddField(
            model_name='friend',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
    ]
