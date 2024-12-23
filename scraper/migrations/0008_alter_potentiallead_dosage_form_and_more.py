# Generated by Django 5.0.4 on 2024-05-07 11:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scraper', '0007_remove_potentiallead_drug'),
    ]

    operations = [
        migrations.AlterField(
            model_name='potentiallead',
            name='dosage_form',
            field=models.CharField(blank=True, max_length=80, null=True),
        ),
        migrations.AlterField(
            model_name='potentiallead',
            name='route',
            field=models.CharField(blank=True, max_length=80, null=True),
        ),
        migrations.AlterField(
            model_name='potentiallead',
            name='strength',
            field=models.CharField(blank=True, max_length=80, null=True),
        ),
    ]
