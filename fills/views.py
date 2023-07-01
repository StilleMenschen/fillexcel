import time

from django.http import JsonResponse
from django.views import generic

from .models import FillingRequirement
from .service import fill_excel


# Create your views here.
class IndexView(generic.ListView):
    template_name = 'fills/index.html'
    context_object_name = 'filling_requirement_list'

    def get_queryset(self):
        return FillingRequirement.objects.all()


def get_requirement(request, req_id: int):
    t0 = time.perf_counter()
    fr = FillingRequirement.objects.get(pk=req_id)
    fill_excel(fr)
    took = time.perf_counter() - t0
    return JsonResponse(dict(requirement=req_id, took=took))
