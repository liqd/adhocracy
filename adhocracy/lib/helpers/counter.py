

class Counter(object):

    def __init__(self):
        self.counters = {}

    def reset_counter(self, name):
        self.counters[name] = 0

    def next(self, name):
        if name not in self.counters:
            self.reset_counter(name)
        self.counters[name] += 1

    def get_letter(self, name):
        return chr(self.counters[name]+64)


counter = Counter()

