# Generated by Django 2.2 on 2019-12-21 13:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0016_genre_view_count'),
    ]

    operations = [
        migrations.AddField(
            model_name='language',
            name='view_count',
            field=models.IntegerField(default=0, verbose_name='View Count'),
        ),
    ]