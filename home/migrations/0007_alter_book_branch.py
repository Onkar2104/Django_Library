# Generated by Django 4.2.15 on 2024-10-31 07:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0006_alter_book_branch'),
    ]

    operations = [
        migrations.AlterField(
            model_name='book',
            name='branch',
            field=models.CharField(choices=[('all', 'All'), ('computer', 'Computer'), ('entc', 'ENTC'), ('mech', 'Mech'), ('civil', 'Civil')], max_length=20, null=True),
        ),
    ]
