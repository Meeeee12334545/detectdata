import { useState } from "react";

import { api } from "../services/api";

export default function LoginPage({ onLogin }) {
  const [username, setUsername] = useState("admin");
  const [password, setPassword] = useState("admin123");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const submit = async (event) => {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      const res = await api.post("/auth/login", { username, password });
      const token = res.data?.access_token;
      if (!token) {
        throw new Error("No token returned");
      }
      localStorage.setItem("eds_token", token);
      onLogin(token);
    } catch {
      setError("Login failed. Check username/password.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <section className="login-panel">
      <h2>Sign In</h2>
      <p className="muted">Use your EDS platform credentials to access data.</p>
      <form onSubmit={submit} className="login-form">
        <label>
          Username
          <input value={username} onChange={(e) => setUsername(e.target.value)} autoComplete="username" />
        </label>
        <label>
          Password
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete="current-password"
          />
        </label>
        {error ? <p className="error-text">{error}</p> : null}
        <button className="primary" disabled={busy} type="submit">
          {busy ? "Signing in..." : "Sign In"}
        </button>
      </form>
    </section>
  );
}
