from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("facilities", "0005_auto_20151031_1947"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="facility",
            options={
                "ordering": ["state", "name", "-general", "address1"],
                "verbose_name_plural": "facilities",
            },
        ),
    ]
