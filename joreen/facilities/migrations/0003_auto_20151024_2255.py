# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('facilities', '0002_auto_20151023_1521'),
    ]

    operations = [
        migrations.CreateModel(
            name='FacilityOperator',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', serialize=False, auto_created=True)),
                ('name', models.CharField(help_text='The company or department that operates, e.g. Corrections Corporation of America; California Department of Corrections', max_length=255)),
            ],
        ),
        migrations.AlterModelOptions(
            name='facility',
            options={'verbose_name_plural': 'facilities', 'ordering': ['state', 'name', 'general']},
        ),
        migrations.AddField(
            model_name='facility',
            name='general',
            field=models.BooleanField(help_text="Is this address a 'general mail' address for facilities with this code?", default=False),
        ),
        migrations.AlterField(
            model_name='facility',
            name='code',
            field=models.CharField(help_text="Facility code provided by facility administrator.  The more unique the better, though some DOC's have many addresses under the same code.", blank=True, max_length=255),
        ),
        migrations.AlterField(
            model_name='facilityadministrator',
            name='name',
            field=models.CharField(help_text='The incarcerating state or entity, e.g. Federal Bureau of Prisons; California', max_length=255),
        ),
    ]
