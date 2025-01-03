# Generated by Django 5.0.4 on 2024-08-30 12:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('smart_search', '0002_alter_consolidateddrugprice_price_start_date_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='consolidateddrugdata',
            name='covered',
            field=models.BooleanField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='consolidateddrugdata',
            name='prime_vendor',
            field=models.BooleanField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='consolidateddrugdata',
            name='va_class',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
