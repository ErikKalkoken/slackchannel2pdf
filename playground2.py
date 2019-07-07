class Parrot:
    def __init__(self, flag):
        if flag:
            self._voltage = 100000
        else:
            self._voltage = 500

    @property
    def voltage(self):
        return self._voltage


x = Parrot(True)
print(x.voltage)

y = Parrot(False)
print(y.voltage)