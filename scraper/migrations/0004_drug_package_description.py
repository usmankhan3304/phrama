# Generated by Django 5.0.4 on 2024-04-29 10:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scraper', '0003_alter_contract_awardee_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='drug',
            name='package_description',
            field=models.TextField(blank=True, null=True),
        ),
    ]
