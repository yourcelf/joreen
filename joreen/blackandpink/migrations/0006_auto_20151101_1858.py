# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blackandpink', '0005_auto_20151101_1818'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='unknownfacility',
            name='address_invalid',
        ),
        migrations.AddField(
            model_name='unknownfacility',
            name='address_valid',
            field=models.BooleanField(default=True),
        ),
        migrations.AlterField(
            model_name='unknownfacility',
            name='flat_address',
            field=models.TextField(verbose_name='Unmatched address'),
        ),
    ]
