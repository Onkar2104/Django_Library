# Generated by Django 4.2.15 on 2024-10-06 07:06

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0003_studentprofile_gender'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='book',
            name='fine_paid',
        ),
    ]
