# Generated by Django 3.0.2 on 2020-01-03 22:12

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounting', '0002_auto_20200103_2056'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='accountpayable',
            name='entity',
        ),
        migrations.RemoveField(
            model_name='accountreceivables',
            name='entity',
        ),
        migrations.RemoveField(
            model_name='classificationcenter',
            name='entity',
        ),
        migrations.RemoveField(
            model_name='depositaccount',
            name='entity',
        ),
        migrations.RemoveField(
            model_name='recurrence',
            name='entity',
        ),
    ]
