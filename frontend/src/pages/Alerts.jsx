import React, { useEffect, useState } from "react";

import { generateAlerts, getAlerts } from "../api/disasterApi";

function levelClass(level) {
  const v = String(level || "").toUpperCase();
  if (v === "HIGH") return "bg-red-500/20 text-red-300 border-red-400/30";
  if (v === "MEDIUM") return "bg-orange-500/20 text-orange-300 border-orange-400/30";
  return "bg-green-500/20 text-green-300 border-green-400/30";
}

export default function Alerts() {
  const [alerts, setAlerts] = useState([]);
  const [error, setError] = useState("");
  const [running, setRunning] = useState(false);

  async function load() {
    try {
      const data = await getAlerts();
      setAlerts(data);
      setError("");
    } catch {
      setError("Failed to fetch alerts");
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
    const t = setInterval(load, 5000);
    return () => clearInterval(t);
  }, []);

  return (
    <div className="p-6 text-white">
      <div className="flex items-center justify-between mb-3">
        <div>
          <h1 className="text-3xl font-bold mb-2">Alerts</h1>
          <p className="text-gray-400">AI alerts from 6-hour prediction engine</p>
        </div>
        <button
          onClick={runEngine}
          disabled={running}
          className="px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 disabled:opacity-60"
        >
          {running ? "Running..." : "Generate Alerts"}
        </button>
      </div>

      {error && <p className="text-red-400 mb-4">{error}</p>}

      <div className="bg-white/5 border border-white/10 rounded-2xl overflow-hidden">
        <table className="w-full">
          <thead className="bg-white/5">
            <tr>
              <th className="text-left p-3">Alert Type</th>
              <th className="text-left p-3">Disaster</th>
              <th className="text-left p-3">Risk</th>
              <th className="text-left p-3">Confidence</th>
              <th className="text-left p-3">Message</th>
              <th className="text-left p-3">Time</th>
            </tr>
          </thead>
          <tbody>
            {alerts.length === 0 ? (
              <tr>
                <td className="p-3 text-gray-400" colSpan={6}>
                  No alerts yet.
                </td>
              </tr>
            ) : (
              alerts.map((a) => (
                <tr key={a.id} className="border-t border-white/10 hover:bg-white/5">
                  <td className="p-3">{a.alert_type || a.type}</td>
                  <td className="p-3 capitalize">{a.disaster || "-"}</td>
                  <td className="p-3">
                    <span className={`px-2 py-1 rounded-md border text-xs font-semibold ${levelClass(a.level)}`}>
                      {a.level}
                    </span>
                  </td>
                  <td className="p-3">{a.confidence ? Number(a.confidence).toFixed(2) : "-"}</td>
                  <td className="p-3">{a.message}</td>
                  <td className="p-3">{new Date(a.created_at).toLocaleString()}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      <p className="text-green-400 mt-4">Auto refresh every 5 seconds</p>
    </div>
  );
}
