from django.urls import path

from . import views

app_name = "fills"

urlpatterns = (
    path("", views.IndexView.as_view(), name="index"),
    path("<int:req_id>", views.generates, name="generates"),
    path("requirement", views.FillingRequirementList.as_view(), {'format': 'json'}, name="requirement"),
    path("requirement/<int:pk>", views.FillingRequirementDetail.as_view(), name="requirement_detail"),
    path("columnRule", views.ColumnRuleList.as_view(), {'format': 'json'}, name="column_rule"),
    path("columnRule/<int:pk>", views.ColumnRuleDetail.as_view(), name="column_rule_detail"),
    path("generateRule", views.get_generate_rule_list, name="generate_rule_list"),
    path("generateRuleParameter", views.get_generate_rule_parameter_list, name="generate_rule_parameter_list"),
)
