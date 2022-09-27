class MinPlusFloat(object):
    def __init__(self, value):
        self.value = value

    def __add__(self, other):
        return self if self.value <= other.value else other

    def __iadd__(self, other):
        self.value = min(self.value, other.value)
        return self

    def __mul__(self, other):
        return MinPlusFloat(self.value + other.value)

    def __imul__(self, other):
        self.value += other.value
        return self

    def __str__(self):
        return str(self.value)

    def __repr__(self):
        return str(self)

def parse(value, atom = None):
    return MinPlusFloat(float(value))

def from_value(value):
    return MinPlusFloat(value)

def negate(value):
    return zero()

def to_string(value):
    return str(value.value)
    
def is_idempotent():
    return True

def zero():
    return MinPlusFloat(float("inf"))

def one():
    return MinPlusFloat(0)

dtype = object
pattern = '[+-]?([0-9]*[.])?[0-9]+'
