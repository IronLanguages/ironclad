
NUMBER_VALUE = 12345

class NumberI(object):
    def __index__(self):
        return int(NUMBER_VALUE)


class NumberF(object):
    def __float__(self):
        return float(NUMBER_VALUE)
