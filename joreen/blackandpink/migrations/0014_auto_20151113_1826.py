from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("blackandpink", "0013_auto_20151112_2100"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="facilityrun", options={"ordering": ["-started"]},
        ),
        migrations.AlterModelOptions(
            name="unknownfacility",
            options={
                "ordering": ["-current_address_count"],
                "verbose_name_plural": "Unmatched zoho facilities",
                "verbose_name": "Unmatched zoho facilities",
            },
        ),
        migrations.AlterModelOptions(
            name="updaterun", options={"ordering": ["-started"]},
        ),
        migrations.AddField(
            model_name="updaterun",
            name="total_count",
            field=models.IntegerField(default=0),
            preserve_default=False,
        ),
    ]
