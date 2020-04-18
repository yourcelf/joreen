from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("blackandpink", "0004_unknownfacility_state"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="unknownfacility",
            options={"verbose_name_plural": "Unknown Facilities"},
        ),
        migrations.AddField(
            model_name="unknownfacility",
            name="current_address_count",
            field=models.IntegerField(
                default=0,
                help_text="How many profiles are listed with this as the current address?",
            ),
            preserve_default=False,
        ),
    ]
