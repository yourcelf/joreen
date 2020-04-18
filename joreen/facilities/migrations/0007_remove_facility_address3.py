from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("facilities", "0006_auto_20151108_2011"),
    ]

    operations = [
        migrations.RemoveField(model_name="facility", name="address3",),
    ]
