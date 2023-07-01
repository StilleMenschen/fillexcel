from django.urls import path

from . import views

app_name = "fills"

urlpatterns = [
    path("", views.IndexView.as_view(), name="index"),
    path("<int:req_id>/", views.get_requirement, name="get_requirement"),
]
