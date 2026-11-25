"""6Degrees V3: three-column explorer built on the approved Stage 6B demo."""
from pathlib import Path
from dataclasses import dataclass

import streamlit as st
from streamlit.components.v1 import declare_component

from main import find_connection
from stage5.connection_map import ranked_routes, map_graph
from stage5.directory import unique_member, search_members
from stage5.demo import DIRECTORY, HOME, NAMES, NETWORK, graph_data


st.set_page_config(page_title="6Degrees V3 · Network explorer", layout="wide")
network_component = declare_component(
    "six_degrees_network", path=str(Path(__file__).parent / "stage5" / "component")
)

profile_component = declare_component("member_profile", path=str(Path(__file__).parent / "stage5" / "profile"))
finder_input = declare_component("finder_input", path=str(Path(__file__).parent / "stage5" / "finder"))


def names(route):
    return " → ".join(NAMES[person] for person in route)


@dataclass
class View:
    route: tuple
    origin: str = "home"
    action: str = "home"
    finder: tuple = ("", None, None)
    limit: int = 3
    finder_page: int = 0


state = st.session_state
if "history" not in state:
    state.history = [View((HOME,))]
    state.revision = state.accepted = 0
    state.consumed_events = set()
    state.query = ""
    state.finder_page = 0
state.setdefault("forward_views", [])

# Component gestures arrive after the finder widgets have been instantiated.
# Apply the new view’s controls before those widgets render on the next run.
if state.pop("reset_finder", False):
    state.finder_page = state.history[-1].finder_page
    state.query, saved_region, state.pick = state.history[-1].finder
    state.region = saved_region or "All states"


def restore(view):
    state.finder_page = view.finder_page
    state.query, saved_region, state.pick = view.finder
    state.region = saved_region or "All states"
    state.route_limit = view.limit
    state.revision += 1


def save_controls():
    state.history[-1].finder_page = state.finder_page
    region = state.get("region")
    state.history[-1].finder = (state.query, None if region == "All states" else region,
                                state.get("pick"))


def back():
    save_controls()
    state.forward_views.append(state.history.pop())
    restore(state.history[-1])
    state.revisit_revision = state.revision


def forward():
    save_controls()
    state.history.append(state.forward_views.pop())
    restore(state.history[-1])
    state.revisit_revision = state.revision


def push(view):
    state.forward_views.clear()
    state.history.append(view)


def home():
    state.forward_views.clear()
    state.home_revision = state.revision + 1
    state.history = [View((HOME,))]
    restore(state.history[0])


def clear_pick():
    state.finder_page = 0
    state.pick = None


def change_limit():
    state.history[-1].limit = state.route_limit
    state.revision += 1


PAGE_SIZE = 25
workspace_css = (Path(__file__).parent / "stage5" / "workspace.css").read_text(encoding="utf-8")
st.html(f"<style>{workspace_css}</style>")
workspace = st.container(key="v3_workspace")
left, controls, profile = workspace.columns([1, 2, 1], gap="medium")
left.title("6Degrees")
left.caption("V3 · Network Explorer")

def open_map(person):
    query = state.query
    region = None if state.region == "All states" else state.region
    if person not in search_members(DIRECTORY, query, state=region):
        return
    finder = (query, region, person)
    current = state.history[-1]
    if current.action == "search" and current.route == (person,):
        # Keep the submitted snapshot when Streamlit replays a checked radio
        # while the user edits the controls for their next search.
        return
    if current.action != "search":
        current.finder = finder
        current.finder_page = state.finder_page
    push(View((person,), "search", "search", finder, finder_page=state.finder_page))
    state.route_limit = 3
    state.revision += 1


def select_result():
    open_map(state.pick)


def turn_results(page, matches):
    state.finder_page = page
    start = page * PAGE_SIZE
    # A page change is presentation only. Re-check the current map's result
    # when the user pages back to it, without opening another view.
    query, region, member = state.history[-1].finder
    same_query = query == state.query and (region or "All states") == state.region
    state.pick = member if same_query and member in matches[start:start + PAGE_SIZE] else None


