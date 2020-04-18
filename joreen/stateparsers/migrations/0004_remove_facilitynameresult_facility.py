# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("stateparsers", "0003_netlocthrottle"),
    ]

    operations = [
        migrations.RemoveField(model_name="facilitynameresult", name="facility",),
    ]
