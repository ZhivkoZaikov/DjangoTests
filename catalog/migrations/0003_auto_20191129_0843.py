# Generated by Django 2.2 on 2019-11-29 08:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0002_language'),
    ]

    operations = [
        migrations.AlterField(
            model_name='language',
            name='name',
            field=models.CharField(help_text='Enter the book language(e.g. Spanish, English, Chinese, etc)', max_length=50, unique=True),
        ),
    ]
