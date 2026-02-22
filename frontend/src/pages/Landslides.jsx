import React, { useEffect, useState } from "react";
import DisasterMap from "../components/DisasterMap";
import { fetchLandslidesToDB, getLandslides } from "../api/disasterApi";

export default function Landslides() {
  const [landslides, setLandslides] = useState([]);
  const [selected, setSelected] = useState(null);
  const [syncing, setSyncing] = useState(false);
  const [error, setError] = useState("");

  async function loadLandslides() {
    try {
      const data = await getLandslides();
      setLandslides(data);
      setError("");

      if (data.length > 0 && !selected) setSelected(data[0]);
    } catch (err) {
      console.error(err);
      setError("Failed to fetch landslides");
    }
  }

  async function syncNow() {
    try {
      setSyncing(true);
      await fetchLandslidesToDB();
      await loadLandslides();
    } catch (err) {
      console.error(err);
      setError("Sync failed");
    } finally {
      setSyncing(false);
    }
  }

  useEffect(() => {
    loadLandslides();
    const interval = setInterval(loadLandslides, 10000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="p-6 text-white">
      <div className="flex justify-between items-center mb-4">
        <div>
          <h1 className="text-3xl font-bold">India Landslide Monitoring</h1>
          <p className="text-gray-400">Mock Landslide Data (Stored in DB)</p>
        </div>
        <button
          onClick={syncNow}
          disabled={syncing}
          className="px-4 py-2 bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-50"
        >
          {syncing ? "Syncing..." : "Sync Now"}
        </button>
      </div>

      {error && <p className="text-red-400 mb-4">{error}</p>}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* ✅ Table */}
        <div className="bg-white/5 border border-white/10 rounded-xl p-4">
          <h2 className="text-lg font-bold mb-3">Recent Landslide Reports</h2>

          {landslides.length === 0 ? (
            <p className="text-gray-400">
              No landslide data stored yet. Click Sync Now.
            </p>
          ) : (
            <table className="w-full border border-white/10">
              <thead className="bg-white/5">
                <tr>
                  <th className="text-left p-3">Place</th>
                  <th className="text-left p-3">Severity</th>
                  <th className="text-left p-3">Time</th>
                </tr>
              </thead>
              <tbody>
                {landslides.map((l) => (
                  <tr
                    key={l.id}
                    onClick={() => setSelected(l)}
                    className={`cursor-pointer border-t border-white/10 hover:bg-white/5 ${
                      selected?.id === l.id ? "bg-blue-500/10" : ""
                    }`}
                  >
                    <td className="p-3">{l.place}</td>
                    <td className="p-3">{l.severity}</td>
                    <td className="p-3 text-gray-300">
                      {new Date(l.time).toLocaleString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        {/* ✅ Map */}
        <DisasterMap selected={selected} title="Landslide Location Map 📍" />
      </div>

      <p className="text-green-400 mt-4">Auto-refresh every 10 seconds ✅</p>
    </div>
  );
}
