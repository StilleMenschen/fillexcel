from django.urls import path

from . import views

app_name = "fills"

urlpatterns = (
    path("", views.IndexView.as_view(), name="index"),
    # 填充表格
    path("<int:req_id>", views.generates, name="generates"),
    # 填充要求
    path("requirement", views.FillingRequirementList.as_view(), {'format': 'json'}, name="requirement"),
    path("requirement/<int:pk>", views.FillingRequirementDetail.as_view(), name="requirement_detail"),
    # 列规则
    path("columnRule", views.ColumnRuleList.as_view(), {'format': 'json'}, name="column_rule"),
    path("columnRule/<int:pk>", views.ColumnRuleDetail.as_view(), name="column_rule_detail"),
    # 列规则参数
    path("dataParameter", views.DataParameterList.as_view(), {'format': 'json'}, name="data_parameter"),
    path("dataParameter/<int:pk>", views.DataParameterDetail.as_view(), name="data_parameter_detail"),
    # 数据集
    path("dataSet", views.DataSetList.as_view(), {'format': 'json'}, name="data_set"),
    path("dataSet/<int:pk>", views.DataSetDetail.as_view(), name="data_set_detail"),
    # 数据集定义
    path("dataSetDefine", views.DataSetDefineList.as_view(), {'format': 'json'}, name="data_set_define"),
    path("dataSetDefine/<int:pk>", views.DataSetDefineDetail.as_view(), name="data_set_define_detail"),
    # 数据集数据
    path("dataSetValue", views.DataSetValueList.as_view(), {'format': 'json'}, name="data_set_value"),
    path("dataSetValue/<int:pk>", views.DataSetValueDetail.as_view(), name="data_set_value_detail"),
    # 数据集绑定
    path("dataSetBind", views.DataSetBindList.as_view(), {'format': 'json'}, name="data_set_bind"),
    path("dataSetBind/<int:pk>", views.DataSetBindDetail.as_view(), name="data_set_bind_detail"),
    # 生成规则和参数
    path("generateRule", views.get_generate_rule_list, name="generate_rule_list"),
    path("generateRuleParameter", views.get_generate_rule_parameter_list, name="generate_rule_parameter_list"),
)
