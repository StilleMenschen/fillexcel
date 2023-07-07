# Generated by Django 4.1 on 2023-07-07 23:12

import django.core.validators
import django.db.models.deletion
from django.db import migrations, models

import fills.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='ColumnRule',
            fields=[
                ('id', models.BigIntegerField(default=fills.models.gen_id, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='修改时间')),
                ('column_name', models.CharField(max_length=8, validators=[django.core.validators.MaxLengthValidator(3, message='不要搞那么后面的列')], verbose_name='单元格列')),
                ('column_type', models.CharField(choices=[('string', '字符串'), ('number', '数值'), ('boolean', '布尔值')], max_length=64, verbose_name='单元格数据类型')),
                ('associated_of', models.BooleanField(default=False, verbose_name='是否需要外部数据集')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='DataSet',
            fields=[
                ('id', models.BigIntegerField(default=fills.models.gen_id, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='修改时间')),
                ('description', models.TextField(verbose_name='描述')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='FillingRequirement',
            fields=[
                ('id', models.BigIntegerField(default=fills.models.gen_id, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='修改时间')),
                ('username', models.CharField(max_length=255, verbose_name='用户名')),
                ('remark', models.TextField(blank=True, verbose_name='备注')),
                ('file_id', models.CharField(max_length=255, verbose_name='对象存储ID')),
                ('original_filename', models.CharField(max_length=255, validators=[django.core.validators.RegexValidator(message='必须为.xlsx格式的excel文件', regex='.xlsx$')], verbose_name='原始文件名')),
                ('start_line', models.PositiveIntegerField(validators=[django.core.validators.MinValueValidator(1, message='起始行在1到42之间'), django.core.validators.MaxValueValidator(42, message='起始行在1到42之间')], verbose_name='起始行')),
                ('line_number', models.PositiveIntegerField(validators=[django.core.validators.MinValueValidator(1, message='支持填充行数在1到200之间'), django.core.validators.MaxValueValidator(200, message='支持填充行数在1到200之间')], verbose_name='结束行')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='GenerateRule',
            fields=[
                ('id', models.BigIntegerField(default=fills.models.gen_id, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='修改时间')),
                ('rule_name', models.CharField(max_length=128, verbose_name='规则名')),
                ('function_name', models.CharField(max_length=255, verbose_name='函数名')),
                ('fill_order', models.PositiveIntegerField(verbose_name='填入顺序')),
                ('description', models.TextField(verbose_name='功能描述')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='GenerateRuleParameter',
            fields=[
                ('id', models.BigIntegerField(default=fills.models.gen_id, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='修改时间')),
                ('name', models.CharField(max_length=255, verbose_name='参数名')),
                ('data_type', models.CharField(choices=[('string', '字符串'), ('number', '数值'), ('boolean', '布尔值')], max_length=255, verbose_name='数据类型')),
                ('description', models.TextField(verbose_name='描述')),
                ('required', models.BooleanField(verbose_name='是否必填')),
                ('default_value', models.CharField(blank=True, max_length=255, verbose_name='默认值')),
                ('need_outside_data', models.BooleanField(verbose_name='是否需要外部数据')),
                ('rule', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='fills.generaterule', verbose_name='关联规则')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='DataSetValue',
            fields=[
                ('id', models.BigIntegerField(default=fills.models.gen_id, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='修改时间')),
                ('item', models.TextField(verbose_name='数据项')),
                ('data_type', models.CharField(choices=[('string', '字符串'), ('dict', '字典')], max_length=255, verbose_name='数据类型（字典或字符串）')),
                ('data_set', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='fills.dataset', verbose_name='关联数据集')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='DataSetDefine',
            fields=[
                ('id', models.BigIntegerField(default=fills.models.gen_id, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='修改时间')),
                ('name', models.CharField(max_length=255, verbose_name='属性名')),
                ('data_type', models.CharField(choices=[('string', '字符串'), ('number', '数值'), ('boolean', '布尔值')], max_length=255, verbose_name='数据类型')),
                ('data_set', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='fills.dataset', verbose_name='关联数据集')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='DataSetBind',
            fields=[
                ('id', models.BigIntegerField(default=fills.models.gen_id, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='修改时间')),
                ('column_name', models.CharField(max_length=8, verbose_name='单元格列名')),
                ('data_name', models.CharField(max_length=255, verbose_name='关联属性名')),
                ('data_set', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='fills.dataset', verbose_name='关联数据集')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='DataParameter',
            fields=[
                ('id', models.BigIntegerField(default=fills.models.gen_id, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='修改时间')),
                ('name', models.CharField(max_length=255, verbose_name='参数名')),
                ('value', models.CharField(blank=True, default=str, max_length=255, verbose_name='参数值')),
                ('expressions', models.CharField(blank=True, max_length=512, verbose_name='计算表达式')),
                ('data_set_id', models.BigIntegerField(blank=True, null=True, verbose_name='关联数据集')),
                ('column_rule', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='fills.columnrule', verbose_name='关联列规则')),
                ('param_rule', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='fills.generateruleparameter', verbose_name='关联参数')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='columnrule',
            name='requirement',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='fills.fillingrequirement', verbose_name='关联填充要求'),
        ),
        migrations.AddField(
            model_name='columnrule',
            name='rule',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='fills.generaterule', verbose_name='关联规则'),
        ),
    ]
