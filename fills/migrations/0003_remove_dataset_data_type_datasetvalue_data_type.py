# Generated by Django 4.1 on 2023-07-05 17:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('fills', '0002_alter_columnrule_column_type_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='dataset',
            name='data_type',
        ),
        migrations.AddField(
            model_name='datasetvalue',
            name='data_type',
            field=models.CharField(choices=[('string', '字符串'), ('dict', '字典')], default=None, max_length=255),
            preserve_default=False,
        ),
    ]
