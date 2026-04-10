from dataclasses import dataclass
from datetime import datetime, timedelta

from playwright.sync_api import Page

from playwright.sync_api import sync_playwright

from app.core.config import settings


@dataclass
class RemoteReading:
    site_name: str
    site_pmac: str | None
    device_name: str
    channel_parameter: str
    units: str | None
    timestamp: datetime
    value: float


@dataclass
class RemoteChannelDef:
    site_name: str
    site_pmac: str
    device_name: str
    channel_parameter: str
    units: str | None
    stream_id: str


class DetectDataClient:
    def __init__(self) -> None:
        self.base_url = settings.detectdata_base_url.rstrip("/")
        self.login_path = settings.detectdata_login_path
        self.username = settings.detectdata_username
        self.password = settings.detectdata_password

    @staticmethod
    def _parameter_from_units(units: str | None) -> str | None:
        normalized = (units or "").strip().lower()
        if normalized in {"m", "mm"}:
            return "depth"
        if normalized == "m/s":
            return "velocity"
        if normalized in {"l/s", "ls", "lps"}:
            return "flow"
        return None

    def _login(self, page: Page) -> bool:
        page.goto(f"{self.base_url}{self.login_path}", wait_until="networkidle")
        page.wait_for_timeout(1200)
        page.locator("#loginUserName").click()
        page.locator("#loginUserName").fill("")
        page.keyboard.type(self.username, delay=35)
        page.wait_for_timeout(250)
        page.locator(".nextButton").first.click()
        page.wait_for_timeout(500)
        page.locator("#loginPassword").click()
        page.locator("#loginPassword").fill("")
        page.keyboard.type(self.password, delay=30)
        page.wait_for_timeout(250)
        page.locator(".signInButton").first.click()
        page.wait_for_timeout(9000)

        if page.title() == "Sign In" or page.locator("#UtiliCoreLoginDialog").count() != 0:
            page.locator("#loginPassword").press("Enter")
            page.wait_for_timeout(3500)

        return page.title() != "Sign In" and page.locator("#UtiliCoreLoginDialog").count() == 0

    @staticmethod
    def _asmx_json(page: Page, method: str, payload: dict | str, timeout_ms: int = 20000):
        return page.evaluate(
            """async ({ method, payload, timeoutMs }) => {
                function callAsmx() {
                    return new Promise((resolve) => {
                        let finished = false;
                        const done = (value) => {
                            if (!finished) {
                                finished = true;
                                resolve(value);
                            }
                        };

                        const timer = setTimeout(() => {
                            done({ ok: false, err: `Timeout calling ${method} after ${timeoutMs}ms` });
                        }, timeoutMs);

                        try {
                            asmxJSON(
                                method,
                                payload,
                                function (data) { clearTimeout(timer); done({ ok: true, data: data }); },
                                function (err) { clearTimeout(timer); done({ ok: false, err: err }); }
                            );
                        } catch (e) {
                            clearTimeout(timer);
                            done({ ok: false, err: String(e) });
                        }
                    });
                }
                return await callAsmx();
            }""",
            {"method": method, "payload": payload, "timeoutMs": timeout_ms},
        )

    @staticmethod
    def _decode_block_points(range_key: str, points: list[dict]) -> list[tuple[datetime, float]]:
        factors = [10, 1000, 60000, 3600000]
        try:
            start_ms = int(str(range_key).split("_")[0])
        except Exception:
            return []

        last_ms = start_ms
        decoded: list[tuple[datetime, float]] = []

        for point in points:
            if not isinstance(point, dict):
                continue

            raw_t = point.get("t")
            raw_v = point.get("v")
            if raw_v is None:
                continue

            try:
                if isinstance(raw_t, (int, float)):
                    if raw_t > 10_000_000_000:
                        ts_ms = int(raw_t)
                    else:
                        ts_ms = last_ms + int(raw_t)
                elif isinstance(raw_t, str) and raw_t:
                    factor_idx = int(raw_t[0])
                    parts = raw_t[1:].split(",") if len(raw_t) > 1 else []
                    delta_ms = 0
                    for part in parts:
                        if part:
                            delta_ms += int(part) * factors[factor_idx]
                        factor_idx += 1
                    ts_ms = last_ms + delta_ms
                else:
                    continue
            except Exception:
                continue

            last_ms = ts_ms
            decoded.append((datetime.utcfromtimestamp(ts_ms / 1000.0), float(raw_v)))

        return decoded

    def fetch_inventory(self) -> list[RemoteChannelDef]:
        if not self.username or not self.password:
            return []

        channel_defs: list[RemoteChannelDef] = []

        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()

            if not self._login(page):
                browser.close()
                raise RuntimeError("DetectData login failed")

            site_locations_result = self._asmx_json(page, "LoggerDetails.ashx/GetSiteLocations", "{}")
            site_locations = site_locations_result.get("data") if site_locations_result.get("ok") else []
            if not isinstance(site_locations, list):
                site_locations = []

            for site in site_locations:
                site_id = site.get("siteId")
                site_name = site.get("name")
                if not site_id or not site_name:
                    continue

                pmac = str(site_id).zfill(4)
                device_name = f"PMAC-{pmac}"
                channels = site.get("channels") or []

                for channel in channels:
                    channel_no = channel.get("channel")
                    units = channel.get("units")
                    if channel_no is None:
                        continue

                    parameter = self._parameter_from_units(units) or f"channel_{channel_no}"
                    channel_defs.append(
                        RemoteChannelDef(
                            site_name=str(site_name),
                            site_pmac=pmac,
                            device_name=device_name,
                            channel_parameter=parameter,
                            units=units,
                            stream_id=f"{site_id}_{channel_no}",
                        )
                    )

            browser.close()

        return channel_defs

    def fetch_readings(
        self,
        channel_defs: list[RemoteChannelDef] | None = None,
        days_back: int = 3,
        latest_only: bool = True,
        chunk_days: int = 90,
    ) -> list[RemoteReading]:
        if not self.username or not self.password:
            return []

        readings: list[RemoteReading] = []
        end_ms = int(datetime.utcnow().timestamp() * 1000)
        start_ms = int((datetime.utcnow() - timedelta(days=max(days_back, 1))).timestamp() * 1000)

        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()

            if not self._login(page):
                browser.close()
                raise RuntimeError("DetectData login failed")

            if channel_defs is None:
                channel_defs = self.fetch_inventory()

            chunk_ms = max(chunk_days, 1) * 24 * 60 * 60 * 1000

            for channel_def in channel_defs:
                if latest_only:
                    ranges = [(start_ms, end_ms)]
                else:
                    ranges = []
                    cursor = start_ms
                    while cursor < end_ms:
                        nxt = min(cursor + chunk_ms, end_ms)
                        ranges.append((cursor, nxt))
                        cursor = nxt

                latest_point: tuple[datetime, float] | None = None

                for range_start, range_end in ranges:
                    stream_result = self._asmx_json(
                        page,
                        "Data.ashx/GetStreamData",
                        {"streamId": channel_def.stream_id, "start": range_start, "end": range_end},
                    )
                    if not stream_result.get("ok"):
                        continue

                    data = stream_result.get("data")
                    if not isinstance(data, dict) or not data:
                        continue

                    for range_key, points in data.items():
                        if not isinstance(points, list) or not points:
                            continue
                        decoded_points = self._decode_block_points(str(range_key), points)
                        if not decoded_points:
                            continue

                        if latest_only:
                            point = decoded_points[-1]
                            if latest_point is None or point[0] > latest_point[0]:
                                latest_point = point
                        else:
                            for ts, val in decoded_points:
                                readings.append(
                                    RemoteReading(
                                        site_name=channel_def.site_name,
                                        site_pmac=channel_def.site_pmac,
                                        device_name=channel_def.device_name,
                                        channel_parameter=channel_def.channel_parameter,
                                        units=channel_def.units,
                                        timestamp=ts,
                                        value=val,
                                    )
                                )

                if latest_only and latest_point is not None:
                    readings.append(
                        RemoteReading(
                            site_name=channel_def.site_name,
                            site_pmac=channel_def.site_pmac,
                            device_name=channel_def.device_name,
                            channel_parameter=channel_def.channel_parameter,
                            units=channel_def.units,
                            timestamp=latest_point[0],
                            value=latest_point[1],
                        )
                    )

            browser.close()

        return readings
