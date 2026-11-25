"""Exercise budgeted and off-graph navigation through a live Streamlit session."""
from playwright.sync_api import expect


def check_expansion(page, url, screenshots=None):
    page.goto(url)
    profile = page.frame_locator('iframe[title$="member_profile"]')
    query = profile.locator("#localSearch")
    scope = profile.locator("#scope")
    rows = profile.locator("#rows")
    finder = page.frame_locator('iframe[title$="finder_input"]').get_by_role("searchbox")
    canvas = page.frame_locator('iframe[title$="six_degrees_network"]').locator("canvas")
    canvas.wait_for()
    frame = next(f for f in page.frames if "six_degrees_network" in f.url)
    back = page.get_by_role("button", name="Back", exact=True)
    home = page.get_by_role("button", name="Home", exact=True)

    def search(term):
        finder.fill(term)
        finder.press("Enter")

    def settled(member, revision):
        frame.wait_for_function("a => focus === a[0] && view === a[1] && !moving", arg=[member,revision])
        expect(profile.locator("#memberId")).to_have_text(f"Member ID {member}")

    search("Sinbad")
    settled(5,1)
    scope.select_option("Mutual")
    expect(rows.locator("button")).to_have_text(["LauraID 4"])
    scope.select_option("Route Relevant")
    expect(rows.locator("button")).to_have_count(3)
    scope.select_option("Direct")
    query.fill("nik")
    rows.get_by_role("button",name="Niko").click()
    settled(19,2)
    expect(finder).to_have_value("")
    expect(profile.locator("#panelTitle")).to_contain_text("Niko's Network")
    scope.select_option("Route Relevant")
    expect(profile.locator("#hint")).to_contain_text("Open a Connection Map")
    back.click()
    settled(5,3)
    expect(finder).to_have_value("Sinbad")
    expect(scope).to_have_value("Direct")
    expect(query).to_have_value("nik")
    search("2000")
    settled(2000,4)
    expect(profile.locator("#count")).to_have_text("100")
    search("2001")
    settled(2001,5)
    expect(profile.locator("#count")).to_have_text("1000")
    expect(rows.locator("button")).to_have_count(25)
    expect(profile.locator("#panelTitle")).to_have_text("Test Hub 1000's Network (1,000)")
    assert len(frame.evaluate("data.nodes")) == 16
    assert 4000 not in frame.evaluate("network.body.data.nodes.getIds()")
    scope.select_option("Mutual")
    expect(profile.locator("#hint")).to_have_text("No matching connections.")
    scope.select_option("All")
    profile.locator("#next").click()
    rows.evaluate("r => r.scrollTop = 120")
    scroll = rows.evaluate("r => r.scrollTop")
    assert scroll > 0
    rows.locator("button").nth(6).click()
    settled(3032,6)
    back.click()
    settled(2001,7)
    expect(profile.locator("#range")).to_have_text("Showing 26–50 of 1,000 matches")
    assert rows.evaluate("r => r.scrollTop") == scroll
    query.fill("#4000")
    expect(rows.locator("button")).to_have_count(1)
    for rev in (8,10):
        rows.locator("button").click()
        settled(4000,rev)
        back.click()
        settled(2001,rev+1)
        expect(query).to_have_value("#4000")
        assert len(frame.evaluate("data.nodes")) == 16
        assert len(frame.evaluate("data.edges")) == 15
    if screenshots:
        profile.locator("#browser").screenshot(path=screenshots / "large-panel.png")
    # Graph clicks use the same history entry as list selection. Check the
    # local panel query survives navigation initiated from the other iframe.
    point = frame.evaluate("network.canvasToDOM(network.getPosition(3001))")
    canvas.click(position=point)
    settled(3001,12)
    back.click()
    settled(2001,13)
    expect(query).to_have_value("#4000")
    expect(finder).to_have_value("2001")
    home.click()
    settled(1,14)
    expect(finder).to_have_value("")
    expect(query).to_have_value("")
    expect(scope).to_have_value("All")
    expect(back).to_be_disabled()
    print("PASS: Sinbad → Niko, all filters, #2000 and #2001, 25 rendered rows, hidden-member search, repeated clicks, page/scroll restoration, Back and Home.")
