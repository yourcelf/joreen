from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("stateparsers", "0003_netlocthrottle"),
    ]

    operations = [
        migrations.RemoveField(model_name="facilitynameresult", name="facility",),
    ]
