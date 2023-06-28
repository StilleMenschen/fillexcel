from django.contrib import admin
from .models import FillingRequirement
from .models import GenerateRule, GenerateRuleParameter


# Register your models here.
class FillingRequirementAdmin(admin.ModelAdmin):
    list_display = ('username', 'remark', 'file_id', 'original_filename',
                    'start_line', 'line_number', 'created_at', 'updated_at')


class GenerateRuleAdmin(admin.ModelAdmin):
    list_display = ('rule_name', 'function_name', 'fill_order', 'description',
                    'created_at', 'updated_at')


class GenerateRuleParameterAdmin(admin.ModelAdmin):
    list_display = ('rule_id', 'name', 'data_type', 'description', 'required',
                    'default_value', 'need_outside_data', 'created_at',
                    'updated_at')


admin.site.register(FillingRequirement, FillingRequirementAdmin)
admin.site.register(GenerateRule, GenerateRuleAdmin)
admin.site.register(GenerateRuleParameter, GenerateRuleParameterAdmin)
