# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("stateparsers", "0002_auto_20151029_1556"),
    ]

    operations = [
        migrations.CreateModel(
            name="NetlocThrottle",
            fields=[
                (
                    "id",
                    models.AutoField(
                        primary_key=True,
                        auto_created=True,
                        verbose_name="ID",
                        serialize=False,
                    ),
                ),
                ("netloc", models.CharField(unique=True, max_length=255)),
                ("wait_until", models.IntegerField()),
            ],
        ),
    ]
