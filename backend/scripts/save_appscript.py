import os

from playwright.sync_api import sync_playwright


def main() -> None:
    base = os.getenv("DETECTDATA_BASE_URL")
    user = os.getenv("DETECTDATA_USERNAME")
    pwd = os.getenv("DETECTDATA_PASSWORD")
    if not base or not user or not pwd:
        print("Missing env vars")
        return

    app_script = ""

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        def on_response(resp):
            nonlocal app_script
            if "AppScript.ashx?x-sessionId=" in resp.url and not app_script:
                try:
                    app_script = resp.text()
                except Exception:
                    app_script = ""

        page.on("response", on_response)
        page.goto(base, wait_until="networkidle")
        page.locator("#loginUserName").click()
        page.keyboard.type(user, delay=40)
        page.locator(".nextButton").first.click()
        page.wait_for_timeout(500)
        page.locator("#loginPassword").click()
        page.keyboard.type(pwd, delay=35)
        page.locator(".signInButton").first.click()
        page.wait_for_timeout(12000)

        if app_script:
            with open("/tmp/appscript.js", "w", encoding="utf-8") as f:
                f.write(app_script)
            print("saved /tmp/appscript.js", len(app_script))
        else:
            print("no appscript captured")

        browser.close()


if __name__ == "__main__":
    main()
