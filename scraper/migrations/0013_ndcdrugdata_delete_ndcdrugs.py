# Generated by Django 5.0.4 on 2024-05-23 09:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scraper', '0012_asphdrugshortagedata_shortage_status_ndcdrugs'),
    ]

    operations = [
        migrations.CreateModel(
            name='NDCDrugData',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ndc_code', models.CharField(max_length=20, unique=True)),
                ('description', models.CharField(max_length=255)),
                ('total_quantity_purchased', models.IntegerField()),
                ('total_publishable_dollars_spent', models.DecimalField(decimal_places=2, max_digits=10)),
            ],
            options={
                'verbose_name': 'Drug Data',
                'verbose_name_plural': 'Drug Data',
            },
        ),
        migrations.DeleteModel(
            name='NDCDrugs',
        ),
    ]
