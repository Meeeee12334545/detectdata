import os
import re

from playwright.sync_api import sync_playwright


def main() -> None:
    base = os.getenv("DETECTDATA_BASE_URL")
    user = os.getenv("DETECTDATA_USERNAME")
    pwd = os.getenv("DETECTDATA_PASSWORD")

    if not base or not user or not pwd:
        print("Missing env vars")
        return

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        app_script_body = ""

        def on_response(resp):
            nonlocal app_script_body
            if "AppScript.ashx?x-sessionId=" in resp.url and not app_script_body:
                try:
                    app_script_body = resp.text()
                except Exception:
                    app_script_body = ""

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

        print("title", page.title())

        if not app_script_body:
            print("No AppScript body captured")
            browser.close()
            return

        endpoints = sorted(set(re.findall(r"[A-Za-z]+\.ashx/[A-Za-z0-9_]+", app_script_body)))
        print("endpoint_count", len(endpoints))
        for ep in endpoints[:500]:
            print(ep)

        browser.close()


if __name__ == "__main__":
    main()
