# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("stateparsers", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="facilitynameresult",
            name="facility",
            field=models.ForeignKey(
                help_text="Set to manually associate a string with a facility, preempting other ways to guess at the identity of this facility.",
                null=True,
                blank=True,
                to="facilities.Facility",
            ),
        ),
    ]
