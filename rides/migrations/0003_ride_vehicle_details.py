# Generated by Django 5.1.5 on 2025-01-28 14:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rides', '0002_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='ride',
            name='vehicle_details',
            field=models.CharField(default='NULL', max_length=255),
            preserve_default=False,
        ),
    ]
