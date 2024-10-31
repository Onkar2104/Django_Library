# Generated by Django 4.2.15 on 2024-10-31 05:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0004_remove_book_fine_paid'),
    ]

    operations = [
        migrations.AddField(
            model_name='book',
            name='branch',
            field=models.CharField(choices=[('computer science', 'Computer Science'), ('entc', 'ENTC'), ('mech', 'Mech'), ('civil', 'Civil')], max_length=20, null=True),
        ),
    ]
