# Generated by Django 4.2.15 on 2024-12-14 18:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0013_alter_readonline_book_pdf'),
    ]

    operations = [
        migrations.AddField(
            model_name='studentprofile',
            name='email_verification',
            field=models.CharField(default=1111, max_length=4),
            preserve_default=False,
        ),
    ]
