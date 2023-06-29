import logging
import operator

from .models import FillingRequirement, ColumnRule, DataParameter, GenerateRule
from .tools import fixed_value_iter, random_number_iter, time_serial_iter

__FUNCTIONS__ = {
    'fixed_value_iter': fixed_value_iter,
    'random_number_iter': random_number_iter,
    'time_serial_iter': time_serial_iter
}

log = logging.getLogger(__name__)


def get_normal_iter(column_rule, rule):
    param_list = DataParameter.objects.filter(column_rule_id__exact=column_rule.id)
    param_dict = dict(((p.name, p.value) for p in param_list))
    log.info(param_dict)
    try:
        it = __FUNCTIONS__.get(rule.function_name, None)(**param_dict)
        return it
    except TypeError:
        log.error(f'传入的方法名称不存在 {rule.function_name}')


def fill_excel(fr: FillingRequirement):
    column_rule_list = ColumnRule.objects.filter(requirement_id__exact=fr.id)
    column_rule_list: list[ColumnRule] = sorted(column_rule_list, key=operator.attrgetter('rule.fill_order'))
    for column_rule in column_rule_list:
        log.info(column_rule.column_name)
        it = get_normal_iter(column_rule, column_rule.rule)
        log.info(it)
        for idx, val in zip(range(10), it):
            log.info(f'{idx}={val}')
