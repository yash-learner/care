# Generated by Django 5.1.1 on 2024-12-02 13:04

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('emr', '0010_observation_parent'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='observation',
            name='encounter',
        ),
    ]
