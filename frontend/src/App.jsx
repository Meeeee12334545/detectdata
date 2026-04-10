import { useMemo, useState } from "react";
import { NavLink, Route, Routes } from "react-router-dom";

import DashboardPage from "./pages/DashboardPage";
import DataPage from "./pages/DataPage";
import LoginPage from "./pages/LoginPage";
import ManagePage from "./pages/ManagePage";

function BrandLogo() {
  return (
    <div className="brand">
      <div className="brand-icon">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
          <path d="M3 12h4l3-9 4 18 3-9h4" />
        </svg>
      </div>
      <div>
        <div className="brand-name">EDS Platform</div>
        <div className="brand-tag">Environmental Data Services</div>
      </div>
    </div>
  );
}

function navClass({ isActive }) {
  return isActive ? "nav-link active" : "nav-link";
}

export default function App() {
  const [token, setToken] = useState(() => localStorage.getItem("eds_token") || "");
  const [mobileNavOpen, setMobileNavOpen] = useState(false);
  const isAuthenticated = useMemo(() => Boolean(token), [token]);

  const logout = () => {
    localStorage.removeItem("eds_token");
    setMobileNavOpen(false);
    setToken("");
  };

  const closeMobileNav = () => setMobileNavOpen(false);

  if (!isAuthenticated) {
    return (
      <div className="app-shell">
        <header className="app-header">
          <BrandLogo />
        </header>
        <LoginPage onLogin={setToken} />
      </div>
    );
  }

  return (
    <div className="app-shell">
      <header className="app-header">
        <BrandLogo />
        <button
          className="mobile-nav-toggle"
          type="button"
          aria-label={mobileNavOpen ? "Close navigation" : "Open navigation"}
          aria-expanded={mobileNavOpen}
          onClick={() => setMobileNavOpen((prev) => !prev)}
        >
          {mobileNavOpen ? "Close" : "Menu"}
        </button>
        <nav className={mobileNavOpen ? "open" : ""}>
          <NavLink to="/" end className={navClass} onClick={closeMobileNav}>Dashboard</NavLink>
          <NavLink to="/data" className={navClass} onClick={closeMobileNav}>Data</NavLink>
          <NavLink to="/manage" className={navClass} onClick={closeMobileNav}>Manage</NavLink>
          <span className="nav-divider" />
          <button className="link-button" onClick={logout} type="button">Sign Out</button>
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
