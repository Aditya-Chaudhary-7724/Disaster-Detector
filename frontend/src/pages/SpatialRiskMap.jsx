import React, { useMemo, useState } from "react";
import { AlertTriangle, Loader2, MapPinned } from "lucide-react";
import { Circle, CircleMarker, MapContainer, Marker, Popup, TileLayer, useMap } from "react-leaflet";
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

function colorForRisk(risk) {
  const score = Number(risk || 0);
  if (score > 0.7) return "#dc2626";
  if (score >= 0.4) return "#facc15";
  return "#16a34a";
}

function FocusLocalArea({ center }) {
  const map = useMap();
  React.useEffect(() => {
    if (!center) return;
    map.flyTo([center.lat, center.lng], 9, { duration: 1.2 });
  }, [center, map]);
  return null;
}

function Legend() {
  return (
    <div className="bg-black/75 text-white px-3 py-2 rounded-lg text-xs border border-white/15">
      <p className="font-semibold mb-1">Danger Zone Legend</p>
      <div className="space-y-1">
        <p><span className="inline-block w-3 h-3 bg-red-600 mr-2" />High</p>
        <p><span className="inline-block w-3 h-3 bg-yellow-400 mr-2" />Medium</p>
        <p><span className="inline-block w-3 h-3 bg-green-600 mr-2" />Low</p>
      </div>
    </div>
  );
}

export default function SpatialRiskMap() {
  const [disasterType, setDisasterType] = useState("landslide");
  const [radiusPreset, setRadiusPreset] = useState(75);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState(null);

  const gridCells = useMemo(() => result?.grid_cells || [], [result]);
  const center = result?.analysis_center || null;

  async function runSpatialPrediction() {
    setLoading(true);
    setError("");
    try {
      const syntheticK = Math.max(4, Math.round(radiusPreset / 15));
      const data = await runSpatialAutoPrediction(disasterType, { method: "local", k: syntheticK });
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
        <p className="text-gray-400">Localized risk modeling with real danger zones, inverse-distance neighbor influence, and AI explanations.</p>
      </div>

      <div className="bg-white/5 border border-white/10 rounded-2xl p-4 flex flex-wrap gap-3 items-center">
        <select value={disasterType} onChange={(e) => setDisasterType(e.target.value)} className="bg-black/30 border border-white/10 rounded-xl px-3 py-2">
          <option value="earthquake">Earthquake</option>
          <option value="flood">Flood</option>
          <option value="landslide">Landslide</option>
        </select>

        <select value={radiusPreset} onChange={(e) => setRadiusPreset(Number(e.target.value))} className="bg-black/30 border border-white/10 rounded-xl px-3 py-2">
          <option value={50}>50 km local area</option>
          <option value={75}>75 km local area</option>
          <option value={100}>100 km local area</option>
        </select>

        <button onClick={runSpatialPrediction} disabled={loading} className="px-5 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 disabled:opacity-60 inline-flex items-center gap-2 font-semibold">
          {loading ? <><Loader2 size={16} className="animate-spin" /> Running Local AI...</> : "Run Local Spatial Prediction"}
        </button>
      </div>

      {error && <p className="text-red-400">{error}</p>}

      <div className="bg-white/5 border border-white/10 rounded-2xl p-3">
        <div className="h-[500px] w-full rounded-xl overflow-hidden border border-white/10 relative">
          <MapContainer center={INDIA_CENTER} zoom={5} scrollWheelZoom className="h-full w-full">
            <TileLayer attribution='&copy; OpenStreetMap contributors' url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
            {center && <FocusLocalArea center={center} />}

            {center && (
              <Marker position={[center.lat, center.lng]}>
                <Popup>
                  <div className="text-sm">
                    <p><b>Local Analysis Center</b></p>
                    <p>Radius: {result?.radius_km} km</p>
                    <p>Events analyzed: {result?.local_event_count}</p>
                  </div>
                </Popup>
              </Marker>
            )}

            {gridCells.map((cell, index) => (
              <Circle
                key={`${cell.lat}-${cell.lng}-${index}`}
                center={[cell.lat, cell.lng]}
                radius={5200}
                pathOptions={{
                  color: colorForRisk(cell.risk_score),
                  fillColor: colorForRisk(cell.risk_score),
                  fillOpacity: 0.38,
                  weight: 1,
                }}
              >
                <Popup>
                  <div className="text-sm">
                    <p><b>Grid Cell</b></p>
                    <p>Risk: {(Number(cell.risk_score) * 100).toFixed(1)}%</p>
                    <p>Level: {cell.risk_level}</p>
                    <p>Neighbor influence: {(Number(cell.neighbor_influence) * 100).toFixed(1)}%</p>
                    {(cell.reasons || []).map((reason) => <p key={reason}>{reason}</p>)}
                  </div>
                </Popup>
              </Circle>
            ))}

            {(result?.danger_zones || []).map((zone) => (
              <CircleMarker
                key={zone.zone_id}
                center={[zone.centroid.lat, zone.centroid.lng]}
                radius={10}
                pathOptions={{
                  color: colorForRisk(zone.risk_score),
                  fillColor: colorForRisk(zone.risk_score),
                  fillOpacity: 0.9,
                  weight: 2,
                }}
              >
                <Popup>
                  <div className="text-sm">
                    <p><b>Danger Zone {zone.zone_id}</b></p>
                    <p>Risk: {(Number(zone.risk_score) * 100).toFixed(1)}%</p>
                    <p>Cells grouped: {zone.cell_count}</p>
                    <p>Level: {zone.risk_level}</p>
                  </div>
                </Popup>
              </CircleMarker>
            ))}
          </MapContainer>

          <div className="absolute right-3 bottom-3 z-[500]">
            <Legend />
          </div>
        </div>
      </div>

      {result && (
        <div className="grid xl:grid-cols-3 gap-4">
          <div className="bg-white/5 border border-white/10 rounded-2xl p-4 space-y-2">
            <p>Disaster: <b className="capitalize">{result.disaster}</b></p>
            <p>Local center: <b>{result.analysis_center?.lat}, {result.analysis_center?.lng}</b></p>
            <p>Radius: <b>{result.radius_km} km</b></p>
            <p>Grid cells: <b>{result.grid_cells?.length || 0}</b></p>
            <p>Danger zones: <b>{result.danger_zones?.length || 0}</b></p>
            <p>Latency: <b>{result.meta?.latency_ms} ms</b></p>
          </div>

          <div className="bg-white/5 border border-white/10 rounded-2xl p-4 space-y-2">
            <p className="font-semibold">AI Explanation</p>
            {(result.explanations || []).length === 0 ? (
              <p className="text-gray-400">No dominant explanations generated.</p>
            ) : (
              (result.explanations || []).map((item) => (
                <p key={item} className="text-gray-200">{item}</p>
              ))
            )}
          </div>

          <div className="bg-white/5 border border-white/10 rounded-2xl p-4 space-y-2">
            {result.cluster_alerts?.length > 0 ? (
              <>
                <p className="font-semibold flex items-center gap-2"><AlertTriangle size={15} /> Danger Zone Alerts</p>
                {result.cluster_alerts.map((a) => (
                  <p key={a.zone_id}>Zone {a.zone_id}: {(Number(a.risk_score) * 100).toFixed(1)}% ({a.risk_level})</p>
                ))}
              </>
            ) : (
              <>
                <p className="font-semibold">Danger Zone Alerts</p>
                <p className="text-gray-400">No high-priority local danger zones detected.</p>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
