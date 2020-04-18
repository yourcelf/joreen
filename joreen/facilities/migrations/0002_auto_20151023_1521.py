# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("facilities", "0001_initial"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="facility", options={"verbose_name_plural": "facilities"},
        ),
        migrations.AlterField(
            model_name="facility",
            name="code",
            field=models.CharField(
                max_length=255,
                blank=True,
                help_text="Facility code provided by facility administrator. Should be unique per department of corrections.",
            ),
        ),
        migrations.AlterField(
            model_name="facility",
            name="provenance",
            field=models.CharField(max_length=255, verbose_name="data source"),
        ),
        migrations.AlterField(
            model_name="facility",
            name="provenance_url",
            field=models.CharField(max_length=255, verbose_name="data source URL"),
        ),
    ]
