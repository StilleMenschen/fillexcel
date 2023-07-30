import datetime
import io
import logging
import re
import time
import typing
import uuid
import threading

from django.contrib.auth.models import User
from django.core.cache import cache
from django.core.paginator import Paginator
from django.http import FileResponse, QueryDict
from django.views import generic
from rest_framework import permissions, status
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import Serializer
from rest_framework.views import APIView

from .cache import CacheManager
from .models import DataSet, DataSetDefine, DataSetValue, DataSetBind
from .models import FillingRequirement, GenerateRule, GenerateRuleParameter, ColumnRule, DataParameter, FileRecord
from .serializers import DataSetSerializer, DataSetDefineSerializer, DataSetValueSerializer, DataSetBindSerializer
from .serializers import FileUploadSerializer, FileRecordSerializer
from .serializers import FillingRequirementSerializer, ColumnRuleSerializer, DataParameterSerializer
from .serializers import GenerateRuleSerializer, GenerateRuleParameterSerializer
from .serializers import UserSerializer
from .service import fill_excel
from .storage import Storage
from .timeunit import dc
from .tools import try_calculate_expressions
from .tools import validate_expressions
from .tools import run_in_thread

log = logging.getLogger(__name__)


# Create your views here.
class UserView(APIView, CacheManager):
    """
    用户信息查询
    """
    permission_classes = (permissions.IsAuthenticated,)
    cache_prefix = 'User'

    @staticmethod
    def get_object(username):
        try:
            return User.objects.get(username__exact=username)
        except User.DoesNotExist:
            raise ValueError('未查询到对应用户信息')

    def get(self, request, username=None):

        def query():
            user = self.get_object(username)
            serializer = UserSerializer(user)
            return serializer.data

        data = self.get_cache(username, query)

        return Response(data)


class IndexView(generic.ListView):
    paginate_by = 8
    ordering = ['-id']
    model = FillingRequirement
    template_name = 'fills/index.html'
    context_object_name = 'filling_requirement_list'


class PagingViewMixin:

    @staticmethod
    def resolve_query_params(query_params: QueryDict, params: tuple[tuple[str, str], ...]):
        query = dict()
        for q, p in params:
            val = query_params.get(p, None)
            if val:
                query[q] = val
        return query

    @staticmethod
    def paging(obj, query_params: QueryDict, serializer: typing.Type[Serializer]):
        # 获得查询条件中的翻页参数
        page = query_params.get('page', default=1)
        size = query_params.get('size', default=8)
        # 生成页码记录
        paginator = Paginator(obj, per_page=size)
        # 获取当前页的记录对象
        page_obj = paginator.get_page(page)
        # 序列化
        serializer = serializer(page_obj, many=True)
        # 构建返回的JSON数据
        response_data = {
            'data': serializer.data,  # 将查询数据转为列表
            'message': None,
            'page': {
                'number': page_obj.number,  # 当前页码
                'totalPage': paginator.num_pages,  # 总页数
                'total': paginator.count,  # 总数
                'hasPrevious': page_obj.has_previous(),  # 是否有上一页
                'hasNext': page_obj.has_next(),  # 是否有下一页
            }
        }
        # 返回JSON响应
        return response_data


class FillingRequirementList(APIView, PagingViewMixin):
    """
    生成要求: 查询所有/新增
    """
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request: Request, format=None):
        query_params = request.query_params
        query = self.resolve_query_params(query_params, (
            ('username__exact', 'username'),
            ('remark__contains', 'remark'),
            ('original_filename__contains', 'original_filename')
        ))
        requirement = FillingRequirement.objects.filter(**query).order_by('-id').values()
        data = self.paging(requirement, query_params, FillingRequirementSerializer)
        return Response(data)

    def post(self, request: Request, format=None):
        serializer = FillingRequirementSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class FillingRequirementDetail(APIView, CacheManager):
    """
    生成要求: 单个查询/修改/删除
    """
    permission_classes = (permissions.IsAuthenticated,)
    cache_prefix = 'FillingRequirementDetail'

    @staticmethod
    def get_object(pk):
        try:
            return FillingRequirement.objects.get(pk=pk)
        except FillingRequirement.DoesNotExist:
            raise ValueError('未查询到对应数据')

    def get(self, request, pk):

        def query():
            requirement = self.get_object(pk)
            serializer = FillingRequirementSerializer(requirement)
            return serializer.data

        data = self.get_cache(pk, query)

        return Response(data)

    def put(self, request, pk):
        requirement = self.get_object(pk)
        serializer = FillingRequirementSerializer(requirement, data=request.data)
        if serializer.is_valid():
            serializer.save()
            self.invalid_cache(pk)
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        requirement = self.get_object(pk)
        requirement.delete()
        self.invalid_cache(pk)
        run_in_thread(self.delete_requirement_file, (requirement.file_id,))
        return Response(status=status.HTTP_204_NO_CONTENT)

    @staticmethod
    def delete_requirement_file(file_id):
        try:
            storage = Storage(retry=0)
            storage.remove_object(file_id, 'requirement')
            log.info(f'填充要求的关联文件已删除: {file_id}')
        except Exception as e:
            log.error("填充要求的关联文件删除异常:" + str(e))


