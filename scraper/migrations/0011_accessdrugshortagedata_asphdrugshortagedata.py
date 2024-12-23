# Generated by Django 5.0.4 on 2024-05-08 06:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scraper', '0010_potentiallead_application_number'),
    ]

    operations = [
        migrations.CreateModel(
            name='AccessDrugShortageData',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('generic_name', models.TextField()),
                ('shortage_status', models.CharField(max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name='AsphDrugShortageData',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('generic_name', models.CharField(max_length=255)),
                ('revision_date', models.DateField()),
                ('created_date', models.DateField()),
            ],
        ),
    ]