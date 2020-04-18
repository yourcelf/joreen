# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import localflavor.us.models


class Migration(migrations.Migration):

    dependencies = [
        ("facilities", "0004_facility_operator"),
    ]

    operations = [
        migrations.AlterField(
            model_name="facility",
            name="state",
            field=localflavor.us.models.USPostalCodeField(
                choices=[
                    ("AL", "Alabama"),
                    ("AK", "Alaska"),
                    ("AS", "American Samoa"),
                    ("AZ", "Arizona"),
                    ("AR", "Arkansas"),
                    ("AA", "Armed Forces Americas"),
                    ("AE", "Armed Forces Europe"),
                    ("AP", "Armed Forces Pacific"),
                    ("CA", "California"),
                    ("CO", "Colorado"),
                    ("CT", "Connecticut"),
                    ("DE", "Delaware"),
                    ("DC", "District of Columbia"),
                    ("FM", "Federated States of Micronesia"),
                    ("FL", "Florida"),
                    ("GA", "Georgia"),
                    ("GU", "Guam"),
                    ("HI", "Hawaii"),
                    ("ID", "Idaho"),
                    ("IL", "Illinois"),
                    ("IN", "Indiana"),
                    ("IA", "Iowa"),
                    ("KS", "Kansas"),
                    ("KY", "Kentucky"),
                    ("LA", "Louisiana"),
                    ("ME", "Maine"),
                    ("MH", "Marshall Islands"),
                    ("MD", "Maryland"),
                    ("MA", "Massachusetts"),
                    ("MI", "Michigan"),
                    ("MN", "Minnesota"),
                    ("MS", "Mississippi"),
                    ("MO", "Missouri"),
                    ("MT", "Montana"),
                    ("NE", "Nebraska"),
                    ("NV", "Nevada"),
                    ("NH", "New Hampshire"),
                    ("NJ", "New Jersey"),
                    ("NM", "New Mexico"),
                    ("NY", "New York"),
                    ("NC", "North Carolina"),
                    ("ND", "North Dakota"),
                    ("MP", "Northern Mariana Islands"),
                    ("OH", "Ohio"),
                    ("OK", "Oklahoma"),
                    ("OR", "Oregon"),
                    ("PW", "Palau"),
                    ("PA", "Pennsylvania"),
                    ("PR", "Puerto Rico"),
                    ("RI", "Rhode Island"),
                    ("SC", "South Carolina"),
                    ("SD", "South Dakota"),
                    ("TN", "Tennessee"),
                    ("TX", "Texas"),
                    ("UT", "Utah"),
                    ("VT", "Vermont"),
                    ("VI", "Virgin Islands"),
                    ("VA", "Virginia"),
                    ("WA", "Washington"),
                    ("WV", "West Virginia"),
                    ("WI", "Wisconsin"),
                    ("WY", "Wyoming"),
                ],
                max_length=2,
            ),
        ),
        migrations.AlterField(
            model_name="facility",
            name="zip",
            field=localflavor.us.models.USZipCodeField(max_length=10),
        ),
    ]
