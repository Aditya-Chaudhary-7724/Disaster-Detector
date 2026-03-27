import React, { useEffect, useMemo, useState } from "react";
import DisasterMap from "../components/DisasterMap";
import { fetchIndiaEarthquakesToDB, getEarthquakes } from "../api/disasterApi";

export default function Earthquakes() {
  const [earthquakes, setEarthquakes] = useState([]);
  const [selected, setSelected] = useState(null);
  const [syncing, setSyncing] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  // ✅ filter only today (optional)
  const todayOnly = useMemo(() => {
    const now = new Date();
    const start = new Date(now.getFullYear(), now.getMonth(), now.getDate()).getTime();
    return earthquakes.filter((q) => q.time >= start);
  }, [earthquakes]);

  async function loadEarthquakes() {
    setLoading(true);
    try {
      const data = await getEarthquakes();
      setEarthquakes(data);
      setError("");

      // ✅ auto select first row always
      if (data.length > 0 && !selected) setSelected(data[0]);
    } catch (err) {
      console.error(err);
      setError("Failed to fetch earthquakes");
    } finally {
      setLoading(false);
    }
  }

  async function syncNow() {
    try {
      setSyncing(true);
      await fetchIndiaEarthquakesToDB();
      await loadEarthquakes();
    } catch (err) {
      console.error(err);
      setError("Sync failed");
    } finally {
      setSyncing(false);
    }
  }

  useEffect(() => {
    loadEarthquakes();
    const interval = setInterval(loadEarthquakes, 10000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="p-6 text-white">
      <div className="flex justify-between items-center mb-4">
        <div>
          <h1 className="text-3xl font-bold">India Earthquakes (Live)</h1>
          <p className="text-gray-400">Data source: USGS (Stored in DB)</p>
        </div>

        <button
          onClick={syncNow}
          disabled={syncing}
          className="px-4 py-2 bg-blue-600 rounded-lg hover:bg-blue-700 transition disabled:opacity-50"
        >
          {syncing ? "Syncing..." : "Sync Now"}
        </button>
      </div>

      {error && <p className="text-red-400 mb-4">{error}</p>}
      {loading && <p className="text-yellow-300 mb-4">Loading earthquake data...</p>}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* ✅ Table */}
        <div className="bg-white/5 border border-white/10 rounded-xl p-4">
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-lg font-bold">Recent Earthquakes</h2>
            <span className="text-xs text-gray-400">
              Total Stored: {earthquakes.length} | Today: {todayOnly.length}
            </span>
          </div>

          {!loading && earthquakes.length === 0 ? (
            <p className="text-gray-400">No earthquake data stored yet. Click Sync Now.</p>
          ) : (
            <div className="overflow-auto max-h-[360px] rounded-lg">
              <table className="w-full border border-white/10">
                <thead className="bg-white/5 sticky top-0">
                  <tr>
                    <th className="text-left p-3">Place</th>
                    <th className="text-left p-3">Magnitude</th>
                    <th className="text-left p-3">Depth</th>
                    <th className="text-left p-3">Time</th>
                  </tr>
                </thead>
                <tbody>
                  {earthquakes.map((q) => (
                    <tr
                      key={q.id}
                      onClick={() => setSelected(q)}
                      className={`cursor-pointer border-t border-white/10 hover:bg-white/5 ${
                        selected?.id === q.id ? "bg-blue-500/10" : ""
                      }`}
                    >
                      <td className="p-3">{q.place}</td>
                      <td className="p-3 font-semibold">{q.magnitude}</td>
                      <td className="p-3">{q.depth} km</td>
                      <td className="p-3 text-gray-300">
                        {new Date(q.time).toLocaleString()}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* ✅ Map */}
        <DisasterMap selected={selected} title="Earthquake Location Map 📍" />
      </div>

      <p className="text-green-400 mt-4">Auto-refresh every 10 seconds ✅</p>
    </div>
  );
}
