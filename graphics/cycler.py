class Cycler:
    def __init__(self, values, default=0):
        self.values = values
        if type(default) is not int or default > len(values):
            default = values.index(default)
        self.i = default

    def choose(self, val):
        if val in self.values:
            self.i = self.values.index(val)

    def nxt(self):  # not named "next" to prevent using a Cycler as an iterator, which would hang
        self.i = (self.i + 1) % len(self.values)
        return self.value()

    def value(self):
        return self.values[self.i]

    def __str__(self):
        return str(self.value())


class PercentCycler(Cycler):
    def __str__(self):
        v = self.value()
        if type(v) == float and (v < .1 or v > .9) and not v in (0., 1.):
            return "%2.2f%%" % (v*100.)
        else:
            return "%2.1f%%" % (v*100.)
