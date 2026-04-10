import os
from datetime import datetime, timedelta

from playwright.sync_api import sync_playwright


def main() -> None:
    base = os.getenv("DETECTDATA_BASE_URL")
    user = os.getenv("DETECTDATA_USERNAME")
    pwd = os.getenv("DETECTDATA_PASSWORD")
    if not base or not user or not pwd:
        print("Missing env vars")
        return

    now = int(datetime.utcnow().timestamp() * 1000)
    start = int((datetime.utcnow() - timedelta(days=7)).timestamp() * 1000)

    stream_ids = [
        "8994_6",
        "8994_7",
        "8994_9",
        "9359_6",
        "9359_7",
        "9359_9",
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
            print("login failed")
            browser.close()
            return

        for sid in stream_ids:
            payload = {"streamId": sid, "start": start, "end": now}
            result = page.evaluate(
                """async (payload) => {
                    try {
                        const res = await fetch('/Data.ashx/GetStreamData', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify(payload),
                            credentials: 'include'
                        });
                        const text = await res.text();
                        return { status: res.status, text };
                    } catch (e) {
                        return { status: -1, text: String(e) };
                    }
                }""",
                payload,
            )
            print(f"\nSID {sid} status {result['status']} len {len(result['text'])}")
            print(result["text"][:700])

        browser.close()


if __name__ == "__main__":
    main()
