
class Distance(object):

    def __init__(self, place_from, place_to, distance):
        self.place_from = place_from
        self.place_to = place_to
        self.distance = distance

    def __lt__(self, other):  # Makes that sortable
        return self.distance < other.distance
