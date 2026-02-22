import React, { useEffect, useState } from "react";
import { getAlerts } from "../api/disasterApi";

export default function Alerts() {
  const [alerts, setAlerts] = useState([]);
  const [error, setError] = useState("");

  async function load() {
    try {
      const data = await getAlerts();
      setAlerts(data);
      setError("");
    } catch (e) {
      setError("Failed to fetch alerts");
    }
  }

  useEffect(() => {
    load();
    const t = setInterval(load, 5000);
    return () => clearInterval(t);
  }, []);

  return (
    <div className="p-6 text-white">
      <h1 className="text-3xl font-bold mb-2">Alerts</h1>
      <p className="text-gray-400 mb-4">Auto alerts created by Prediction Engine</p>

      {error && <p className="text-red-400">{error}</p>}

      <div className="bg-white/5 border border-white/10 rounded-2xl overflow-hidden">
        <table className="w-full">
          <thead className="bg-white/5">
            <tr>
              <th className="text-left p-3">Type</th>
              <th className="text-left p-3">Level</th>
              <th className="text-left p-3">Message</th>
              <th className="text-left p-3">Time</th>
            </tr>
          </thead>
          <tbody>
            {alerts.length === 0 ? (
              <tr>
                <td className="p-3 text-gray-400" colSpan={4}>
                  No alerts yet. Go to Predictor and create one ✅
                </td>
              </tr>
            ) : (
              alerts.map((a) => (
                <tr key={a.id} className="border-t border-white/10 hover:bg-white/5">
                  <td className="p-3">{a.type}</td>
                  <td className="p-3">{a.level}</td>
                  <td className="p-3">{a.message}</td>
                  <td className="p-3">{new Date(a.created_at).toLocaleString()}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      <p className="text-green-400 mt-4">Auto refresh every 5 seconds ✅</p>
    </div>
  );
}
