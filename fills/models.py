import reprlib

from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator, MaxLengthValidator
from django.db import models

from .utils import SnowFlake

DATA_TYPE = (
    ('string', '字符串'),
    ('number', '数值'),
    ('boolean', '布尔值')
)

DEFINE_DATA_TYPE = (
    ('string', '字符串'),
    ('dict', '字典')
)


def gen_id():
    return SnowFlake(0, 0).next_id()


# Create your models here.
class IdDateTimeBase(models.Model):
    """基础类
    包含ID生成和时间记录
    """
    id = models.BigIntegerField(primary_key=True, editable=False, default=gen_id)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('修改时间', auto_now=True)

    class Meta:
        # 对 Django 声明这是一个抽象类
        abstract = True


class FillingRequirement(IdDateTimeBase):
    username = models.CharField('用户名', max_length=255)
    remark = models.TextField('备注', blank=True)
    file_id = models.CharField('对象存储ID', max_length=255)
    original_filename = models.CharField('原始文件名', max_length=255, validators=(
        RegexValidator(regex=r'.xlsx$', message='必须为.xlsx格式的excel文件'),))
    start_line = models.PositiveIntegerField('起始行', validators=(
        MinValueValidator(1, message='起始行在1到42之间'),
        MaxValueValidator(42, message='起始行在1到42之间')))
    line_number = models.PositiveIntegerField('结束行', validators=(
        MinValueValidator(1, message='支持填充行数在1到200之间'),
        MaxValueValidator(200, message='支持填充行数在1到200之间')))

    def __str__(self):
        return f"<[{self.original_filename}] {self.start_line} of {self.line_number} line>"


class GenerateRule(IdDateTimeBase):
    rule_name = models.CharField('规则名', max_length=128)
    function_name = models.CharField('函数名', max_length=255)
    fill_order = models.PositiveIntegerField('填入顺序')
    description = models.TextField('功能描述')

    def __str__(self):
        return f"<[{self.rule_name}] {self.function_name}>"


class GenerateRuleParameter(IdDateTimeBase):
    rule = models.ForeignKey(GenerateRule, on_delete=models.CASCADE, verbose_name='关联规则')

    name = models.CharField('参数名', max_length=255)
    data_type = models.CharField('数据类型', choices=DATA_TYPE, max_length=255)
    description = models.TextField('描述')
    required = models.BooleanField('是否必填')
    default_value = models.CharField('默认值', blank=True, max_length=255)
    need_outside_data = models.BooleanField('是否需要外部数据')

    def __str__(self) -> str:
        return f'<[{self.name}] {self.data_type} {self.description}>'


class DataSet(IdDateTimeBase):
    description = models.TextField('描述')

    def __str__(self) -> str:
        return f'<[{self.__class__.__name__}] {self.description}>'


class DataSetDefine(IdDateTimeBase):
    data_set = models.ForeignKey(DataSet, on_delete=models.CASCADE, verbose_name='关联数据集')

    name = models.CharField('属性名', max_length=255)
    data_type = models.CharField('数据类型', choices=DATA_TYPE, max_length=255)

    def __str__(self) -> str:
        return f'<[{self.name}] {self.data_type}>'


class DataSetValue(IdDateTimeBase):
    data_set = models.ForeignKey(DataSet, on_delete=models.CASCADE, verbose_name='关联数据集')

    item = models.TextField('数据项')
    data_type = models.CharField('数据类型（字典或字符串）', choices=DEFINE_DATA_TYPE, max_length=255)

    def __str__(self) -> str:
        return f'<[{self.__class__.__name__}] {reprlib.repr(self.item)}>'


class DataSetBind(IdDateTimeBase):
    data_set = models.ForeignKey(DataSet, on_delete=models.CASCADE, verbose_name='关联数据集')

    column_name = models.CharField('单元格列名', max_length=8)
    data_name = models.CharField('关联属性名', max_length=255)

    def __str__(self) -> str:
        return f'<[{self.__class__.__name__}] {self.data_name} = {self.column_name}>'


class ColumnRule(IdDateTimeBase):
    requirement = models.ForeignKey(FillingRequirement, on_delete=models.CASCADE, verbose_name='关联填充要求')
    rule = models.OneToOneField(GenerateRule, on_delete=models.CASCADE, verbose_name='关联规则')

    column_name = models.CharField('单元格列', max_length=8, validators=(MaxLengthValidator(3, message='不要搞那么后面的列'),))
    column_type = models.CharField('单元格数据类型', choices=DATA_TYPE, max_length=64)
    associated_of = models.BooleanField('是否需要外部数据集', default=False)

    def __str__(self):
        return f"<[{self.column_name}] {self.column_type} - {self.rule_id}>"


class DataParameter(IdDateTimeBase):
    column_rule = models.ForeignKey(ColumnRule, on_delete=models.CASCADE, verbose_name='关联列规则')
    param_rule = models.OneToOneField(GenerateRuleParameter, on_delete=models.CASCADE, verbose_name='关联参数')

    name = models.CharField('参数名', max_length=255)
    value = models.CharField('参数值', blank=True, default=str, max_length=255)
    expressions = models.CharField('计算表达式', blank=True, max_length=512)
    data_set_id = models.BigIntegerField('关联数据集', null=True, blank=True)

    def __str__(self) -> str:
        return f'<[{self.name}] {self.value}>'
