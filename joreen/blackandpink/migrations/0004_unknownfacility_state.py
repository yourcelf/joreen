from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("blackandpink", "0003_unknownfacility_zoho_id"),
    ]

    operations = [
        migrations.AddField(
            model_name="unknownfacility",
            name="state",
            field=models.CharField(max_length=255, blank=True),
        ),
    ]
