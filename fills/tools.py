import datetime
import functools
import itertools
import random
import re
import threading


def fixed_value_iter(fixed_value):
    return itertools.cycle([fixed_value])


def value_list_iter(values):
    values = tuple(values)
    return itertools.cycle(values)


def none_iter():
    while True:
        yield None


def random_number_iter(start=1, stop=42, is_decimal=False, ndigits=2):
    if is_decimal:
        start, stop, ndigits = float(start), float(stop), int(ndigits)
        if stop < start:
            start, stop = stop, start
        func = functools.partial(_random_decimal, start, stop, ndigits)
    else:
        start, stop = int(start), int(stop)
        if stop < start:
            start, stop = stop, start
        func = functools.partial(random.randrange, int(start), int(stop))
    while True:
        yield str(func())


def time_serial_iter(repeat=1):
    repeat = int(repeat)
    now = datetime.datetime.now()
    prefix = now.strftime('%Y%m%d-%H%M%S')
    c = itertools.count(1)
    while True:
        s = f'{prefix}-{next(c)}-{random.randrange(100, 999)}'
        for _ in range(repeat):
            yield s


def join_string(columns, value_dict, delimiter=' '):
    return delimiter.join((value_dict[col] for col in columns))


def calculate_expressions(expressions, value_dict):
    if str(expressions) and not validate_expressions(expressions):
        raise ValueError('expressions is invalid, allow character: 0-9 a-z A-Z +-*/. [space] {} ()')
    if isinstance(value_dict, dict) and not len(value_dict):
        return None
    compiled_expressions = _replace_expressions_variable(expressions, value_dict)
    return str(eval(compiled_expressions))


def associated_fill(key_map_list: tuple, value_dict: dict):
    for column, name in key_map_list:
        yield column, value_dict.get(name, None)


def _random_decimal(start, stop, ndigits):
    return round(random.uniform(start, stop), ndigits)


def _replace_expressions_variable(expressions, value_dict):
    pattern = re.compile(r"\{([A-Z]+)\}")

    def inner_data_get(match):
        val = value_dict.get(match.group(1), match.group(0))
        # 正则替换的数据类型必须是字符串
        return val

    return pattern.sub(inner_data_get, expressions)


def try_calculate_expressions(expressions):
    pattern = re.compile(r"\{([A-Z]+)\}")

    def inner_data_get(_):
        return '1'

    expressions = pattern.sub(inner_data_get, expressions)

    try:
        eval(expressions)
    except Exception:
        raise ValueError('表达式计算验证失败')


def validate_expressions(text):
    valid = re.compile('^[0-9A-Z-+*/.{}() ]+$')
    if valid.match(text):
        return True
    else:
        return False


def run_in_thread(target=None, args=()):
    if not target:
        return
    t = threading.Thread(target=target, args=args)
    t.start()


def is_basic_ascii_visible(string):
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
