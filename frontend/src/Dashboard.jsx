import React, { useEffect, useMemo, useState } from "react";
import { Activity, ExternalLink, Mountain, Waves } from "lucide-react";
import { useNavigate } from "react-router-dom";

import HazardZoneMap from "./HazardZoneMap.jsx";
import { getDashboardData } from "./api/disasterApi.js";

const DISASTER_OPTIONS = [
  { value: "flood", label: "Flood", icon: Waves, subtitle: "Rainfall, river level, and soil moisture zonation" },
  { value: "earthquake", label: "Earthquake", icon: Activity, subtitle: "Magnitude clustering and seismic concentration zonation" },
  { value: "landslide", label: "Landslide", icon: Mountain, subtitle: "Slope instability and rainfall-sensitive hill zonation" },
];

function metricLabel(disaster) {
  if (disaster === "flood") return "Rainfall";
  if (disaster === "earthquake") return "Magnitude";
  return "Risk";
}

function metricValue(disaster, item) {
  if (disaster === "flood") return `${Number(item.rainfall).toFixed(0)} mm`;
  if (disaster === "earthquake") return Number(item.magnitude).toFixed(1);
  return Number(item.risk_score).toFixed(2);
}

function buildMapLink(disaster, item) {
  const params = new URLSearchParams({
    disaster,
    lat: String(item.lat),
    lon: String(item.lon),
    label: item.zone_name,
    region: item.region,
    value: `${metricLabel(disaster)}: ${metricValue(disaster, item)}`,
  });
  return `/map?${params.toString()}`;
}

function PredictionSummary({ disaster, prediction, onOpenMap }) {
  if (!prediction) {
    return (
      <div className="premium-card">
        <h3>Prediction Result</h3>
        <p className="body-copy">No prediction data available.</p>
      </div>
    );
  }

  return (
    <div className="premium-card feature-card">
      <div className="card-topline">
        <span className="pill-label">Prediction Result</span>
        <span className={`risk-badge ${String(prediction.risk_level).toLowerCase()}`}>{prediction.risk_level}</span>
      </div>
      <h3>{prediction.zone_name}</h3>
      <p className="body-copy">{prediction.region} is currently the highest priority zone for the selected disaster.</p>
      <div className="metric-stack">
        <p>Risk Score: {Number(prediction.risk_score).toFixed(2)}</p>
        <p>{metricLabel(disaster)}: {metricValue(disaster, prediction)}</p>
        <p>Timestamp: {new Date(prediction.timestamp).toLocaleString()}</p>
      </div>
      <button type="button" className="secondary-button" onClick={onOpenMap}>
        <ExternalLink size={15} />
        Open in Map
      </button>
    </div>
  );
}

function DataCard({ disaster, item, active, onSelect, onOpenMap }) {
  return (
    <div className={`data-card ${active ? "active" : ""}`}>
      <button type="button" className="card-action" onClick={onSelect}>
        <div className="card-topline">
          <span className="pill-label">{item.region}</span>
          <span className={`risk-badge ${String(item.risk_level).toLowerCase()}`}>{item.risk_level}</span>
        </div>
        <p className="list-title">{item.zone_name}</p>
        <div className="metric-stack compact">
          <p>{metricLabel(disaster)}: {metricValue(disaster, item)}</p>
          <p>Risk Score: {Number(item.risk_score).toFixed(2)}</p>
          <p>Updated: {new Date(item.timestamp).toLocaleString()}</p>
        </div>
      </button>
      <button type="button" className="secondary-button compact-button" onClick={onOpenMap}>
        <ExternalLink size={15} />
        Full Map
      </button>
    </div>
  );
}

function MetricBar({ label, value }) {
  return (
    <div className="metric-bar-card">
      <span>{label}</span>
      <strong>{(Number(value) * 100).toFixed(1)}%</strong>
    </div>
  );
}

function LoadingPanel() {
  return (
    <div className="dashboard-shell">
      <div className="dashboard-left">
        <div className="premium-card skeleton-card" />
        <div className="premium-card skeleton-card tall" />
        <div className="premium-card skeleton-card" />
      </div>
      <div className="dashboard-right">
        <div className="premium-card skeleton-card map" />
      </div>
    </div>
  );
}

