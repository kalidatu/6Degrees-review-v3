"""Back/Forward, branch replacement and adaptive-height browser acceptance tests."""
from math import isclose

from playwright.sync_api import expect


def check_history(page, url, screenshots=None):
    page.goto(url)
    canvas = page.frame_locator('iframe[title$="six_degrees_network"]').locator("canvas")
    canvas.wait_for()
    graph = next(f for f in page.frames if "six_degrees_network" in f.url)
    profile = page.frame_locator('iframe[title$="member_profile"]')
    rows = profile.locator("#rows")
    query = profile.locator("#localSearch")
    scope = profile.locator("#scope")
    finder = page.frame_locator('iframe[title$="finder_input"]').get_by_role("searchbox")
    back = page.get_by_role("button", name="Back", exact=True)
    forward = page.get_by_role("button", name="Forward", exact=True)
    home = page.get_by_role("button", name="Home", exact=True)

    def at(member, revision):
        graph.wait_for_function("a => focus===a[0] && view===a[1] && !moving",arg=[member,revision])
        expect(profile.locator("#memberId")).to_have_text(f"Member ID {member}")

    def node(member):
        p = graph.evaluate("id => network.canvasToDOM(network.getPosition(id))",member)
        canvas.click(position=p)

    def heights(count, scrolls):
        expect(rows.locator("button")).to_have_count(min(count,25))
        h, total = rows.evaluate("r => [r.clientHeight,r.scrollHeight]")
        assert (total > h) == scrolls, (count,h,total)
        print(f"List size {count}: {h}px viewport / {total}px content")

    def camera_matches(saved):
        actual = graph.evaluate("camera()")
        assert isclose(actual["scale"],saved["scale"])
        for axis in ("x","y"):
            assert isclose(actual["position"][axis],saved["position"][axis],abs_tol=1e-8)

    at(1,0)
    expect(back).to_be_disabled()
    expect(forward).to_be_disabled()
    heights(2,False)
    node(2)
    at(2,1)
    heights(9,False)
    rows.get_by_role("button",name="Bram").click()
    at(7,2)
    graph.evaluate("network.moveTo({position:{x:80,y:40},scale:0.9})")
    bram_camera = graph.evaluate("camera()")
    node(6)
    at(6,3)
    graph.evaluate("network.moveTo({position:{x:99,y:33},scale:1.2})")
    alba_camera = graph.evaluate("camera()")
    for button,person,rev in [(back,7,4),(back,2,5),(forward,7,6),(forward,6,7),(back,7,8)]:
        button.click()
        at(person,rev)
        if person == 7:
            camera_matches(bram_camera)
        elif person == 6:
            camera_matches(alba_camera)
    node(2)
    at(2,9)
    expect(forward).to_be_disabled()
    finder.fill("2001")
    finder.press("Enter")
    at(2001,10)
    heights(1000,True)
    page.get_by_role("radiogroup", name="Maximum routes").get_by_text("5",exact=True).click()
    at(2001,11)
    scope.select_option("Direct")
    profile.locator("#next").click()
    rows.evaluate("r => r.scrollTop=100")
    rows.locator("button").nth(6).click()
    at(3032,12)
    query.fill("Hub")
    back.click()
    at(2001,13)
    expect(finder).to_have_value("2001")
    expect(scope).to_have_value("Direct")
    expect(profile.locator("#range")).to_have_text("Showing 26–50 of 1,000 matches")
    expect(rows.locator('[aria-current="true"]')).to_contain_text("3032")
    assert rows.evaluate("r => r.scrollTop") == 100
    expect(page.get_by_role("radio",name="5",exact=True)).to_be_checked()
    forward.click()
    at(3032,14)
    expect(finder).to_have_value("")
    expect(query).to_have_value("Hub")
    back.click()
    at(2001,15)
    home.click()
    at(1,16)
    expect(back).to_be_disabled()
    expect(forward).to_be_disabled()
    expect(finder).to_have_value("")

    # Restore a connected five-route map in the forward direction too.
    finder.fill("Sinbad")
    finder.press("Enter")
    at(5,17)
    page.get_by_role("radiogroup", name="Maximum routes").get_by_text("5",exact=True).click()
    at(5,18)
    data = graph.evaluate("JSON.stringify(data)")
    scope.select_option("Route Relevant")
    query.fill("Gio")
    back.click()
    at(1,19)
    forward.click()
    at(5,20)
    assert graph.evaluate("JSON.stringify(data)") == data
    expect(finder).to_have_value("Sinbad")
    expect(page.get_by_role("radio",name="5",exact=True)).to_be_checked()
    expect(query).to_have_value("Gio")
    expect(scope).to_have_value("Route Relevant")

    finder.fill("2000")
    finder.press("Enter")
    at(2000,21)
    heights(100,True)
    # A 15-contact presentation fixture, drawn from the real hub without
    # modifying the relationship network or its calculations.
    rows.evaluate("() => showConnections({...panel,depth:panel.depth+1,contacts:panel.contacts.slice(0,15)})")
    heights(15,False)
    print("PASS: mixed graph/panel walk, two-step Back/Forward, zoom and pan, branch replacement, "
          "map/explore and five-route map restoration, selected row, query/filter/page/scroll and Home reset.")
