# Generated by Django 4.2.15 on 2024-10-01 00:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='book',
            name='fine_paid',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='borrow',
            name='borrowed_date',
            field=models.DateTimeField(),
        ),
    ]
