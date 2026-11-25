"""All relationships in this fictional demo are public, explicit and undirected."""
from os import environ
from math import cos, sin, radians

from main import find_connection

from stage5.directory import public_directory
from stage5.stress_fixture import review_network

CORE_NAMES = dict(enumerate((
    "David", "Mary", "Kevin", "Laura", "Sinbad", "Alba", "Bram", "Cleo",
    "Dara", "Emil", "Faye", "Gio", "Hana", "Ivo", "Juno", "Kira",
    "Luca", "Mira", "Niko", "Opal", "Paz", "Quin", "Rhea", "Sol", "Tala",
), start=1))
# One isolated component, with 100 contacts shared by the two synthetic hubs.
STRESS_NAMES = {2000: "Test Hub 100", 2001: "Test Hub 1000"}
STRESS_NAMES.update({3000 + i: f"Test {i:04d}" for i in range(1, 1001)})
REVIEW_NAMES, REVIEW_EDGES = review_network() if environ.get("SIXDEGREES_REVIEW_FIXTURES", "1") != "0" else ({}, [])
DIRECTORY = public_directory(CORE_NAMES | STRESS_NAMES | REVIEW_NAMES)
NAMES = {i: member.name for i, member in DIRECTORY.items()}
HOME = 1
RELATIONSHIPS = [
    (1, 2), (2, 3), (3, 4), (1, 4), (4, 5),
    (2, 6), (2, 7), (2, 8), (2, 9), (2, 10), (2, 11), (2, 12),
    (3, 8), (3, 9), (3, 12), (3, 13), (3, 14), (3, 15), (3, 16),
    (4, 11), (4, 14), (4, 17), (4, 18),
    (5, 12), (5, 16), (5, 18), (5, 19), (5, 20),
    (6, 7), (8, 9), (13, 15), (17, 18), (19, 20),
    (7, 21), (13, 21), (17, 22), (19, 23), (21, 24), (22, 24),
    (23, 25), (24, 25),
    # Long Beach John connects through Alba, Paz and Tala.
    (6, 101), (21, 101), (25, 101),
    # Tacoma John and his local circle form an independent component.
    (102, 104), (102, 105), (102, 106), (104, 105),
]
RELATIONSHIPS.extend((2000, i) for i in range(3901, 4001))
RELATIONSHIPS.extend((2001, i) for i in range(3001, 4001))
RELATIONSHIPS.extend((i, i + 1) for i in range(3901, 4000))
RELATIONSHIPS.extend(REVIEW_EDGES)
NETWORK = {person: [] for person in NAMES}
for first, second in RELATIONSHIPS:
    NETWORK[first].append(second)
    NETWORK[second].append(first)


NODE_BUDGET = max(1, int(environ.get("SIXDEGREES_NODE_BUDGET", 16)))
EDGE_BUDGET = max(1, int(environ.get("SIXDEGREES_EDGE_BUDGET", 32)))


def visible_members(focus, required, node_budget=NODE_BUDGET, edge_budget=EDGE_BUDGET):
    """Keep all induced edges. Spend remaining capacity on direct contacts in ID order."""
    visible = set(required) | {focus}
    edges = sum(sum(n in visible for n in NETWORK[i]) for i in visible) // 2
    for candidate in sorted(NETWORK[focus]):
        if len(visible) >= node_budget:
            break
        if candidate in visible:
            continue
        cost = sum(n in visible for n in NETWORK[candidate])
        if edges + cost <= edge_budget:
            visible.add(candidate)
            edges += cost
    return visible


def layout(route, visible):
    focus = route[-1]
    positions = {focus: (0, 0)}
    # Leave enough room for labels even on deep walks. Pan to inspect the tail.
    for index, person in enumerate(reversed(route[:-1]), start=1):
        positions[person] = (-100 * index, -60 if index % 2 else 35)
    neighbors = sorted((visible & set(NETWORK[focus])) - set(route))
    spread = min(76, 20 * len(neighbors))
    for index, person in enumerate(neighbors):
        angle = radians(-spread + 2 * spread * index / (len(neighbors) - 1)) if len(neighbors) > 1 else 0
        if len(neighbors) > 10:
            positions[person] = (160 + 145 * (index % 2), (index // 2 - (len(neighbors)-1)/4) * 67)
        else:
            positions[person] = (round(243 * cos(angle)), round(214 * sin(angle)))
    for index, person in enumerate(sorted(visible - positions.keys())):
        positions[person] = (-96 - index * 100, 155)
    return positions


def path_edges(route):
    return {tuple(sorted(pair)) for pair in zip(route, route[1:])}


def graph_data(route, shortest):
    focus = route[-1]
    anchor = find_connection(HOME, route[0], NETWORK)
    visible = visible_members(focus, set(anchor or ()) | set(route) | set(shortest or ()))
    positions = layout(route, visible)
    return render_graph(positions, focus, path_edges(route), path_edges(shortest or ()))


def render_graph(positions, focus, bold_edges, shortest_edges):
    visible = positions.keys()
    nodes = []
    for person in sorted(visible):
        x, y = positions[person]
        nodes.append(dict(id=person, label=NAMES[person], x=x, y=y, fixed=True,
                          size=26 if person == focus else 18,
                          color="#e3a640" if person == focus else "#5fa69b"))
    edges = []
    for a, b in RELATIONSHIPS:
        if a not in visible or b not in visible:
            continue
        key = (a, b)
        style = {}
        if key in shortest_edges:
            style = dict(color="#194d98", width=4, dashes=True)
        elif key in bold_edges:
            style = dict(color="#087565", width=4)
        edges.append({"id": f"{a}-{b}", "from": a, "to": b, **style})
    return {"nodes": nodes, "edges": edges}
