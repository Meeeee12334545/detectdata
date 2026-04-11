import { useEffect, useRef, useState } from "react";

import { api } from "../services/api";

// Maximum number of automatic retry attempts after the first login request.
const MAX_AUTO_RETRIES = 8;

export default function LoginPage({ onLogin }) {
  const [username, setUsername] = useState("admin");
  const [password, setPassword] = useState("admin123");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [countdown, setCountdown] = useState(0);
  const retryRef = useRef(null);
  const retryCountRef = useRef(0);

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
        if (!token) {
          // Unexpected server response — treat as a definitive failure so we
          // don't loop forever on a malformed reply.
          setBusy(false);
          setError("Login failed. Unexpected server response.");
          return;
        }
        localStorage.setItem("eds_token", token);
        onLogin(token);
      })
      .catch((err) => {
        // Retry automatically on 503 (service starting) or any network/timeout
        // error where there is no HTTP response at all (e.g. cold-start spin-up).
        const isTransient = err?.response?.status === 503 || !err?.response;
        if (isTransient && retryCountRef.current < MAX_AUTO_RETRIES) {
          retryCountRef.current += 1;
          setError("Service is starting up, please wait…");
          let secs = 5;
          setCountdown(secs);
          // Keep busy=true so the button stays disabled during the countdown
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
          // Definitive error (401 wrong credentials, max retries reached, etc.)
          setBusy(false);
          if (err?.response?.status === 401) {
            setError("Invalid username or password.");
          } else if (isTransient) {
            setError(
              "Service is unavailable after several attempts. " +
              "Please try again later or contact support if the problem persists."
            );
          } else {
            setError("Login failed. Please try again.");
          }
        }
      });
  };

  const submit = (event) => {
    event.preventDefault();
    retryCountRef.current = 0;
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
            {countdown > 0 ? `Retrying in ${countdown}s…` : busy ? "Signing in…" : "Sign In"}
          </button>
          <p className="login-help">Default local credentials are admin / admin123.</p>
        </form>
      </div>
    </div>
  );
}
