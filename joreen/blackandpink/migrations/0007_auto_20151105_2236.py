# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("blackandpink", "0006_auto_20151101_1858"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="unknownfacility",
            options={
                "verbose_name_plural": "Unknown Facilities",
                "ordering": ["-current_address_count"],
            },
        ),
        migrations.AlterModelOptions(
            name="unknownfacilitymatch", options={"ordering": ["-score"]},
        ),
        migrations.RemoveField(model_name="memberprofile", name="zoho_url",),
        migrations.RemoveField(model_name="unknownfacility", name="zoho_url",),
        migrations.AlterField(
            model_name="contactcheck",
            name="status",
            field=models.CharField(
                max_length=255,
                choices=[
                    ("Not Found", "Not Found"),
                    (
                        "Found search result, but facility unknown",
                        "Found search result, but facility unknown",
                    ),
                    (
                        "Found, facility matches zoho's",
                        "Found, facility matches zoho's",
                    ),
                    (
                        "Found, facility differs, zoho has facility",
                        "Found, facility differs, zoho has facility",
                    ),
                    (
                        "Found, facility differs, zoho lacks facility",
                        "Found, facility differs, zoho lacks facility",
                    ),
                ],
            ),
        ),
        migrations.AlterField(
            model_name="updaterun",
            name="finished",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="updaterun",
            name="started",
            field=models.DateTimeField(auto_now_add=True),
        ),
    ]
