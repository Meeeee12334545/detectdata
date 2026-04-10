import { useEffect, useMemo, useState } from "react";

import { api } from "../services/api";

function getMeterStatus(lastSeen) {
  if (!lastSeen) return "offline";
  const ts = new Date(lastSeen).getTime();
  if (Number.isNaN(ts)) return "offline";
  const minutesAgo = (Date.now() - ts) / 60000;
  if (minutesAgo < 30) return "online";
  if (minutesAgo < 120) return "stale";
  return "offline";
}

const STATUS_LABEL = { online: "Online", stale: "Stale", offline: "Offline" };
const STATUS_CLASS = { online: "badge-online", stale: "badge-stale", offline: "badge-offline" };

export default function DashboardPage() {
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get("/data/latest")
      .then((res) => setRows(res.data || []))
      .catch(() => setRows([]))
      .finally(() => setLoading(false));
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

    return Array.from(map.values())
      .sort((a, b) => new Date(b.lastSeen) - new Date(a.lastSeen))
      .map((meter) => ({
        ...meter,
        channels: Array.from(meter.channels.values()).sort((a, b) => a.parameter.localeCompare(b.parameter)),
      }));
  }, [rows]);

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
          Live readings from all connected meters &mdash; {meterCards.length} meter{meterCards.length !== 1 ? "s" : ""} reporting
        </p>
      </div>
      <div className="card-grid">
        {meterCards.map((meter) => {
          const status = getMeterStatus(meter.lastSeen);
          return (
            <article className="reading-card" key={`${meter.pmac}-${meter.site}-${meter.device}`}>
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
            </article>
          );
        })}
      </div>
    </section>
  );
}
