import React, { useEffect, useMemo, useState } from "react";
import { AlertTriangle, Loader2, MapPinned } from "lucide-react";
import { MapContainer, Marker, Popup, TileLayer, useMap } from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";

import { runSpatialAutoPrediction } from "../api/autoPredictorApi";

import markerIcon2x from "leaflet/dist/images/marker-icon-2x.png";
import markerIcon from "leaflet/dist/images/marker-icon.png";
import markerShadow from "leaflet/dist/images/marker-shadow.png";

delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: markerIcon2x,
  iconUrl: markerIcon,
  shadowUrl: markerShadow,
});

const INDIA_CENTER = [22.9734, 78.6569];

function HeatLayer({ points }) {
  const map = useMap();

  useEffect(() => {
    if (!map || !points?.length) return;

    let layer = null;

    const apply = () => {
      if (typeof L.heatLayer !== "function") return;
      layer = L.heatLayer(points, {
        radius: 30,
        blur: 22,
        maxZoom: 8,
        minOpacity: 0.35,
        gradient: {
          0.0: "#16a34a",
          0.5: "#f59e0b",
          0.7: "#f97316",
          1.0: "#dc2626",
        },
      }).addTo(map);
    };

    if (typeof L.heatLayer === "function") {
      apply();
    } else {
      const script = document.createElement("script");
      script.src = "https://unpkg.com/leaflet.heat/dist/leaflet-heat.js";
      script.async = true;
      script.onload = apply;
      document.body.appendChild(script);
    }

    return () => {
      if (layer) map.removeLayer(layer);
    };
  }, [map, points]);

  return null;
}

function Legend() {
  return (
    <div className="bg-black/70 text-white px-3 py-2 rounded-lg text-xs border border-white/15">
      <p className="font-semibold mb-1">Risk Heat Legend</p>
      <div className="space-y-1">
        <p><span className="inline-block w-3 h-3 bg-green-500 mr-2" />0.0 - Low</p>
        <p><span className="inline-block w-3 h-3 bg-orange-500 mr-2" />0.5 - Medium</p>
        <p><span className="inline-block w-3 h-3 bg-red-600 mr-2" />0.7+ - High</p>
      </div>
    </div>
  );
}

export default function SpatialRiskMap() {
  const [disasterType, setDisasterType] = useState("landslide");
  const [method, setMethod] = useState("kmeans");
  const [k, setK] = useState(5);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState(null);

  const heatPoints = useMemo(() => {
    if (!result?.heatmap) return [];
    return result.heatmap.map((p) => [Number(p[0]), Number(p[1]), Number(p[2])]);
  }, [result]);

  async function runSpatialPrediction() {
    setLoading(true);
    setError("");
    try {
      const data = await runSpatialAutoPrediction(disasterType, { method, k });
      setResult(data);
    } catch (e) {
      setError(e.message || "Spatial prediction failed");
      setResult(null);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="p-6 text-white space-y-5">
      <div>
        <h1 className="text-3xl font-bold flex items-center gap-2"><MapPinned size={30} /> Spatial Risk Map</h1>
        <p className="text-gray-400">Cluster-based spatio-temporal risk prediction with heatmap visualization.</p>
      </div>

      <div className="bg-white/5 border border-white/10 rounded-2xl p-4 flex flex-wrap gap-3 items-center">
        <select value={disasterType} onChange={(e) => setDisasterType(e.target.value)} className="bg-black/30 border border-white/10 rounded-xl px-3 py-2">
          <option value="earthquake">Earthquake</option>
          <option value="flood">Flood</option>
          <option value="landslide">Landslide</option>
        </select>

        <select value={method} onChange={(e) => setMethod(e.target.value)} className="bg-black/30 border border-white/10 rounded-xl px-3 py-2">
          <option value="kmeans">KMeans</option>
          <option value="dbscan">DBSCAN</option>
        </select>

        <input
          type="number"
          min={2}
          max={10}
          value={k}
          onChange={(e) => setK(Number(e.target.value) || 5)}
          className="w-24 bg-black/30 border border-white/10 rounded-xl px-3 py-2"
          title="Cluster count (KMeans)"
        />

        <button onClick={runSpatialPrediction} disabled={loading} className="px-5 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 disabled:opacity-60 inline-flex items-center gap-2 font-semibold">
          {loading ? <><Loader2 size={16} className="animate-spin" /> Running Spatial AI...</> : "Run Spatial AI Prediction"}
        </button>
      </div>

      {error && <p className="text-red-400">{error}</p>}

      <div className="bg-white/5 border border-white/10 rounded-2xl p-3">
        <div className="h-[460px] w-full rounded-xl overflow-hidden border border-white/10 relative">
          <MapContainer center={INDIA_CENTER} zoom={5} scrollWheelZoom className="h-full w-full">
            <TileLayer attribution='&copy; OpenStreetMap contributors' url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
            {heatPoints.length > 0 && <HeatLayer points={heatPoints} />}

            {(result?.clusters || []).map((c) => (
              <Marker key={c.cluster_id} position={[c.centroid.lat, c.centroid.lon]}>
                <Popup>
                  <div className="text-sm">
                    <p><b>Cluster {c.cluster_id}</b></p>
                    <p>Risk: {(Number(c.risk_score) * 100).toFixed(1)}%</p>
                    <p>Level: {c.risk_level}</p>
                    <p>Rule: {(Number(c.rule_score) * 100).toFixed(1)}%</p>
                    <p>ML: {(Number(c.ml_score) * 100).toFixed(1)}%</p>
                    <p>Satellite: {(Number(c.satellite_score) * 100).toFixed(1)}%</p>
                  </div>
                </Popup>
              </Marker>
            ))}
          </MapContainer>

          <div className="absolute right-3 bottom-3 z-[500]">
            <Legend />
          </div>
        </div>
      </div>

      {result && (
        <div className="bg-white/5 border border-white/10 rounded-2xl p-4 space-y-2">
          <p>Disaster: <b className="capitalize">{result.disaster}</b></p>
          <p>Clusters: <b>{result.clusters?.length || 0}</b></p>
          <p>Latency: <b>{result.meta?.latency_ms} ms</b></p>
          {result.cluster_alerts?.length > 0 && (
            <div className="mt-2 text-orange-300">
              <p className="font-semibold flex items-center gap-2"><AlertTriangle size={15} /> Cluster Alerts</p>
              {result.cluster_alerts.map((a) => (
                <p key={a.cluster_id}>Cluster {a.cluster_id}: {(Number(a.risk_score) * 100).toFixed(1)}% ({a.risk_level})</p>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
