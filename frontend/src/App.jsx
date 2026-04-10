import { useMemo, useState } from "react";
import { Link, Route, Routes } from "react-router-dom";

import DashboardPage from "./pages/DashboardPage";
import DataPage from "./pages/DataPage";
import LoginPage from "./pages/LoginPage";
import ManagePage from "./pages/ManagePage";

export default function App() {
  const [token, setToken] = useState(() => localStorage.getItem("eds_token") || "");
  const isAuthenticated = useMemo(() => Boolean(token), [token]);

  const logout = () => {
    localStorage.removeItem("eds_token");
    setToken("");
  };

  if (!isAuthenticated) {
    return (
      <div className="app-shell">
        <header className="app-header">
          <div>
            <p className="eyebrow">Environmental Data Services</p>
            <h1>EDS Data Platform</h1>
          </div>
        </header>
        <main className="app-main">
          <LoginPage onLogin={setToken} />
        </main>
      </div>
    );
  }

  return (
    <div className="app-shell">
      <header className="app-header">
        <div>
          <p className="eyebrow">Environmental Data Services</p>
          <h1>EDS Data Platform</h1>
        </div>
        <nav>
          <Link to="/">Dashboard</Link>
          <Link to="/data">Data</Link>
          <Link to="/manage">Manage</Link>
          <button className="link-button" onClick={logout} type="button">Logout</button>
        </nav>
      </header>

      <main className="app-main">
        <Routes>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/data" element={<DataPage />} />
          <Route path="/manage" element={<ManagePage />} />
        </Routes>
      </main>
    </div>
  );
}
