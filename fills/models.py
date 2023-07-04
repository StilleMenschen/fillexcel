import reprlib

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator

from .utils import SnowFlake

DATA_TYPE = (
    ('string', '字符串'),
    ('number', '数值'),
    ('boolean', '布尔值')
)


def gen_id():
    return SnowFlake(0, 0).next_id()


# Create your models here.
class IdDateTimeBase(models.Model):
    """基础类
    包含ID生成和时间记录
    """
    id = models.BigIntegerField(primary_key=True, editable=False, default=gen_id)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        # 对 Django 声明这是一个抽象类
        abstract = True


class FillingRequirement(IdDateTimeBase):
    username = models.CharField(max_length=255)
    remark = models.TextField(blank=True)
    file_id = models.CharField(max_length=255)
    original_filename = models.CharField(max_length=255, validators=(
        RegexValidator(regex=r'.xlsx$', message='必须为.xlsx格式的excel文件'),))
    start_line = models.PositiveIntegerField(validators=(
        MinValueValidator(1, message='起始行在1到42之间'),
        MaxValueValidator(42, message='起始行在1到42之间')))
    line_number = models.PositiveIntegerField(validators=(
        MinValueValidator(1, message='支持填充行数在1到200之间'),
        MaxValueValidator(200, message='支持填充行数在1到200之间')))

    class Meta:
        ordering = ['-id']

    def __str__(self):
        return f"<[{self.original_filename}] {self.start_line} of {self.line_number} line>"


class GenerateRule(IdDateTimeBase):
    rule_name = models.CharField(max_length=128)
    function_name = models.CharField(max_length=255)
    fill_order = models.PositiveIntegerField()
    description = models.TextField()

    def __str__(self):
        return f"<[{self.rule_name}] {self.function_name}>"


class GenerateRuleParameter(IdDateTimeBase):
    # 规则
    rule = models.ForeignKey(GenerateRule, on_delete=models.CASCADE)

    name = models.CharField(max_length=255)
    data_type = models.CharField(choices=DATA_TYPE, max_length=255)
    description = models.TextField()
    required = models.BooleanField()
    default_value = models.CharField(blank=True, max_length=255)
    need_outside_data = models.BooleanField()

    def __str__(self) -> str:
        return f'<[{self.name}] {self.data_type} {self.description}>'


class DataSet(IdDateTimeBase):
    description = models.TextField()
    data_type = models.CharField(max_length=255)

    def __str__(self) -> str:
        return f'<[{self.description}] {self.data_type}>'


class DataSetDefine(IdDateTimeBase):
    # 数据集主表
    data_set = models.ForeignKey(DataSet, on_delete=models.CASCADE)

    name = models.CharField(max_length=255)
    data_type = models.CharField(choices=DATA_TYPE, max_length=255)

    def __str__(self) -> str:
        return f'<[{self.name}] {self.data_type}>'


class DataSetValue(IdDateTimeBase):
    # 数据集主表
    data_set = models.ForeignKey(DataSet, on_delete=models.CASCADE)

    item = models.TextField()

    def __str__(self) -> str:
        return f'<[{self.__class__.__name__}] {reprlib.repr(self.item)}>'


class DataSetBind(IdDateTimeBase):
    # 数据集主表
    data_set = models.ForeignKey(DataSet, on_delete=models.CASCADE)

    column_name = models.CharField(max_length=255)
    data_name = models.CharField(max_length=255)

    def __str__(self) -> str:
        return f'<[{self.__class__.__name__}] {self.data_name} = {self.column_name}>'


class ColumnRule(IdDateTimeBase):
    # 填充要求
    requirement = models.ForeignKey(FillingRequirement, on_delete=models.CASCADE)
    # 规则
    rule = models.ForeignKey(GenerateRule, on_delete=models.CASCADE)

    column_name = models.CharField(max_length=255)
    column_type = models.CharField(choices=DATA_TYPE, max_length=128)
    associated_of = models.BooleanField(default=False)

    def __str__(self):
        return f"<[{self.column_name}] {self.column_type} - {self.rule_id}>"


class DataParameter(IdDateTimeBase):
    # 列规则
    column_rule = models.ForeignKey(ColumnRule, on_delete=models.CASCADE)
    # 规则
    param_rule = models.ForeignKey(GenerateRuleParameter, on_delete=models.CASCADE)

    name = models.CharField(max_length=255)
    value = models.CharField(blank=True, default=str, max_length=255)
    expressions = models.CharField(blank=True, max_length=512)
    data_set_id = models.BigIntegerField(null=True, blank=True)

    def __str__(self) -> str:
        return f'<[{self.name}] {self.value}>'
