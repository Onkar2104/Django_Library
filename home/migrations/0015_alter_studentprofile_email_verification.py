# Generated by Django 4.2.15 on 2024-12-14 18:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0014_studentprofile_email_verification'),
    ]

    operations = [
        migrations.AlterField(
            model_name='studentprofile',
            name='email_verification',
            field=models.CharField(blank=True, max_length=4),
        ),
    ]
