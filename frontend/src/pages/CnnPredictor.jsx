import React, { useMemo, useState } from "react";
import { CloudRain, Cpu, Loader2, MapPinned, ScanSearch, Satellite } from "lucide-react";
import { Circle, MapContainer, Marker, Popup, TileLayer, useMap } from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";

import { getEnvironmentalData, getHighRiskLocation, getNearestRisks, runCnnPredict } from "../api/disasterApi";

import markerIcon2x from "leaflet/dist/images/marker-icon-2x.png";
import markerIcon from "leaflet/dist/images/marker-icon.png";
import markerShadow from "leaflet/dist/images/marker-shadow.png";

delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: markerIcon2x,
  iconUrl: markerIcon,
  shadowUrl: markerShadow,
});

const STEPS = [
  "Locating high-risk zone...",
  "Fetching satellite data...",
  "Analyzing rainfall patterns...",
  "Combining environmental signals...",
  "Producing final prediction...",
];

const THINKING_TEXT = [
  "Searching the database for the latest high-risk coordinates.",
  "Loading NASA true-color imagery and satellite context.",
  "Ingesting RainViewer radar intensity and rainfall movement.",
  "Combining weather, terrain, and geospatial image signals.",
  "Scoring hazard probabilities and confidence.",
];

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function FlyToLocation({ center, zoom }) {
  const map = useMap();

  React.useEffect(() => {
    if (!center) return;
    map.flyTo(center, zoom, { duration: 1.6 });
  }, [center, zoom, map]);

  return null;
}

