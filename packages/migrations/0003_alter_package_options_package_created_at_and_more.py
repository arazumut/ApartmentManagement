# Generated by Django 5.2.1 on 2025-07-07 15:11

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('packages', '0002_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='package',
            options={'ordering': ['-created_at'], 'verbose_name': 'Package', 'verbose_name_plural': 'Packages'},
        ),
        migrations.AddField(
            model_name='package',
            name='created_at',
            field=models.DateTimeField(default=django.utils.timezone.now, verbose_name='created at'),
        ),
        migrations.AddField(
            model_name='package',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, verbose_name='updated at'),
        ),
    ]
