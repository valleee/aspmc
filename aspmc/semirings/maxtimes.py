class MaxTimesFloat(object):
    def __init__(self, value):
        self.value = value

    def __add__(self, other):
        return self if self.value >= other.value else other

    def __iadd__(self, other):
        self.value = max(self.value, other.value)
        return self

    def __mul__(self, other):
        return MaxTimesFloat(self.value * other.value)

    def __imul__(self, other):
        self.value *= other.value
        return self

    def __str__(self):
        return str(self.value)

    def __repr__(self):
        return str(self)

def parse(value, atom = None):
    return MaxTimesFloat(float(value))

def from_value(value):
    return MaxTimesFloat(value)

def negate(value):
    return zero()

def to_string(value):
    return str(value.value)

def is_idempotent():
    return True

def zero():
    return MaxTimesFloat(0.0)
def one():
    return MaxTimesFloat(1.0)
dtype = object
pattern = '(1(\\.0[0]*)?|0\\.[0-9]+)'