import datetime
import functools
import itertools
import random
import re


def fixed_value_iter(value):
    return itertools.cycle([value])


def value_list_iter(values):
    values = tuple(values)
    return itertools.cycle(values)


def none_iter():
    while True:
        yield None


def random_number_iter(start=1, stop=42, is_decimal=False, ndigits=2):
    if is_decimal:
        start, stop = float(start), float(stop)
        func = functools.partial(_random_decimal, start, stop, ndigits)
    else:
        start, stop = int(start), int(stop)
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


def join_string(value_dict, delimiter=' '):
    return delimiter.join(value_dict.values())


def calculate_expressions(expressions, value_dict):
    if str(expressions) and not _validate_expressions(expressions):
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


def _validate_expressions(text):
    valid = re.compile('^[0-9a-zA-Z-+*/.{}() ]+$')
    if valid.match(text):
        return True
    else:
        return False


if __name__ == '__main__':
    for item in zip(range(10), random_number_iter()):
        print(item, end=', ')
    for item in zip(range(10), random_number_iter(is_decimal=True)):
        print(item, end=', ')
    for item in zip(range(10), time_serial_iter(2)):
        print(item, end=', ')
