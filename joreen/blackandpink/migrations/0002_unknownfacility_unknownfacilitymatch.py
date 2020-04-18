from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("facilities", "0005_auto_20151031_1947"),
        ("blackandpink", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="UnknownFacility",
            fields=[
                (
                    "id",
                    models.AutoField(
                        primary_key=True,
                        verbose_name="ID",
                        auto_created=True,
                        serialize=False,
                    ),
                ),
                ("flat_address", models.TextField()),
                ("zoho_url", models.URLField()),
                ("address_invalid", models.BooleanField(default=False)),
                ("comment", models.TextField(blank=True)),
                ("created", models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name="UnknownFacilityMatch",
            fields=[
                (
                    "id",
                    models.AutoField(
                        primary_key=True,
                        verbose_name="ID",
                        auto_created=True,
                        serialize=False,
                    ),
                ),
                ("score", models.IntegerField()),
                ("breakdown", models.TextField()),
                (
                    "match",
                    models.ForeignKey(
                        to="facilities.Facility", on_delete=models.CASCADE
                    ),
                ),
                (
                    "unknown_facility",
                    models.ForeignKey(
                        to="blackandpink.UnknownFacility", on_delete=models.CASCADE
                    ),
                ),
            ],
        ),
    ]