with left.container(border=True, key="v3_finder"):
    st.subheader("People Finder")
    edit = finder_input(query=state.query, view=state.revision, key="finder_input")
    region = st.selectbox("State (optional)", ["All states", *sorted({
        member.state for member in DIRECTORY.values() if member.state
    })], key="region", on_change=clear_pick)
    if region == "All states":
        region = None
    if (isinstance(edit, dict) and edit.get("view") == state.revision
            and isinstance(edit.get("query"), str) and edit.get("event") != state.get("last_edit")):
        state.last_edit = edit["event"]
        if state.query != edit["query"]:
            state.query = edit["query"]
            clear_pick()
        if edit.get("action") == "enter":
            person = unique_member(DIRECTORY, state.query, state=region)
            if person is not None:
                state.pick = person
                open_map(person)
                st.rerun()
    query = state.query
    matches = search_members(DIRECTORY, query, state=region)
    selection = None
    if matches:
        page = min(state.finder_page, (len(matches) - 1) // PAGE_SIZE)
        start = page * PAGE_SIZE
        shown = matches[start:start + PAGE_SIZE]
        with st.container(key="v3_results"):
            selection = st.radio("Matching members", shown, index=None,
                                 format_func=lambda i: DIRECTORY[i].label(i),
                                 key="pick", on_change=select_result)
        if len(matches) > PAGE_SIZE:
            st.caption(f"Showing {start + 1:,}–{start + len(shown):,} of {len(matches):,} matches")
            with st.container(horizontal=True):
                st.button("Previous", disabled=page == 0, on_click=turn_results, args=(page - 1, matches))
                st.button("Next", disabled=start + PAGE_SIZE >= len(matches),
                          on_click=turn_results, args=(page + 1, matches))
    elif query.strip():
        st.info("No matching members. Try another name, ID, or state.")

current = state.history[-1]
route, origin = current.route, current.origin
is_map = current.action == "search"
focus = route[-1]
shortest = find_connection(HOME, focus, NETWORK)
controls.subheader(f"Connection Map · David to {NAMES[focus]}" if is_map else "Explore Mode")
limit_slot = controls.empty()
if is_map:
    limit_slot.radio("Maximum routes", [3, 5], horizontal=True, key="route_limit", on_change=change_limit)
    routes = ranked_routes(NETWORK, HOME, focus, current.limit)
    shortest = routes[0] if routes else None
    graph = map_graph(focus, routes)
else:
    graph = graph_data(route, shortest)

def navigate(event, allowed):
    # Widget values survive reruns. Validate both the originating view and the
    # gesture identity before allowing any mutation of the session history.
    if isinstance(event, dict) and event.get("view") == state.revision:
        person = event.get("person")
        event_id = event.get("event")
        if (isinstance(event_id, str) and event_id and event_id not in state.consumed_events
                and (is_map or person != focus) and person in allowed):
            state.consumed_events.add(event_id)
            next_origin = origin
            if person in route:
                next_route = route[:route.index(person) + 1]
            elif person in NETWORK[focus]:
                next_route = (*route, person)
            else:
                # Jump to a visible route reference without inventing a manual edge.
                next_origin = "reference"
                next_route = (person,)
            next_view = View(next_route, next_origin, "click")
            if is_map:
                state.reset_finder = True
            else:
                current.finder_page = next_view.finder_page = state.finder_page
                current.finder = next_view.finder = (query, region, selection)
            push(next_view)
            state.accepted += 1
            state.revision += 1
            st.rerun()


with controls:
    with st.container(horizontal=True):
        st.button("Home", on_click=home)
        st.button("Back", on_click=back, disabled=len(state.history) == 1)
        st.button("Forward", on_click=forward, disabled=not state.forward_views)
    trail = []
    for entry in state.history:
        member_id = entry.route[-1]
        label = NAMES[member_id]
        if entry.action == "search":
            label = f"Search ({label} · ID {member_id})"
        trail.append(label)
    st.write("**Navigation trail**", " → ".join(trail))
    event = network_component(graph=graph, mapMode=is_map, view=state.revision, focus=focus, depth=len(state.history), revisit=state.get("revisit_revision") == state.revision, reset=state.get("home_revision") == state.revision,
                              key="explorer", default=None)
    visible = {node["id"] for node in graph["nodes"]}
    navigate(event, visible)
    hidden = len(set(NETWORK[focus]) - visible)
    if hidden:
        st.caption(f"{hidden:,} more direct connections in the Connections panel.")
    st.caption("Drag the background to pan. Scroll to zoom.")
    bold_label = "secondary connection route" if is_map else "manual trail"
    st.caption(f"Thin solid · direct relationship　 Bold solid · {bold_label}　 Dashed blue · shortest route")
    if is_map:
        for rank, path in enumerate(routes, 1):
            hops = len(path) - 1
            st.write(f"{rank}. {names(path)} · {hops} {'degree' if hops == 1 else 'degrees'}")
    st.write("**Explored route**", "No manual steps yet" if origin == "search" and len(route) == 1 else names(route))
    if origin == "search":
        st.caption(f"Search jump to {NAMES[route[0]]} · ID {route[0]}")
    elif route[0] != HOME:
        st.caption(f"This segment began by selecting {NAMES[route[0]]} from a displayed route.")
    st.write("**Shortest known route**", names(shortest) if shortest else "No known connection to David.")
    st.caption(f"Accepted node clicks: {state.accepted} · View revision: {state.revision}")

with profile:
    member = DIRECTORY[focus]
    contacts = NETWORK[focus]
    bio = member.biography.strip()
    viewer_contacts = set(NETWORK[HOME])
    relevant = set().union(*routes) if is_map else set()
    event = profile_component(
        depth=len(state.history), revisit=state.get("revisit_revision") == state.revision, reset=state.get("home_revision") == state.revision,
        map_mode=is_map,
        view=state.revision, id=focus, name=member.name,
        location=", ".join(filter(None, (member.city, member.state))),
        bio=bio if len(bio) <= 200 else bio[:199].rstrip() + "…",
        photo=member.photo_url, distance=len(shortest) - 1 if shortest else None,
        is_self=focus == HOME, connected=focus in NETWORK[HOME],
        contacts=[{"id": i, "name": NAMES[i], "mutual": i in viewer_contacts,
                   "relevant": i in relevant} for i in contacts],
        key="profile_card", default=None,
    )
    navigate(event, contacts)
