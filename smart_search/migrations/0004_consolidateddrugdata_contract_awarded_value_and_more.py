# Generated by Django 5.0.4 on 2024-09-03 14:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('smart_search', '0003_consolidateddrugdata_covered_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='consolidateddrugdata',
            name='contract_awarded_value',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True),
        ),
        migrations.AddField(
            model_name='consolidateddrugdata',
            name='contract_awardee',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='consolidateddrugdata',
            name='contract_estimated_annual_quantities',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='consolidateddrugdata',
            name='contract_start_date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='consolidateddrugdata',
            name='contract_stop_date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='consolidateddrugdata',
            name='manufactured_by_address',
            field=models.CharField(blank=True, max_length=500, null=True),
        ),
    ]
