# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blackandpink', '0015_auto_20151203_1606'),
    ]

    operations = [
        migrations.AddField(
            model_name='memberprofile',
            name='zoho_id',
            field=models.CharField(default='', max_length=255),
        ),
    ]
