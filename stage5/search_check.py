"""End-to-end checks for keyboard search, radio navigation and map history."""
from math import isclose

from playwright.sync_api import expect
from stage5.demo import NETWORK, RELATIONSHIPS
from stage5.connection_map import ranked_routes


def check_finder(page, url, screenshots):
    page.goto(url)
    canvas = page.frame_locator('iframe[title$="six_degrees_network"]').locator("canvas")
    canvas.wait_for()
    frame = next(f for f in page.frames if "six_degrees_network" in f.url)
    query = page.frame_locator('iframe[title$="finder_input"]').get_by_role("searchbox")
    profile = page.frame_locator('iframe[title$="member_profile"]').locator("article")
    region = page.get_by_role("combobox", name="State (optional)")
    back = page.get_by_role("button", name="Back", exact=True)
    radios = page.get_by_role("radiogroup", name="Matching members")
    maximum = page.get_by_role("radiogroup", name="Maximum routes")

    def settled(revision, person, clicks):
        frame.wait_for_function("r => view === r && !moving", arg=revision)
        expect(profile.get_by_role("heading", name=person, exact=True)).to_be_visible()
        expect(page.get_by_text(f"Accepted node clicks: {clicks} · View revision: {revision}")).to_be_visible()

    def empty():
        expect(query).to_have_value("")
        expect(page.get_by_test_id("stSelectbox")).to_contain_text("All states")
        expect(radios).to_have_count(0)

    def choose_state(label):
        region.click()
        page.get_by_role("option", name=label, exact=True).click()

    def node(member):
        point = frame.evaluate("id => network.canvasToDOM(network.getPosition(id))", member)
        canvas.click(position=point)

    def snapshot():
        return frame.evaluate("({data, positions:network.getPositions(), camera:camera()})"), profile.inner_text()

    def check_restored(saved):
        actual, profile_text = snapshot()
        expected, expected_profile = saved
        assert profile_text == expected_profile, (profile_text, expected_profile)
        for key in ("data", "positions"):
            assert actual[key] == expected[key], key
        camera, original = actual["camera"], expected["camera"]
        assert isclose(camera["scale"], original["scale"], abs_tol=1e-9)
        for axis in ("x", "y"):
            assert isclose(camera["position"][axis], original["position"][axis], abs_tol=1e-9)

    def shot(name):
        if screenshots:
            page.screenshot(path=screenshots / name, full_page=True)
            canvas.screenshot(path=screenshots / name.replace(".png", "-graph.png"))

    def check_map(person, limit):
        routes = ranked_routes(NETWORK, 1, person, limit)
        ids = set(NETWORK[person]) | {person}
        for route in routes:
            ids.update(route)
        assert set(frame.evaluate("network.body.data.nodes.getIds()")) == ids
        edges = frame.evaluate("data.edges.map(e => [e.from, e.to])")
        assert sorted(map(tuple, edges)) == sorted(e for e in RELATIONSHIPS if set(e) <= ids)
        return routes

    def selected(label):
        expect(radios.get_by_role("radio", name=label)).to_be_checked()

    def enter(value):
        query.fill(value)
        query.press("Enter")

    settled(0, "David", 0)
    for term in ("Nobody Here", "103", "Jules North"):
        enter(term)
        expect(page.get_by_text("No matching members.", exact=False)).to_be_visible()
        settled(0, "David", 0)
    query.fill("Sin")
    expect(radios.get_by_role("radio")).to_have_count(1)
    settled(0, "David", 0)
    query.fill("Sinbad")
    query.press("Tab")
    expect(radios.get_by_role("radio")).not_to_be_checked()
    settled(0, "David", 0)
    enter("  jOhN  ")
    expect(radios.get_by_role("radio")).to_have_count(2)
    settled(0, "David", 0)
    long_beach = "John Smith · ID 101 · Long Beach, California"
    tacoma = "John Smith · ID 102 · Tacoma, Washington"
    # Click actual labels to exercise native radio events.
    radios.get_by_text(long_beach, exact=True).click()
    settled(1, "John Smith", 0)
    selected(long_beach)
    expect(profile.locator("#chips button")).to_have_text(["Alba", "Paz", "Tala"])
    expect(page.get_by_text("Shortest known route David → Mary → Alba → John Smith")).to_be_visible()
    check_map(101, 3)
    shot("06-connected-john.png")
    radios.get_by_text(tacoma, exact=True).click()
    settled(2, "John Smith", 0)
    selected(tacoma)
    expect(profile.locator("#chips button")).to_have_text(["Nell Vale", "Ada Finch", "Tess Reed"])
    expect(page.get_by_text("Shortest known route No known connection to David.")).to_be_visible()
    assert check_map(102, 3) == []
    shot("07-independent-john.png")
    node(104)
    settled(3, "Nell Vale", 1)
    empty()
    assert set(frame.evaluate("network.body.data.nodes.getIds()")) == {102,104,105}
    back.click()
    settled(4, "John Smith", 1)
    selected(tacoma)
    choose_state("California")
    expect(radios.get_by_role("radio")).to_have_count(1)
    expect(radios.get_by_role("radio")).not_to_be_checked()
    settled(4, "John Smith", 1)
    query.press("Enter")
    settled(5, "John Smith", 1)
    selected(long_beach)
    john_map = snapshot()
    choose_state("All states")
    enter("  sIn ")
    settled(6, "Sinbad", 1)
    selected("Sinbad · ID 5 · Location unlisted")
    three = check_map(5, 3)
    assert len(three) == 3 and three[0] == [1,4,5]
    shot("08-sinbad-three.png")
    query.press("Enter")
    settled(6, "Sinbad", 1)
    maximum.get_by_text("5", exact=True).click()
    settled(7, "Sinbad", 1)
    assert len(check_map(5, 5)) == 5
    sinbad_map = snapshot()
    shot("09-sinbad-five.png")
    node(12)
    settled(8, "Gio", 2)
    empty()
    expect(page.get_by_role("heading", name="Explore Mode")).to_be_visible()
    shot("10-gio-empty-finder.png")
    node(2)
    settled(9, "Mary", 3)
    empty()
    back.click()
    settled(10, "Gio", 3)
    empty()
    back.click()
    settled(11, "Sinbad", 3)
    expect(query).to_have_value("  sIn ")
    selected("Sinbad · ID 5 · Location unlisted")
    expect(maximum.get_by_role("radio", name="5", exact=True)).to_be_checked()
    check_restored(sinbad_map)
    back.click()
    settled(12, "John Smith", 3)
    expect(query).to_have_value("  jOhN  ")
    selected(long_beach)
    expect(page.get_by_test_id("stSelectbox")).to_contain_text("California")
    check_restored(john_map)
    page.get_by_role("button", name="Home").click()
    settled(13, "David", 3)
    empty()
    expect(back).to_be_disabled()
    assert set(frame.evaluate("network.body.data.nodes.getIds()")) == {1,2,4}
    finder_frame = next(f for f in page.frames if "finder_input" in f.url)
    finder_frame.evaluate("""() => send("streamlit:setComponentValue", {
        dataType:"json", value:{action:"enter", query:"Sinbad", view:7, event:"late-enter"}
    })""")
    page.wait_for_timeout(350)
    settled(13, "David", 3)
    empty()
    print("PASS: exact Enter, partial/ambiguous results, radio switching, filters, both John networks, "
          "3/5 routes, induced edges, multi-step Back including viewport, Home, 3 node clicks/13 revisions.")
