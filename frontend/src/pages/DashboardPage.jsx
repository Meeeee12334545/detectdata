import { useEffect, useMemo, useState } from "react";

import { api } from "../services/api";

function getMeterStatus(lastSeen) {
  if (!lastSeen) return "no-data";
  const ts = new Date(lastSeen).getTime();
  if (Number.isNaN(ts)) return "no-data";
  const minutesAgo = (Date.now() - ts) / 60000;
  if (minutesAgo < 30) return "online";
  if (minutesAgo < 120) return "stale";
  return "offline";
}

const STATUS_LABEL = { online: "Online", stale: "Stale", offline: "Offline", "no-data": "No Data" };
const STATUS_CLASS = { online: "badge-online", stale: "badge-stale", offline: "badge-offline", "no-data": "badge-offline" };

export default function DashboardPage() {
  const [rows, setRows] = useState([]);
  const [allSites, setAllSites] = useState([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState(null);
  const [siteFilter, setSiteFilter] = useState("");

  useEffect(() => {
    let errorCount = 0;
    Promise.all([
      api.get("/data/latest").then((res) => res.data || []).catch((err) => {
        if (err?.response?.status !== 401) errorCount += 1;
        return [];
      }),
      api.get("/sites").then((res) => res.data || []).catch((err) => {
        if (err?.response?.status !== 401) errorCount += 1;
        return [];
      }),
    ]).then(([latestRows, sites]) => {
      setRows(latestRows);
      setAllSites(sites);
      if (errorCount > 0) setLoadError("Some data failed to load. Please refresh the page or check your connection.");
    }).finally(() => setLoading(false));
  }, []);

  const meterCards = useMemo(() => {
    const map = new Map();

    for (const row of rows) {
      const meterKey = `${row.pmac || "na"}|${row.site}|${row.device}`;
      if (!map.has(meterKey)) {
        map.set(meterKey, {
          pmac: row.pmac || "N/A",
          site: row.site,
          device: row.device,
          lastSeen: row.timestamp,
          channels: new Map(),
        });
      }

      const meter = map.get(meterKey);
      if (new Date(row.timestamp) > new Date(meter.lastSeen)) {
        meter.lastSeen = row.timestamp;
      }

      if (!meter.channels.has(row.parameter)) {
        meter.channels.set(row.parameter, {
          parameter: row.parameter,
          value: row.value,
          units: row.units || "",
          timestamp: row.timestamp,
        });
      }
    }

    // Add empty cards for sites with no data
    const sitesWithData = new Set(Array.from(map.values()).map((m) => m.site));
    for (const site of allSites) {
      if (!sitesWithData.has(site.site_name)) {
        map.set(`no-data|${site.site_name}`, {
          pmac: site.pmac_code || "N/A",
          site: site.site_name,
          device: site.pmac_code ? `PMAC-${site.pmac_code}` : "Unknown",
          lastSeen: null,
          channels: new Map(),
        });
      }
    }

    return Array.from(map.values())
      .sort((a, b) => {
        if (a.lastSeen && !b.lastSeen) return -1;
        if (!a.lastSeen && b.lastSeen) return 1;
        return new Date(b.lastSeen) - new Date(a.lastSeen);
      })
      .map((meter) => ({
        ...meter,
        channels: Array.from(meter.channels.values()).sort((a, b) => a.parameter.localeCompare(b.parameter)),
      }));
  }, [rows, allSites]);

  const filteredMeterCards = useMemo(() => {
    const q = siteFilter.trim().toLowerCase();
    if (!q) return meterCards;
    return meterCards.filter((meter) => {
      return [meter.site, meter.pmac, meter.device].some((value) =>
        String(value || "").toLowerCase().includes(q)
      );
    });
  }, [meterCards, siteFilter]);

  const statusSummary = useMemo(() => {
    return filteredMeterCards.reduce(
      (acc, meter) => {
        acc[getMeterStatus(meter.lastSeen)] += 1;
        return acc;
      },
      { online: 0, stale: 0, offline: 0, "no-data": 0 }
    );
  }, [filteredMeterCards]);

  if (loading) {
    return (
      <section>
        <div className="page-header">
          <h2 className="page-title">Dashboard</h2>
          <p className="page-desc">Live readings from all connected meters</p>
        </div>
        <div className="loading-state">
          <div className="spinner" />
          <span>Loading latest readings…</span>
        </div>
      </section>
    );
  }

  if (meterCards.length === 0) {
    return (
      <section>
        <div className="page-header">
          <h2 className="page-title">Dashboard</h2>
          <p className="page-desc">Live readings from all connected meters</p>
        </div>
        {loadError && <p className="error" style={{ marginBottom: "1rem" }}>{loadError}</p>}
        <div className="empty-state">
          <div className="empty-state-icon">📡</div>
          <h3>No meters found</h3>
          <p>No data has been received yet. Check your meter connections and data ingestion pipeline.</p>
        </div>
      </section>
    );
  }

  return (
    <section>
      <div className="page-header">
        <h2 className="page-title">Dashboard</h2>
        <p className="page-desc">
          {meterCards.length} site{meterCards.length !== 1 ? "s" : ""} &mdash; {meterCards.filter((m) => m.lastSeen).length} with data
        </p>
      </div>

      {loadError && <p className="error" style={{ marginBottom: "1rem" }}>{loadError}</p>}

      <div className="dashboard-toolbar">
        <div className="status-summary" aria-label="Status summary">
          <span className="status-chip status-chip-online">Online {statusSummary.online}</span>
          <span className="status-chip status-chip-stale">Stale {statusSummary.stale}</span>
          <span className="status-chip status-chip-offline">Offline {statusSummary.offline}</span>
          <span className="status-chip status-chip-nodata">No Data {statusSummary["no-data"]}</span>
        </div>
        <div className="dashboard-filter">
          <label htmlFor="dashboard-site-filter">Quick filter</label>
          <input
            id="dashboard-site-filter"
            type="search"
            value={siteFilter}
            onChange={(e) => setSiteFilter(e.target.value)}
            placeholder="Site, PMAC, or device"
          />
        </div>
      </div>

      {filteredMeterCards.length === 0 ? (
        <div className="empty-state">
          <div className="empty-state-icon">🔎</div>
          <h3>No matching sites</h3>
          <p>Try a different filter value or clear the current search.</p>
        </div>
      ) : (
      <div className="card-grid">
        {filteredMeterCards.map((meter) => {
          const status = getMeterStatus(meter.lastSeen);
          return (
            <article className={`reading-card${status === "no-data" ? " reading-card-nodata" : ""}`} key={`${meter.pmac}-${meter.site}-${meter.device}`}>
              <div className="reading-card-header">
                <div>
                  <h3>{meter.site}</h3>
                  <div className="card-meta">
                    <span>PMAC: {meter.pmac}</span>
                    <span>{meter.device}</span>
                  </div>
                </div>
                <span className={`badge ${STATUS_CLASS[status]}`}>{STATUS_LABEL[status]}</span>
              </div>
              {meter.channels.length > 0 ? (
                <>
                  <div className="channel-list">
                    {meter.channels.map((channel) => (
                      <div className="channel-row" key={`${meter.pmac}-${channel.parameter}`}>
                        <span className="channel-name">{channel.parameter}</span>
                        <span className="metric">{channel.value}{channel.units ? ` ${channel.units}` : ""}</span>
                      </div>
                    ))}
                  </div>
                  <div className="reading-card-footer">
                    Updated {new Date(meter.lastSeen).toLocaleString()}
                  </div>
                </>
              ) : (
                <div className="channel-list">
                  <div className="no-data-msg">No historical data available</div>
                </div>
              )}
            </article>
          );
        })}
      </div>
      )}
    </section>
  );
}
