from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("facilities", "0003_auto_20151024_2255"),
    ]

    operations = [
        migrations.AddField(
            model_name="facility",
            name="operator",
            field=models.ForeignKey(
                null=True, to="facilities.FacilityOperator", on_delete=models.CASCADE
            ),
        ),
    ]
