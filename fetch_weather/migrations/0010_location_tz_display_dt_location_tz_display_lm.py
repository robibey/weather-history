# Generated by Django 4.1.5 on 2023-02-12 19:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('fetch_weather', '0009_alter_location_unique_together'),
    ]

    operations = [
        migrations.AddField(
            model_name='location',
            name='tz_display_dt',
            field=models.CharField(default='test', max_length=30),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='location',
            name='tz_display_lm',
            field=models.CharField(default='test', max_length=30),
            preserve_default=False,
        ),
    ]
