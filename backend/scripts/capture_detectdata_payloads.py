import os
import time

from playwright.sync_api import sync_playwright


def main() -> None:
    base = os.getenv("DETECTDATA_BASE_URL")
    user = os.getenv("DETECTDATA_USERNAME")
    pwd = os.getenv("DETECTDATA_PASSWORD")

    if not base or not user or not pwd:
        print("Missing required env vars")
        return

    interesting = [
        "Dashboard.ashx/GetLatest",
        "LoggerSearch.ashx/GetSiteList",
        "LoggerDetails.ashx/GetSiteLocations",
        "Dashboard.ashx/GetDashboardSettings",
    ]
    captured: dict[str, str] = {}

    def do_login(page) -> bool:
        page.goto(base, wait_until="networkidle")
        page.wait_for_timeout(1500)
        page.locator("#loginUserName").click()
        page.locator("#loginUserName").fill("")
        page.keyboard.type(user, delay=40)
        page.wait_for_timeout(250)
        page.locator(".nextButton").first.click()
        page.wait_for_timeout(600)
        page.locator("#loginPassword").click()
        page.locator("#loginPassword").fill("")
        page.keyboard.type(pwd, delay=35)
        page.wait_for_timeout(350)
        page.locator(".signInButton").first.click()
        page.wait_for_timeout(9000)

        if page.title() == "Sign In" or page.locator("#UtiliCoreLoginDialog").count() != 0:
            page.locator("#loginPassword").press("Enter")
            page.wait_for_timeout(4000)

        return page.title() != "Sign In" and page.locator("#UtiliCoreLoginDialog").count() == 0

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        def on_response(resp):
            url = resp.url
            for token in interesting:
                if token in url and token not in captured:
                    try:
                        captured[token] = resp.text()
                    except Exception as ex:
                        captured[token] = f"<no-body: {ex}>"

        page.on("response", on_response)

        logged_in = False
        for _ in range(3):
            if do_login(page):
                logged_in = True
                break
            time.sleep(1)

        if logged_in:
            page.wait_for_timeout(10000)

        print("title", page.title())
        print("url", page.url)

        for token in interesting:
            body = captured.get(token)
            print(f"\n=== {token} ===")
            if not body:
                print("<missing>")
            else:
                print(body[:3000])

        browser.close()


if __name__ == "__main__":
    main()
