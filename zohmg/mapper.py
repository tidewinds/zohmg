from zohmg.config import Config

class Mapper(object):
    def __init__(self, usermapper):
        self.usermapper = usermapper
        self.projections = Config().projections()

    # wrapper around the user's mapper.
    def __call__(self, key, value):
        # from the usermapper: a timestamp, a point in n-space, units and their values.
        for (ts, point, units) in self.usermapper(key, value):
            for p in self.projections:
                # perform dimensionality reduction,
                reduced = {}
                for d in p:
                    reduced[d] = point[d]
                # yield for each requested projection.
                # include the projections list to get the order right.
                for u in units:
                    value = units[u]
                    yield (ts, p, reduced, u), value
