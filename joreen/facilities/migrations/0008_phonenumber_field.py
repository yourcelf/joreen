# Generated by Django 2.2.12 on 2020-04-18 16:16

from django.db import migrations
import phonenumber_field.modelfields


class Migration(migrations.Migration):

    dependencies = [
        ("facilities", "0007_remove_facility_address3"),
    ]

    operations = [
        migrations.AlterField(
            model_name="facility",
            name="phone",
            field=phonenumber_field.modelfields.PhoneNumberField(
                blank=True, max_length=255, region=None
            ),
        ),
    ]
