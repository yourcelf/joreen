# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("stateparsers", "0004_remove_facilitynameresult_facility"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="facilitynameresult",
            options={
                "verbose_name": "Facility name reported by search backend",
                "verbose_name_plural": "Facility names reported by search backends",
            },
        ),
    ]
