# Generated by Django 5.0.4 on 2024-06-03 10:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scraper', '0023_alter_contract_awardee_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='accessdrugshortagedata',
            name='generic_name',
            field=models.CharField(blank=True, max_length=500, null=True),
        ),
        migrations.AlterField(
            model_name='doddrugdata',
            name='description',
            field=models.TextField(max_length=500),
        ),
    ]