# Generated by Django 5.0.4 on 2024-08-23 16:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scraper', '0037_remove_fssdrug_number_of_bidders'),
    ]

    operations = [
        migrations.AddField(
            model_name='manufacturer',
            name='address',
            field=models.CharField(blank=True, max_length=500, null=True),
        ),
    ]
