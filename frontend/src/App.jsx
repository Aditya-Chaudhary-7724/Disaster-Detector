import React, { useEffect, useState } from "react";
import {
  AlertTriangle,
  Ambulance,
  BarChart3,
  Home,
  Map as MapIcon,
  Menu,
  Radar,
  X,
} from "lucide-react";
import { NavLink, Navigate, Route, Routes } from "react-router-dom";

import Alerts from "./Alerts.jsx";
import { useAuth } from "./AuthContext.jsx";
import Dashboard from "./Dashboard.jsx";
import HomePage from "./Home.jsx";
import LiveData from "./LiveData.jsx";
import Login from "./Login.jsx";
import Map from "./Map.jsx";
import Mitigation from "./Mitigation.jsx";
import Predictor from "./Predictor.jsx";
import ProtectedRoute from "./ProtectedRoute.jsx";
import Signup from "./Signup.jsx";
import "./App.css";

const NAV_ITEMS = [
  { to: "/home", label: "Home", icon: Home },
  { to: "/dashboard", label: "Dashboard", icon: BarChart3 },
  { to: "/alerts", label: "Alerts", icon: AlertTriangle },
  { to: "/mitigation", label: "Mitigation", icon: Ambulance },
  { to: "/map", label: "Map", icon: MapIcon },
  { to: "/live-data", label: "Live Data", icon: Radar },
];

function TopNav() {
  const [menuOpen, setMenuOpen] = useState(false);
  const { user, logout } = useAuth();

  return (
    <header className="topbar">
      <div className="brand-block">
        <img src="/logo.png" alt="DisasterGuard AI shield logo" className="brand-logo" />
        <div>
          <p className="brand-name">DisasterGuard AI</p>
          <p className="brand-tagline">Smart Multi-Hazard Prediction &amp; Alert System</p>
        </div>
      </div>

      <button
        type="button"
        className="menu-toggle"
        onClick={() => setMenuOpen((open) => !open)}
        aria-label="Toggle navigation"
      >
        {menuOpen ? <X size={20} /> : <Menu size={20} />}
      </button>

      <nav className={`topnav ${menuOpen ? "open" : ""}`}>
        {NAV_ITEMS.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) => `topnav-link ${isActive ? "active" : ""}`}
              onClick={() => setMenuOpen(false)}
            >
              <Icon size={16} />
              <span>{item.label}</span>
            </NavLink>
          );
        })}
        {user ? (
          <button
            type="button"
            className="topnav-link topnav-button"
            onClick={async () => {
              await logout();
              setMenuOpen(false);
            }}
          >
            <span>Logout</span>
          </button>
        ) : (
          <>
            <NavLink to="/login" className={({ isActive }) => `topnav-link ${isActive ? "active" : ""}`} onClick={() => setMenuOpen(false)}>
              <span>Login</span>
            </NavLink>
            <NavLink to="/signup" className={({ isActive }) => `topnav-link ${isActive ? "active" : ""}`} onClick={() => setMenuOpen(false)}>
              <span>Signup</span>
            </NavLink>
          </>
        )}
      </nav>
    </header>
  );
}

function Footer() {
  return (
    <footer className="site-footer">
      © 2026 DisasterGuard AI | Built for Disaster Risk Reduction
    </footer>
  );
}

export default function App() {
  useEffect(() => {
    document.title = "DisasterGuard AI";
  }, []);

  return (
    <div className="site-shell">
      <TopNav />
      <main className="site-main">
        <Routes>
          <Route path="/" element={<Navigate to="/home" replace />} />
          <Route path="/home" element={<HomePage />} />
          <Route path="/login" element={<Login />} />
          <Route path="/signup" element={<Signup />} />
          <Route path="/dashboard" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
          <Route path="/alerts" element={<ProtectedRoute><Alerts /></ProtectedRoute>} />
          <Route path="/mitigation" element={<ProtectedRoute><Mitigation /></ProtectedRoute>} />
          <Route path="/map" element={<ProtectedRoute><Map /></ProtectedRoute>} />
          <Route path="/live-data" element={<ProtectedRoute><LiveData /></ProtectedRoute>} />
          <Route path="/predictor" element={<ProtectedRoute><Predictor /></ProtectedRoute>} />
        </Routes>
      </main>
      <Footer />
    </div>
  );
}
