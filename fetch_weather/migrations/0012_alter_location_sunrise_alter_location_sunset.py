# Generated by Django 4.1.5 on 2023-02-12 19:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('fetch_weather', '0011_alter_location_sunrise_alter_location_sunset'),
    ]

    operations = [
        migrations.AlterField(
            model_name='location',
            name='sunrise',
            field=models.CharField(max_length=30),
        ),
        migrations.AlterField(
            model_name='location',
            name='sunset',
            field=models.CharField(max_length=30),
        ),
    ]
