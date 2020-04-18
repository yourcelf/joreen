# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("stateparsers", "0005_auto_20151112_2046"),
    ]

    operations = [
        migrations.AlterField(
            model_name="facilitynameresult",
            name="facility_url",
            field=models.TextField(
                help_text="URL to the facility in question if provided by search site",
                blank=True,
            ),
        ),
    ]
