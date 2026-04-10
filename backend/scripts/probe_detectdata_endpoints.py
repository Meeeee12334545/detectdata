import json
import os

from playwright.sync_api import sync_playwright


def main() -> None:
    base = os.getenv("DETECTDATA_BASE_URL")
    user = os.getenv("DETECTDATA_USERNAME")
    pwd = os.getenv("DETECTDATA_PASSWORD")

    if not base or not user or not pwd:
        print("Missing env vars")
        return

    probes = [
        ("LoggerSearch.ashx/GetSiteList", {}),
        ("LoggerDetails.ashx/GetSiteLocations", {}),
        ("LoggerSearch.ashx/GetSiteInfo", {"id": "8994"}),
        ("LoggerSearch.ashx/GetSiteInfo", {"siteId": 8994}),
        ("LoggerDetails.ashx/GetAll", {"siteId": 8994}),
        ("LoggerDetails.ashx/GetAll", {"id": 8994}),
        ("LoggerDetails.ashx/GetAll", {"siteId": "8994"}),
        ("Data.ashx/GetStreamInfo", {"siteId": 8994}),
        ("Data.ashx/GetStreamDetails", {"siteId": 8994}),
        ("Data.ashx/GetAxesAndStreams", {"siteId": 8994}),
        ("Data.ashx/GetIndexes", {"siteId": 8994}),
    ]

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        page.goto(base, wait_until="networkidle")
        page.locator("#loginUserName").click()
        page.keyboard.type(user, delay=40)
        page.locator(".nextButton").first.click()
        page.wait_for_timeout(500)
        page.locator("#loginPassword").click()
        page.keyboard.type(pwd, delay=35)
        page.locator(".signInButton").first.click()
        page.wait_for_timeout(11000)

        if page.title() == "Sign In":
            print("Login failed")
            browser.close()
            return

        for endpoint, payload in probes:
            result = page.evaluate(
                """async ({ endpoint, payload }) => {
                    try {
                        const res = await fetch('/' + endpoint, {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify(payload),
                            credentials: 'include'
                        });
                        const text = await res.text();
                        return { endpoint, ok: res.ok, status: res.status, text: text.slice(0, 900) };
                    } catch (e) {
                        return { endpoint, ok: false, status: -1, text: String(e) };
                    }
                }""",
                {"endpoint": endpoint, "payload": payload},
            )
            print("\n---", endpoint, payload, "---")
            print("status", result["status"], "ok", result["ok"])
            print(result["text"])

        browser.close()


if __name__ == "__main__":
    main()
