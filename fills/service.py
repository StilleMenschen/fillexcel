import json
import logging
import operator
import sys
import time

from .models import DataSetBind, DataSetValue
from .models import FillingRequirement, ColumnRule, DataParameter
from .models import GenerateRule
from .tasks import write_to_excel
from .tools import fixed_value_iter, random_number_iter, time_serial_iter
from .tools import none_iter
from .tools import value_list_iter, associated_fill, calculate_expressions, join_string

__NORMAL_FUNCTIONS__ = {
    'fixed_value_iter': fixed_value_iter,
    'random_number_iter': random_number_iter,
    'time_serial_iter': time_serial_iter
}

log = logging.getLogger(__name__)


def write_value_list(column_rule: ColumnRule, rule: GenerateRule,
                     start_line: int, end_line: int, column_data: dict):
    """写入字符串数组"""
    param = DataParameter.objects.get(column_rule_id__exact=column_rule.id)
    data_value_list = DataSetValue.objects.filter(data_set__exact=param.data_set_id)
    if not len(data_value_list):
        log.warning(f'{rule.function_name} -> {column_rule.column_name}: 关联填充数据为空')
        return
    values = tuple(d.item for d in data_value_list)
    log.info('column: ' + column_rule.column_name)
    log.info('function: ' + rule.function_name)
    log.info('values: ' + str(values))
    column_range = range(start_line, end_line)
    column_data[column_rule.column_name] = tuple(val for _, val in zip(column_range, value_list_iter(values)))


def write_associated_list(column_rule: ColumnRule, rule: GenerateRule,
                          start_line: int, end_line: int, column_data: dict):
    """写入关联填入的对象数组"""
    t0 = time.perf_counter()
    param = DataParameter.objects.get(column_rule_id__exact=column_rule.id)
    data_bind = DataSetBind.objects.filter(data_set__exact=param.data_set_id, column_rule_id__exact=column_rule.id)
    data_value = DataSetValue.objects.filter(data_set__exact=param.data_set_id)
    if not len(data_bind) or not len(data_value):
        log.warning(f'{rule.function_name} -> {column_rule.column_name}: 关联填充数据为空')
        return
    log.info('function: ' + rule.function_name)
    # 数据集
    value_iter = value_list_iter((json.loads(v.item) for v in data_value))
    # 数据绑定
    bind_list = tuple((v.column_name, v.data_name) for v in data_bind)
    # 初始化列的数组
    for col, _ in bind_list:
        column_data[col] = []
    # 逐行执行
    for _ in range(start_line, end_line):
        # 每行的所有关联数据
        for col, val in associated_fill(bind_list, next(value_iter)):
            column_data[col].append(val)
    log.info(f'associated fill {time.perf_counter() - t0}')


def write_calculate_expressions(column_rule: ColumnRule, rule: GenerateRule,
                                start_line: int, end_line: int, column_data: dict):
    """计算给定的表达式"""
    t0 = time.perf_counter()
    param = DataParameter.objects.get(column_rule_id__exact=column_rule.id)
    expressions = param.value
    log.info('function: ' + rule.function_name)
    log.info('expressions: ' + expressions)
    count = 0
    data_list = []
    # 逐行执行
    for _ in range(start_line, end_line):
        try:
            # 取出当前行的列值
            value_dict = dict(((key, values[count]) for key, values in column_data.items()))
            # 添加计算值到数据列表
            data_list.append(calculate_expressions(expressions, value_dict))
        except Exception as e:
            log.error(e, exc_info=sys.exc_info())
            return
        count += 1
    # 填入数据
    column_data[column_rule.column_name] = data_list
    log.info(f'calculate expressions {time.perf_counter() - t0}')


