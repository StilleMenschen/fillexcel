import time

from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views import generic
from django.views.decorators.http import require_GET, require_http_methods

from .models import FillingRequirement, GenerateRule, GenerateRuleParameter
from .service import fill_excel


# Create your views here.
class IndexView(generic.ListView):
    paginate_by = 8
    ordering = ['-id']
    model = FillingRequirement
    template_name = 'fills/index.html'
    context_object_name = 'filling_requirement_list'


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
    all_gr = GenerateRuleParameter.objects.order_by('rule_id', 'id').values()

    page = request.GET.get('page', default=1)
    size = request.GET.get('size', default=8)
    return base_list(all_gr, page, size)
