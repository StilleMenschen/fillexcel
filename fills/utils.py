import time


class IllegalArgumentError(Exception):
    pass


class SnowFlake:
    """雪花算法

    没有考虑并发的加锁问题
    """
    # start at 2023-06-22T00:00:00
    TIME_EPOCH = 1687363200000

    SEQUENCE_BIT = 3
    MACHINE_BIT = 5
    DATACENTER_BIT = 5

    MAX_DATACENTER_NUM = ~(-1 << DATACENTER_BIT)
    MAX_MACHINE_NUM = ~(-1 << MACHINE_BIT)
    MAX_SEQUENCE = ~(-1 << SEQUENCE_BIT)
    # MAX_SEQUENCE = -1 ^ (-1 << SEQUENCE_BIT)

    MACHINE_LEFT = SEQUENCE_BIT
    DATACENTER_LEFT = SEQUENCE_BIT + MACHINE_BIT

    TIMESTAMP_LEFT = DATACENTER_LEFT + DATACENTER_BIT

    sequence = 0
    last_stamp = -1

    def __init__(self, datacenter_id, machine_id):
        if datacenter_id > self.MAX_DATACENTER_NUM or datacenter_id < 0:
            raise IllegalArgumentError("datacenterId can't be greater than MAX_DATACENTER_NUM or less than 0")
        if machine_id > self.MAX_MACHINE_NUM or machine_id < 0:
            raise IllegalArgumentError("machineId can't be greater than MAX_MACHINE_NUM or less than 0")
        self.machine_id = machine_id
        self.datacenter_id = datacenter_id

    def next_id(self):
        curr_stamp = self.get_new_stamp()
        if curr_stamp < self.last_stamp:
            raise RuntimeError("Clock moved backwards. Refusing to generate id")

        if curr_stamp == self.last_stamp:
            # Self-incrementing serial number within the same millisecond
            self.sequence = (self.sequence + 1) & self.MAX_SEQUENCE
            # The number of sequences in the same millisecond has reached its maximum
            if self.sequence == 0:
                curr_stamp = self.get_next_mill()
        else:
            # Within different milliseconds, the serial number is set to 0
            self.sequence = 0

        self.last_stamp = curr_stamp

        return (curr_stamp - self.TIME_EPOCH) << self.TIMESTAMP_LEFT | self.datacenter_id << \
            self.DATACENTER_LEFT | self.machine_id << self.MACHINE_LEFT | self.sequence

    def get_next_mill(self):
        mill = self.get_new_stamp()
        while mill <= self.last_stamp:
            mill = self.get_new_stamp()
        return mill

    @staticmethod
    def get_new_stamp():
        return int(time.time() * 1000)


if __name__ == '__main__':
    sf = SnowFlake(0, 0)
    for _ in range(8):
        print(sf.next_id())
