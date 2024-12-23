# Generated by Django 5.0.4 on 2024-08-13 12:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scraper', '0028_foiauniquendcdata_address_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='StationData',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('station_id', models.CharField(max_length=20, unique=True)),
                ('facility_name', models.CharField(max_length=255)),
                ('address', models.TextField()),
                ('state', models.CharField(max_length=2)),
                ('phone', models.CharField(max_length=15)),
            ],
        ),
        migrations.RemoveField(
            model_name='foiauniquendcdata',
            name='address',
        ),
        migrations.RemoveField(
            model_name='foiauniquendcdata',
            name='facility_name',
        ),
    ]