export default function Dashboard() {
  const [selectedDisaster, setSelectedDisaster] = useState("flood");
  const [dashboard, setDashboard] = useState(null);
  const [selectedZone, setSelectedZone] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const navigate = useNavigate();

  const selectedOption = DISASTER_OPTIONS.find((option) => option.value === selectedDisaster) || DISASTER_OPTIONS[0];
  const SelectedIcon = selectedOption.icon;

  useEffect(() => {
    async function loadDashboard() {
      try {
        setLoading(true);
        setError("");
        const response = await getDashboardData(selectedDisaster);
        setDashboard(response);
        setSelectedZone(response?.prediction || null);
      } catch (err) {
        setError(err.message || "Unable to load dashboard data.");
      } finally {
        setLoading(false);
      }
    }

    loadDashboard();
  }, [selectedDisaster]);

  const focusItem = useMemo(() => {
    if (!selectedZone) {
      return null;
    }
    return {
      lat: selectedZone.lat,
      lon: selectedZone.lon,
      label: selectedZone.zone_name,
      region: selectedZone.region,
      disaster: selectedDisaster,
      value: `${metricLabel(selectedDisaster)}: ${metricValue(selectedDisaster, selectedZone)}`,
    };
  }, [selectedDisaster, selectedZone]);

  if (loading) {
    return (
      <section className="page">
        <div className="page-header">
          <div>
            <p className="eyebrow">Hazard Zonation Dashboard</p>
            <h2>Dashboard</h2>
            <p className="page-copy">Loading the latest zonation view for the selected disaster.</p>
          </div>
        </div>
        <LoadingPanel />
      </section>
    );
  }

  return (
    <section className="page">
      <div className="page-header">
        <div>
          <p className="eyebrow">Hazard Zonation Dashboard</p>
          <h2>Dashboard</h2>
          <p className="page-copy">
            Switch disaster views, inspect live API data, and interact with the hazard map from a single responsive screen.
          </p>
        </div>
      </div>

      {error ? <div className="premium-card error-text">{error}</div> : null}

      <div className="dashboard-shell">
        <div className="dashboard-left">
          <div className="premium-card selector-card">
            <div className="selector-header">
              <div className="icon-chip">
                <SelectedIcon size={18} />
              </div>
              <div>
                <p className="pill-label">Disaster Selector</p>
                <h3>{selectedOption.label}</h3>
                <p className="body-copy">{selectedOption.subtitle}</p>
              </div>
            </div>

            <label className="field">
              <span>Select Disaster</span>
              <select value={selectedDisaster} onChange={(event) => setSelectedDisaster(event.target.value)}>
                {DISASTER_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </label>

            <div className="validation-strip">
              <MetricBar label="Accuracy" value={dashboard?.validation?.accuracy || 0} />
              <MetricBar label="Precision" value={dashboard?.validation?.precision || 0} />
              <MetricBar label="Recall" value={dashboard?.validation?.recall || 0} />
            </div>
          </div>

          <PredictionSummary
            disaster={selectedDisaster}
            prediction={dashboard?.prediction}
            onOpenMap={() => navigate(buildMapLink(selectedDisaster, dashboard.prediction))}
          />

          <div className="premium-card">
            <div className="card-topline">
              <span className="pill-label">Latest API Data</span>
              <span className="body-copy">{(dashboard?.latest_data || []).length} zones</span>
            </div>
            <div className="latest-data-list">
              {(dashboard?.latest_data || []).map((item) => (
                <DataCard
                  key={item.id}
                  disaster={selectedDisaster}
                  item={item}
                  active={selectedZone?.id === item.id}
                  onSelect={() => setSelectedZone(item)}
                  onOpenMap={() => navigate(buildMapLink(selectedDisaster, item))}
                />
              ))}
            </div>
          </div>
        </div>

        <div className="dashboard-right">
          <div className="premium-card map-panel">
            <div className="card-topline">
              <span className="pill-label">Map Visualization</span>
              <span className="body-copy">Zone-based risk shading</span>
            </div>
            <HazardZoneMap disaster={selectedDisaster} zones={dashboard?.zones || []} focusItem={focusItem} className="leaflet-map dashboard-map" />
            <div className="legend-row">
              <span className="legend-item"><i className="legend-dot high" /> High Risk</span>
              <span className="legend-item"><i className="legend-dot medium" /> Medium Risk</span>
              <span className="legend-item"><i className="legend-dot low" /> Low Risk</span>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
