from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("blackandpink", "0012_auto_20151112_2050"),
    ]

    operations = [
        migrations.AlterField(
            model_name="facilityrun",
            name="finished",
            field=models.DateTimeField(blank=True, unique=True, null=True),
        ),
        migrations.AlterField(
            model_name="updaterun",
            name="finished",
            field=models.DateTimeField(blank=True, unique=True, null=True),
        ),
    ]
