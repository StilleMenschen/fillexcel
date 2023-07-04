from django.contrib.auth.models import User, Group
from rest_framework import serializers
from django.core.validators import RegexValidator

from .models import FillingRequirement


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
