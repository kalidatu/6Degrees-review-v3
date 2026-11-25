"""Run from repository root with python -m unittest stage5.test_demo."""
import unittest
from itertools import combinations

from main import find_connection
from stage5.demo import REVIEW_NAMES, CORE_NAMES, DIRECTORY, HOME, NAMES, NETWORK, RELATIONSHIPS, graph_data


ORIGINAL = [i for i in NAMES if i < 2000 and i not in REVIEW_NAMES]


class DemoTests(unittest.TestCase):
    def test_explicit_fixture(self):
        self.assertEqual(len(CORE_NAMES), 25)
        self.assertEqual([len(NETWORK[i]) for i in range(1, 6)], [2, 9, 9, 7, 6])
        self.assertEqual(set(NETWORK[HOME]), {2, 4})
        self.assertEqual(set(NETWORK[HOME]) & set(NETWORK[5]), {4})
        self.assertEqual(len(set(RELATIONSHIPS)), len(RELATIONSHIPS))
        for a, b in RELATIONSHIPS:
            self.assertTrue(a in NAMES and b in NAMES and a < b)
        self.assertEqual(find_connection(1, 5, NETWORK), [1, 4, 5])

    def test_all_pairs(self):
        # Floyd–Warshall oracle, independent of the application's BFS.
        d = {(a, b): 0 if a == b else 100 for a in ORIGINAL for b in ORIGINAL}
        for a, b in RELATIONSHIPS:
            if a in ORIGINAL:
                d[a, b] = d[b, a] = 1
        for k in ORIGINAL:
            for a in ORIGINAL:
                for b in ORIGINAL:
                    d[a, b] = min(d[a, b], d[a, k] + d[k, b])
        for (a, b), distance in d.items():
            route = find_connection(a, b, NETWORK)
            if distance == 100:
                self.assertIsNone(route)
                continue
            self.assertEqual((route[0], route[-1], len(route)-1), (a, b, distance))
            self.assertTrue(all(v in NETWORK[u] for u, v in zip(route, route[1:])))

    def test_every_neighborhood(self):
        for focus in ORIGINAL:
            shortest = find_connection(HOME, focus, NETWORK)
            graph = graph_data(shortest or (focus,), shortest)
            ids = [node["id"] for node in graph["nodes"]]
            visible = {focus} | set(shortest or ()) | set(NETWORK[focus])
            self.assertCountEqual(ids, visible)
            self.assertCountEqual([(e["from"], e["to"]) for e in graph["edges"]],
                                  [e for e in RELATIONSHIPS if set(e) <= visible])
            for u, v in combinations(graph["nodes"], 2):
                self.assertGreater((u["x"]-v["x"])**2 + (u["y"]-v["y"])**2, 48**2)

    def test_stress_neighborhoods(self):
        from stage5.connection_map import ranked_routes, map_graph
        from stage5.demo import visible_members
        for focus, count in [(2000,100),(2001,1000)]:
            self.assertEqual(len(NETWORK[focus]), count)
            self.assertIsNone(find_connection(HOME, focus, NETWORK))
            graph = map_graph(focus, [])
            self.assertEqual(len(graph["nodes"]),16)
            self.assertLessEqual(len(graph["edges"]),32)
        # All shared intermediates are outside the large hub's default view.
        before = visible_members(2001, [])
        paths = ranked_routes(NETWORK, 2001, 2000, 5)
        self.assertEqual(len(paths), 5)
        self.assertTrue(all(len(p) == 3 and p[1] not in before for p in paths))
        short = find_connection(2001, 2000, NETWORK)
        self.assertEqual(len(short)-1, 2)
        self.assertNotIn(short[1], before)

    def test_named_review_members(self):
        from stage5.directory import unique_member
        from stage5.stress_fixture import REVIEW_HUBS
        for hub, name, _, first, count in REVIEW_HUBS:
            self.assertEqual(unique_member(DIRECTORY, name), hub)
            self.assertEqual(unique_member(DIRECTORY, str(hub)), hub)
            self.assertEqual(NETWORK[hub], list(range(first, first + count)))
            self.assertTrue(all(NETWORK[n] == [hub] for n in NETWORK[hub]))
            self.assertIsNone(find_connection(HOME, hub, NETWORK))

    def test_budget_priorities(self):
        from stage5.demo import visible_members, render_graph
        for node_cap, edge_cap in [(1,1),(7,3),(20,12)]:
            required = {1,2,3,4,5,12}
            visible = visible_members(5,required,node_cap,edge_cap)
            self.assertTrue(required <= visible)
            graph = render_graph(dict.fromkeys(visible,(0,0)),5,set(),set())
            induced = [e for e in RELATIONSHIPS if set(e)<=visible]
            self.assertCountEqual([(e["from"],e["to"]) for e in graph["edges"]],induced)
            if len(visible) > node_cap or len(induced) > edge_cap:
                self.assertEqual(visible,required)
        limited = visible_members(2000, [], 16, 5)
        self.assertLess(len(limited),16)
        self.assertLessEqual(sum(set(e)<=limited for e in RELATIONSHIPS),5)

    def test_search(self):
        from stage5.directory import search_members
        for query, region, expected in [
            ("  jOhN SMITH ", None, [101, 102]), ("sMi", None, [101, 102]),
            ("John", "Washington", [102]), ("#101", None, [101]),
            (" 5 ", None, [5]), ("10", None, [10]), ("102", "California", []),
            ("999", None, []), ("nobody", None, []), (" ", None, []),
            ("103", None, []), ("Jules North", None, []),
        ]:
            with self.subTest(query=query, region=region):
                self.assertEqual(search_members(DIRECTORY, query, state=region), expected)

    def test_unique_enter(self):
        from stage5.directory import unique_member
        for term, region, expected in [
            ("  sINbaD ", None, 5), ("#101", "California", 101), ("102", None, 102),
            ("Sin", None, 5), ("Taylor Thousand", None, 904), ("903", None, 903), ("John", "California", 101), ("John Smith", None, None), ("John Smith", "Washington", 102),
            ("101", "Washington", None), ("103", None, None),
        ]:
            with self.subTest(term=term, region=region):
                self.assertEqual(unique_member(DIRECTORY, term, state=region), expected)

    def test_public_projection(self):
        self.assertNotIn(103, NETWORK)
        self.assertNotIn("Oregon", {m.state for m in DIRECTORY.values()})
        self.assertNotIn("Cedar Hollow", repr(DIRECTORY))
        self.assertEqual(set(ORIGINAL) - set(CORE_NAMES), {101, 102, 104, 105, 106})

    def test_john_networks(self):
        from stage5.connection_map import ranked_routes, map_graph
        self.assertCountEqual(NETWORK[101], [6, 21, 25])
        self.assertEqual(ranked_routes(NETWORK, HOME, 101, 3)[0], [1, 2, 6, 101])
        self.assertCountEqual(NETWORK[102], [104, 105, 106])
        for member in [102, 104, 105, 106]:
            self.assertEqual(ranked_routes(NETWORK, HOME, member, 5), [])
        graph = map_graph(102, [])
        self.assertCountEqual([n["id"] for n in graph["nodes"]], [102, 104, 105, 106])
        self.assertCountEqual([(e["from"], e["to"]) for e in graph["edges"]],
                              [(102, 104), (102, 105), (102, 106), (104, 105)])

    def test_ranked_routes(self):
        from stage5.connection_map import ranked_routes
        # Exhaustive oracle only on this small tie-heavy test fixture.
        g = {1:[4,3,2], 2:[1,3,5], 3:[1,2,4,5], 4:[1,3,5], 5:[2,3,4], 6:[]}
        paths = []
        def visit(path):
            if path[-1] == 5:
                paths.append(path)
                return
            for n in g[path[-1]]:
                if n not in path:
                    visit([*path,n])
        visit([1])
        reversed_graph = {k:list(reversed(v)) for k,v in reversed(g.items())}
        for limit in [3,5]:
            routes = ranked_routes(g,1,5,limit)
            self.assertEqual([len(p) for p in routes], sorted(map(len,paths))[:limit])
            self.assertEqual(len(set(map(tuple,routes))),limit)
            self.assertTrue(all(p in paths for p in routes))
            self.assertEqual(routes, ranked_routes(reversed_graph,1,5,limit))
        self.assertEqual(ranked_routes(g,1,6,5),[])
        self.assertEqual(ranked_routes(g,1,1,3),[[1]])
        self.assertEqual(ranked_routes({1:[2],2:[1]},1,2,5),[[1,2]])

    def test_map_styles(self):
        from stage5.connection_map import ranked_routes, map_graph
        from stage5.demo import path_edges
        for limit in [3,5]:
            routes = ranked_routes(NETWORK,1,5,limit)
            self.assertEqual(routes[0],[1,4,5])
            primary = path_edges(routes[0])
            secondary = set().union(*(path_edges(p) for p in routes[1:]))
            self.assertTrue(primary & secondary)
            data = map_graph(5,routes)
            visible = set(NETWORK[5]).union(*routes)
            self.assertEqual({n['id'] for n in data['nodes']},visible)
            self.assertCountEqual([(e['from'],e['to']) for e in data['edges']],
                                  [e for e in RELATIONSHIPS if set(e)<=visible])
            for edge in data['edges']:
                pair = edge['from'],edge['to']
                self.assertEqual(edge.get('dashes',False),pair in primary)
                self.assertEqual(edge.get('color'), '#194d98' if pair in primary else
                                 '#087565' if pair in secondary else None)
        explore = graph_data([1,4,5],[1,4,5])
        self.assertTrue(all(e.get('dashes') for e in explore['edges']
                            if (e['from'], e['to']) in {(1,4),(4,5)}))

    def test_many_possible_paths(self):
        from stage5.connection_map import ranked_routes
        # Two choices in each of 24 layers give at least 2**24 simple paths.
        layers = [[0]] + [[2*i+1, 2*i+2] for i in range(24)] + [[49]]
        graph = {n: [] for layer in layers for n in layer}
        for left, right in zip(layers, layers[1:]):
            for a in left:
                for b in right:
                    graph[a].append(b)
                    graph[b].append(a)
        routes = ranked_routes(graph, 0, 49, 5)
        self.assertEqual(len(set(map(tuple, routes))), 5)
        self.assertTrue(all(len(path) == 26 and len(set(path)) == 26 for path in routes))
