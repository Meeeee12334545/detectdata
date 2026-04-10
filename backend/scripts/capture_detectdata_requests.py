import os

from playwright.sync_api import sync_playwright


def main() -> None:
    base = os.getenv("DETECTDATA_BASE_URL")
    user = os.getenv("DETECTDATA_USERNAME")
    pwd = os.getenv("DETECTDATA_PASSWORD")

    if not base or not user or not pwd:
        print("Missing env vars")
        return

    targets = {
        "Dashboard.ashx/GetLatest",
        "LoggerSearch.ashx/GetSiteList",
        "LoggerDetails.ashx/GetSiteLocations",
        "Dashboard.ashx/GetDashboardSettings",
        "CoreServices.ashx/GetAppSettings",
    }

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        captured = []

        def on_request(req):
            for t in targets:
                if t in req.url:
                    hdr = req.headers
                    captured.append(
                        {
                            "url": req.url,
                            "method": req.method,
                            "post_data": req.post_data,
                            "content_type": hdr.get("content-type"),
                            "x_requested_with": hdr.get("x-requested-with"),
                            "x_session_id": hdr.get("x-sessionid") or hdr.get("x-session-id"),
                        }
                    )

        page.on("request", on_request)

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
        for idx, c in enumerate(captured, 1):
            print(f"\n[{idx}] {c['method']} {c['url']}")
            print("content_type:", c["content_type"])
            print("x_requested_with:", c["x_requested_with"])
            print("x_session_id:", c["x_session_id"])
            print("post_data:", c["post_data"])

        browser.close()


if __name__ == "__main__":
    main()
