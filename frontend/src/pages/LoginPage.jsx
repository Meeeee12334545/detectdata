import { useEffect, useRef, useState } from "react";

import { api } from "../services/api";

export default function LoginPage({ onLogin }) {
  const [username, setUsername] = useState("admin");
  const [password, setPassword] = useState("admin123");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [countdown, setCountdown] = useState(0);
  const retryRef = useRef(null);

  useEffect(() => {
    return () => {
      if (retryRef.current) clearInterval(retryRef.current);
    };
  }, []);

  const attemptLogin = (usr, pwd) => {
    if (retryRef.current) {
      clearInterval(retryRef.current);
      retryRef.current = null;
    }
    setCountdown(0);
    setBusy(true);
    setError("");
    api
      .post("/auth/login", { username: usr, password: pwd })
      .then((res) => {
        const token = res.data?.access_token;
        if (!token) throw new Error("No token returned");
        localStorage.setItem("eds_token", token);
        onLogin(token);
      })
      .catch((err) => {
        if (err?.response?.status === 503) {
          setError("Service is starting up, please wait…");
          let secs = 5;
          setCountdown(secs);
          retryRef.current = setInterval(() => {
            secs -= 1;
            setCountdown(secs);
            if (secs <= 0) {
              clearInterval(retryRef.current);
              retryRef.current = null;
              attemptLogin(usr, pwd);
            }
          }, 1000);
        } else {
          setError("Login failed. Check your username and password.");
        }
      })
      .finally(() => {
        setBusy(false);
      });
  };

  const submit = (event) => {
    event.preventDefault();
    attemptLogin(username, password);
  };

  const errorMsg =
    countdown > 0 ? `Service is starting up, retrying in ${countdown}s…` : error;

  return (
    <div className="login-shell">
      <div className="login-card">
        <div className="login-logo">
          <div className="login-logo-icon">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <path d="M3 12h4l3-9 4 18 3-9h4" />
            </svg>
          </div>
          <div className="login-logo-text">
            <h2>EDS Platform</h2>
            <p>Environmental Data Services</p>
          </div>
        </div>

        <form onSubmit={submit} className="login-form">
          <div className="form-group">
            <label className="form-label" htmlFor="username">Username</label>
            <input
              id="username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              autoComplete="username"
              placeholder="Enter your username"
            />
          </div>
          <div className="form-group">
            <label className="form-label" htmlFor="password">Password</label>
            <input
              id="password"
              type={showPassword ? "text" : "password"}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete="current-password"
              placeholder="Enter your password"
            />
            <label className="inline-check login-inline-check" htmlFor="show-password">
              <input
                id="show-password"
                type="checkbox"
                checked={showPassword}
                onChange={(e) => setShowPassword(e.target.checked)}
              />
              Show password
            </label>
          </div>
          {errorMsg ? <p className="error-text">{errorMsg}</p> : null}
          <button className="primary login-submit" disabled={busy} type="submit">
            {busy ? "Signing in…" : "Sign In"}
          </button>
          <p className="login-help">Default local credentials are admin / admin123.</p>
        </form>
      </div>
    </div>
  );
}
