import json
import os
from itertools import product

from playwright.sync_api import sync_playwright


def main() -> None:
    base = os.getenv("DETECTDATA_BASE_URL")
    user = os.getenv("DETECTDATA_USERNAME")
    pwd = os.getenv("DETECTDATA_PASSWORD")

    if not base or not user or not pwd:
        print("Missing env vars")
        return

    site_id = 8994

    endpoints = [
        "LoggerStatus.ashx/GetLoggerStatus",
        "LoggerSearch.ashx/GetSiteInfo",
        "LoggerDetails.ashx/GetAll",
        "CommsList.ashx/GetSiteDetails",
        "Data.ashx/GetStreamInfo",
        "Data.ashx/GetStreamDetails",
        "Data.ashx/GetAxesAndStreams",
        "Data.ashx/GetIndexes",
        "Data.ashx/GetStreamData",
        "GoogleMap.ashx/GetLoggerChannelDataForMap",
        "DynamicWidget.ashx/GetData",
    ]

    payloads = [
        {"id": site_id},
        {"siteId": site_id},
        {"siteID": site_id},
        {"loggerId": site_id},
        {"site": site_id},
        {"siteId": str(site_id)},
        {"id": str(site_id)},
        {"siteIds": [site_id]},
        {"siteIds": str(site_id)},
        {"ids": [site_id]},
        {"deviceId": site_id},
        {"siteId": site_id, "channel": 6},
        {"siteId": site_id, "channel": 7},
        {"siteId": site_id, "channel": 9},
        {"siteId": site_id, "start": 0, "end": 0},
        {"siteId": site_id, "startDate": "2026-04-01", "endDate": "2026-04-10"},
        {},
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
        page.wait_for_timeout(10000)

        if page.title() == "Sign In":
            print("Login failed")
            browser.close()
            return

        interesting_hits = 0
        for endpoint, payload in product(endpoints, payloads):
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
                        return { status: res.status, ok: res.ok, text };
                    } catch (e) {
                        return { status: -1, ok: false, text: String(e) };
                    }
                }""",
                {"endpoint": endpoint, "payload": payload},
            )

            body = result["text"] or ""
            body_l = body.lower()
            if any(k in body_l for k in ["value", "stream", "channel", "m/s", "l/s", "timestamp", "mm", "depth", "velocity", "flow"]):
                interesting_hits += 1
                print("\nENDPOINT", endpoint)
                print("PAYLOAD", json.dumps(payload))
                print("STATUS", result["status"], "OK", result["ok"], "LEN", len(body))
                print(body[:1200].replace("\n", " "))

        print("interesting_hits", interesting_hits)
        browser.close()


if __name__ == "__main__":
    main()
