import os
import time

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

        records: list[tuple[str, int, str]] = []

        def on_response(resp):
            url = resp.url
            if (
                "ServerEvent.ashx" in url
                or "LoggerSearch.ashx/GetSiteList" in url
                or "LoggerDetails.ashx/GetSiteLocations" in url
                or "Data.ashx/" in url
            ):
                try:
                    body = resp.text()
                except Exception:
                    body = ""
                records.append((url, resp.status, body))

        page.on("response", on_response)

        def do_login() -> bool:
            page.goto(base, wait_until="networkidle")
            page.wait_for_timeout(1500)
            page.locator("#loginUserName").click()
            page.locator("#loginUserName").fill("")
            page.keyboard.type(user, delay=40)
            page.wait_for_timeout(250)
            page.locator(".nextButton").first.click()
            page.wait_for_timeout(550)
            page.locator("#loginPassword").click()
            page.locator("#loginPassword").fill("")
            page.keyboard.type(pwd, delay=35)
            page.wait_for_timeout(300)
            page.locator(".signInButton").first.click()
            page.wait_for_timeout(9000)
            if page.title() == "Sign In" or page.locator("#UtiliCoreLoginDialog").count() != 0:
                page.locator("#loginPassword").press("Enter")
                page.wait_for_timeout(3500)
            return page.title() != "Sign In" and page.locator("#UtiliCoreLoginDialog").count() == 0

        success = False
        for _ in range(3):
            if do_login():
                success = True
                break
            time.sleep(1)

        if success:
            page.wait_for_timeout(18000)

        print("title", page.title())
        print("url", page.url)

        for url, status, body in records:
            print(f"\nURL {url} status {status} len {len(body)}")
            print(body[:1200].replace("\n", " "))

        browser.close()


if __name__ == "__main__":
    main()
