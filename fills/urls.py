from django.urls import path

from . import views

app_name = "fills"

urlpatterns = [
    path("", views.IndexView.as_view(), name="index"),
    path("<int:req_id>", views.generates, name="generates"),
    path("requirement", views.get_requirement_list, name="requirement_list"),
    path("generateRule", views.get_generate_rule_list, name="generate_rule_list"),
    path("generateRuleParameter", views.get_generate_rule_parameter_list, name="generate_rule_parameter_list"),
]
