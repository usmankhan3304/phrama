# Generated by Django 5.0.4 on 2024-05-23 12:49

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scraper', '0014_alter_ndcdrugdata_total_publishable_dollars_spent'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='ndcdrugdata',
            options={'verbose_name': 'NDC Drug Data', 'verbose_name_plural': 'NDC Drug Data'},
        ),
        migrations.AlterField(
            model_name='ndcdrugdata',
            name='total_publishable_dollars_spent',
            field=models.DecimalField(decimal_places=2, default=0.0, max_digits=15),
        ),
        migrations.AlterField(
            model_name='ndcdrugdata',
            name='total_quantity_purchased',
            field=models.IntegerField(default=0),
        ),
        migrations.CreateModel(
            name='FIOADrugsData',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('mckesson_station_number', models.IntegerField()),
                ('quantity_purchased', models.IntegerField()),
                ('publishable_dollars_spent', models.DecimalField(decimal_places=2, max_digits=15)),
                ('ndc_code', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='purchase_records', to='scraper.ndcdrugdata')),
            ],
            options={
                'verbose_name': 'FOIA Drugs Data',
                'verbose_name_plural': 'FOIA Drugs Data',
            },
        ),
    ]