# Generated by Django 2.2 on 2019-12-22 13:47

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0018_auto_20191221_1310'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='author',
            unique_together={('first_name', 'last_name')},
        ),
    ]
