import logging
import time
import typing

from django.contrib.auth.models import User, Group
from django.core.paginator import Paginator
from django.http import JsonResponse, QueryDict, Http404
from django.views import generic
from django.views.decorators.cache import cache_page
from django.views.decorators.http import require_GET, require_http_methods
from rest_framework import permissions, viewsets, status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import Serializer
from rest_framework.views import APIView

from .cache import CacheManager
from .models import FillingRequirement, GenerateRule
from .serializers import FillingRequirementSerializer
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
    permission_classes = [permissions.IsAuthenticated]


class GroupViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows groups to be viewed or edited.
    """
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    permission_classes = [permissions.IsAuthenticated]


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
    处理查询所有/新增
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
    处理单个查询/修改/删除
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
        self.invalid_cache(pk)
        requirement = self.get_object(pk)
        serializer = FillingRequirementSerializer(requirement, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        self.invalid_cache(pk)
        requirement = self.get_object(pk)
        requirement.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@require_http_methods(['GET', 'POST'])
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
@cache_page(60 * 60 * 6)
def get_requirement_list(request):
    all_fr = FillingRequirement.objects.order_by('-id').values()

    page = request.GET.get('page', default=1)
    size = request.GET.get('size', default=8)
    return base_list(all_fr, page, size)


@require_GET
def get_generate_rule_list(request):
    all_gr = GenerateRule.objects.order_by('id').values()

    page = request.GET.get('page', default=1)
    size = request.GET.get('size', default=8)
    return base_list(all_gr, page, size)


@require_GET
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
