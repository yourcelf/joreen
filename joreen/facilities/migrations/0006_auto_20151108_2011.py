# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('facilities', '0005_auto_20151031_1947'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='facility',
            options={'ordering': ['state', 'name', '-general', 'address1'], 'verbose_name_plural': 'facilities'},
        ),
    ]
