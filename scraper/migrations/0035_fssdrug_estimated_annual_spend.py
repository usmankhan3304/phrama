# Generated by Django 5.1 on 2024-08-22 07:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scraper', '0034_fssdrug_offers'),
    ]

    operations = [
        migrations.AddField(
            model_name='fssdrug',
            name='estimated_annual_spend',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True),
        ),
    ]
