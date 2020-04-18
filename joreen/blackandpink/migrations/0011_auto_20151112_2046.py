# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("blackandpink", "0010_updaterun_errors"),
    ]

    operations = [
        migrations.CreateModel(
            name="FacilityRun",
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
                ("started", models.DateTimeField(auto_now_add=True)),
                ("finished", models.DateTimeField()),
            ],
        ),
        migrations.AlterModelOptions(
            name="contactcheck",
            options={
                "verbose_name": "Member address check",
                "verbose_name_plural": "Member address checks",
                "ordering": ["-created"],
                "get_latest_by": "created",
            },
        ),
        migrations.AlterModelOptions(
            name="unknownfacility",
            options={
                "verbose_name": "Unmatched Black and Pink Facility",
                "verbose_name_plural": "Unknown Black and Pink Facilities",
                "ordering": ["-current_address_count"],
            },
        ),
        migrations.AlterModelOptions(
            name="unknownfacilitymatch",
            options={
                "verbose_name": "Rejected facility match",
                "verbose_name_plural": "Rejected facility matches",
                "ordering": ["-score"],
            },
        ),
        migrations.AlterField(
            model_name="contactcheck",
            name="status",
            field=models.CharField(
                max_length=255,
                choices=[
                    ("not_found", "Not Found"),
                    (
                        "found_unknown_facility",
                        "Found search result, but facility unknown",
                    ),
                    ("found_facility_matches", "Found, facility matches zoho's"),
                    (
                        "found_facility_differs_zoho_has",
                        "Found, facility differs, zoho has facility",
                    ),
                    (
                        "found_facility_differs_zoho_lacks",
                        "Found, facility differs, zoho lacks facility",
                    ),
                    ("found_released_zoho_agrees", "Found, released, zoho agrees"),
                    (
                        "found_released_zoho_disagrees",
                        "Found, released, zoho disagrees",
                    ),
                ],
            ),
        ),
    ]
