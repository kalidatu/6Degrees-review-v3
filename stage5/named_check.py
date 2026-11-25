"""Final local review for the four named hubs and both navigation entry points."""
from time import perf_counter
from playwright.sync_api import expect

from stage5.demo import NAMES
from stage5.stress_fixture import REVIEW_HUBS


def check_named(page, url, screenshots=None):
    page.goto(url)
    graph = page.frame_locator('iframe[title$="six_degrees_network"]').locator("canvas")
    graph.wait_for()
    frame = next(f for f in page.frames if "six_degrees_network" in f.url)
    profile = page.frame_locator('iframe[title$="member_profile"]')
    rows = profile.locator("#rows")
    panel_search = profile.locator("#localSearch")
    finder = page.frame_locator('iframe[title$="finder_input"]').get_by_role("searchbox")
    back = page.get_by_role("button", name="Back", exact=True)
    forward = page.get_by_role("button", name="Forward", exact=True)
    home = page.get_by_role("button", name="Home", exact=True)

    def at(member):
        frame.wait_for_function("id => focus === id && !moving", arg=member)
        expect(profile.locator("#memberId")).to_have_text(f"Member ID {member}")

    def search(term):
        finder.fill(term)
        finder.press("Enter")

    for method in ("graph", "panel"):
        def choose(member):
            if method == "graph":
                graph.click(position=frame.evaluate("id => network.canvasToDOM(network.getPosition(id))",member))
            else:
                rows.get_by_role("button", name=NAMES[member]).click()
            at(member)

        for member in (2, 8, 3):
            choose(member)
        for control, member in [(back,8),(back,2),(forward,8),(forward,3),(back,8)]:
            control.click()
            at(member)
        choose(9)
        expect(forward).to_be_disabled()
        home.click()
        at(1)
        expect(back).to_be_disabled()
        expect(forward).to_be_disabled()
        print(f"PASS: {method} David → Mary → Cleo → Kevin, double Back/Forward, branch to Dara and Home.")

    for hub, name, prefix, first, count in REVIEW_HUBS:
        for term in (name.removeprefix("Test ") if hub == 904 else name, str(hub)):
            search(term)
            at(hub)
            expect(finder).to_have_value(term)
            expect(profile.locator("#panelTitle")).to_have_text(f"{name}'s Network ({count:,})")
            expect(profile.locator("#count")).to_have_text(str(count))
            expect(profile.locator("#distance")).to_have_text("No known connection")
            if term != str(hub):
                home.click()
                at(1)
        total = f"{count:,}"
        expect(profile.locator("#matchCount")).to_have_text(f"Showing all {total} connections")
        if hub == 904:
            panel_search.fill("11")
            expect(profile.locator("#matchCount")).to_have_text("19 of 1,000 connections match")
            expect(profile.locator("#range")).to_have_text("Showing 1–19 of 19 matches")
            expect(profile.locator("#range")).to_be_visible()
            profile.locator("#scope").select_option("Mutual")
            expect(profile.locator("#matchCount")).to_have_text("0 of 1,000 connections match")
            expect(rows.locator("button")).to_have_count(0)
            profile.locator("#scope").select_option("Direct")
            expect(profile.locator("#matchCount")).to_have_text("19 of 1,000 connections match")
            panel_search.fill("")
            expect(profile.locator("#matchCount")).to_have_text("1,000 of 1,000 connections match")
            profile.locator("#scope").select_option("All")
            expect(profile.locator("#range")).to_have_text("Showing 1–25 of 1,000 matches")
        n_nodes, n_edges = frame.evaluate("[data.nodes.length,data.edges.length]")
        assert n_nodes == min(16,count+1) and n_edges == n_nodes-1
        expect(rows.locator("button")).to_have_count(min(25,count))
        height, full = rows.evaluate("r => [r.clientHeight,r.scrollHeight]")
        assert (full > height) == (count > 15)
        if count > 15:
            rows.evaluate("r => r.scrollTo({top:r.scrollHeight, behavior:'smooth'})")
            profile.locator("#rows button").last.wait_for()
            # Wait for native smooth scrolling to settle without guessing a duration.
            rows.evaluate("""async r => {
              const end = performance.now()+2500;
              while(r.scrollTop + r.clientHeight < r.scrollHeight-1 && performance.now()<end)
                await new Promise(requestAnimationFrame);
              if(r.scrollTop+r.clientHeight < r.scrollHeight-1) throw Error("Scroll did not finish");
            }""")
            profile.locator("#next").click()
            expect(rows.locator("button").first).to_contain_text(str(first+25))
        last = first + count-1
        if count > 15:
            assert last not in frame.evaluate("network.body.data.nodes.getIds()")
        partial = f"{prefix} Circle {count:04d}"[:-1]
        started = perf_counter()
        panel_search.fill(partial)
        expect(rows.locator("button").last).to_contain_text(str(last))
        elapsed = (perf_counter()-started)*1000
        panel_search.fill(f"#{last}")
        expect(rows.locator("button")).to_have_count(1)
        rows.locator("button").click()
        at(last)
        expect(page.get_by_role("heading",name="Explore Mode")).to_be_visible()
        expect(page.locator("p").filter(has_text="Navigation trail")).to_contain_text(NAMES[last])
        expect(profile.locator("#panelTitle")).to_have_text(f"{NAMES[last]}'s Network (1)")
        expect(finder).to_have_value("")
        back.click()
        at(hub)
        expect(finder).to_have_value(str(hub))
        expect(panel_search).to_have_value(f"#{last}")
        expect(profile.locator("#matchCount")).to_have_text(f"1 of {total} connections matches")
        expect(profile.locator("#range")).to_have_text("Showing 1–1 of 1 match")
        forward.click()
        at(last)
        home.click()
        at(1)
        print(f"PASS: {name} #{hub}: {count} contacts, {min(25,count)} list rows, "
              f"{height}/{full}px viewport/content, {n_nodes} nodes/{n_edges} edges, "
              f"partial-name filter {elapsed:.0f} ms (Playwright wall time), final contact #{last}.")
