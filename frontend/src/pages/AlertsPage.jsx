import React, { useState } from "react";
import { Clock } from "lucide-react";
import { mockAlerts } from "../data/mockEarthquakeData";

export default function AlertsPage() {
  const [alerts, setAlerts] = useState(mockAlerts);
  const [filterSeverity, setFilterSeverity] = useState("all");

  const filteredAlerts = alerts.filter((alert) => {
    if (filterSeverity !== "all" && alert.severity !== filterSeverity) return false;
    return true;
  });

  const markResolved = (id) => {
    setAlerts((prev) => prev.map((a) => (a.id === id ? { ...a, resolved: true } : a)));
  };

  const getSeverityColor = (severity) => {
    const colors = {
      critical: "bg-red-500/20 text-red-400 border-red-500/30",
      high: "bg-orange-500/20 text-orange-400 border-orange-500/30",
      medium: "bg-yellow-500/20 text-yellow-400 border-yellow-500/30",
      low: "bg-green-500/20 text-green-400 border-green-500/30",
    };
    return colors[severity] || colors.low;
  };

  return (
    <div>
      <h1 className="text-3xl font-bold text-white mb-8">Alert Management</h1>

      <div className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl p-6 mb-8">
        <label className="block text-gray-300 mb-2">Severity Filter</label>
        <select
          value={filterSeverity}
          onChange={(e) => setFilterSeverity(e.target.value)}
          className="px-4 py-2 bg-white/5 border border-white/20 rounded-lg text-white focus:outline-none focus:border-blue-400"
        >
          <option value="all">All Severities</option>
          <option value="critical">Critical</option>
          <option value="high">High</option>
          <option value="medium">Medium</option>
          <option value="low">Low</option>
        </select>
      </div>

      <div className="space-y-4">
        {filteredAlerts.map((alert) => (
          <div
            key={alert.id}
            className={`bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl p-6 ${
              alert.resolved ? "opacity-60" : ""
            }`}
          >
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
              <div className="flex-1">
                <div className="flex items-center gap-3 mb-2">
                  <span className={`px-3 py-1 rounded-full text-xs font-semibold border ${getSeverityColor(alert.severity)}`}>
                    {alert.severity.toUpperCase()}
                  </span>

                  {alert.resolved && (
                    <span className="px-3 py-1 bg-gray-500/20 text-gray-400 rounded-full text-xs font-semibold border border-gray-500/30">
                      RESOLVED
                    </span>
                  )}
                </div>

                <h3 className="text-white font-bold text-lg mb-1">{alert.location}</h3>
                <p className="text-gray-300 mb-2">{alert.message}</p>

                <div className="flex items-center gap-2 text-gray-400 text-sm">
                  <Clock className="w-4 h-4" />
                  <span>{alert.time}</span>
                </div>
              </div>

              {!alert.resolved && (
                <button
                  onClick={() => markResolved(alert.id)}
                  className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
                >
                  Mark as Resolved
                </button>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
