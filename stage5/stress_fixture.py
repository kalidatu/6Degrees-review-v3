"""Optional local review fixtures. Each hub owns a disjoint, ordered ID range."""

# Member ID, exact directory name, prefix for its contacts, first contact ID, degree.
REVIEW_HUBS = (
    (901, "Test Nina Nine", "Nina", 10001, 9),
    (902, "Test Felix Fifteen", "Felix", 11001, 15),
    (903, "Test Alex Morgan", "Alex", 12001, 126),
    (904, "Test Taylor Thousand", "Taylor", 13001, 1000),
)


def review_network():
    names = {}
    edges = []
    for hub, name, prefix, first, degree in REVIEW_HUBS:
        names[hub] = name
        for position in range(degree):
            member = first + position
            names[member] = f"{prefix} Circle {position + 1:04d}"
            edges.append((hub, member))
    return names, edges
