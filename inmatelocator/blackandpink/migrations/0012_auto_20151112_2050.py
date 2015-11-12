# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blackandpink', '0011_auto_20151112_2046'),
    ]

    operations = [
        migrations.AlterField(
            model_name='facilityrun',
            name='finished',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
