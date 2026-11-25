"""Run against a local Stage 5 server with a fresh Chromium browser context."""
import argparse
from pathlib import Path
from itertools import combinations

from main import find_connection
from stage5.demo import NAMES, NETWORK, RELATIONSHIPS

from playwright.sync_api import expect, sync_playwright


def check(page, url, screenshots):
    page.add_init_script("""window.nodeEvents = [];
      window.addEventListener("message", e => {
        if (e.data?.type === "streamlit:setComponentValue") window.nodeEvents.push(e.data.value);
      });""")
    page.goto(url)
    frame = page.frame_locator('iframe[title$="six_degrees_network"]')
    canvas = frame.locator("canvas")
    canvas.wait_for()

    iframe = next(f for f in page.frames if "six_degrees_network" in f.url)
    clicks = revision = 0

    def view(route):
        person = route[-1]
        shortest = find_connection(1, person, NETWORK)
        visible = set(route) | set(shortest) | set(NETWORK[person])
        iframe.wait_for_function("v => view === v && !moving", arg=revision)
        profile = page.frame_locator('iframe[title$="member_profile"]').locator("article")
        expect(profile.get_by_role("heading", name=NAMES[person], exact=True)).to_be_visible()
        expect(profile.get_by_text(f"Member ID {person}")).to_be_visible()
        expect(profile.locator("#chips button")).to_have_text([NAMES[n] for n in NETWORK[person]])
        expect(profile.locator("#distance")).to_have_text(str(len(shortest)-1))
        for label, path in [("Explored route", route), ("Shortest known route", shortest)]:
            expect(page.locator("p").filter(has_text=label)).to_have_text(
                label + " " + " → ".join(NAMES[n] for n in path))
        expect(page.get_by_text(f"Accepted node clicks: {clicks} · View revision: {revision}",
                                exact=True)).to_be_visible()
        edges = iframe.evaluate("network.body.data.edges.get().map(e => [e.from,e.to])")
        assert sorted(map(tuple, edges)) == sorted(e for e in RELATIONSHIPS if set(e) <= visible)
        boxes = iframe.evaluate("""() => Object.fromEntries(network.body.data.nodes.getIds().map(id =>
            [id, network.getBoundingBox(id)]))""")
        assert set(map(int, boxes)) == visible
        for a, b in combinations(boxes.values(), 2):
            assert (a["right"] < b["left"] or b["right"] < a["left"] or
                    a["bottom"] < b["top"] or b["bottom"] < a["top"]), (person, a, b)

    def click(kind, target=None):
        # Read actual vis layout, confirm hit target, then drive a real mouse click.
        point = canvas.evaluate("""(canvas, [kind, target]) => {
          const pos = id => network.canvasToDOM(network.getPosition(id));
          let p;
          if (kind === "node") p = pos(target);
          if (kind === "background") p = {x: 8, y: 8};
          if (kind === "edge") {
            const [a,b] = target.map(pos);
            p = {x:(a.x+b.x)/2, y:(a.y+b.y)/2};
          }
          const node = network.getNodeAt(p), edge = network.getEdgeAt(p);
          if (kind === "node" ? node !== target :
              node !== undefined || ((kind === "edge") !== (edge !== undefined)))
            throw Error("Unexpected canvas hit target");
          return p;
        }""", [kind, target])
        canvas.click(position=point)

    def capture(filename):
        if screenshots:
            screenshots.mkdir(parents=True, exist_ok=True)
            page.screenshot(path=screenshots / filename, animations="disabled", full_page=True)

    def select(person, route):
        nonlocal clicks, revision
        click("node", person)
        clicks += 1
        revision += 1
        view(route)

    def control(label, route):
        nonlocal revision
        page.get_by_role("button", name=label, exact=True).click()
        revision += 1
        view(route)

    view([1])
    capture("01-david.png")
    iframe.evaluate("""() => {
      window.framesByView = {};
      network.on("afterDrawing", () => {
        if (moving) (framesByView[view] ??= new Set()).add(network.getPosition(focus).x);
      });
    }""")
    for person in [2, 3, 4, 5]:
        select(person, list(range(1, person + 1)))
        assert iframe.evaluate("framesByView[view].size") > 2
        capture(f"0{person}-{NAMES[person].lower()}.png")
    click("edge", [4, 5])
    click("background")
    control("Back", [1, 2, 3, 4])
    # Resend the Sinbad click with a stale view and then its consumed ID in the current view.
    for current in (False, True):
        iframe.evaluate("""([value,current]) => send("streamlit:setComponentValue", {
          dataType:"json", value: {...value, view: current ? view : value.view}
        })""", [page.evaluate("nodeEvents[3]"), current])
        page.wait_for_timeout(300)
        view([1, 2, 3, 4])
    assert page.evaluate("nodeEvents.length") == 6
    control("Home", [1])
    capture_camera = lambda: iframe.evaluate("camera()")
    original = capture_camera()
    canvas.hover(position={"x": 80, "y": 70})
    page.mouse.wheel(0, -120)
    page.wait_for_timeout(300)
    zoomed = capture_camera()
    assert zoomed["scale"] > original["scale"]
    bounds = canvas.bounding_box()
    x, y = bounds["x"] + 28, bounds["y"] + 30
    page.mouse.move(x, y)
    page.mouse.down()
    page.mouse.move(x + 35, y + 25, steps=6)
    page.mouse.up()
    saved = capture_camera()
    assert saved["position"] != zoomed["position"]
    select(4, [1, 4])
    control("Back", [1])
    restored = capture_camera()
    assert abs(saved["scale"] - restored["scale"]) < 0.001
    assert all(abs(saved["position"][k] - restored["position"][k]) < 0.5 for k in ("x", "y"))
    for walk in ([1, 2, 7, 21, 24, 25], [1, 4, 5, 19, 23, 25], [1, 2, 12, 5, 18, 4]):
        for i in range(1, len(walk)):
            select(walk[i], walk[:i+1])
        select(1, [1])
        control("Back", walk)
        control("Home", [1])
    # Mary appears on the shortest route to Hana, yet Hana and Mary are
    # not connected. Selecting the reference begins a fresh explored segment.
    for i, person in enumerate([4, 3, 13], 1):
        select(person, [1, 4, 3, 13][:i+1])
    select(2, [2])
    expect(page.get_by_text("This segment began by selecting Mary", exact=False)).to_be_visible()
    control("Back", [1, 4, 3, 13])
    assert page.evaluate("nodeEvents.length") == clicks + 2
    print(f"PASS: {clicks} deliberate node clicks, {revision} revisions; core and outer walks, "
          "edges, labels, motion, replay rejection and zoomed/panned Back.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://127.0.0.1:8501")
    parser.add_argument("--chromium")
    parser.add_argument("--screenshots", type=Path)
    parser.add_argument("--width", type=int, default=1280)
    parser.add_argument("--height", type=int, default=900)
    args = parser.parse_args()
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(executable_path=args.chromium)
        check(browser.new_page(viewport={"width": args.width, "height": args.height}),
              args.url, args.screenshots)
        from stage5.search_check import check_finder
        check_finder(browser.new_page(viewport={"width": args.width, "height": args.height}),
                     args.url, args.screenshots)
        from stage5.profile_check import check_profile
        check_profile(browser.new_page(viewport={"width": args.width, "height": args.height}),
                      args.url, args.screenshots)
        from stage5.expansion_check import check_expansion
        check_expansion(browser.new_page(viewport={"width": args.width, "height": args.height}),
                        args.url, args.screenshots)
        from stage5.history_check import check_history
        check_history(browser.new_page(viewport={"width": args.width, "height": args.height}),
                      args.url, args.screenshots)
        from stage5.named_check import check_named
        check_named(browser.new_page(viewport={"width": args.width, "height": args.height}),
                    args.url, args.screenshots)
        browser.close()