class ColumnRuleList(APIView, PagingViewMixin):
    """
    列规则: 查询所有/新增
    """
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request: Request, format=None):
        query_params = request.query_params
        requirement_id = query_params.get('requirement_id', None)
        if not requirement_id:
            raise ValueError('查询列规则必须传需求ID')
        query = {'requirement_id__exact': int(requirement_id)}
        column_name = query_params.get('column_name', None)
        if column_name:
            query['column_name__iexact'] = column_name
        column_rule = ColumnRule.objects.filter(**query).order_by('-id').values()
        data = self.paging(column_rule, query_params, ColumnRuleSerializer)
        return Response(data)

    def post(self, request: Request, format=None):
        # 同一个填充要求中存在列名重复判断
        column_name = request.data['column_name']
        if ColumnRule.objects.filter(requirement_id__exact=request.data['requirement_id'],
                                     column_name__exact=column_name).exists():
            raise ValueError(f'新增的列名 "{column_name}" 已经存在')
        serializer = ColumnRuleSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ColumnRuleDetail(APIView, CacheManager):
    """
    列规则: 单个查询/修改/删除
    """
    permission_classes = (permissions.IsAuthenticated,)
    cache_prefix = 'ColumnRuleDetail'

    @staticmethod
    def get_object(pk):
        try:
            return ColumnRule.objects.get(pk=pk)
        except ColumnRule.DoesNotExist:
            raise ValueError('未查询到对应数据')

    def get(self, request, pk):

        def query():
            column_rule = self.get_object(pk)
            serializer = ColumnRuleSerializer(column_rule)
            return serializer.data

        data = self.get_cache(pk, query)

        return Response(data)

    def put(self, request, pk):
        # 同一个填充要求中存在列名重复判断
        column_name = request.data['column_name']
        if ColumnRule.objects.exclude(id__exact=pk).filter(requirement_id__exact=request.data['requirement_id'],
                                                           column_name__exact=column_name).exists():
            raise ValueError(f'修改后的列名 "{column_name}" 已经存在')
        column_rule = self.get_object(pk)
        serializer = ColumnRuleSerializer(column_rule, data=request.data)
        if serializer.is_valid():
            serializer.save()
            self.invalid_cache(pk)
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        column_rule = self.get_object(pk)
        column_rule.delete()
        self.invalid_cache(pk)
        return Response(status=status.HTTP_204_NO_CONTENT)


