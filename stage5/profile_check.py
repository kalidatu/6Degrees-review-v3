"""Stage 6A profile acceptance checks in a fresh browser session."""
from playwright.sync_api import expect


def check_profile(page, url, screenshots):
    page.add_init_script("""window.chipEvents = [];
        addEventListener("message", e => {
          const source = document.querySelector('iframe[title$="member_profile"]');
          if (source && e.source === source.contentWindow && e.data?.type === "streamlit:setComponentValue")
            chipEvents.push(e.data.value);
        });""")
    page.goto(url)
    card = page.frame_locator('iframe[title$="member_profile"]').locator("article")
    graph = page.frame_locator('iframe[title$="six_degrees_network"]').locator("canvas")
    finder = page.frame_locator('iframe[title$="finder_input"]').get_by_role("searchbox")
    back = page.get_by_role("button", name="Back", exact=True)
    home = page.get_by_role("button", name="Home", exact=True)

    def check(person, member_id, distance, count, revision, clicks):
        expect(card.get_by_role("heading", name=person, exact=True)).to_be_visible()
        expect(card.locator("#memberId")).to_have_text(f"Member ID {member_id}")
        expect(card.locator("#distance")).to_have_text(str(distance))
        expect(card.locator("#count")).to_have_text(str(count))
        expect(card.locator("#chips button")).to_have_count(count)
        expect(page.get_by_text(f"Accepted node clicks: {clicks} · View revision: {revision}")).to_be_visible()
        graph.evaluate("""async (_, rev) => { while(view !== rev || moving)
            await new Promise(resolve => requestAnimationFrame(resolve)); }""", revision)
        assert graph.evaluate("focus") == member_id
        footer = card.locator("footer")
        message = footer.get_by_role("button", name="Message", exact=True)
        connect = footer.get_by_role("button", name="Connect", exact=True)
        note = footer.get_by_text("Connection requests and messaging coming soon.", exact=True)
        if member_id == 1:
            expect(footer.get_by_role("button")).to_have_count(0)
            expect(note).to_be_hidden()
        else:
            expect(note).to_be_visible()
            expect(message).to_be_visible()
            expect(message).to_be_disabled()
            if distance == 1:
                expect(footer.get_by_text("Connected", exact=True)).to_be_visible()
                expect(connect).to_have_count(0)
            else:
                expect(connect).to_be_visible()
                expect(connect).to_be_disabled()
        if screenshots:
            screenshots.mkdir(parents=True, exist_ok=True)
            card.screenshot(path=screenshots / f"profile-{member_id}.png")

    def chip(person, member_id):
        card.get_by_role("button", name=f"Explore {person} · ID {member_id}", exact=True).click()

    check("David", 1, 0, 2, 0, 0)
    expect(card.locator("#connect")).to_be_hidden()
    chip("Mary", 2)
    check("Mary", 2, 1, 9, 1, 1)
    expect(card.locator("#connected")).to_be_visible()
    back.click()
    check("David", 1, 0, 2, 2, 1)
    chip("Laura", 4)
    check("Laura", 4, 1, 7, 3, 2)
    finder.fill("Sinbad")
    finder.press("Enter")
    check("Sinbad", 5, 2, 6, 4, 2)
    expect(card.locator("#location")).to_be_hidden()
    expect(card.locator("#connect")).to_be_disabled()
    page.get_by_role("radiogroup", name="Maximum routes").get_by_text("5",exact=True).click()
    check("Sinbad", 5, 2, 6, 5, 2)
    if screenshots:
        page.screenshot(path=screenshots / "connection-map-and-profile.png")
    chip("Gio", 12)
    expect(finder).to_have_value("")
    expect(page.get_by_role("heading", name="Explore Mode")).to_be_visible()
    expect(card.locator("#bio")).to_have_text("No biography added yet")
    expect(card.locator("#photo")).to_be_hidden()
    expect(card.locator("#initials")).to_have_text("G")
    back.click()
    check("Sinbad", 5, 2, 6, 7, 3)
    expect(finder).to_have_value("Sinbad")
    expect(page.get_by_role("radio",name="5",exact=True)).to_be_checked()
    for rev, mid, distance in [(8,101,3),(9,102,"No known connection")]:
        finder.fill(str(mid))
        finder.press("Enter")
        check("John Smith", mid, distance, 3, rev, 3)
    chip("Nell Vale",104)
    check("Nell Vale",104,"No known connection",2,10,4)
    home.click()
    check("David",1,0,2,11,4)
    expect(finder).to_have_value("")
    expect(back).to_be_disabled()
    assert page.evaluate("chipEvents.length") == 4
    mary_event = page.evaluate("chipEvents[0]")
    for replay in (mary_event, {**mary_event, "view": 11}):
        card.evaluate("""(_, value) => send("streamlit:setComponentValue", {dataType:"json", value})""", replay)
        page.wait_for_timeout(250)
        expect(page.get_by_text("Accepted node clicks: 4 · View revision: 11")).to_be_visible()
        expect(back).to_be_disabled()
    # Exercise image success and failure with local browser fixtures only.
    test_url = "https://avatar.invalid/demo"
    page.route(test_url, lambda route: route.fulfill(content_type="image/svg+xml",
               body='<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10"/>'))
    card.evaluate("""(article, photo) => render({id:1,name:"David",contacts:[],is_self:true,photo})""", test_url)
    expect(card.locator("#photo")).to_be_visible()
    page.route(test_url+"/broken", lambda route: route.abort())
    card.evaluate("""(article, photo) => render({id:1,name:"David",contacts:[],is_self:true,photo})""", test_url+"/broken")
    expect(card.locator("#photo")).to_be_hidden()
    expect(card.locator("#initials")).to_have_text("D")
    print("PASS: six requested profiles, live counts and distances, chip exploration in both modes, "
          "finder reset, five-route Back, Home, disabled Connect, missing fields and photo fallback.")