export default function CnnPredictor() {
  const [result, setResult] = useState(null);
  const [riskLocation, setRiskLocation] = useState(null);
  const [environmental, setEnvironmental] = useState(null);
  const [dangerZones, setDangerZones] = useState([]);
  const [error, setError] = useState("");
  const [running, setRunning] = useState(false);
  const [activeStep, setActiveStep] = useState(-1);
  const [thinking, setThinking] = useState("");
  const [mapZoom, setMapZoom] = useState(5);

  async function runPrediction() {
    setRunning(true);
    setError("");
    setResult(null);
    setRiskLocation(null);
    setEnvironmental(null);
    setDangerZones([]);
    setActiveStep(0);
    setThinking(THINKING_TEXT[0]);
    setMapZoom(5);

    try {
      const location = await getHighRiskLocation();
      setRiskLocation(location);
      setMapZoom(10);
      await sleep(850);

      setActiveStep(1);
      setThinking(THINKING_TEXT[1]);
      const env = await getEnvironmentalData(location.lat, location.lng);
      setEnvironmental(env);
      await sleep(700);

      setActiveStep(2);
      setThinking(THINKING_TEXT[2]);
      const [nearby, dataPromise] = await Promise.all([
        getNearestRisks(location.lat, location.lng),
        runCnnPredict({
        lat: location.lat,
        lng: location.lng,
        disaster: location.disaster,
        location_name: location.location_name,
        }),
      ]);
      setDangerZones(nearby.items || []);
      await sleep(900);

      setActiveStep(3);
      setThinking(THINKING_TEXT[3]);
      await sleep(850);

      setActiveStep(4);
      setThinking(THINKING_TEXT[4]);
      const data = await dataPromise;
      setResult({ ...data, location_name: location.location_name || location.location });
      await sleep(250);
    } catch (err) {
      setError(err.message || "CNN prediction failed");
      setActiveStep(-1);
      setThinking("");
    } finally {
      setRunning(false);
    }
  }

  const progress = activeStep >= 0 ? ((activeStep + 1) / STEPS.length) * 100 : 0;
  const center = riskLocation ? [riskLocation.lat, riskLocation.lng] : [22.9734, 78.6569];
  const dominantScore = Math.max(Number(result?.flood_prob || 0), Number(result?.landslide_prob || 0));
  const displayDisaster = useMemo(() => riskLocation?.disaster || result?.disaster || "-", [riskLocation, result]);
  const weather = result?.weather || environmental?.weather || {};
  const satelliteTile = environmental?.satellite?.satellite_tile_url;
  const rainTile = environmental?.rain?.rain_layer_url;

  function zoneColor(riskScore) {
    const score = Number(riskScore || 0);
    if (score > 0.7) return "#dc2626";
    if (score >= 0.4) return "#facc15";
    return "#16a34a";
  }

  return (
    <div className="p-6 text-white space-y-6">
      <div>
        <h1 className="text-3xl font-bold flex items-center gap-2">
          <Cpu size={30} /> CNN Predictor
        </h1>
        <p className="text-gray-400">Real-time geospatial AI using DB coordinates, live weather, NASA GIBS satellite tiles, and RainViewer radar overlays.</p>
      </div>

      <div className="bg-white/5 border border-white/10 rounded-2xl p-5 flex flex-wrap items-center justify-between gap-4">
        <div>
          <p className="font-semibold">Live Environmental Inference</p>
          <p className="text-sm text-gray-400">The system fetches a high-risk location, overlays live satellite and rain layers, and combines environmental signals before prediction.</p>
        </div>
        <button
          onClick={runPrediction}
          disabled={running}
          className="px-5 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 disabled:opacity-60 inline-flex items-center gap-2 font-semibold"
        >
          {running ? <><Loader2 size={16} className="animate-spin" /> Running...</> : <><ScanSearch size={16} /> Start Live Analysis</>}
        </button>
      </div>

      <div className="grid xl:grid-cols-[0.95fr,1.05fr] gap-4">
        <div className="bg-white/5 border border-white/10 rounded-2xl p-5 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold">Analysis Pipeline</h2>
            <span className="text-sm text-gray-400">{progress.toFixed(0)}%</span>
          </div>
          <div className="w-full h-2 rounded-full bg-white/10 overflow-hidden">
            <div className="h-full bg-cyan-500 transition-all duration-500" style={{ width: `${progress}%` }} />
          </div>
          <div className="rounded-xl border border-cyan-400/20 bg-cyan-500/10 p-4">
            <p className="text-sm text-cyan-100">{thinking || "Awaiting start command."}</p>
          </div>
          <div className="grid gap-3">
            {STEPS.map((step, index) => {
              const isDone = activeStep > index || (!running && activeStep === index && !!result);
              const isActive = activeStep === index && (running || (!running && !result && activeStep >= 0));
              return (
                <div
                  key={step}
                  className={`rounded-xl border p-4 transition ${isDone ? "border-cyan-400/40 bg-cyan-500/10" : isActive ? "border-orange-400/40 bg-orange-500/10" : "border-white/10 bg-black/20"}`}
                >
                  <p className="font-medium">{step}</p>
                  <p className="text-sm text-gray-400 mt-1">{isDone ? "Completed" : isActive ? "In progress..." : "Waiting"}</p>
                </div>
              );
            })}
          </div>
        </div>

        <div className="space-y-4">
          <div className="bg-white/5 border border-white/10 rounded-2xl p-5">
            <div className="flex items-center justify-between mb-3">
              <h2 className="text-xl font-semibold flex items-center gap-2">
                <MapPinned size={18} /> Live Geospatial Map
              </h2>
              <span className="text-sm text-gray-400">{riskLocation ? `${riskLocation.lat.toFixed(3)}, ${riskLocation.lng.toFixed(3)}` : "India overview"}</span>
            </div>
            <div className="h-[320px] rounded-2xl overflow-hidden border border-white/10">
              <MapContainer center={center} zoom={5} scrollWheelZoom className="h-full w-full">
                <TileLayer attribution='&copy; OpenStreetMap contributors' url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
                {satelliteTile ? <TileLayer url={satelliteTile} opacity={0.6} /> : null}
                {rainTile ? <TileLayer url={rainTile} opacity={0.45} /> : null}
                <FlyToLocation center={center} zoom={mapZoom} />
                {riskLocation && <Marker position={[riskLocation.lat, riskLocation.lng]} />}
                {dangerZones.map((zone, index) => (
                  <Circle
                    key={`${zone.disaster}-${zone.latitude}-${zone.longitude}-${index}`}
                    center={[zone.latitude, zone.longitude]}
                    radius={Math.max(3500, 12000 - Number(zone.distance_km || 0) * 45)}
                    pathOptions={{
                      color: zoneColor(zone.risk_score),
                      fillColor: zoneColor(zone.risk_score),
                      fillOpacity: 0.3,
                      weight: 2,
                    }}
                  >
                    <Popup>
                      <div className="text-sm">
                        <p><b className="capitalize">{zone.disaster} zone</b></p>
                        <p>{zone.title}</p>
                        <p>Risk: {(Number(zone.risk_score || 0) * 100).toFixed(1)}%</p>
                        <p>Distance: {Number(zone.distance_km || 0).toFixed(1)} km</p>
                      </div>
                    </Popup>
                  </Circle>
                ))}
              </MapContainer>
            </div>
          </div>

          <div className="bg-white/5 border border-white/10 rounded-2xl p-5">
            <h2 className="text-xl font-semibold mb-3">Satellite Image Preview</h2>
            <div className="relative aspect-[4/3] rounded-2xl border border-white/10 overflow-hidden bg-black/20">
              {result?.image_url ? (
                <>
                  <img src={result.image_url} alt="Satellite preview" className="w-full h-full object-cover" />
                  <div
                    className="absolute inset-0 pointer-events-none"
                    style={{
                      backgroundImage:
                        "linear-gradient(rgba(255,255,255,0.16) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.16) 1px, transparent 1px)",
                      backgroundSize: "34px 34px",
                    }}
                  />
                </>
              ) : (
                <div className="h-full w-full flex items-center justify-center text-gray-400">
                  Live satellite preview will appear here after data fetch.
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {(weather?.source || result) && (
        <div className="grid lg:grid-cols-3 gap-4">
          <div className="bg-white/5 border border-white/10 rounded-2xl p-5 space-y-2">
            <h2 className="text-xl font-semibold flex items-center gap-2">
              <CloudRain size={18} /> Weather Summary
            </h2>
            <p>Rainfall: <b>{Number(weather.rainfall_mm || 0).toFixed(1)} mm</b></p>
            <p>Humidity: <b>{Number(weather.humidity || 0).toFixed(0)}%</b></p>
            <p>Temperature: <b>{Number(weather.temperature_c || 0).toFixed(1)} C</b></p>
            <p>Wind: <b>{Number(weather.wind_speed_mps || 0).toFixed(1)} m/s</b></p>
            <p>Source: <b>{weather.source || "-"}</b></p>
          </div>

          <div className="bg-white/5 border border-white/10 rounded-2xl p-5 space-y-2">
            <h2 className="text-xl font-semibold flex items-center gap-2">
              <Satellite size={18} /> Overlay Status
            </h2>
            <p>Satellite layer: <b>{environmental?.satellite?.source || "-"}</b></p>
            <p>Rain layer: <b>{environmental?.rain?.source || "-"}</b></p>
            <p>Live analysis: <b>{running ? "Active" : result ? "Completed" : "Idle"}</b></p>
            <p>Location: <b>{riskLocation?.location_name || "-"}</b></p>
            <p>Detected zones: <b>{dangerZones.length}</b></p>
          </div>

          {result && (
            <div className="bg-white/5 border border-white/10 rounded-2xl p-5 space-y-2">
              <h2 className="text-xl font-semibold">Final Output</h2>
              <p>Disaster type: <b className="capitalize">{displayDisaster}</b></p>
              <p>Risk score: <b>{(dominantScore * 100).toFixed(1)}%</b></p>
              <p>Confidence: <b>{(Number(result.confidence || 0) * 100).toFixed(1)}%</b></p>
              <p>Location name: <b>{result.location_name || riskLocation?.location_name || "Unknown"}</b></p>
            </div>
          )}
        </div>
      )}

      {result && (
        <div className="grid lg:grid-cols-2 gap-4">
          <div className="bg-white/5 border border-white/10 rounded-2xl p-5 space-y-2">
            <h2 className="text-xl font-semibold">Prediction Result</h2>
            <p>Flood probability: <b>{(Number(result.flood_prob || 0) * 100).toFixed(1)}%</b></p>
            <p>Landslide probability: <b>{(Number(result.landslide_prob || 0) * 100).toFixed(1)}%</b></p>
            <p>Matched similarity: <b>{(Number(result.similarity || dominantScore) * 100).toFixed(1)}% similarity to known {displayDisaster} patterns</b></p>
          </div>

          <div className="bg-white/5 border border-white/10 rounded-2xl p-5 space-y-2">
            <h2 className="text-xl font-semibold">Live Analysis Display</h2>
            <p>Analyzing region...</p>
            <p>Fetching satellite data...</p>
            <p>Analyzing rainfall patterns...</p>
            <p>Combining environmental signals...</p>
            <p>Image source: <b>{result.image_source}</b></p>
            <p>Backend: <b>{result.backend}</b></p>
          </div>
        </div>
      )}

      {dangerZones.length > 0 && (
        <div className="bg-white/5 border border-white/10 rounded-2xl p-5">
          <h2 className="text-xl font-semibold mb-3">Detected Zones</h2>
          <div className="grid md:grid-cols-3 gap-3">
            {dangerZones.map((zone, index) => (
              <div key={`${zone.disaster}-${index}`} className="rounded-xl border border-white/10 bg-black/20 p-3">
                <p className="font-semibold capitalize">{zone.disaster}</p>
                <p className="text-sm text-gray-300">{zone.title}</p>
                <p className="text-sm text-gray-400 mt-1">Risk: {(Number(zone.risk_score || 0) * 100).toFixed(1)}%</p>
                <p className="text-sm text-gray-400">Distance: {Number(zone.distance_km || 0).toFixed(1)} km</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {error && <p className="text-red-400">{error}</p>}
    </div>
  );
}
