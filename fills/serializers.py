from django.contrib.auth.models import User, Group
from rest_framework import serializers

from .models import DataSet, DataSetDefine, DataSetValue, DataSetBind
from .models import FillingRequirement, ColumnRule, DataParameter
from .models import GenerateRule, GenerateRuleParameter


class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ['url', 'username', 'email', 'groups']


class GroupSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Group
        fields = ['url', 'name']


class FillingRequirementSerializer(serializers.ModelSerializer):
    class Meta:
        model = FillingRequirement
        fields = ('id', 'username', 'file_id', 'original_filename', 'start_line', 'line_number', 'created_at',
                  'updated_at')


class FillingRequirementRelatedField(serializers.RelatedField):
    """填充要求外键关联序列化"""
    queryset = FillingRequirement.objects.get_queryset

    def to_representation(self, value):
        return value

    def to_internal_value(self, data):
        return data


class GenerateRuleRelatedField(serializers.RelatedField):
    """生成规则外键关联序列化"""
    queryset = GenerateRule.objects.get_queryset

    def to_representation(self, value):
        return value

    def to_internal_value(self, data):
        return data


class ColumnRuleSerializer(serializers.ModelSerializer):
    requirement_id = FillingRequirementRelatedField()
    rule_id = GenerateRuleRelatedField()

    def validate_column_name(self, value):
        requirement_id = self.initial_data.get('requirement_id', 0)
        if ColumnRule.objects.filter(requirement_id__exact=requirement_id, column_name__exact=value).exists():
            raise serializers.ValidationError(f'同一个填充要求里不能有重复的列定义：{value}')
        return value

    class Meta:
        model = ColumnRule
        fields = ('id', 'requirement_id', 'rule_id', 'column_name', 'column_type', 'associated_of', 'created_at',
                  'updated_at')


class ColumnRuleRelatedField(serializers.RelatedField):
    """列规则外键关联序列化"""
    queryset = ColumnRule.objects.get_queryset

    def to_representation(self, value):
        return value

    def to_internal_value(self, data):
        return data


class GenerateRuleParameterRelatedField(serializers.RelatedField):
    """生成规则参数外键关联序列化"""
    queryset = GenerateRuleParameter.objects.get_queryset

    def to_representation(self, value):
        return value

    def to_internal_value(self, data):
        return data


class DataParameterSerializer(serializers.ModelSerializer):
    column_rule_id = ColumnRuleRelatedField()
    param_rule_id = GenerateRuleParameterRelatedField()

    class Meta:
        model = DataParameter
        fields = ('id', 'column_rule_id', 'param_rule_id', 'name', 'value', 'data_set_id', 'created_at', 'updated_at')


class DataSetSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataSet
        fields = ('id', 'username', 'description', 'data_type', 'created_at', 'updated_at')


class DataSetRelatedField(serializers.RelatedField):
    """数据集外键关联序列化"""
    queryset = DataSet.objects.get_queryset

    def to_representation(self, value):
        return value

    def to_internal_value(self, data):
        return data


class DataSetDefineSerializer(serializers.ModelSerializer):
    data_set_id = DataSetRelatedField()

    class Meta:
        model = DataSetDefine
        fields = ('id', 'data_set_id', 'name', 'data_type', 'created_at', 'updated_at')


class DataSetValueSerializer(serializers.ModelSerializer):
    data_set_id = DataSetRelatedField()

    class Meta:
        model = DataSetValue
        fields = ('id', 'data_set_id', 'item', 'data_type', 'created_at', 'updated_at')


class DataSetBindSerializer(serializers.ModelSerializer):
    data_set_id = DataSetRelatedField()

    class Meta:
        model = DataSetBind
        fields = ('id', 'data_set_id', 'column_name', 'data_name', 'created_at', 'updated_at')


class GenerateRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = GenerateRule
        fields = ('id', 'rule_name', 'function_name', 'fill_order', 'description', 'created_at', 'updated_at')


class GenerateRuleParameterSerializer(serializers.ModelSerializer):
    rule_id = GenerateRuleRelatedField()

    class Meta:
        model = GenerateRuleParameter
        fields = ('id', 'rule_id', 'name', 'data_type', 'description', 'required', 'default_value', 'need_outside_data',
                  'created_at', 'updated_at')
