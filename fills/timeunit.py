import time
from enum import Enum

NANOSECONDS_PER_MICROSECOND = 1000
NANOSECONDS_PER_MILLISECOND = 1000 * NANOSECONDS_PER_MICROSECOND
NANOSECONDS_PER_SECOND = 1000 * NANOSECONDS_PER_MILLISECOND
NANOSECONDS_PER_MINUTES = 60 * NANOSECONDS_PER_SECOND
NANOSECONDS_PER_HOURS = 60 * NANOSECONDS_PER_MINUTES
NANOSECONDS_PER_DAYS = 24 * NANOSECONDS_PER_HOURS


class TimeUnit(Enum):
    """时间计算工具，未考虑计算数值溢出问题"""
    __slots__ = ()
    NANOSECONDS = 1
    MICROSECONDS = 2
    MILLISECONDS = 3
    SECONDS = 4
    MINUTES = 5
    HOURS = 6
    DAYS = 7

    @staticmethod
    def to_nanoseconds(duration, time_unit):
        if time_unit == TimeUnit.DAYS:
            return duration * NANOSECONDS_PER_DAYS
        elif time_unit == TimeUnit.HOURS:
            return duration * NANOSECONDS_PER_HOURS
        elif time_unit == TimeUnit.MINUTES:
            return duration * NANOSECONDS_PER_MINUTES
        elif time_unit == TimeUnit.SECONDS:
            return duration * NANOSECONDS_PER_SECOND
        elif time_unit == TimeUnit.MILLISECONDS:
            return duration * NANOSECONDS_PER_MILLISECOND
        elif time_unit == TimeUnit.MICROSECONDS:
            return duration * NANOSECONDS_PER_MICROSECOND
        elif time_unit == TimeUnit.NANOSECONDS:
            return duration
        else:
            raise ValueError('Invalid time unit')

    @staticmethod
    def convert(duration, source_time_unit, target_time_unit):
        nanoseconds = TimeUnit.to_nanoseconds(duration, source_time_unit)
        if target_time_unit == TimeUnit.DAYS:
            return nanoseconds / NANOSECONDS_PER_DAYS
        elif target_time_unit == TimeUnit.HOURS:
            return nanoseconds / NANOSECONDS_PER_HOURS
        elif target_time_unit == TimeUnit.MINUTES:
            return nanoseconds / NANOSECONDS_PER_MINUTES
        elif target_time_unit == TimeUnit.SECONDS:
            return nanoseconds / NANOSECONDS_PER_SECOND
        elif target_time_unit == TimeUnit.MILLISECONDS:
            return nanoseconds / NANOSECONDS_PER_MILLISECOND
        elif target_time_unit == TimeUnit.MICROSECONDS:
            return nanoseconds / NANOSECONDS_PER_MICROSECOND
        elif target_time_unit == TimeUnit.NANOSECONDS:
            return nanoseconds
        else:
            raise ValueError('Invalid time unit')

    @staticmethod
    def sleep(duration, time_unit):
        nanoseconds = TimeUnit.to_nanoseconds(duration, time_unit)
        time.sleep(nanoseconds / NANOSECONDS_PER_SECOND)


class TimeWrapper:
    """时间计算的包装类"""
    __slots__ = ('base_unit',)

    def __init__(self, base_unit=TimeUnit.NANOSECONDS):
        self.base_unit = base_unit

    def to_nanoseconds(self, duration):
        return TimeUnit.convert(duration, self.base_unit, TimeUnit.NANOSECONDS)

    def to_microseconds(self, duration):
        return TimeUnit.convert(duration, self.base_unit, TimeUnit.MICROSECONDS)

    def to_milliseconds(self, duration):
        return TimeUnit.convert(duration, self.base_unit, TimeUnit.MILLISECONDS)

    def to_seconds(self, duration):
        return TimeUnit.convert(duration, self.base_unit, TimeUnit.SECONDS)

    def to_minutes(self, duration):
        return TimeUnit.convert(duration, self.base_unit, TimeUnit.MINUTES)

    def to_hours(self, duration):
        return TimeUnit.convert(duration, self.base_unit, TimeUnit.HOURS)

    def to_days(self, duration):
        return TimeUnit.convert(duration, self.base_unit, TimeUnit.DAYS)


class DurationCalculator:
    """时间计算器
    第一个属性值为基础单位，第二个值为需要转换的单位

    dc = DurationCalculator()
    dc.hours.to_minutes(4)  # 240.0
    dc.minutes.to_seconds(20)  # 1200.0
    dc.days.to_minutes(2.5)  # 3600.0
    """
    __slots__ = ()
    nanoseconds = TimeWrapper(TimeUnit.NANOSECONDS)
    microseconds = TimeWrapper(TimeUnit.MICROSECONDS)
    milliseconds = TimeWrapper(TimeUnit.MILLISECONDS)
    seconds = TimeWrapper(TimeUnit.SECONDS)
    minutes = TimeWrapper(TimeUnit.MINUTES)
    hours = TimeWrapper(TimeUnit.HOURS)
    days = TimeWrapper(TimeUnit.DAYS)


dc = DurationCalculator()

if __name__ == '__main__':
    print(dc.hours.to_minutes(4))
    print(dc.minutes.to_seconds(20))
    print(dc.days.to_minutes(2.5))
