from django.urls import path

from . import views

app_name = "fills"

urlpatterns = (
    path("", views.IndexView.as_view(), name="index"),
    # 填充表格
    path("<int:requirement_id>", views.GeneratesView.as_view(), name="generates"),
    path("upload", views.FileUploadView.as_view(), name="upload"),
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
    # 文件生成记录
    path("fileRecord", views.FileRecordList.as_view(), {'format': 'json'}, name="file_record"),
    path("fileRecord/<int:pk>", views.FileRecordDetail.as_view(), name="file_record_detail"),
    # 生成规则
    path("generateRule", views.GenerateRuleList.as_view(), {'format': 'json'}, name="generate_rule"),
    path("generateRule/<int:pk>", views.GenerateRuleDetail.as_view(), name="generate_rule_detail"),
    # 生成规则参数
    path("generateRuleParameter", views.GenerateRuleParameterList.as_view(), {'format': 'json'},
         name="generate_rule_parameter"),
    path("generateRuleParameter/<int:pk>", views.GenerateRuleParameterDetail.as_view(),
         name="generate_rule_parameter_detail"),
)