def write_join_string(column_rule: ColumnRule, rule: GenerateRule,
                      start_line: int, end_line: int, column_data: dict):
    """特定字符拼接其它单元格的值"""
    t0 = time.perf_counter()
    param_list = DataParameter.objects.filter(column_rule_id__exact=column_rule.id)
    # 转换参数为字典
    param_dict = dict(((p.name, p.value) for p in param_list))
    delimiter = param_dict['delimiter']
    columns = param_dict['columns'].split(',')
    if not len(columns):
        log.warning(f'{rule.function_name} -> {column_rule.column_name}: 关联填充数据为空')
        return
    log.info('function: ' + rule.function_name)
    log.info('delimiter: ' + delimiter)
    log.info('columns: ' + str(columns))
    count = 0
    data_list = []
    # 逐行执行
    for _ in range(start_line, end_line):
        # 取出当前行的所需列值
        value_dict = dict(((key, values[count]) for key, values in column_data.items()))
        # 添加连接值到数据列表
        s = join_string(columns, value_dict, delimiter)
        data_list.append(s)
        count += 1
    # 填入数据
    column_data[column_rule.column_name] = data_list
    log.info(f'joining string {time.perf_counter() - t0}')


__ASSOCIATED_FUNCTION__ = {
    'value_list_iter': write_value_list,
    'associated_fill': write_associated_list,
    'calculate_expressions': write_calculate_expressions,
    'join_string': write_join_string
}


def exec_associated_of_iter(column_rule: ColumnRule, rule: GenerateRule,
                            start_line: int, end_line: int, column_data: dict):
    """执行关联数据的填入

    :param column_rule 列规则
    :param rule 生成规则
    :param start_line 起始行
    :param end_line 填入行数
    :param column_data 写入 Excel 的数据
    """
    # 传入的参数和值
    args = dict(**locals())
    a_f = __ASSOCIATED_FUNCTION__.get(rule.function_name, None)
    if a_f:
        return a_f(**args)
    else:
        return none_iter()


def match_normal_iter(column_rule: ColumnRule, rule: GenerateRule):
    """指定一般数据的填入"""
    param_list = DataParameter.objects.filter(column_rule_id__exact=column_rule.id)
    # 将参数转为字典，传给调用方法的命名关键字参数
    param_dict = dict(((p.name, p.value) for p in param_list))
    log.info('column: ' + column_rule.column_name)
    log.info('function: ' + rule.function_name)
    log.info('value: ' + str(param_dict))
    n_f = __NORMAL_FUNCTIONS__.get(rule.function_name, None)
    if n_f:
        return n_f(**param_dict)
    return none_iter()


def fill_excel(fr: FillingRequirement, hash_id):
    """填入数据到 Excel

    :param fr 填充规则
    :param hash_id 生成的文件ID
    """
    column_rule_list = ColumnRule.objects.filter(requirement_id__exact=fr.id)
    if not len(column_rule_list):
        raise ValueError('没有定义列填充规则，请先定义规则')
    # 按定义的顺序填充, 需要关联其它数据的放在后面处理, 先处理固定值的
    column_rule_list: list[ColumnRule] = sorted(column_rule_list, key=operator.attrgetter('rule.fill_order'))
    fill_data = {'requirementId': fr.id, 'fileId': fr.file_id, 'username': fr.username, 'hashId': hash_id,
                 'filename': fr.original_filename, 'startLine': fr.start_line, 'data': {}}
    column_data = fill_data['data']
    # 生成数据
    start_line, end_line = fr.start_line, fr.start_line + fr.line_number
    for column_rule in column_rule_list:
        # 有数据关联
        if column_rule.associated_of:
            exec_associated_of_iter(column_rule, column_rule.rule, start_line, end_line, column_data)
        # 非关联
        else:
            it = match_normal_iter(column_rule, column_rule.rule)
            column_range = range(start_line, end_line)
            column_data[column_rule.column_name] = tuple(val for _, val in zip(column_range, it))
    # 异步处理写入数据
    write_to_excel.apply_async(args=(fill_data,))
    del fill_data
    # result = write_to_excel.apply_async(args=(fill_data,))
    # log.info(result.get())
