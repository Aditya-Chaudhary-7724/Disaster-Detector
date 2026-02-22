import React, { useEffect, useState } from "react";
import DisasterMap from "../components/DisasterMap";
import { fetchFloodsToDB, getFloods } from "../api/disasterApi";

export default function Floods() {
  const [floods, setFloods] = useState([]);
  const [selected, setSelected] = useState(null);
  const [syncing, setSyncing] = useState(false);
  const [error, setError] = useState("");

  async function loadFloods() {
    try {
      const data = await getFloods();
      setFloods(data);
      setError("");

      // ✅ auto select first row
      if (data.length > 0 && !selected) setSelected(data[0]);
    } catch (err) {
      console.error(err);
      setError("Failed to fetch floods");
    }
  }

  async function syncNow() {
    try {
      setSyncing(true);
      await fetchFloodsToDB();
      await loadFloods();
    } catch (err) {
      console.error(err);
      setError("Sync failed");
    } finally {
      setSyncing(false);
    }
  }

  useEffect(() => {
    loadFloods();
    const interval = setInterval(loadFloods, 10000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="p-6 text-white">
      <div className="flex justify-between items-center mb-4">
        <div>
          <h1 className="text-3xl font-bold">India Flood Monitoring</h1>
          <p className="text-gray-400">Mock Flood Data (Stored in DB)</p>
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
          <h2 className="text-lg font-bold mb-3">Recent Flood Reports</h2>

          {floods.length === 0 ? (
            <p className="text-gray-400">
              No flood data stored yet. Click Sync Now.
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
                {floods.map((f) => (
                  <tr
                    key={f.id}
                    onClick={() => setSelected(f)}
                    className={`cursor-pointer border-t border-white/10 hover:bg-white/5 ${
                      selected?.id === f.id ? "bg-blue-500/10" : ""
                    }`}
                  >
                    <td className="p-3">{f.place}</td>
                    <td className="p-3">{f.severity}</td>
                    <td className="p-3 text-gray-300">
                      {new Date(f.time).toLocaleString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        {/* ✅ Map */}
        <DisasterMap selected={selected} title="Flood Location Map 📍" />
      </div>

      <p className="text-green-400 mt-4">Auto-refresh every 10 seconds ✅</p>
    </div>
  );
}
