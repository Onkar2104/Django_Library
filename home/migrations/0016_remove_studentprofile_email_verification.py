# Generated by Django 4.2.15 on 2024-12-14 19:21

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0015_alter_studentprofile_email_verification'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='studentprofile',
            name='email_verification',
        ),
    ]
