# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import jsonfield.fields


class Migration(migrations.Migration):

    dependencies = [
        ("blackandpink", "0009_contactcheck_administrator"),
    ]

    operations = [
        migrations.AddField(
            model_name="updaterun",
            name="errors",
            field=jsonfield.fields.JSONField(default=[]),
            preserve_default=False,
        ),
    ]
