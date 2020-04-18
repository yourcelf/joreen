# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("blackandpink", "0014_auto_20151113_1826"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="facilityrun",
            options={"ordering": ["-started"], "get_latest_by": "finished"},
        ),
        migrations.AlterModelOptions(
            name="unknownfacility",
            options={
                "verbose_name_plural": "Unmatched zoho facilities",
                "ordering": ["-current_address_count"],
                "verbose_name": "Unmatched zoho facility",
            },
        ),
    ]
