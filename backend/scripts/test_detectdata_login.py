import os
import time
from playwright.sync_api import sync_playwright


def attempt(page, user: str, pwd: str, idx: int) -> bool:
    page.goto(os.getenv("DETECTDATA_BASE_URL", "https://www.detecdata-en.com"), wait_until="networkidle")
    page.wait_for_timeout(1500)

    page.locator("#loginUserName").click()
    page.locator("#loginUserName").fill("")
    page.keyboard.type(user, delay=40)
    page.wait_for_timeout(300)
    page.locator(".nextButton").first.click()
    page.wait_for_timeout(600)

    page.locator("#loginPassword").click()
    page.locator("#loginPassword").fill("")
    page.keyboard.type(pwd, delay=35)
    page.wait_for_timeout(400)

    page.locator(".signInButton").first.click()
    page.wait_for_timeout(9000)

    title = page.title()
    login_count = page.locator("#UtiliCoreLoginDialog").count()
    login_style = page.locator("#UtiliCoreLoginDialog").first.get_attribute("style") if login_count else "<none>"

    print(f"attempt={idx} title={title} login_count={login_count} style={login_style}")

    if title != "Sign In" and login_count == 0:
        page.screenshot(path=f"/tmp/dd-login-ok-{idx}.png", full_page=True)
        return True

    # Try enter key fallback
    page.locator("#loginPassword").press("Enter")
    page.wait_for_timeout(4000)
    title2 = page.title()
    login_count2 = page.locator("#UtiliCoreLoginDialog").count()
    print(f"attempt={idx} after-enter title={title2} login_count={login_count2}")

    ok = title2 != "Sign In" and login_count2 == 0
    if ok:
        page.screenshot(path=f"/tmp/dd-login-ok-enter-{idx}.png", full_page=True)
    else:
        page.screenshot(path=f"/tmp/dd-login-fail-{idx}.png", full_page=True)
    return ok


def main() -> None:
    user = os.getenv("DETECTDATA_USERNAME", "")
    pwd = os.getenv("DETECTDATA_PASSWORD", "")
    if not user or not pwd:
        print("Missing credentials")
        return

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        success = False
        for i in range(1, 4):
            if attempt(page, user, pwd, i):
                success = True
                break
            time.sleep(1)

        print("login_success", success)
        browser.close()


if __name__ == "__main__":
    main()
