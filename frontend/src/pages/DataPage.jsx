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

export default function DataPage() {
  const [inventory, setInventory] = useState([]); // [{site, pmac, device, channels:[{parameter,channel_id,units}]}]
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

  // Load inventory from latest readings
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
    const found = inventory.find(
      (s) => `${s.pmac}|${s.site}` === selectedSite
    );
    return found ? found.channels : [];
  }, [inventory, selectedSite]);

  // Reset channel when site changes
  useEffect(() => {
    setSelectedChannel("");
    setChartData([]);
  }, [selectedSite]);

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
    const base = import.meta.env.VITE_API_BASE || "/api/v1";
    const token = localStorage.getItem("eds_token");
    // Build a link with auth header workaround: open via fetch/blob
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

  return (
    <section>
      <h2>Historical Data</h2>

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

        <button onClick={loadData} disabled={!selectedChannel || loading}>
          {loading ? "Loading…" : "Load"}
        </button>

        <button onClick={exportCsv} disabled={!selectedChannel || chartData.length === 0} className="btn-secondary">
          Download CSV
        </button>
      </div>

      {error && <p className="error">{error}</p>}

      {chartData.length > 0 ? (
        <div className="chart-panel">
          <p className="muted">{chartData.length} data points</p>
          <ResponsiveContainer width="100%" height={360}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />
              <XAxis dataKey="t" tick={{ fontSize: 11 }} interval="preserveStartEnd" />
              <YAxis
                tick={{ fontSize: 11 }}
                label={{ value: units, angle: -90, position: "insideLeft", offset: 10 }}
              />
              <Tooltip
                formatter={(val) => [`${val} ${units}`, "Value"]}
              />
              <Line
                type="monotone"
                dataKey="v"
                stroke="#006d77"
                strokeWidth={2}
                dot={false}
                isAnimationActive={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      ) : (
        !loading && (
          <p className="muted">
            {selectedChannel
              ? "Click Load to fetch data for the selected date range."
              : "Select a site and channel above to view historical readings."}
          </p>
        )
      )}
    </section>
  );
}

