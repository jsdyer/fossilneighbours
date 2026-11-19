"""Exercise the built explorer at a project subpath in Chromium."""
from functools import partial
import os
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import shutil
import tempfile
import threading
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def main():
    screenshots = ROOT / "browser-checks"
    screenshots.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory() as temporary:
        shutil.copytree(ROOT / "dist", Path(temporary) / "example-tool")
        server = ThreadingHTTPServer(("127.0.0.1", 0), partial(QuietHandler, directory=temporary))
        threading.Thread(target=server.serve_forever, daemon=True).start()
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(executable_path=os.environ.get("CHROMIUM_PATH"))
                page = browser.new_page(viewport={"width": 1280, "height": 1000})
                errors = []
                page.on("pageerror", lambda error: errors.append(str(error)))
                page.goto(f"http://127.0.0.1:{server.server_port}/example-tool/")
                page.locator("#focus-name").filter(has_text="Coal Mine Point").wait_for()
                assert "7 collections" in page.locator("#totals").inner_text()
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
                page.screenshot(path=str(screenshots / "desktop.png"), full_page=True)
                page.set_viewport_size({"width": 390, "height": 844})
                assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
                page.screenshot(path=str(screenshots / "mobile.png"), full_page=True)
                assert not errors, errors
                browser.close()
            print("Browser checks passed: project subpath, source records, filters and mobile layout")
        finally:
            server.shutdown()


if __name__ == "__main__":
    main()
