from django.shortcuts import render
from django.views import generic
from .models import FillingRequirement


# Create your views here.
class IndexView(generic.ListView):
    template_name = 'fills/index.html'
    context_object_name = 'filling_requirement_list'

    def get_queryset(self):
        return FillingRequirement.objects.all()