class DataParameterList(APIView, PagingViewMixin):
    """
    填充函数参数: 查询所有/新增
    """
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request: Request, format=None):
        query_params = request.query_params
        query = self.resolve_query_params(query_params, (
            ('column_rule_id__exact', 'column_rule_id'),
        ))
        data_parameter = DataParameter.objects.filter(**query).order_by('-id').values()
        data = self.paging(data_parameter, query_params, DataParameterSerializer)
        return Response(data)

    def post(self, request: Request, format=None):
        # 部分规则参数必要校验
        for data_param in request.data:
            self.validate_parameter_related_columns(data_param)
        serializer = DataParameterSerializer(data=request.data, many=True)
        if serializer.is_valid():
            # 删除旧的数据
            self.remove_data_parameter(serializer.data[0]['column_rule_id'])
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @staticmethod
    def remove_data_parameter(column_rule_id):
        old_data_parameter = DataParameter.objects.filter(column_rule_id__exact=column_rule_id)
        if old_data_parameter.exists():
            old_data_parameter.delete()

    def validate_parameter_related_columns(self, data_param):
        gen_rule_param_id, column_rule_id = data_param['param_rule_id'], data_param['column_rule_id']
        # 尽量读缓存
        param = GenerateRuleParameter.get_with_cache(gen_rule_param_id)
        gen_rule = GenerateRule.get_with_cache(param.rule_id)
        rule_func_name = gen_rule.function_name
        # 单元格列值连接必须都是有配置的列
        if rule_func_name == 'join_string' and param.name == 'columns':
            pattern = re.compile(r'^[A-Z]+(,[A-Z]+)*$')
            if not pattern.match(data_param['value']):
                raise ValueError('传入关联的列数据不正确，必须是以英文逗号拼接的列名')
            columns: str = data_param['value']
            column_rule = ColumnRule.objects.get(pk=column_rule_id)
            # 单元格列必须存在
            for column in iter(columns.split(',')):
                self.validate_column(column_rule, column)
        # 单元格列值计算必须都是有配置的列
        if rule_func_name == 'calculate_expressions' and param.name == 'expressions':
            expressions: str = data_param['value']
            if validate_expressions(expressions):
                pattern = re.compile(r"\{([A-Z]+)\}")
                column_rule = ColumnRule.objects.get(pk=column_rule_id)
                # 单元格列必须存在
                for match in pattern.finditer(expressions):
                    column = match.group(1)
                    self.validate_column(column_rule, column)
                # 尝试填入数字 1 计算
                try_calculate_expressions(expressions)
            else:
                raise ValueError('传入表达式不正确')

    @staticmethod
    def validate_column(column_rule, column_name):
        if column_name == column_rule.column_name:
            raise ValueError(f'关联的列不能包含自身 "{column_name}"')
        expected_column = ColumnRule.objects.filter(requirement_id__exact=column_rule.requirement.id,
                                                    column_name__iexact=column_name)
        if not expected_column.exists():
            raise ValueError(f'传入的关联列 "{column_name}" 未在此填充规则中定义')
        # 查询对应列的绑定规则数据
        column_rule = expected_column[0]
        generate_rule = GenerateRule.get_with_cache(column_rule.rule.id)
        if generate_rule.function_name in {'join_string', 'calculate_expressions'}:
            raise ValueError(f'传入的关联列 "{column_name}" 的生成规则不能为列值拼接、表达式计算')


class DataParameterDetail(APIView, CacheManager):
    """
    填充函数参数: 单个查询/修改/删除
    """
    permission_classes = (permissions.IsAuthenticated,)
    cache_prefix = 'DataParameterDetail'

    @staticmethod
    def get_object(pk):
        try:
            return DataParameter.objects.get(pk=pk)
        except DataParameter.DoesNotExist:
            raise ValueError('未查询到对应数据')

    def get(self, request, pk):

        def query():
            data_parameter = self.get_object(pk)
            serializer = DataParameterSerializer(data_parameter)
            return serializer.data

        data = self.get_cache(pk, query)

        return Response(data)

    def put(self, request, pk):
        data_parameter = self.get_object(pk)
        serializer = DataParameterSerializer(data_parameter, data=request.data)
        if serializer.is_valid():
            serializer.save()
            self.invalid_cache(pk)
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        data_parameter = self.get_object(pk)
        data_parameter.delete()
        self.invalid_cache(pk)
        return Response(status=status.HTTP_204_NO_CONTENT)


class DataSetList(APIView, PagingViewMixin):
    """
    数据集: 查询所有/新增
    """
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request: Request, format=None):
        query_params = request.query_params
        query = self.resolve_query_params(query_params, (
            ('username__exact', 'username'),
            ('data_type__exact', 'data_type'),
            ('description__contains', 'description')
        ))
        data_set = DataSet.objects.filter(**query).order_by('-id').values()
        data = self.paging(data_set, query_params, DataSetSerializer)
        return Response(data)

    def post(self, request: Request, format=None):
        serializer = DataSetSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DataSetDetail(APIView, CacheManager):
    """
    数据集: 单个查询/修改/删除
    """
    permission_classes = (permissions.IsAuthenticated,)
    cache_prefix = 'DataSetDetail'

    @staticmethod
    def get_object(pk):
        try:
            return DataSet.objects.get(pk=pk)
        except DataSet.DoesNotExist:
            raise ValueError('未查询到对应数据')

    def get(self, request, pk):

        def query():
            data_set = self.get_object(pk)
            serializer = DataSetSerializer(data_set)
            return serializer.data

        data = self.get_cache(pk, query)

        return Response(data)

    def put(self, request, pk):
        data_set = self.get_object(pk)
        serializer = DataSetSerializer(data_set, data=request.data)
        if serializer.is_valid():
            serializer.save()
            self.invalid_cache(pk)
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        # 列绑定和规则绑定的数据集都不能删除
        if DataSetBind.objects.filter(data_set_id__exact=pk).exists() or DataParameter.objects.filter(
                data_set_id__exact=pk).exists():
            raise ValueError('已存在绑定此数据集的生成规则配置，不能删除')
        data_set = self.get_object(pk)
        data_set.delete()
        self.invalid_cache(pk)
        return Response(status=status.HTTP_204_NO_CONTENT)


