# Generated by Django 5.0.4 on 2024-05-27 11:41

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('scraper', '0016_alter_fioadrugsdata_mckesson_station_number'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='NDCDrugData',
            new_name='FIOAPurchaseRecords',
        ),
    ]