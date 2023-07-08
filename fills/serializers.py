from django.contrib.auth.models import User, Group
from rest_framework import serializers

from .models import DataSet, DataSetDefine, DataSetValue, DataSetBind
from .models import FillingRequirement, ColumnRule, DataParameter


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


class ColumnRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = ColumnRule
        fields = ('id', 'requirement_id', 'rule_id', 'column_name', 'column_type', 'associated_of', 'created_at',
                  'updated_at')


class DataParameterSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataParameter
        fields = ('id', 'column_rule_id', 'param_rule_id', 'name', 'value', 'expressions', 'data_set_id', 'created_at',
                  'updated_at')


class DataSetSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataSet
        fields = ('id', 'username', 'description', 'created_at', 'updated_at')


class DataSetDefineSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataSetDefine
        fields = ('id', 'data_set_id', 'name', 'data_type', 'created_at', 'updated_at')


class DataSetValueSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataSetValue
        fields = ('id', 'data_set_id', 'item', 'data_type', 'created_at', 'updated_at')


class DataSetBindSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataSetBind
        fields = ('id', 'data_set_id', 'column_name', 'data_name', 'created_at', 'updated_at')
