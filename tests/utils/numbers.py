
NUMBER_VALUE = 12345

class NumberI(object):
    def __int__(self):
        return int(NUMBER_VALUE)


class NumberL(object):
    def __long__(self):
        return long(NUMBER_VALUE)


class NumberF(object):
    def __float__(self):
        return float(NUMBER_VALUE)
