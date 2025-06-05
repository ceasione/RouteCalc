
class Distance:
    """
    Represents a directional distance between two geographic places, optionally including
    a numeric distance value in meters.

    Attributes:
        place_from: The starting location (must have .lat and .lng attributes).
        place_to: The destination location (must have .lat and .lng attributes).
        distance (float or int, optional): The resolved distance between the two locations in meters.
        resolved (bool): Indicates whether the distance value has been set.

    Methods:
        __eq__(other): Compares two Distance objects based on their coordinates.
        __lt__(other): Compares two resolved distances numerically.
        __hash__(): Allows Distance to be used in sets, based on lat/lng.
        __repr__(): Returns a human-readable string representation of the Distance.

    Exceptions:
        DistanceIsNotResolved: Raised when accessing or comparing an unresolved distance.

    Example:
        d = Distance(place_a, place_b)
        d.distance = 12300  # Resolves the distance to 12.3 km
        r. = Distance(place_a, place_b, 12300) # Creates resolved Distance at once
        print(d)  # Distance(place_a -> place_b, 12300)
    """
    class DistanceIsNotResolved(AttributeError):
        pass

    def __init__(self, place_from, place_to, distance=None):
        self.place_from = place_from
        self.place_to = place_to
        self._distance = None
        self.resolved: bool = False

        if distance is not None:
            self.distance = distance

    @property
    def distance(self):
        if self.resolved:
            return self._distance
        raise Distance.DistanceIsNotResolved(f'Distance between {self.place_from} and {self.place_to} is not resolved')

    @distance.setter
    def distance(self, dist):
        if dist is not None and isinstance(dist, (int, float)):
            self._distance = dist
            self.resolved = True

    def __lt__(self, other):
        if not isinstance(other, Distance):
            return NotImplemented
        if not self.resolved or not other.resolved:
            raise Distance.DistanceIsNotResolved("Both distances must be resolved to compare.")

        return self._distance < other._distance

    def __eq__(self, other):
        if not isinstance(other, Distance):
            return NotImplemented
        return all((
            round(self.place_from.lat, 6) == round(other.place_from.lat, 6),
            round(self.place_from.lng, 6) == round(other.place_from.lng, 6),
            round(self.place_to.lat, 6) == round(other.place_to.lat, 6),
            round(self.place_to.lng, 6) == round(other.place_to.lng, 6)
        ))

    def __hash__(self):
        return hash((
            round(self.place_from.lat, 6),
            round(self.place_from.lng, 6),
            round(self.place_to.lat, 6),
            round(self.place_to.lng, 6)
        ))

    def __repr__(self):
        if self.resolved:
            return f"Distance({self.place_from} -> {self.place_to}, {self._distance})"
        return f"Distance({self.place_from} -> {self.place_to}, unresolved)"
