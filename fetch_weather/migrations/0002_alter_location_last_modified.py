# Generated by Django 4.1.5 on 2023-02-03 17:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('fetch_weather', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='location',
            name='last_modified',
            field=models.DateTimeField(auto_now=True),
        ),
    ]