class DataSetDefineList(APIView, PagingViewMixin, CacheManager):
    """
    数据集定义: 查询所有/新增
    """
    permission_classes = (permissions.IsAuthenticated,)
    cache_prefix = 'DataSetDefineList'

    def get(self, request: Request, format=None):
        query_params = request.query_params
        data_set_id = query_params.get('data_set_id', None)
        if not data_set_id:
            raise ValueError('必须传数据集ID参数')

        def query():
            params = {'data_set_id__exact': data_set_id}
            data_set_define = DataSetDefine.objects.filter(**params).order_by('id').values()
            return self.paging(data_set_define, query_params, DataSetDefineSerializer)

        data = self.get_cache(str(data_set_id), query)
        return Response(data)

    def post(self, request: Request, format=None):
        serializer = DataSetDefineSerializer(data=request.data, many=True)
        define_list: list[dict] = request.data
        names = set()
        for define in define_list:
            name = define['name']
            if name not in names:
                names.add(name)
            else:
                raise ValueError('不能定义重复的字段属性')
        if serializer.is_valid():
            data_set_id = define_list[0]['data_set_id']
            DataSetDefine.objects.filter(data_set_id__exact=data_set_id).delete()
            serializer.save()
            self.invalid_cache(str(data_set_id))
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DataSetDefineDetail(APIView, CacheManager):
    """
    数据集定义: 单个查询/修改/删除
    """
    permission_classes = (permissions.IsAuthenticated,)
    cache_prefix = 'DataSetDefineDetail'

    @staticmethod
    def get_object(pk):
        try:
            return DataSetDefine.objects.get(pk=pk)
        except DataSetDefine.DoesNotExist:
            raise ValueError('未查询到对应数据')

    def get(self, request, pk):

        def query():
            data_set_define = self.get_object(pk)
            serializer = DataSetDefineSerializer(data_set_define)
            return serializer.data

        data = self.get_cache(pk, query)

        return Response(data)

    def delete(self, request, pk):
        data_set_define = self.get_object(pk)
        data_set_define.delete()
        self.invalid_cache(pk)
        return Response(status=status.HTTP_204_NO_CONTENT)


class DataSetValueList(APIView, PagingViewMixin):
    """
    数据集数据: 查询所有/新增
    """
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request: Request, format=None):
        query_params = request.query_params
        data_set_id = query_params.get('data_set_id', None)
        if not data_set_id:
            raise ValueError('必须传数据集ID参数')
        query = {'data_set_id__exact': data_set_id}
        data_set_value = DataSetValue.objects.filter(**query).order_by('-id').values()
        data = self.paging(data_set_value, query_params, DataSetValueSerializer)
        return Response(data)

    def post(self, request: Request, format=None):
        serializer = DataSetValueSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DataSetValueDetail(APIView, CacheManager):
    """
    数据集数据: 单个查询/修改/删除
    """
    permission_classes = (permissions.IsAuthenticated,)
    cache_prefix = 'DataSetValueDetail'

    @staticmethod
    def get_object(pk):
        try:
            return DataSetValue.objects.get(pk=pk)
        except DataSetValue.DoesNotExist:
            raise ValueError('未查询到对应数据')

    def get(self, request, pk):

        def query():
            data_set_value = self.get_object(pk)
            serializer = DataSetValueSerializer(data_set_value)
            return serializer.data

        data = self.get_cache(pk, query)

        return Response(data)

    def put(self, request, pk):
        data_set_value = self.get_object(pk)
        serializer = DataSetValueSerializer(data_set_value, data=request.data)
        if serializer.is_valid():
            serializer.save()
            self.invalid_cache(pk)
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        data_set_value = self.get_object(pk)
        data_set_value.delete()
        self.invalid_cache(pk)
        return Response(status=status.HTTP_204_NO_CONTENT)


