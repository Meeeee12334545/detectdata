import { useEffect, useMemo, useState } from "react";

import { api } from "../services/api";

export default function ManagePage() {
  const [sites, setSites] = useState([]);
  const [selectedSiteId, setSelectedSiteId] = useState("");
  const [channels, setChannels] = useState([]);
  const [hydraulic, setHydraulic] = useState({
    enabled: false,
    pipe_shape: "circular",
    depth_channel_id: "",
    velocity_channel_id: "",
    flow_channel_id: "",
    diameter_m: "",
    width_m: "",
    height_m: "",
    output_units: "L/s",
  });
  const [status, setStatus] = useState("");

  useEffect(() => {
    api.get("/sites").then((res) => {
      setSites(res.data || []);
      if (res.data?.length) {
        setSelectedSiteId(String(res.data[0].site_id));
      }
    });
  }, []);

  useEffect(() => {
    if (!selectedSiteId) return;
    api.get(`/admin/sites/${selectedSiteId}/channels`).then((res) => {
      setChannels((res.data?.channels || []).map((c) => ({ ...c, display_name: c.display_name || "" })));
    });
    api.get(`/admin/sites/${selectedSiteId}/hydraulic-config`).then((res) => {
      const cfg = res.data || {};
      setHydraulic({
        enabled: Boolean(cfg.enabled),
        pipe_shape: cfg.pipe_shape || "circular",
        depth_channel_id: cfg.depth_channel_id ? String(cfg.depth_channel_id) : "",
        velocity_channel_id: cfg.velocity_channel_id ? String(cfg.velocity_channel_id) : "",
        flow_channel_id: cfg.flow_channel_id ? String(cfg.flow_channel_id) : "",
        diameter_m: cfg.diameter_m ?? "",
        width_m: cfg.width_m ?? "",
        height_m: cfg.height_m ?? "",
        output_units: cfg.output_units || "L/s",
      });
    });
  }, [selectedSiteId]);

  const channelOptions = useMemo(
    () => channels.map((c) => ({ label: `${c.parameter} (${c.units || "-"})`, value: String(c.channel_id) })),
    [channels]
  );

  const updateVisibility = (channelId, patch) => {
    setChannels((prev) => prev.map((c) => (c.channel_id === channelId ? { ...c, ...patch } : c)));
  };

  const saveVisibility = async () => {
    await api.post(`/admin/sites/${selectedSiteId}/channels/visibility`, {
      items: channels.map((c) => ({
        channel_id: c.channel_id,
        is_viewable: c.is_viewable,
        display_name: c.display_name || null,
      })),
    });
    setStatus("Channel visibility saved.");
  };

  const createFlowChannel = async () => {
    const res = await api.post(`/admin/sites/${selectedSiteId}/hydraulic-config/create-flow-channel`);
    const id = String(res.data?.channel_id || "");
    if (id) {
      setHydraulic((prev) => ({ ...prev, flow_channel_id: id }));
    }
    const channelsRes = await api.get(`/admin/sites/${selectedSiteId}/channels`);
    setChannels((channelsRes.data?.channels || []).map((c) => ({ ...c, display_name: c.display_name || "" })));
    setStatus("Derived flow channel is ready.");
  };

  const saveHydraulic = async () => {
    await api.post(`/admin/sites/${selectedSiteId}/hydraulic-config`, {
      enabled: hydraulic.enabled,
      pipe_shape: hydraulic.pipe_shape,
      depth_channel_id: hydraulic.depth_channel_id ? Number(hydraulic.depth_channel_id) : null,
      velocity_channel_id: hydraulic.velocity_channel_id ? Number(hydraulic.velocity_channel_id) : null,
      flow_channel_id: hydraulic.flow_channel_id ? Number(hydraulic.flow_channel_id) : null,
      diameter_m: hydraulic.diameter_m === "" ? null : Number(hydraulic.diameter_m),
      width_m: hydraulic.width_m === "" ? null : Number(hydraulic.width_m),
      height_m: hydraulic.height_m === "" ? null : Number(hydraulic.height_m),
      output_units: hydraulic.output_units,
    });
    setStatus("Hydraulic configuration saved.");
  };

  return (
    <section>
      <h2>Admin Site Configuration</h2>
      <p className="muted">Control channel visibility and derive flow channels from depth + velocity for each PMAC/site.</p>

      <div className="manage-grid">
        <article>
          <h3>Select Site</h3>
          <select value={selectedSiteId} onChange={(e) => setSelectedSiteId(e.target.value)}>
            {sites.map((s) => (
              <option key={s.site_id} value={String(s.site_id)}>
                {(s.pmac_code || "N/A")} - {s.site_name}
              </option>
            ))}
          </select>
        </article>

        <article>
          <h3>Channel Visibility</h3>
          <div className="manage-list">
            {channels.map((c) => (
              <div key={c.channel_id} className="manage-row">
                <label>
                  <input
                    type="checkbox"
                    checked={Boolean(c.is_viewable)}
                    onChange={(e) => updateVisibility(c.channel_id, { is_viewable: e.target.checked })}
                  />
                  {c.parameter} ({c.units || "-"})
                </label>
                <input
                  placeholder="Display label"
                  value={c.display_name}
                  onChange={(e) => updateVisibility(c.channel_id, { display_name: e.target.value })}
                />
              </div>
            ))}
          </div>
          <button className="primary" type="button" onClick={saveVisibility}>Save Visibility</button>
        </article>

        <article>
          <h3>Hydraulic Flow Config</h3>
          <label className="inline-check">
            <input
              type="checkbox"
              checked={hydraulic.enabled}
              onChange={(e) => setHydraulic((p) => ({ ...p, enabled: e.target.checked }))}
            />
            Enable derived flow
          </label>

          <div className="manage-row">
            <span>Pipe shape</span>
            <select
              value={hydraulic.pipe_shape}
              onChange={(e) => setHydraulic((p) => ({ ...p, pipe_shape: e.target.value }))}
            >
              <option value="circular">Circular</option>
              <option value="square">Square</option>
            </select>
          </div>

          <div className="manage-row">
            <span>Depth channel</span>
            <select
              value={hydraulic.depth_channel_id}
              onChange={(e) => setHydraulic((p) => ({ ...p, depth_channel_id: e.target.value }))}
            >
              <option value="">Select</option>
              {channelOptions.map((o) => (
                <option key={o.value} value={o.value}>{o.label}</option>
              ))}
            </select>
          </div>

          <div className="manage-row">
            <span>Velocity channel</span>
            <select
              value={hydraulic.velocity_channel_id}
              onChange={(e) => setHydraulic((p) => ({ ...p, velocity_channel_id: e.target.value }))}
            >
              <option value="">Select</option>
              {channelOptions.map((o) => (
                <option key={o.value} value={o.value}>{o.label}</option>
              ))}
            </select>
          </div>

          <div className="manage-row">
            <span>Flow output channel</span>
            <select
              value={hydraulic.flow_channel_id}
              onChange={(e) => setHydraulic((p) => ({ ...p, flow_channel_id: e.target.value }))}
            >
              <option value="">Select</option>
              {channelOptions.map((o) => (
                <option key={o.value} value={o.value}>{o.label}</option>
              ))}
            </select>
          </div>

          <div className="manage-row">
            <span>Diameter (m)</span>
            <input
              value={hydraulic.diameter_m}
              onChange={(e) => setHydraulic((p) => ({ ...p, diameter_m: e.target.value }))}
              placeholder="for circular"
            />
          </div>
          <div className="manage-row">
            <span>Width (m)</span>
            <input
              value={hydraulic.width_m}
              onChange={(e) => setHydraulic((p) => ({ ...p, width_m: e.target.value }))}
              placeholder="for square"
            />
          </div>
          <div className="manage-row">
            <span>Height (m)</span>
            <input
              value={hydraulic.height_m}
              onChange={(e) => setHydraulic((p) => ({ ...p, height_m: e.target.value }))}
              placeholder="optional max depth"
            />
          </div>

          <div className="manage-actions">
            <button className="primary" type="button" onClick={createFlowChannel}>Create Flow Channel</button>
            <button className="primary" type="button" onClick={saveHydraulic}>Save Hydraulic Config</button>
          </div>
        </article>
      </div>

      {status ? <p className="muted">{status}</p> : null}
    </section>
  );
}
