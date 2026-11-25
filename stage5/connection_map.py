"""Bounded loopless route selection and a left-to-right route diagram."""
from itertools import islice

import networkx as nx

from stage5.demo import HOME, NAMES, NETWORK, layout, path_edges, render_graph, visible_members


def ranked_routes(network, origin, target, limit):
    if limit not in (3, 5):
        raise ValueError("Choose 3 or 5 routes")
    graph = nx.Graph()
    graph.add_nodes_from(sorted(network))
    graph.add_edges_from(sorted((a, b) for a in network for b in network[a] if a < b))
    try:
        # Yen's algorithm generates only the requested prefix. Canonical
        # insertion order makes tie discovery repeatable for stable member IDs.
        return list(islice(nx.shortest_simple_paths(graph, origin, target), limit))
    except nx.NetworkXNoPath:
        return []


def map_graph(target, routes):
    visible = visible_members(target, set().union(*routes))
    positions = layout((target,), visible)
    if routes:
        # Put the endpoints on the middle row and give each alternate route
        # its own lane. Shared people reuse their earliest-ranked position.
        span = max(2, max(len(path)-1 for path in routes)) * 125
        positions = {HOME: (0, 0), target: (span, 0)}
        for rank, path in enumerate(routes):
            row = ((rank+1)//2) * (1 if rank % 2 else -1)
            for index, person in enumerate(path[1:-1], 1):
                positions.setdefault(person, (round(span * index / (len(path)-1)), row * 100))
        context = sorted(visible - positions.keys())
        for index, person in enumerate(context):
            positions[person] = (span + 155 + (index % 2) * 75, (index-(len(context)-1)/2)*77)
    secondary = set().union(*(path_edges(path) for path in routes[1:]))
    data = render_graph(positions, target, secondary, path_edges(routes[0]) if routes else set())
    for node in data["nodes"]:
        if node["id"] == target:
            role = "Origin & destination" if target == HOME else "Destination"
            node["label"] = f"{NAMES[target]}\n{role}"
        elif node["id"] == HOME:
            node.update(label=f"{NAMES[HOME]}\nOrigin", color="#588ac1")
    return data
