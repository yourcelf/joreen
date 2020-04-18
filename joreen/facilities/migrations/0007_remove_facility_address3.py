# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('facilities', '0006_auto_20151108_2011'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='facility',
            name='address3',
        ),
    ]
