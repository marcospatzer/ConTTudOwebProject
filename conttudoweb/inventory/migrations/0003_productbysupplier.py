# Generated by Django 3.0.2 on 2020-01-16 20:23

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_auto_20200114_2006'),
        ('inventory', '0002_auto_20200116_1921'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProductBySupplier',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('reference', models.CharField(max_length=20, verbose_name='referência')),
                ('description', models.CharField(max_length=120, verbose_name='descrição')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='inventory.Product')),
                ('supplier', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.People')),
            ],
            options={
                'verbose_name': 'produto por fornecedor',
                'verbose_name_plural': 'produtos por fornecedor',
            },
        ),
    ]