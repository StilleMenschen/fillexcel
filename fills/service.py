import operator

from .models import FillingRequirement, ColumnRule

from tools import *


def fill_excel(fr: FillingRequirement):
    column_rule_list = ColumnRule.objects.filter(filling_requirement_id__exact=fr.id)
    column_rule_list: list[ColumnRule] = sorted(column_rule_list, key=operator.attrgetter('rule.fill_order'))
    for column_rule in column_rule_list:
        print(column_rule.column_name)
