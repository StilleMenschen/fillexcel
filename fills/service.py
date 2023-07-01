import json
import logging
import operator

from fills.tasks import excel
from .models import DataValueList
from .models import FillingRequirement, ColumnRule, DataParameter
from .models import GenerateRule
from .tools import fixed_value_iter, random_number_iter, time_serial_iter
from .tools import none_iter
from .tools import value_list_iter

__NORMAL_FUNCTIONS__ = {
    'fixed_value_iter': fixed_value_iter,
    'random_number_iter': random_number_iter,
    'time_serial_iter': time_serial_iter
}
log = logging.getLogger(__name__)


def get_value_list_iter(column_rule: ColumnRule, rule: GenerateRule):
    param = DataParameter.objects.get(column_rule_id__exact=column_rule.id)
    value_group_id = int(param.value)
    data_value = DataValueList.objects.get(group_id__exact=value_group_id)
    values = json.loads(data_value.value_list)
    log.info('column: ' + column_rule.column_name)
    log.info('function: ' + rule.function_name)
    log.info('group_id: ' + param.value)
    return value_list_iter(values)


__ASSOCIATED_FUNCTION__ = {
    'value_list_iter': get_value_list_iter
}


def match_associated_of_iter(column_rule: ColumnRule, rule: GenerateRule):
    a_f = __ASSOCIATED_FUNCTION__.get(rule.function_name, None)
    if a_f:
        return a_f(column_rule, rule)
    else:
        return none_iter()


def match_normal_iter(column_rule: ColumnRule, rule: GenerateRule):
    param_list = DataParameter.objects.filter(column_rule_id__exact=column_rule.id)
    param_dict = dict(((p.name, p.value) for p in param_list))
    log.info('column: ' + column_rule.column_name)
    log.info('function: ' + rule.function_name)
    log.info('value: ' + str(param_dict))
    n_f = __NORMAL_FUNCTIONS__.get(rule.function_name, None)
    if n_f:
        return n_f(**param_dict)
    return none_iter()


def fill_excel(fr: FillingRequirement):
    column_rule_list = ColumnRule.objects.filter(requirement_id__exact=fr.id)
    column_rule_list: list[ColumnRule] = sorted(column_rule_list, key=operator.attrgetter('rule.fill_order'))
    fill_data = {'filename': fr.original_filename, 'startLine': fr.start_line, 'data': {}}
    data = fill_data['data']
    for column_rule in column_rule_list:
        # 有数据关联
        if column_rule.associated_of:
            it = match_associated_of_iter(column_rule, column_rule.rule)
        # 非关联
        else:
            it = match_normal_iter(column_rule, column_rule.rule)
        column_range = range(fr.start_line, fr.start_line + fr.line_number + 1)
        data[column_rule.column_name] = [val for _, val in zip(column_range, it)]
    result = excel.delay(fill_data)
    log.info(result.get())
