import os

from playwright.sync_api import sync_playwright


def main() -> None:
    endpoints = [
        "Download.ashx/CsvData",
        "Download.ashx/SiteList",
        "Download.ashx/SiteInfoReporter",
        "Download.ashx/DatFiles",
        "Data.ashx/GetDatExport",
        "Data.ashx/GetStreamData",
        "AnalysisWidget.ashx/GetManualReport",
    ]

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
            print("login failed")
            browser.close()
            return

        for endpoint in endpoints:
            result = page.evaluate(
                """async (ep) => {
                    try {
                        const res = await fetch('/' + ep, {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: '{}',
                            credentials: 'include'
                        });
                        const text = await res.text();
                        return { status: res.status, text: text.slice(0, 1000) };
                    } catch (e) {
                        return { status: -1, text: String(e) };
                    }
                }""",
                endpoint,
            )
            print(f"\n{endpoint} status {result['status']}")
            print(result["text"])

        browser.close()


if __name__ == "__main__":
    main()
