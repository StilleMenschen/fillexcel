import datetime
import io
import logging
import time
import typing

from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.http import FileResponse
from django.utils.decorators import method_decorator
from django.views import generic
from django.views.decorators.cache import cache_page
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
    def paging(obj, page, size, serializer: typing.Type[Serializer]):
        # 获得查询条件中的翻页参数
        # page = query_params.get('page', default=1)
        # size = query_params.get('size', default=8)
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
        username = query_params.get('username', None)
        remark = query_params.get('remark', None)
        original_filename = query_params.get('original_filename', None)
        requirement = FillingRequirement.objects.get_queryset()
        if username:
            requirement = requirement.filter(username__exact=username)
        if remark:
            requirement = requirement.filter(remark__contains=remark)
        if original_filename:
            requirement = requirement.filter(original_filename__contains=original_filename)
        requirement = requirement.order_by('-id').values()
        page = query_params.get('page', default=1)
        size = query_params.get('size', default=8)
        data = self.paging(requirement, page, size, FillingRequirementSerializer)
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
        try:
            storage = Storage(retry=0)
            storage.remove_object(requirement.file_id, 'requirement')
        except Exception as e:
            log.error("删除填充要求的关联文件异常:" + str(e))
        return Response(status=status.HTTP_204_NO_CONTENT)


class ColumnRuleList(APIView, PagingViewMixin):
    """
    列规则: 查询所有/新增
    """
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request: Request, format=None):
        query_params = request.query_params
        requirement_id = query_params.get('requirementId', None)
        column_name = query_params.get('columnName', None)
        if not requirement_id:
            raise ValueError('查询列规则必须传需求ID')
        column_rule = ColumnRule.objects.get_queryset()
        if requirement_id:
            column_rule = column_rule.filter(requirement_id__exact=int(requirement_id))
        if column_name:
            column_rule = column_rule.filter(column_name__iexact=column_name)
        column_rule = column_rule.order_by('-id').values()
        page = query_params.get('page', default=1)
        size = query_params.get('size', default=8)
        data = self.paging(column_rule, page, size, ColumnRuleSerializer)
        return Response(data)

    def post(self, request: Request, format=None):
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
        column_rule_id = query_params.get('columnRuleId', None)
        data_parameter = DataParameter.objects.get_queryset()
        if column_rule_id:
            data_parameter = data_parameter.filter(column_rule_id__exact=int(column_rule_id))
        data_parameter = data_parameter.order_by('-id').values()
        page = query_params.get('page', default=1)
        size = query_params.get('size', default=8)
        data = self.paging(data_parameter, page, size, DataParameterSerializer)
        return Response(data)

    def post(self, request: Request, format=None):
        serializer = DataParameterSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


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
        data_set = DataSet.objects.order_by('-id').values()
        query_params = request.query_params
        page = query_params.get('page', default=1)
        size = query_params.get('size', default=8)
        data = self.paging(data_set, page, size, DataSetSerializer)
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
        if DataSetBind.objects.filter(data_set__id__exact=pk).exists():
            raise RuntimeError('已经存在绑定此数据的生成请求，不能删除')
        data_set = self.get_object(pk)
        data_set.delete()
        self.invalid_cache(pk)
        return Response(status=status.HTTP_204_NO_CONTENT)


class DataSetDefineList(APIView, PagingViewMixin):
    """
    数据集定义: 查询所有/新增
    """
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request: Request, format=None):
        query_params = request.query_params
        data_set_id = query_params.get('dataSetId', None)
        data_set_define = DataSetDefine.objects.get_queryset()
        if data_set_id:
            data_set_define = data_set_define.filter(data_set_id__exact=int(data_set_id))
        data_set_define = data_set_define.order_by('-id').values()
        page = query_params.get('page', default=1)
        size = query_params.get('size', default=8)
        data = self.paging(data_set_define, page, size, DataSetDefineSerializer)
        return Response(data)

    def post(self, request: Request, format=None):
        serializer = DataSetDefineSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
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

    def put(self, request, pk):
        data_set_define = self.get_object(pk)
        serializer = DataSetDefineSerializer(data_set_define, data=request.data)
        if serializer.is_valid():
            serializer.save()
            self.invalid_cache(pk)
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

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
        data_set_id = query_params.get('dataSetId', None)
        data_set_value = DataSetValue.objects.get_queryset()
        if data_set_id:
            data_set_value = data_set_value.filter(data_set_id__exact=int(data_set_id))
        data_set_value = data_set_value.order_by('-id').values()
        page = query_params.get('page', default=1)
        size = query_params.get('size', default=8)
        data = self.paging(data_set_value, page, size, DataSetValueSerializer)
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
        data_set_id = query_params.get('dataSetId', None)
        data_set_bind = DataSetBind.objects.get_queryset()
        if data_set_id:
            data_set_bind = data_set_bind.filter(data_set_id__exact=int(data_set_id))
        data_set_bind = data_set_bind.order_by('-id').values()
        page = query_params.get('page', default=1)
        size = query_params.get('size', default=8)
        data = self.paging(data_set_bind, page, size, DataSetBindSerializer)
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
        def query():
            generate_rule = GenerateRule.objects.order_by('-id').values()
            return self.paging(generate_rule, page, size, GenerateRuleSerializer)

        query_params = request.query_params
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
        rule_id = query_params.get('ruleId', None)
        if rule_id == -1:
            raise ValueError("未传生成规则ID")
        if not GenerateRule.objects.filter(id__exact=rule_id).exists():
            raise ValueError("生成规则数据不存在")

        def query():
            generate_rule_parameter = GenerateRuleParameter.objects.filter(
                rule_id__exact=int(rule_id)).order_by('-id').values()
            return self.paging(generate_rule_parameter, page, size, GenerateRuleParameterSerializer)

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
        t0 = time.perf_counter()
        fr = FillingRequirement.objects.get(pk=req_id)
        fill_excel(fr)
        took = time.perf_counter() - t0
        return Response(dict(requirement=req_id, took=took))

    def get(self, request: Request, requirement_id=None):
        return self.generates(requirement_id)

    def post(self, request: Request, requirement_id=None):
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
                hash_id = storage.store_object(file.file, file.size, 'requirement',
                                               'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
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
        requirement_id = query_params.get('requirementId', None)
        username = query_params.get('username', None)
        file_record = FileRecord.objects.get_queryset()
        if requirement_id:
            file_record = file_record.filter(requirement_id__exact=int(requirement_id))
        if username:
            file_record = file_record.filter(username__exact=username)
        file_record = file_record.order_by('-id').values()
        page = query_params.get('page', default=1)
        size = query_params.get('size', default=8)
        data = self.paging(file_record, page, size, FileRecordSerializer)
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
        return Response(status=status.HTTP_204_NO_CONTENT)
