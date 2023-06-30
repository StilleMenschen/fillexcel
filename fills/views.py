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
    fr = FillingRequirement.objects.get(pk=req_id)
    fill_excel(fr)
    return JsonResponse(dict(name='jack', age=18))
