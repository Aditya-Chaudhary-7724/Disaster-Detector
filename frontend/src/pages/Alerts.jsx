import React, { useEffect, useState } from "react";
import { AlertTriangle, Loader2, LocateFixed } from "lucide-react";

import { generateAlerts, getAlerts, getNearestRisks } from "../api/disasterApi";

function levelClass(level) {
  const v = String(level || "").toUpperCase();
  if (v === "HIGH") return "bg-red-500/20 text-red-300 border-red-400/30";
  if (v === "MEDIUM") return "bg-orange-500/20 text-orange-300 border-orange-400/30";
  return "bg-green-500/20 text-green-300 border-green-400/30";
}

function advisoryText(level) {
  const v = String(level || "").toUpperCase();
  if (v === "HIGH") return "Warning";
  if (v === "MEDIUM") return "Watch";
  return "Advisory";
}

export default function Alerts() {
  const [alerts, setAlerts] = useState([]);
  const [error, setError] = useState("");
  const [running, setRunning] = useState(false);
  const [loading, setLoading] = useState(true);
  const [nearest, setNearest] = useState([]);
  const [locationState, setLocationState] = useState("idle");

  async function load() {
    try {
      setLoading(true);
      const data = await getAlerts();
      setAlerts(Array.isArray(data) ? data : []);
      setError("");
    } catch {
      setError("Failed to fetch alerts");
    } finally {
      setLoading(false);
    }
  }

  async function runEngine() {
    try {
      setRunning(true);
      await generateAlerts();
      await load();
    } catch {
      setError("Failed to run alert engine");
    } finally {
      setRunning(false);
    }
  }

  useEffect(() => {
    load();
    const t = setInterval(load, 10000);
    return () => clearInterval(t);
  }, []);

  async function findNearestRisks() {
    if (!navigator.geolocation) {
      setLocationState("unsupported");
      return;
    }
    setLocationState("loading");
    navigator.geolocation.getCurrentPosition(
      async (position) => {
        try {
          const data = await getNearestRisks(position.coords.latitude, position.coords.longitude);
          setNearest(data.items || []);
          setLocationState("ready");
        } catch {
          setLocationState("error");
        }
      },
      () => setLocationState("error"),
      { enableHighAccuracy: true, timeout: 7000 }
    );
  }

  return (
    <div className="p-6 text-white space-y-5">
      <div className="flex items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <AlertTriangle size={28} /> Alerts Center
          </h1>
          <p className="text-gray-400">Color-coded AI alerts with advisory, watch, and warning levels.</p>
        </div>
        <button
          onClick={runEngine}
          disabled={running}
          className="px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 disabled:opacity-60 inline-flex items-center gap-2"
        >
          {running ? <><Loader2 size={16} className="animate-spin" /> Generating...</> : "Generate Alerts"}
        </button>
      </div>

      {error && <p className="text-red-400">{error}</p>}

      <div className="grid md:grid-cols-3 gap-4">
        <SummaryCard title="Total Alerts" value={alerts.length} />
        <SummaryCard title="Warnings" value={alerts.filter((a) => String(a.level).toUpperCase() === "HIGH").length} />
        <SummaryCard title="Watches / Advisories" value={alerts.filter((a) => String(a.level).toUpperCase() !== "HIGH").length} />
      </div>

      <div className="rounded-2xl border border-white/10 bg-white/5 p-5">
        <div className="flex items-center justify-between gap-3 mb-4">
          <div>
            <h2 className="text-xl font-semibold">Nearest Risks</h2>
            <p className="text-sm text-gray-400">Use browser geolocation to find nearby disaster records.</p>
          </div>
          <button onClick={findNearestRisks} className="px-4 py-2 rounded-xl bg-cyan-600 hover:bg-cyan-700 inline-flex items-center gap-2">
            <LocateFixed size={16} /> {locationState === "loading" ? "Locating..." : "Use My Location"}
          </button>
        </div>
        {locationState === "unsupported" && <p className="text-gray-400">Geolocation is not supported in this browser.</p>}
        {locationState === "error" && <p className="text-red-400">Unable to fetch your nearby risks.</p>}
        {nearest.length > 0 && (
          <div className="grid md:grid-cols-3 gap-3">
            {nearest.map((item, index) => (
              <div key={`${item.disaster}-${index}`} className="rounded-xl border border-white/10 bg-black/20 p-3">
                <p className="font-semibold capitalize">{item.disaster}</p>
                <p className="text-sm text-gray-300">{item.title}</p>
                <p className="text-sm text-gray-400 mt-1">{item.distance_km} km away</p>
                <p className="text-sm text-gray-300">Risk: {(Number(item.risk_score) * 100).toFixed(1)}%</p>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="grid gap-3">
        {loading ? (
          <div className="rounded-2xl border border-white/10 bg-white/5 p-6 text-gray-300">Loading alerts...</div>
        ) : alerts.length === 0 ? (
          <div className="rounded-2xl border border-white/10 bg-white/5 p-6 text-gray-400">No alerts stored yet.</div>
        ) : (
          alerts.map((alert) => (
            <div key={alert.id} className="rounded-2xl border border-white/10 bg-white/5 p-5">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <p className="text-lg font-semibold">{alert.alert_type || alert.type || "Alert"}</p>
                  <p className="text-sm text-gray-400 capitalize">{alert.disaster || "unknown"} • {alert.location || alert.region || "Unknown location"}</p>
                </div>
                <div className={`px-3 py-1.5 rounded-xl border text-sm font-semibold ${levelClass(alert.level)}`}>
                  {alert.level} {advisoryText(alert.level)}
                </div>
              </div>
              <p className="mt-3 text-gray-200">{alert.message}</p>
              <div className="mt-4 grid md:grid-cols-4 gap-3 text-sm">
                <Info label="Risk Score" value={alert.risk_score !== null && alert.risk_score !== undefined ? `${(Number(alert.risk_score) * 100).toFixed(1)}%` : "-"} />
                <Info label="Confidence" value={alert.confidence !== null && alert.confidence !== undefined ? `${(Number(alert.confidence) * 100).toFixed(1)}%` : "-"} />
                <Info label="Timestamp" value={alert.timestamp || (alert.created_at ? new Date(alert.created_at).toLocaleString() : "-")} />
                <Info label="Coordinates" value={alert.lat !== null && alert.lon !== null ? `${Number(alert.lat).toFixed(3)}, ${Number(alert.lon).toFixed(3)}` : "-"} />
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

function SummaryCard({ title, value }) {
  return (
    <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
      <p className="text-sm text-gray-400">{title}</p>
      <p className="text-2xl font-bold mt-1">{value}</p>
    </div>
  );
}

function Info({ label, value }) {
  return (
    <div className="rounded-xl border border-white/10 bg-black/20 p-3">
      <p className="text-gray-400">{label}</p>
      <p className="font-medium mt-1">{value}</p>
    </div>
  );
}