class DataSetBindList(APIView, PagingViewMixin):
    """
    数据集绑定: 查询所有/新增
    """
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request: Request, format=None):
        query_params = request.query_params
        data_set_id = query_params.get('data_set_id', None)
        if not data_set_id:
            raise ValueError('必须传数据集ID参数')
        query = {'data_set_id__exact': data_set_id}
        data_set_bind = DataSetBind.objects.filter(**query).order_by('-id').values()
        data = self.paging(data_set_bind, query_params, DataSetBindSerializer)
        return Response(data)

    def post(self, request: Request, format=None):
        serializer = DataSetBindSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DataSetBindDetail(APIView, CacheManager):
    """
    数据集绑定: 单个查询/修改/删除
    """
    permission_classes = (permissions.IsAuthenticated,)
    cache_prefix = 'DataSetBindDetail'

    @staticmethod
    def get_object(pk):
        try:
            return DataSetBind.objects.get(pk=pk)
        except DataSetBind.DoesNotExist:
            raise ValueError('未查询到对应数据')

    def get(self, request, pk):

        def query():
            data_set_bind = self.get_object(pk)
            serializer = DataSetBindSerializer(data_set_bind)
            return serializer.data

        data = self.get_cache(pk, query)

        return Response(data)

    def put(self, request, pk):
        data_set_bind = self.get_object(pk)
        serializer = DataSetBindSerializer(data_set_bind, data=request.data)
        if serializer.is_valid():
            serializer.save()
            self.invalid_cache(pk)
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        data_set_bind = self.get_object(pk)
        data_set_bind.delete()
        self.invalid_cache(pk)
        return Response(status=status.HTTP_204_NO_CONTENT)


class GenerateRuleList(APIView, PagingViewMixin, CacheManager):
    """
    生成规则: 查询所有
    """
    permission_classes = (permissions.IsAuthenticated,)
    cache_prefix = 'GenerateRuleList'

    def get(self, request: Request, format=None):
        query_params = request.query_params

        def query():
            generate_rule = GenerateRule.objects.order_by('-id').values()
            return self.paging(generate_rule, query_params, GenerateRuleSerializer)

        page = query_params.get('page', default=1)
        size = query_params.get('size', default=8)
        data = self.get_cache(f'{page}of{size}', query)
        return Response(data)


class GenerateRuleDetail(APIView, CacheManager):
    """
    生成规则: 单个查询
    """
    permission_classes = (permissions.IsAuthenticated,)
    cache_prefix = 'GenerateRuleDetail'

    @staticmethod
    def get_object(pk):
        try:
            return GenerateRule.objects.get(pk=pk)
        except GenerateRule.DoesNotExist:
            raise ValueError('未查询到对应数据')

    def get(self, request, pk):

        def query():
            generate_rule = self.get_object(pk)
            serializer = GenerateRuleSerializer(generate_rule)
            return serializer.data

        data = self.get_cache(pk, query)

        return Response(data)


class GenerateRuleParameterList(APIView, PagingViewMixin, CacheManager):
    """
    生成规则残参数: 查询所有
    """
    permission_classes = (permissions.IsAuthenticated,)
    cache_prefix = 'GenerateRuleParameterList'

    def get(self, request: Request, format=None):
        query_params = request.query_params
        rule_id = query_params.get('rule_id', None)
        if rule_id == -1:
            raise ValueError("未传生成规则ID")
        if not GenerateRule.objects.filter(id__exact=rule_id).exists():
            raise ValueError("生成规则数据不存在")

        def query():
            generate_rule_parameter = GenerateRuleParameter.objects.filter(
                rule_id__exact=int(rule_id)).order_by('-id').values()
            return self.paging(generate_rule_parameter, query_params, GenerateRuleParameterSerializer)

        page = query_params.get('page', default=1)
        size = query_params.get('size', default=8)
        data = self.get_cache(f'{rule_id}@{page}of{size}', query)
        return Response(data)


