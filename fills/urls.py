from django.urls import path

from . import views

app_name = "fills"

urlpatterns = [
    path("", views.IndexView.as_view(), name="index"),
    path("<int:req_id>/", views.generates, name="generates"),
    path("requirement/", views.get_paging_requirement_list, name="requirement_list"),
]
