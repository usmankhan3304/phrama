# Generated by Django 5.0.4 on 2024-08-13 12:49

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('scraper', '0029_stationdata_remove_foiauniquendcdata_address_and_more'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='StationData',
            new_name='FOIAStationData',
        ),
    ]
