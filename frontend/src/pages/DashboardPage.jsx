import { useEffect, useMemo, useState } from "react";

import { api } from "../services/api";

export default function DashboardPage() {
  const [rows, setRows] = useState([]);

  useEffect(() => {
    api.get("/data/latest")
      .then((res) => setRows(res.data || []))
      .catch(() => setRows([]));
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

  return (
    <section>
      <h2>Latest Readings</h2>
      <p className="muted">Each box is one meter (PMAC + site) with latest values for all available channels.</p>
      <div className="card-grid">
        {meterCards.map((meter) => (
          <article className="reading-card" key={`${meter.pmac}-${meter.site}-${meter.device}`}>
            <h3>{meter.site}</h3>
            <p className="muted">PMAC: {meter.pmac}</p>
            <p>{meter.device}</p>
            <div className="channel-list">
              {meter.channels.map((channel) => (
                <div className="channel-row" key={`${meter.pmac}-${channel.parameter}`}>
                  <span className="channel-name">{channel.parameter}</span>
                  <span className="metric">{channel.value} {channel.units}</span>
                </div>
              ))}
            </div>
            <p className="muted">Updated: {new Date(meter.lastSeen).toLocaleString()}</p>
          </article>
        ))}
      </div>
    </section>
  );
}