class GenerateRuleParameterDetail(APIView, CacheManager):
    """
    生成规则残参数: 单个查询
    """
    permission_classes = (permissions.IsAuthenticated,)
    cache_prefix = 'GenerateRuleParameterDetail'

    @staticmethod
    def get_object(pk):
        try:
            return GenerateRuleParameter.objects.get(pk=pk)
        except GenerateRuleParameter.DoesNotExist:
            raise ValueError('未查询到对应数据')

    def get(self, request, pk):

        def query():
            generate_rule_parameter = self.get_object(pk)
            serializer = GenerateRuleParameterSerializer(generate_rule_parameter)
            return serializer.data

        data = self.get_cache(pk, query)

        return Response(data)


class GeneratesView(APIView):
    """
    按要求填入并生成excel文件
    """
    permission_classes = (permissions.IsAuthenticated,)

    @staticmethod
    def generates(req_id: int):
        limit_cache_key = 'GeneratesView:GenerateLimit'
        request_count = cache.get(limit_cache_key, 0)

        if request_count >= 42:
            raise ValueError('您的操作频率太快，请稍后再试！')

        cache.set(limit_cache_key, request_count + 1, dc.minutes.to_seconds(1))

        t0 = time.perf_counter()
        fr = FillingRequirement.objects.get(pk=req_id)
        hash_id = uuid.uuid1().hex
        fill_excel(fr, hash_id)
        took = time.perf_counter() - t0
        return Response(dict(requirement=req_id, fileId=hash_id, took=took))

    def get(self, request: Request, requirement_id: int):
        return self.generates(requirement_id)

    def post(self, request: Request, requirement_id: int):
        return self.generates(requirement_id)


class FileUploadView(APIView):
    """文件上传"""
    parser_classes = (MultiPartParser, FormParser)
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        serializer = FileUploadSerializer(data=request.data)

        if serializer.is_valid():
            file = serializer.validated_data['file']
            try:
                storage = Storage(retry=0)
                hash_id = uuid.uuid1().hex
                storage.store_object(hash_id, file.file, file.size, folder='requirement',
                                     content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
                return Response(dict(fileId=hash_id, createdAt=datetime.datetime.now()), status=status.HTTP_201_CREATED)
            except Exception as e:
                log.error('上传文件异常' + str(e))
                raise ValueError('处理上传文件失败，请稍后再试')

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class FileRecordList(APIView, PagingViewMixin):
    """
    生成文件记录: 查询所有/新增
    """
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request: Request, format=None):
        query_params = request.query_params
        query = self.resolve_query_params(query_params, (
            ('requirement_id__exact', 'requirementId'),
            ('username__exact', 'username'),
            ('filename__contains', 'filename')
        ))
        file_record = FileRecord.objects.filter(**query).order_by('-id').values()
        data = self.paging(file_record, query_params, FileRecordSerializer)
        return Response(data)


class FileRecordDetail(APIView):
    """
    生成文件记录: 单个查询/删除
    """
    permission_classes = (permissions.IsAuthenticated,)

    @staticmethod
    def get_object(pk):
        try:
            return FileRecord.objects.get(pk=pk)
        except FileRecord.DoesNotExist:
            raise ValueError('未查询到对应数据')

    def get(self, request, pk):

        limit_cache_key = 'FileRecordDetail:DownloadLimit'
        request_count = cache.get(limit_cache_key, 0)

        if request_count >= 30:
            raise ValueError('您的操作频率太快，请稍后再试！')

        cache.set(limit_cache_key, request_count + 1, dc.minutes.to_seconds(1))

        file_record = self.get_object(pk)
        try:
            storage = Storage(retry=0)
            data = io.BytesIO(storage.get_object(file_record.file_id))
            data.seek(0)
            # 返回文件下载
            return FileResponse(data, as_attachment=True, filename=file_record.filename,
                                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        except Exception as e:
            log.error('处理下载文件异常' + str(e))
            raise ValueError('处理下载文件异常，请稍后再试')

    def delete(self, request, pk):
        file_record = self.get_object(pk)
        file_record.delete()
        run_in_thread(self.delete_record_file, (file_record.file_id,))
        return Response(status=status.HTTP_204_NO_CONTENT)

    @staticmethod
    def delete_record_file(file_id):
        try:
            storage = Storage(retry=0)
            storage.remove_object(file_id)
            log.info(f'生成记录的文件已删除: {file_id}')
        except Exception as e:
            log.error('生成记录的文件删除异常:' + str(e))
