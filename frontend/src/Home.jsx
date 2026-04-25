import React from "react";
import { AlertTriangle, ArrowRight, BarChart3, Map, ShieldCheck } from "lucide-react";
import { Link } from "react-router-dom";

const FEATURES = [
  {
    title: "Multi-Hazard Dashboard",
    text: "Switch between flood, earthquake, and landslide views in one clean zonation dashboard.",
    icon: BarChart3,
    to: "/dashboard",
  },
  {
    title: "Risk Alerts",
    text: "Track prediction-backed alerts and model validation metrics in a simple readable layout.",
    icon: AlertTriangle,
    to: "/alerts",
  },
  {
    title: "Interactive Map",
    text: "Open live records on the map and inspect the selected disaster location instantly.",
    icon: Map,
    to: "/map",
  },
];

export default function HomePage() {
  return (
    <section className="page">
      <div className="hero-card">
        <div className="hero-copy">
          <p className="eyebrow">Disaster Risk Reduction Platform</p>
          <h1 className="hero-title">DisasterGuard AI</h1>
          <p className="hero-tagline">Smart Multi-Hazard Prediction &amp; Alert System</p>
          <p className="page-copy">
            A responsive disaster intelligence web app for zonation mapping, live data inspection, risk prediction,
            and emergency-aware mitigation guidance.
          </p>

          <div className="hero-actions">
            <Link to="/dashboard" className="primary-button">
              Open Dashboard
            </Link>
            <Link to="/live-data" className="secondary-button">
              Explore Live Data
            </Link>
          </div>
        </div>

        <div className="hero-panel">
          <div className="hero-badge">
            <ShieldCheck size={18} />
            <span>Deployment Ready</span>
          </div>
          <div className="hero-metrics">
            <div className="metric-bar-card">
              <span>Modules</span>
              <strong>Dashboard, Alerts, Map</strong>
            </div>
            <div className="metric-bar-card">
              <span>Coverage</span>
              <strong>Flood, Earthquake, Landslide</strong>
            </div>
            <div className="metric-bar-card">
              <span>Focus</span>
              <strong>Clean, explainable, responsive</strong>
            </div>
          </div>
        </div>
      </div>

      <div className="grid three-column">
        {FEATURES.map((feature) => {
          const Icon = feature.icon;
          return (
            <Link className="premium-card feature-link-card" key={feature.title} to={feature.to}>
              <div className="icon-chip">
                <Icon size={18} />
              </div>
              <h3>{feature.title}</h3>
              <p className="body-copy">{feature.text}</p>
              <span className="inline-link">
                Open <ArrowRight size={15} />
              </span>
            </Link>
          );
        })}
      </div>
    </section>
  );
}
