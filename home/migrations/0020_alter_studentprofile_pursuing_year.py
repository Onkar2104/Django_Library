# Generated by Django 4.2.15 on 2024-09-21 13:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0019_alter_studentprofile_pursuing_year'),
    ]

    operations = [
        migrations.AlterField(
            model_name='studentprofile',
            name='pursuing_year',
            field=models.IntegerField(default='1'),
        ),
    ]
