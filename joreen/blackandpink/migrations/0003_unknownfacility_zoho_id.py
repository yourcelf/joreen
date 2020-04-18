from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("blackandpink", "0002_unknownfacility_unknownfacilitymatch"),
    ]

    operations = [
        migrations.AddField(
            model_name="unknownfacility",
            name="zoho_id",
            field=models.CharField(default=None, unique=True, max_length=255),
            preserve_default=False,
        ),
    ]
