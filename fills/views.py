import logging
import time
import typing

from django.contrib.auth.models import User, Group
from django.core.paginator import Paginator
from django.http import JsonResponse, QueryDict
from django.views import generic
from django.views.decorators.cache import cache_page
from django.views.decorators.http import require_GET
from rest_framework import permissions, viewsets, status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import Serializer
from rest_framework.views import APIView

from .cache import CacheManager
from .models import DataSet, DataSetDefine, DataSetValue, DataSetBind
from .models import FillingRequirement, GenerateRule, ColumnRule, DataParameter
from .serializers import DataSetSerializer, DataSetDefineSerializer, DataSetValueSerializer, DataSetBindSerializer
from .serializers import FillingRequirementSerializer, ColumnRuleSerializer, DataParameterSerializer
from .serializers import UserSerializer, GroupSerializer
from .service import fill_excel

log = logging.getLogger(__name__)


# Create your views here.
class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserSerializer
    permission_classes = (permissions.IsAuthenticated,)


class GroupViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows groups to be viewed or edited.
    """
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    permission_classes = (permissions.IsAuthenticated,)


class IndexView(generic.ListView):
    paginate_by = 8
    ordering = ['-id']
    model = FillingRequirement
    template_name = 'fills/index.html'
    context_object_name = 'filling_requirement_list'


class PagingViewMixin:

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
        return Response(response_data)


class FillingRequirementList(APIView, PagingViewMixin):
    """
    生成要求: 查询所有/新增
    """
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request: Request, format=None):
        requirement = FillingRequirement.objects.order_by('-id').values()
        return self.paging(requirement, request.query_params, FillingRequirementSerializer)

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
        return Response(status=status.HTTP_204_NO_CONTENT)


class ColumnRuleList(APIView, PagingViewMixin):
    """
    列规则: 查询所有/新增
    """
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request: Request, format=None):
        requirement_id = request.query_params.get('requirement_id', None)
        column_rule = ColumnRule.objects.get_queryset()
        if requirement_id:
            column_rule = column_rule.filter(requirement_id__exact=int(requirement_id))
        column_rule = column_rule.order_by('-id').values()
        return self.paging(column_rule, request.query_params, ColumnRuleSerializer)

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
        column_rule_id = request.query_params.get('column_rule_id', None)
        data_parameter = DataParameter.objects.get_queryset()
        if column_rule_id:
            data_parameter = data_parameter.filter(column_rule_id__exact=int(column_rule_id))
        data_parameter = data_parameter.order_by('-id').values()
        return self.paging(data_parameter, request.query_params, DataParameterSerializer)

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
        return self.paging(data_set, request.query_params, DataSetSerializer)

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
        data_set_id = request.query_params.get('data_set_id', None)
        data_set_define = DataSetDefine.objects.get_queryset()
        if data_set_id:
            data_set_define = data_set_define.filter(data_set_id__exact=int(data_set_id))
        data_set_define = data_set_define.order_by('-id').values()
        return self.paging(data_set_define, request.query_params, DataSetDefineSerializer)

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
        data_set_id = request.query_params.get('data_set_id', None)
        data_set_value = DataSetValue.objects.get_queryset()
        if data_set_id:
            data_set_value = data_set_value.filter(data_set_id__exact=int(data_set_id))
        data_set_value = data_set_value.order_by('-id').values()
        return self.paging(data_set_value, request.query_params, DataSetValueSerializer)

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
        data_set_id = request.query_params.get('data_set_id', None)
        data_set_bind = DataSetBind.objects.get_queryset()
        if data_set_id:
            data_set_bind = data_set_bind.filter(data_set_id__exact=int(data_set_id))
        data_set_bind = data_set_bind.order_by('-id').values()
        return self.paging(data_set_bind, request.query_params, DataSetBindSerializer)

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


@require_GET
def generates(request, req_id: int):
    t0 = time.perf_counter()
    fr = FillingRequirement.objects.get(pk=req_id)
    fill_excel(fr)
    took = time.perf_counter() - t0
    return JsonResponse(dict(requirement=req_id, took=took))


def base_list(obj, page: int = 1, size: int = 8):
    paginator = Paginator(obj, per_page=size)

    # 获取当前页的记录对象
    page_obj = paginator.get_page(page)

    # 构建返回的JSON数据
    response_data = {
        'data': tuple(page_obj),  # 将查询数据转为列表
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
    return JsonResponse(response_data)


@require_GET
@cache_page(60 * 60 * 2)
def get_generate_rule_list(request):
    all_gr = GenerateRule.objects.order_by('id').values()

    page = request.GET.get('page', default=1)
    size = request.GET.get('size', default=8)
    return base_list(all_gr, page, size)


@require_GET
@cache_page(60 * 60 * 2)
def get_generate_rule_parameter_list(request):
    """
    根据生成规则ID查询规则需要传的参数
    """
    rule_id = request.GET.get('rule', -1)
    if rule_id == -1:
        raise ValueError("未传生成规则ID")
    if not GenerateRule.objects.filter(id__exact=rule_id).exists():
        raise ValueError("生成规则数据不存在")
    gr = GenerateRule.objects.get(pk=rule_id)
    all_grp = gr.generateruleparameter_set.order_by('id').values()

    page = request.GET.get('page', default=1)
    size = request.GET.get('size', default=8)
    return base_list(all_grp, page, size)
