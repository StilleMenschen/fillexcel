import json
import logging
import operator

from .models import DataSetValue
from .models import FillingRequirement, ColumnRule, DataParameter
from .models import GenerateRule
from .tasks import excel
from .tools import fixed_value_iter, random_number_iter, time_serial_iter
from .tools import none_iter
from .tools import value_list_iter

__NORMAL_FUNCTIONS__ = {
    'fixed_value_iter': fixed_value_iter,
    'random_number_iter': random_number_iter,
    'time_serial_iter': time_serial_iter
}

log = logging.getLogger(__name__)


def get_value_list_iter(column_rule: ColumnRule, rule: GenerateRule,
                        start_line: int, end_line: int, column_data: dict):
    param = DataParameter.objects.get(column_rule_id__exact=column_rule.id)
    data_value = DataSetValue.objects.get(data_set__exact=param.data_set_id)
    values = json.loads(data_value.item)
    log.info('column: ' + column_rule.column_name)
    log.info('function: ' + rule.function_name)
    log.info('values: ' + data_value.item)
    column_range = range(start_line, end_line)
    column_data[column_rule.column_name] = [val for _, val in zip(column_range, value_list_iter(values))]


__ASSOCIATED_FUNCTION__ = {
    'value_list_iter': get_value_list_iter
}


def exec_associated_of_iter(column_rule: ColumnRule, rule: GenerateRule,
                            start_line: int, end_line: int, column_data: dict):
    # 传入的参数和值
    args = dict(**locals())
    a_f = __ASSOCIATED_FUNCTION__.get(rule.function_name, None)
    if a_f:
        return a_f(**args)
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
    column_data = fill_data['data']

    start_line, end_line = fr.start_line, fr.start_line + fr.line_number + 1
    for column_rule in column_rule_list:
        # 有数据关联
        if column_rule.associated_of:
            exec_associated_of_iter(column_rule, column_rule.rule, start_line, end_line, column_data)
        # 非关联
        else:
            it = match_normal_iter(column_rule, column_rule.rule)
            column_range = range(start_line, end_line)
            column_data[column_rule.column_name] = [val for _, val in zip(column_range, it)]

    result = excel.delay(fill_data)
    log.info(result.get())
