# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("facilities", "0004_facility_operator"),
    ]

    operations = [
        migrations.CreateModel(
            name="FacilityNameResult",
            fields=[
                (
                    "id",
                    models.AutoField(
                        verbose_name="ID",
                        primary_key=True,
                        auto_created=True,
                        serialize=False,
                    ),
                ),
                ("name", models.CharField(max_length=255)),
                (
                    "facility_url",
                    models.CharField(
                        help_text="URL to the facility in question if provided by search site",
                        max_length=255,
                        blank=True,
                    ),
                ),
                ("created", models.DateTimeField(auto_now_add=True)),
                (
                    "administrator",
                    models.ForeignKey(
                        to="facilities.FacilityAdministrator", on_delete=models.CASCADE
                    ),
                ),
                (
                    "facility",
                    models.ForeignKey(
                        to="facilities.Facility",
                        null=True,
                        blank=True,
                        on_delete=models.CASCADE,
                    ),
                ),
            ],
        ),
    ]
