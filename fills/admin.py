from django.contrib import admin

from .models import FillingRequirement, ColumnRule, DataParameter
from .models import GenerateRule, GenerateRuleParameter


# Register your models here.
class FillingRequirementAdmin(admin.ModelAdmin):
    list_display = ('username', 'remark', 'file_id', 'original_filename', 'start_line', 'line_number', 'created_at',
                    'updated_at')


class ColumnRuleAdmin(admin.ModelAdmin):
    list_display = ('filling_requirement_id', 'rule_id', 'data_param_id', 'column_name', 'column_type', 'associated_of')


class DataParameterAdmin(admin.ModelAdmin):
    list_display = ('param_rule_id', 'name', 'value', 'expressions', 'data_define_group_id', 'data_bind_group_id')


class GenerateRuleAdmin(admin.ModelAdmin):
    list_display = ('id', 'rule_name', 'function_name', 'fill_order', 'description', 'created_at', 'updated_at')


class GenerateRuleParameterAdmin(admin.ModelAdmin):
    list_display = ('rule_id', 'name', 'data_type', 'description', 'required', 'default_value',
                    'need_outside_data', 'created_at', 'updated_at')


admin.site.register(FillingRequirement, FillingRequirementAdmin)
admin.site.register(ColumnRule, ColumnRuleAdmin)
admin.site.register(DataParameter, DataParameterAdmin)
admin.site.register(GenerateRule, GenerateRuleAdmin)
admin.site.register(GenerateRuleParameter, GenerateRuleParameterAdmin)
