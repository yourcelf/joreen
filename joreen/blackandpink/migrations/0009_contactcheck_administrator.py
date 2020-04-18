# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("facilities", "0005_auto_20151031_1947"),
        ("blackandpink", "0008_auto_20151105_2335"),
    ]

    operations = [
        migrations.AddField(
            model_name="contactcheck",
            name="administrator",
            field=models.ForeignKey(
                blank=True, to="facilities.FacilityAdministrator", null=True
            ),
        ),
    ]
