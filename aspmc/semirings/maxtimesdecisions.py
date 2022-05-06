names = []

class MaxTimesFloat(object):
    def __init__(self, value, decisions):
        self.value = value
        self.decisions = decisions

    def __add__(self, other):
        return self if self.value >= other.value else other

    def __iadd__(self, other):
        if self.value < other.value:
            self.value = other.value
            self.decisions = other.decisions
        return self

    def __mul__(self, other):
        return MaxTimesFloat(self.value * other.value, self.decisions | other.decisions)

    def __imul__(self, other):
        self.value *= other.value
        self.decisions |= other.decisions
        return self

    def __str__(self):
        decisions = [ names[i] for i in range(len(names)) if self.decisions & 2**i ]
        decisions = ", ".join(decisions)
        return f"{self.value} with true atoms: {decisions}"

    def __repr__(self):
        return str(self)

def parse(value, atom = None):
    value = value[1:-1]
    value = value.split(',')
    return MaxTimesFloat(float(value[0]), int(value[1]))

def from_value(value):
    return MaxTimesFloat(value, 0)

def negate(value):
    return one()

def to_string(value):
    return f"({value.value},{value.decisions})"

def zero():
    return MaxTimesFloat(float("-inf"), 0)
def one():
    return MaxTimesFloat(1, 0)

dtype = object
pattern = '([+-]?([0-9]*[.])?[0-9]+,[0-9]+)'