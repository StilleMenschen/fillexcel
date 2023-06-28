from django.db import models

from .utils import SnowFlake


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
    remark = models.TextField(null=True)
    file_id = models.CharField(max_length=255)
    original_filename = models.CharField(max_length=255)
    start_line = models.PositiveIntegerField()
    line_number = models.PositiveIntegerField()

    def __str__(self):
        return f"<[{self.original_filename}] {self.start_line} of {self.line_number} line>"


class ColumnRule(IdDateTimeBase):
    # Foreign key association
    filling_requirement = models.ForeignKey(FillingRequirement,
                                            on_delete=models.CASCADE)
    # Attribute
    rule_id = models.BigIntegerField()
    data_param_id = models.BigIntegerField()
    column_name = models.CharField(max_length=255)
    column_type = models.CharField(max_length=128)
    associated_of = models.BooleanField(default=False)

    def __str__(self):
        return f"<[{self.column_name}] {self.column_type} - {self.rule_id}>"


class GenerateRule(IdDateTimeBase):
    rule_name = models.CharField(max_length=128)
    function_name = models.CharField(max_length=255)
    fill_order = models.PositiveIntegerField()
    description = models.TextField()

    def __str__(self):
        return f"<[{self.rule_name}] {self.function_name}>"


class GenerateRuleParameter(IdDateTimeBase):
    # Foreign key association
    rule = models.ForeignKey(GenerateRule, on_delete=models.CASCADE)
    # Attribute
    name = models.CharField(max_length=255)
    data_type = models.CharField(max_length=255)
    description = models.TextField()
    required = models.BooleanField()
    default_value = models.CharField(null=True, max_length=255)
    need_outside_data = models.BooleanField()

    def __str__(self) -> str:
        return f'<[{self.name}] {self.data_type}>'


class DataDefine(IdDateTimeBase):
    group_id = models.BigIntegerField()
    name = models.CharField(max_length=255)
    data_type = models.CharField(max_length=128)
    data_group_id = models.BigIntegerField()

    def __str__(self) -> str:
        return f'<[{self.name} - {self.data_type}] {self.group_id} {self.data_group_id}>'


class DataValueList(IdDateTimeBase):
    group_id = models.BigIntegerField()
    value_list = models.TextField()

    def __str__(self) -> str:
        return f'<[{self.group_id}]>'


class DataBind(IdDateTimeBase):
    group_id = models.BigIntegerField()
    data_name = models.CharField(max_length=255)
    column_name = models.CharField(max_length=255)

    def __str__(self) -> str:
        return f'<[{self.data_name} - {self.column_name}] {self.group_id}>'


class DataParameter(IdDateTimeBase):
    param_rule_id = models.BigIntegerField()
    name = models.CharField(max_length=255)
    value = models.CharField(max_length=255)
    expressions = models.CharField(max_length=512)
    data_define_group_id = models.BigIntegerField()
    data_bind_group_id = models.BigIntegerField()

    def __str__(self) -> str:
        return f'<[{self.name}] {self.value}>'
