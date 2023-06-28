import datetime
import functools
import itertools
import random
import re


def fixed_value_iter(value):
    return itertools.cycle([value])


def value_list_iter(values):
    values = list(values)
    return itertools.cycle(values)


def random_number_iter(start=1, stop=42, is_decimal=False, ndigits=2):
    if is_decimal:
        func = lambda: round(random.uniform(start, stop), ndigits)
    else:
        func = functools.partial(random.randrange, int(start), int(stop))
    while True:
        yield func()


def time_serial_iter(repeat=1):
    now = datetime.datetime.now()
    prefix = now.strftime('%Y%m%d-%H%M%S')
    c = itertools.count(1)
    while True:
        s = f'{prefix}-{next(c)}-{random.randrange(100, 999)}'
        for _ in range(repeat):
            yield s


def join_string(value_dict, delimiter=' '):
    if delimiter not in ' -_':
        raise ValueError("delimiter allow character: [space] - _")
    return delimiter.join(value_dict.values())


def calculate_expressions(expressions, value_dict):
    if str(expressions) and not _validate_expressions(expressions):
        raise ValueError('expressions is invalid, allow character: 0-9 a-z A-Z +-*/. [space] {} ()')
    if isinstance(value_dict, dict) and not len(value_dict):
        return ''
    compiled_expressions = _replace_expressions_variable(expressions, value_dict)
    return eval(compiled_expressions)


def associated_fill(key_map_list: list[tuple], value_dict: dict):
    for name, column in key_map_list:
        yield column, value_dict.get(name, '')


def _replace_expressions_variable(expressions, value_dict):
    pattern = re.compile(r"\{([A-Z]+)\}")
    return pattern.sub(lambda m: value_dict.get(m.group(1), m.group(0)), expressions)


def _validate_expressions(text):
    valid = re.compile('^[0-9a-zA-Z\-+*/.{}() ]+$')
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
