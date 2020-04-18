# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("facilities", "0005_auto_20151031_1947"),
        ("blackandpink", "0007_auto_20151105_2236"),
    ]

    operations = [
        migrations.AddField(
            model_name="contactcheck",
            name="facility",
            field=models.ForeignKey(
                null=True,
                to="facilities.Facility",
                blank=True,
                on_delete=models.CASCADE,
            ),
        ),
        migrations.AlterField(
            model_name="contactcheck",
            name="status",
            field=models.CharField(
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
                ],
                max_length=255,
            ),
        ),
    ]
