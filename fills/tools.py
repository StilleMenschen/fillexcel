import datetime
import functools
import itertools
import random
import re
import threading


def fixed_value_iter(fixed_value):
    """固定值"""
    return itertools.cycle([fixed_value])


def value_list_iter(values):
    """特定的字符串数组"""
    values = tuple(values)
    return itertools.cycle(values)


def none_iter():
    """空的循环迭代"""
    while True:
        yield None


def random_number_iter(start=1, stop=42, is_decimal=False, ndigits=2):
    """范围随机整数或小数

    :param start 起始值
    :param stop 结束值
    :param is_decimal 是否包含小数位
    :param ndigits 小数位数
    """
    if is_decimal:
        start, stop, ndigits = max(1.0, float(start)), max(2.0, float(stop)), max(0, int(ndigits))
        if stop < start:
            start, stop = stop, start
        # 冻结参数
        func = functools.partial(_random_decimal, start, stop, ndigits)
    else:
        start, stop = max(1, int(start)), max(1, int(stop))
        if stop < start:
            start, stop = stop, start
        # 冻结参数
        func = functools.partial(random.randrange, int(start), int(stop))
    while True:
        # 数值转为字符串
        yield str(func())


def time_serial_iter(repeat=1):
    """日期时间组成的字符串

    :param repeat 每个字符串的重复次数
    """
    repeat = max(1, int(repeat))
    now = datetime.datetime.now()
    prefix = now.strftime('%Y%m%d-%H%M%S')
    c = itertools.count(1)
    while True:
        s = f'{prefix}-{next(c)}-{random.randrange(100, 999)}'
        for _ in range(repeat):
            yield s


def join_string(columns, value_dict, delimiter=None):
    """特定字符拼接多个值

    :param columns Excel 列名称，如 A AC AAD
    :param value_dict 列对应的值
    :param delimiter 拼接的字符，为空默认设为空字符串
    """
    if not delimiter:
        delimiter = str()
    return delimiter.join((value_dict[col] for col in columns))


def calculate_expressions(expressions, value_dict):
    """表达式计算

    :param expressions 表达式
    :param value_dict 单元格列对应的值
    """
    # 先校验正确性
    if str(expressions) and not validate_expressions(expressions):
        raise ValueError('expressions is invalid, allow character: 0-9 a-z A-Z +-*/. [space] {} ()')
    # 如果传入的值都是空的直接返回空
    if isinstance(value_dict, dict) and not len(value_dict):
        return None
    # 填入实际的单元格值
    compiled_expressions = _replace_expressions_variable(expressions, value_dict)
    # 利用内置的方法执行计算
    # 返回的数值转为字符串
    return str(eval(compiled_expressions))


def associated_fill(key_map_list: tuple, value_dict: dict):
    """关联填入数据

    :param key_map_list 单元格列名称
    :param value_dict
    """
    for column, name in key_map_list:
        yield column, value_dict.get(name, None)


def _random_decimal(start, stop, ndigits):
    """经过包装的随机范围小数生成"""
    return round(random.uniform(start, stop), ndigits)


def _replace_expressions_variable(expressions, value_dict):
    """利用正则表达式的方法将变量替换为实际的值

    如 A = 10, B = 101

    {A} * {B} + 100  --->  10 * 101 + 100
    """
    pattern = re.compile(r"\{([A-Z]+)\}")

    def inner_data_get(match):
        val = value_dict.get(match.group(1), match.group(0))
        # 正则替换的数据类型必须是字符串
        return val

    return pattern.sub(inner_data_get, expressions)


def try_calculate_expressions(expressions):
    """尝试填入1来计算表达式"""
    pattern = re.compile(r"\{([A-Z]+)\}")

    def inner_data_get(_):
        return '1'

    expressions = pattern.sub(inner_data_get, expressions)

    try:
        eval(expressions)
    except Exception:
        raise ValueError('表达式计算验证失败')


def validate_expressions(text):
    """校验表达式包含的字符是否符合要求"""
    valid = re.compile('^[0-9A-Z-+*/.{}() ]+$')
    if valid.match(text):
        return True
    else:
        return False


def run_in_thread(target=None, args=()):
    """线程中运行

    可以考虑将涉及 IO 的操作放在线程中调度

    :param target 目标函数
    :param args 函数参数
    """
    if not target:
        return
    t = threading.Thread(target=target, args=args)
    t.start()


def is_basic_ascii_visible(string):
    """校验字符串是否ASCII可见字符（不含空格）"""
    if not string or not len(string):
        return False
    # 遍历字符串中的每个字符
    for char in string:
        # 检查字符的ASCII值是否在32-126之间（不包括空格）
        if ord(char) <= 32 or ord(char) > 126:
            return False

    return True


if __name__ == '__main__':
    for item in zip(range(10), random_number_iter()):
        print(item, end=', ')
    for item in zip(range(10), random_number_iter(is_decimal=True)):
        print(item, end=', ')
    for item in zip(range(10), time_serial_iter(2)):
        print(item, end=', ')
