import reprlib

from django.core.cache import cache
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator
from django.db import models
from django.db.models import UniqueConstraint

from .timeunit import dc
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
    file_id = models.CharField('对象存储ID', unique=True, max_length=255)
    original_filename = models.CharField('原始文件名', max_length=255, validators=(
        RegexValidator(regex=r'.xlsx$', message='必须为.xlsx格式的excel文件'),))
    start_line = models.PositiveIntegerField('起始行', validators=(
        MinValueValidator(1, message='起始行在1到42之间'),
        MaxValueValidator(42, message='起始行在1到42之间')))
    line_number = models.PositiveIntegerField('结束行', validators=(
        MinValueValidator(1, message='支持填充行数在1到200之间'),
        MaxValueValidator(200, message='支持填充行数在1到200之间')))

    class Meta:
        db_table = 'filling_requirement'
        verbose_name = '填充要求'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f"<[{self.original_filename}] {self.start_line} of {self.line_number} line>"


class GenerateRule(IdDateTimeBase):
    rule_name = models.CharField('规则名', unique=True, max_length=128)
    function_name = models.CharField('函数名', unique=True, max_length=255)
    fill_order = models.PositiveIntegerField('填入顺序')
    description = models.TextField('功能描述')

    @classmethod
    def get_with_cache(cls, pk):
        cache_key = f'GenerateRule:{pk}'
        obj = cache.get(cache_key)
        if not obj:
            obj = cls.objects.get(pk=pk)
            # 4 小时缓存数
            cache.set(cache_key, obj, dc.hours.to_seconds(4))
        return obj

    class Meta:
        db_table = 'generate_rule'
        verbose_name = '生成规则'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f"<[{self.rule_name}] {self.function_name}>"


class GenerateRuleParameter(IdDateTimeBase):
    rule = models.ForeignKey(GenerateRule, on_delete=models.CASCADE, verbose_name='关联规则')

    name = models.CharField('参数名', max_length=255)
    data_type = models.CharField('数据类型', choices=DATA_TYPE, max_length=255)
    description = models.CharField('描述', max_length=512)
    hints = models.CharField('输入提示', blank=True, max_length=512)
    required = models.BooleanField('是否必填')
    default_value = models.CharField('默认值', blank=True, max_length=255)
    need_outside_data = models.BooleanField('是否需要外部数据')

    @classmethod
    def get_with_cache(cls, pk):
        cache_key = f'GenerateRuleParameter:{pk}'
        obj = cache.get(cache_key)
        if not obj:
            obj = cls.objects.get(pk=pk)
            # 4 小时缓存数
            cache.set(cache_key, obj, dc.hours.to_seconds(4))
        return obj

    class Meta:
        db_table = 'generate_rule_parameter'
        verbose_name = '生成规则参数'
        verbose_name_plural = verbose_name
        constraints = (UniqueConstraint(fields=('rule_id', 'name'), name='unique_param_name'),)

    def __str__(self):
        return f'<[{self.name}] {self.data_type} {self.description}>'


class DataSet(IdDateTimeBase):
    username = models.CharField('用户名', max_length=255)
    description = models.TextField('描述')
    data_type = models.CharField('数据类型（字典或字符串）', choices=DEFINE_DATA_TYPE, max_length=255)

    class Meta:
        db_table = 'data_set'
        verbose_name = '数据集'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f'<[{self.__class__.__name__}] {reprlib.repr(self.description)}>'


class DataSetDefine(IdDateTimeBase):
    data_set = models.ForeignKey(DataSet, on_delete=models.CASCADE, verbose_name='关联数据集')

    name = models.CharField('属性名', max_length=255, validators=(
        RegexValidator(regex=r'^[a-zA-Z]+$', message='属性命名只能为大小写英文字母'),))
    data_type = models.CharField('数据类型', choices=DATA_TYPE, max_length=255)

    class Meta:
        db_table = 'data_set_define'
        verbose_name = '数据集定义'
        verbose_name_plural = verbose_name
        constraints = (UniqueConstraint(fields=('data_set_id', 'name'), name='unique_data_attr_name'),)

    def __str__(self):
        return f'<[{self.name}] {self.data_type}>'


