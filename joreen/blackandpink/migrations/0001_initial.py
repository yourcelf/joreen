from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="ContactCheck",
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
                ("raw_facility_name", models.CharField(max_length=255, blank=True)),
                ("entry_before", models.TextField()),
                ("entry_after", models.TextField()),
                ("search_result", models.TextField()),
                ("entry_changed", models.BooleanField(default=False)),
                (
                    "status",
                    models.CharField(
                        max_length=255,
                        choices=[
                            ("ok", "Address OK"),
                            ("not found", "Not Found"),
                            ("unknown facility", "Unknowon Facility"),
                            ("seemingly released", "Seemingly Released"),
                        ],
                    ),
                ),
                ("created", models.DateTimeField(auto_now_add=True)),
            ],
            options={"get_latest_by": "created", "ordering": ["-created"]},
        ),
        migrations.CreateModel(
            name="MemberProfile",
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
                ("bp_member_number", models.IntegerField()),
                ("zoho_url", models.CharField(max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name="UpdateRun",
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
                ("started", models.DateTimeField()),
                ("finished", models.DateTimeField()),
            ],
        ),
        migrations.AddField(
            model_name="contactcheck",
            name="member",
            field=models.ForeignKey(
                to="blackandpink.MemberProfile", on_delete=models.CASCADE
            ),
        ),
        migrations.AddField(
            model_name="contactcheck",
            name="update_run",
            field=models.ForeignKey(
                to="blackandpink.UpdateRun", on_delete=models.CASCADE
            ),
        ),
    ]
