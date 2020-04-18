from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("stateparsers", "0004_remove_facilitynameresult_facility"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="facilitynameresult",
            options={
                "verbose_name": "Facility name reported by search backend",
                "verbose_name_plural": "Facility names reported by search backends",
            },
        ),
    ]
