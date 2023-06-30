import logging
import operator

from .models import FillingRequirement, ColumnRule, DataParameter
from .tools import fixed_value_iter, random_number_iter, time_serial_iter
from fills.tasks import excel

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
    it = __FUNCTIONS__.get(rule.function_name, None)(**param_dict)
    return it


def fill_excel(fr: FillingRequirement):
    column_rule_list = ColumnRule.objects.filter(requirement_id__exact=fr.id)
    column_rule_list: list[ColumnRule] = sorted(column_rule_list, key=operator.attrgetter('rule.fill_order'))
    fill_data = {'filename': fr.original_filename, 'startLine': fr.start_line, 'data': {}}
    data = fill_data['data']
    for column_rule in column_rule_list:
        log.info(column_rule.column_name)
        it = get_normal_iter(column_rule, column_rule.rule)
        data[column_rule.column_name] = [val for _, val in zip(range(fr.start_line, fr.line_number + 1), it)]
    result = excel.delay(fill_data)
    log.info(result.get())
