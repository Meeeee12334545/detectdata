import os

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

        # call helper in page context
        result = page.evaluate(
            """async () => {
                function callAsmx(method, payload) {
                    return new Promise((resolve) => {
                        try {
                            asmxJSON(
                                method,
                                payload,
                                function (data) { resolve({ ok: true, data: data }); },
                                function (err) { resolve({ ok: false, err: err }); }
                            );
                        } catch (e) {
                            resolve({ ok: false, err: String(e) });
                        }
                    });
                }

                const siteList = await callAsmx("LoggerSearch.ashx/GetSiteList", "{}");
                const siteLocs = await callAsmx("LoggerDetails.ashx/GetSiteLocations", "{}");

                const streamCandidates = [
                    "8994_6",
                    "8994_7",
                    "8994_9",
                    "8994_6_0",
                    "8994_7_0",
                    "8994_9_0",
                    "9359_6",
                    "9359_7",
                    "9359_9",
                    "9359_6_0",
                    "9359_7_0",
                    "9359_9_0"
                ];

                const now = Date.now();
                const start = now - (7 * 24 * 60 * 60 * 1000);
                const streamResults = [];
                for (const sid of streamCandidates) {
                    const r = await callAsmx("Data.ashx/GetStreamData", { streamId: sid, start: start, end: now });
                    streamResults.push({ sid, ok: r.ok, sample: JSON.stringify(r.ok ? r.data : r.err).slice(0, 300) });
                }

                return {
                    siteListOk: siteList.ok,
                    siteListSample: JSON.stringify(siteList.ok ? siteList.data : siteList.err).slice(0, 400),
                    siteLocOk: siteLocs.ok,
                    siteLocSample: JSON.stringify(siteLocs.ok ? siteLocs.data : siteLocs.err).slice(0, 400),
                    streamResults,
                };
            }"""
        )

        print("siteListOk", result["siteListOk"])
        print("siteListSample", result["siteListSample"])
        print("siteLocOk", result["siteLocOk"])
        print("siteLocSample", result["siteLocSample"])
        print("streamResults")
        for row in result["streamResults"]:
            print(row)

        browser.close()


if __name__ == "__main__":
    main()
