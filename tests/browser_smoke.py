"""Exercise the built explorer at a project subpath in Chromium."""
from functools import partial
import json
import os
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import shutil
import tempfile
import threading
from playwright.sync_api import expect, sync_playwright

ROOT = Path(__file__).resolve().parents[1]


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def main():
    screenshots = ROOT / "browser-checks"
    screenshots.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory() as temporary:
        shutil.copytree(ROOT / "dist", Path(temporary) / "example-tool")
        # The hub supplies the common metrics script at the origin root.
        (Path(temporary) / "assets").mkdir()
        (Path(temporary) / "assets/tool-metrics.js").write_text("")
        server = ThreadingHTTPServer(("127.0.0.1", 0), partial(QuietHandler, directory=temporary))
        threading.Thread(target=server.serve_forever, daemon=True).start()
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(executable_path=os.environ.get("CHROMIUM_PATH"))
                page = browser.new_page(viewport={"width": 1280, "height": 1000})
                errors = []
                page.on("pageerror", lambda error: errors.append(str(error)))
                url = f"http://127.0.0.1:{server.server_port}/example-tool/"
                snapshot = json.loads((ROOT / "dist/data/records.json").read_text())
                page.goto(url)
                page.locator("#focus-name").filter(has_text="Coal Mine Point").wait_for()
                assert f"{len(snapshot['presets']['Joggins'])} collections" in page.locator("#totals").inner_text()
                page.locator("#search").fill("Hylonomus")
                assert page.locator("#records article").count() > 0
                assert page.locator("#records article").count() < 15
                page.locator("#scope").select_option("formation")
                page.locator("#age").fill("318")
                assert page.locator("#records article").count() > 0
                page.locator("#age").fill("80")
                assert page.locator("#records article").count() == 0
                page.locator("#formation").select_option("Haslam")
                assert page.locator("#province").text_content() == "British Columbia"
                page.locator("#environment").check()
                page.locator("#peers button").first.click()
                assert page.locator("#return").is_visible()
                page.locator("#return").click()
                page.locator("#formation").select_option("Joggins")
                page.goto(url)
                expect(page.locator("#explorer")).to_be_visible()
                page.screenshot(path=str(screenshots / "desktop.png"))
                page.set_viewport_size({"width": 390, "height": 844})
                overflow = page.evaluate("""() => [...document.querySelectorAll('body *')]
                    .filter(e => e.getBoundingClientRect().right > innerWidth + 1)
                    .map(e => [e.tagName, e.id, e.className, e.getBoundingClientRect().width])""")
                assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth"), overflow
                page.screenshot(path=str(screenshots / "mobile.png"))
                example = page.locator(".example-name a")
                box = example.bounding_box()
                assert box and 0 <= box["y"] <= box["y"] + box["height"] < 844
                example_path = example.get_attribute("href")
                example.click()
                expect(page.get_by_role("heading",level=1)).to_contain_text("Coal Mine Point")
                expect(page.locator("main")).to_contain_text("Hylonomus lyelli")
                expect(page.locator("#literature")).to_have_text("Source literature")
                page.screenshot(path=str(screenshots / "mobile-collection.png"))
                assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
                page.get_by_role("link",name="Age neighbours",exact=True).click()
                peer_link = page.locator("#neighbours ~ ul.profile-list").first.locator("a").first
                peer_path = peer_link.get_attribute("href")
                peer_id = int(peer_path.rstrip("/").split("/")[-1])
                peer_name = peer_link.text_content()
                peer_link.click()
                expect(page.get_by_role("heading",level=1)).to_contain_text(peer_name)
                page.get_by_role("link",name="Explore this collection’s occurrence records").click()
                expect(page.locator("#examining")).to_contain_text(peer_name)
                expect(page.locator("#active-profile a")).to_have_attribute("href", f"./records/collections/{peer_id}/")
                assert page.locator("#records article").count() == sum(row["col"] == peer_id for row in snapshot["occurrences"])
                page.goto(url + "records/formations/haslam/")
                page.get_by_role("link",name="Search the Haslam occurrence records").click()
                expect(page.locator("#formation")).to_have_value("Haslam")
                expect(page.locator("#scope")).to_have_value("formation")
                page.goto(url)
                page.get_by_role("link",name="Find Hylonomus in this collection").click()
                expect(page.locator("#search")).to_have_value("Hylonomus")
                expect(page.locator("#record-count")).to_contain_text("matching occurrence")
                static = browser.new_page(java_script_enabled=False, viewport={"width":390,"height":844})
                static.goto(url)
                static.get_by_role("link",name="Browse all fossil profiles").click()
                expect(static.get_by_role("heading",level=1)).to_contain_text("Canadian fossil collection")
                static.get_by_role("link",name="Joggins Formation",exact=True).click()
                expect(static.locator("main")).to_contain_text("accepted taxa")
                assert static.get_by_role("link",name="explore the Joggins coal seams",exact=False).get_attribute("href") == "https://coolcode.ca/coalbelow/"
                static.get_by_role("link",name="Coal Mine Point",exact=False).first.click()
                expect(static.get_by_role("heading",level=1)).to_contain_text("Coal Mine Point")
                assert static.locator("link[rel=canonical]").get_attribute("href") == "https://coolcode.ca/fossilneighbours/" + example_path.removeprefix("./")
                assert not errors, errors
                browser.close()
            print("Browser checks passed: source records, connected age peers, restored search, mobile profiles and the script-free directory")
        finally:
            server.shutdown()


if __name__ == "__main__":
    main()
