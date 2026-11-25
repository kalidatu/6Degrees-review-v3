"""V3 layout checks against the running local Streamlit application."""
import re
from pathlib import Path
from playwright.sync_api import expect
from stage5.demo import NAMES


def check_layout(page, url, screenshots=None):
    for width, height in ((1366, 768), (1920, 1080)):
        page.set_viewport_size({"width":width, "height":height})
        page.goto(url)
        canvas = page.frame_locator('iframe[title$="six_degrees_network"]').locator("canvas")
        finder = page.frame_locator('iframe[title$="finder_input"]').get_by_role("searchbox")
        card = page.frame_locator('iframe[title$="member_profile"]').locator("article")
        results = page.get_by_role("radiogroup", name="Matching members")
        expect(card.get_by_role("heading", name="David")).to_be_visible()
        canvas.wait_for()
        before = canvas.bounding_box()
        finder.fill("Test")
        expect(results.get_by_role("radio")).to_have_count(25)
        expect(page.get_by_text("Showing 1–25 of 1,006 matches")).to_be_visible()
        after = canvas.bounding_box()
        left, right = finder.bounding_box(), card.bounding_box()
        assert left["x"] + left["width"] <= after["x"]
        assert after["x"] + after["width"] <= right["x"]
        assert right["x"] + right["width"] <= width + 1
        assert right["y"] < after["y"] + 48 and after["y"]+after["height"] <= height
        assert abs(before["y"]-after["y"]) < 1
        assert results.evaluate("e => e.scrollHeight > e.clientHeight && getComputedStyle(e).overflowY==='auto'")
        if screenshots:
            Path(screenshots).mkdir(exist_ok=True,parents=True)
            page.screenshot(path=Path(screenshots) / f"V3-{width}.png")
        page.get_by_role("button",name="Next",exact=True).click()
        expect(page.get_by_text("Showing 26–50 of 1,006 matches")).to_be_visible()
        target = results.get_by_role("radio").nth(4)
        label = target.locator("..").inner_text()
        mid = int(re.search(r"ID (\d+)",label)[1])
        target.locator("..").click()
        expect(card.locator("#memberId")).to_have_text(f"Member ID {mid}")
        page.get_by_role("button",name="Back",exact=True).click()
        expect(card.locator("#name")).to_have_text("David")
        expect(finder).to_have_value("Test")
        expect(results.get_by_role("radio").nth(4)).to_be_checked()
        page.get_by_role("button",name="Forward",exact=True).click()
        expect(card.locator("#memberId")).to_have_text(f"Member ID {mid}")
        for term in ("9","99","999","Nobody Nowhere"):
            finder.fill(term)
            finder.press("Enter")
            if term == "9":
                expect(card.locator("#name")).to_have_text(NAMES[9])
            else:
                expect(page.get_by_text("No matching members.",exact=False)).to_be_visible()
                expect(card.locator("#memberId")).to_have_text("Member ID 9")
        finder.fill("Taylor Thousand")
        expect(results.get_by_role("radio")).to_have_count(1)
        expect(card.locator("#memberId")).to_have_text("Member ID 9")
        finder.press("Enter")
        expect(card.locator("#memberId")).to_have_text("Member ID 904")
        print(f"PASS {width}x{height}, 100% zoom: canvas y {before['y']:.0f} → {after['y']:.0f}, "
              f"width {after['width']:.0f}; 1,006 matches / 25 mounted radios, page-2 selection, history and numeric searches.")

    for width in (390, 820):
        page.set_viewport_size({"width": width, "height": 844})
        page.goto(url)
        expect(card.locator("#memberId")).to_have_text("Member ID 1")
        canvas.wait_for()
        assert finder.bounding_box()["y"] < canvas.bounding_box()["y"] < card.bounding_box()["y"]
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
        print(f"PASS {width}px: finder, graph and profile stack in order without horizontal overflow.")


if __name__ == "__main__":
    import argparse
    from playwright.sync_api import sync_playwright
    parser = argparse.ArgumentParser()
    parser.add_argument("--url",default="http://127.0.0.1:8501")
    parser.add_argument("--screenshots",type=Path)
    args = parser.parse_args()
    with sync_playwright() as runner:
        browser = runner.chromium.launch()
        check_layout(browser.new_page(),args.url,args.screenshots)
        browser.close()