class DataSetValue(IdDateTimeBase):
    data_set = models.ForeignKey(DataSet, on_delete=models.CASCADE, verbose_name='关联数据集')

    item = models.TextField('数据项')
    data_type = models.CharField('数据类型（字典或字符串）', choices=DEFINE_DATA_TYPE, max_length=255)

    class Meta:
        db_table = 'data_set_value'
        verbose_name = '数据集数据'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f'<[{self.__class__.__name__}] {reprlib.repr(self.item)}>'


class DataSetBind(IdDateTimeBase):
    data_set = models.ForeignKey(DataSet, on_delete=models.CASCADE, verbose_name='关联数据集')

    column_name = models.CharField('单元格列名', max_length=3)
    data_name = models.CharField('关联属性名', max_length=255)

    class Meta:
        db_table = 'data_set_bind'
        verbose_name = '数据集绑定列'
        verbose_name_plural = verbose_name
        constraints = (UniqueConstraint(fields=('column_name', 'data_name'), name='unique_data_attr_bind'),)

    def __str__(self):
        return f'<[{self.__class__.__name__}] {self.data_name} = {self.column_name}>'


class ColumnRule(IdDateTimeBase):
    requirement = models.ForeignKey(FillingRequirement, on_delete=models.CASCADE, verbose_name='关联填充要求')
    rule = models.ForeignKey(GenerateRule, on_delete=models.CASCADE, verbose_name='关联规则')

    column_name = models.CharField('单元格列', max_length=3, validators=(
        RegexValidator(regex=r'^[A-Z]+$', message='单元格名称必须是大写英文字母'),))
    column_type = models.CharField('单元格数据类型', choices=DATA_TYPE, max_length=64)
    associated_of = models.BooleanField('是否需要外部数据集', default=False)

    @classmethod
    def get_with_cache(cls, pk):
        cache_key = f'ColumnRule:{pk}'
        obj = cache.get(cache_key)
        if not obj:
            obj = cls.objects.get(pk=pk)
            # 4 小时缓存数
            cache.set(cache_key, obj, dc.hours.to_seconds(4))
        return obj

    @classmethod
    def remove_cache(cls, pk):
        cache_key = f'ColumnRule:{pk}'
        val = cache.get(cache_key, None)
        if val:
            cache.delete(cache_key)

    class Meta:
        db_table = 'column_rule'
        verbose_name = '列规则'
        verbose_name_plural = verbose_name
        constraints = (UniqueConstraint(fields=('requirement_id', 'column_name'), name='unique_column_name'),)

    def __str__(self):
        return f"<[{self.column_name}] {self.column_type} - {self.rule_id}>"


class DataParameter(IdDateTimeBase):
    column_rule = models.ForeignKey(ColumnRule, on_delete=models.CASCADE, verbose_name='关联列规则')
    param_rule = models.ForeignKey(GenerateRuleParameter, on_delete=models.CASCADE, verbose_name='关联参数')

    name = models.CharField('参数名', max_length=255)
    value = models.CharField('参数值', blank=True, default=str, max_length=512)
    data_set_id = models.BigIntegerField('关联数据集', null=True, default=None)

    class Meta:
        db_table = 'data_parameter'
        verbose_name = '列规则参数'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f'<[{self.name}] {self.value}>'


class FileRecord(IdDateTimeBase):
    requirement_id = models.BigIntegerField('关联填充要求')
    username = models.CharField('用户名', max_length=255)
    file_id = models.CharField('对象存储ID', unique=True, max_length=255)
    filename = models.CharField('原始文件名', max_length=255)

    class Meta:
        db_table = 'file_record'
        verbose_name = '文件记录'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f'<[{self.file_id}] {self.filename} - {self.username}>'
