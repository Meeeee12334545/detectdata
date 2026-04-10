import { useEffect, useMemo, useState } from "react";
import {
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  CartesianGrid,
} from "recharts";

import { api } from "../services/api";

function toLocalDatetimeValue(date) {
  const d = new Date(date);
  d.setMinutes(d.getMinutes() - d.getTimezoneOffset());
  return d.toISOString().slice(0, 16);
}

function round2(n) {
  return Math.round(n * 100) / 100;
}

export default function DataPage() {
  const [inventory, setInventory] = useState([]);
  const [selectedSite, setSelectedSite] = useState("");
  const [selectedChannel, setSelectedChannel] = useState("");
  const [start, setStart] = useState(() => {
    const d = new Date();
    d.setDate(d.getDate() - 7);
    return toLocalDatetimeValue(d);
  });
  const [end, setEnd] = useState(() => toLocalDatetimeValue(new Date()));
  const [chartData, setChartData] = useState([]);
  const [units, setUnits] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    api.get("/data/latest").then((res) => {
      const rows = res.data || [];
      const siteMap = new Map();
      for (const row of rows) {
        const key = `${row.pmac || "na"}|${row.site}`;
        if (!siteMap.has(key)) {
          siteMap.set(key, { site: row.site, pmac: row.pmac, channels: new Map() });
        }
        const entry = siteMap.get(key);
        if (!entry.channels.has(row.channel_id)) {
          entry.channels.set(row.channel_id, {
            channel_id: row.channel_id,
            parameter: row.parameter,
            units: row.units || "",
          });
        }
      }
      const inv = Array.from(siteMap.values()).map((s) => ({
        ...s,
        channels: Array.from(s.channels.values()).sort((a, b) =>
          a.parameter.localeCompare(b.parameter)
        ),
      }));
      inv.sort((a, b) => (a.site || "").localeCompare(b.site || ""));
      setInventory(inv);
    });
  }, []);

  const siteChannels = useMemo(() => {
    const found = inventory.find((s) => `${s.pmac}|${s.site}` === selectedSite);
    return found ? found.channels : [];
  }, [inventory, selectedSite]);

  useEffect(() => {
    setSelectedChannel("");
    setChartData([]);
  }, [selectedSite]);

  const chartStats = useMemo(() => {
    if (chartData.length === 0) return null;
    const values = chartData.map((d) => d.v).filter((v) => v != null);
    if (values.length === 0) return null;
    const min = round2(Math.min(...values));
    const max = round2(Math.max(...values));
    const avg = round2(values.reduce((a, b) => a + b, 0) / values.length);
    return { min, max, avg };
  }, [chartData]);

  async function loadData() {
    if (!selectedChannel) return;
    setLoading(true);
    setError(null);
    try {
      const res = await api.get("/data/timeseries", {
        params: {
          channel_id: selectedChannel,
          start: new Date(start).toISOString(),
          end: new Date(end).toISOString(),
        },
        timeout: 30000,
      });
      const ch = siteChannels.find((c) => String(c.channel_id) === String(selectedChannel));
      setUnits(ch ? ch.units : "");
      setChartData(
        (res.data || []).map((d) => ({
          t: new Date(d.timestamp).toLocaleString(),
          v: d.value,
        }))
      );
    } catch {
      setError("Failed to load data. Check the date range and try again.");
    } finally {
      setLoading(false);
    }
  }

  function exportCsv() {
    if (!selectedChannel) return;
    const params = new URLSearchParams({
      channel_id: selectedChannel,
      start: new Date(start).toISOString(),
      end: new Date(end).toISOString(),
    });
    api
      .get(`/data/export.csv?${params.toString()}`, {
        responseType: "blob",
        timeout: 30000,
      })
      .then((res) => {
        const url = URL.createObjectURL(res.data);
        const a = document.createElement("a");
        a.href = url;
        a.download = `channel_${selectedChannel}.csv`;
        a.click();
        URL.revokeObjectURL(url);
      });
  }

  const selectedChannelObj = siteChannels.find((c) => String(c.channel_id) === String(selectedChannel));

  return (
    <section>
      <div className="page-header">
        <h2 className="page-title">Historical Data</h2>
        <p className="page-desc">Select a site and channel to visualise time-series readings</p>
      </div>

      <div className="data-controls-card">
        <div className="data-controls">
          <label>
            Site
            <select value={selectedSite} onChange={(e) => setSelectedSite(e.target.value)}>
              <option value="">— select site —</option>
              {inventory.map((s) => (
                <option key={`${s.pmac}|${s.site}`} value={`${s.pmac}|${s.site}`}>
                  {s.pmac ? `${s.pmac} – ` : ""}{s.site}
                </option>
              ))}
            </select>
          </label>

          <label>
            Channel
            <select
              value={selectedChannel}
              onChange={(e) => setSelectedChannel(e.target.value)}
              disabled={!selectedSite}
            >
              <option value="">— select channel —</option>
              {siteChannels.map((c) => (
                <option key={c.channel_id} value={c.channel_id}>
                  {c.parameter}{c.units ? ` (${c.units})` : ""}
                </option>
              ))}
            </select>
          </label>

          <label>
            From
            <input type="datetime-local" value={start} onChange={(e) => setStart(e.target.value)} />
          </label>
          <label>
            To
            <input type="datetime-local" value={end} onChange={(e) => setEnd(e.target.value)} />
          </label>

          <button className="btn btn-primary" onClick={loadData} disabled={!selectedChannel || loading}>
            {loading ? "Loading…" : "Load Data"}
          </button>

          <button
            className="btn btn-secondary"
            onClick={exportCsv}
            disabled={!selectedChannel || chartData.length === 0}
          >
            Export CSV
          </button>
        </div>
      </div>

      {error && <p className="error" style={{ marginBottom: "1rem" }}>{error}</p>}

      {loading && (
        <div className="loading-state">
          <div className="spinner" />
          <span>Fetching data…</span>
        </div>
      )}

      {!loading && chartData.length > 0 && (
        <div className="chart-container">
          <div className="chart-header">
            <div>
              <div className="chart-title">
                {selectedChannelObj ? selectedChannelObj.parameter : "Reading"}
                {units ? ` (${units})` : ""}
              </div>
              <div className="chart-subtitle">{chartData.length.toLocaleString()} data points</div>
            </div>
            {chartStats && (
              <div className="chart-stats">
                <div className="chart-stat">
                  <span className="chart-stat-label">Min</span>
                  <span className="chart-stat-value">{chartStats.min} {units}</span>
                </div>
                <div className="chart-stat">
                  <span className="chart-stat-label">Avg</span>
                  <span className="chart-stat-value">{chartStats.avg} {units}</span>
                </div>
                <div className="chart-stat">
                  <span className="chart-stat-label">Max</span>
                  <span className="chart-stat-value">{chartStats.max} {units}</span>
                </div>
              </div>
            )}
          </div>
          <ResponsiveContainer width="100%" height={360}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis dataKey="t" tick={{ fontSize: 11, fill: "#64748b" }} interval="preserveStartEnd" />
              <YAxis
                tick={{ fontSize: 11, fill: "#64748b" }}
                label={{ value: units, angle: -90, position: "insideLeft", offset: 10, style: { fill: "#64748b", fontSize: 11 } }}
              />
              <Tooltip
                contentStyle={{ border: "1px solid #e2e8f0", borderRadius: "0.5rem", fontSize: "0.8125rem" }}
                formatter={(val) => [`${val} ${units}`, "Value"]}
              />
              <Line
                type="monotone"
                dataKey="v"
                stroke="#2563eb"
                strokeWidth={2}
                dot={false}
                isAnimationActive={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      {!loading && chartData.length === 0 && (
        <div className="empty-state">
          <div className="empty-state-icon">📈</div>
          <h3>{selectedChannel ? "No data in range" : "Select a channel"}</h3>
          <p>
            {selectedChannel
              ? "Click Load Data to fetch readings for the selected date range."
              : "Choose a site and channel above to view historical readings."}
          </p>
        </div>
      )}
    </section>
  );
}
