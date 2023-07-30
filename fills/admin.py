from django.contrib import admin

from .models import DataSet, DataSetDefine, DataSetValue, DataSetBind
from .models import FileRecord
from .models import FillingRequirement, ColumnRule, DataParameter
from .models import GenerateRule, GenerateRuleParameter


# Register your models here.
class FillingRequirementAdmin(admin.ModelAdmin):
    list_display = ('id', 'username', 'remark', 'file_id', 'original_filename', 'start_line', 'line_number',
                    'created_at', 'updated_at')
    list_per_page = 16


class ColumnRuleAdmin(admin.ModelAdmin):
    list_display = ('requirement_id', 'rule_id', 'column_name', 'column_type', 'associated_of')
    list_filter = ('requirement_id',)
    list_per_page = 16


class DataParameterAdmin(admin.ModelAdmin):
    list_display = ('param_rule_id', 'column_rule_id', 'name', 'value', 'data_set_id')
    list_filter = ("param_rule_id", 'column_rule_id')
    list_per_page = 16


class GenerateRuleAdmin(admin.ModelAdmin):
    list_display = ('id', 'rule_name', 'function_name', 'fill_order', 'description', 'created_at', 'updated_at')


class GenerateRuleParameterAdmin(admin.ModelAdmin):
    list_display = ('rule_id', 'name', 'data_type', 'description', 'hints', 'required', 'default_value',
                    'need_outside_data', 'created_at', 'updated_at')
    list_filter = ("rule_id",)


class DataSetAdmin(admin.ModelAdmin):
    list_display = ('id', 'username', 'description', 'data_type', 'created_at', 'updated_at')
    list_per_page = 16


class DataSetDefineAdmin(admin.ModelAdmin):
    list_display = ('id', 'data_set_id', 'name', 'data_type', 'created_at', 'updated_at')
    list_filter = ('data_set_id',)
    list_per_page = 16


class DataSetValueAdmin(admin.ModelAdmin):
    list_display = ('id', 'data_set_id', 'item', 'data_type', 'created_at', 'updated_at')
    list_filter = ('data_set_id',)
    list_per_page = 16


class DataSetBindAdmin(admin.ModelAdmin):
    list_display = ('id', 'data_set_id', 'column_name', 'data_name', 'created_at', 'updated_at')
    list_per_page = 16


class FileRecordAdmin(admin.ModelAdmin):
    list_display = ('id', 'requirement_id', 'username', 'file_id', 'filename', 'created_at')
    list_per_page = 16


admin.site.register(FillingRequirement, FillingRequirementAdmin)
admin.site.register(ColumnRule, ColumnRuleAdmin)
admin.site.register(DataParameter, DataParameterAdmin)
admin.site.register(GenerateRule, GenerateRuleAdmin)
admin.site.register(GenerateRuleParameter, GenerateRuleParameterAdmin)

admin.site.register(DataSet, DataSetAdmin)
admin.site.register(DataSetDefine, DataSetDefineAdmin)
admin.site.register(DataSetValue, DataSetValueAdmin)
admin.site.register(DataSetBind, DataSetBindAdmin)

admin.site.register(FileRecord, FileRecordAdmin)
