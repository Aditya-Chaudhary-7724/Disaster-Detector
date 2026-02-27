import React, { useMemo, useState } from "react";
import { Activity, Brain, Gauge, Mountain, Waves } from "lucide-react";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { predictDisasterRisk, runAlertCheck } from "../api/disasterApi";

const COLORS = {
  Low: "text-green-300 border-green-400/40 bg-green-500/20",
  Medium: "text-orange-300 border-orange-400/40 bg-orange-500/20",
  High: "text-red-300 border-red-400/40 bg-red-500/20",
};

export default function Predictor() {
  const [disaster, setDisaster] = useState("flood");
  const [payload, setPayload] = useState({
    latitude: 26.14,
    longitude: 91.73,
    rainfall_24h_mm: 140,
    soil_moisture: 0.62,
    slope_deg: 18,
    ndvi: 0.45,
    plant_density: 0.5,
    seismic_mag: 2.4,
    depth_km: 30,
  });
  const [result, setResult] = useState(null);
  const [alertRes, setAlertRes] = useState(null);
  const [loading, setLoading] = useState(false);
  const [logs, setLogs] = useState([]);
  const [error, setError] = useState("");

  const preparedPayload = useMemo(
    () => ({
      disaster,
      disaster_type: disaster,
      latitude: Number(payload.latitude),
      longitude: Number(payload.longitude),
      rainfall_24h_mm: Number(payload.rainfall_24h_mm),
      soil_moisture: Number(payload.soil_moisture),
      slope_deg: Number(payload.slope_deg),
      ndvi: Number(payload.ndvi),
      plant_density: Number(payload.plant_density),
      seismic_mag: Number(payload.seismic_mag),
      seismic_magnitude: Number(payload.seismic_mag),
      depth_km: Number(payload.depth_km),
    }),
    [payload, disaster]
  );

  const fiRows = result?.feature_importance
    ? Object.entries(result.feature_importance)
        .map(([feature, value]) => ({ feature, importance: Number(value) }))
        .sort((a, b) => b.importance - a.importance)
    : [];

  function setField(name, value) {
    setPayload((prev) => ({ ...prev, [name]: value }));
  }

  function pushLog(message) {
    const line = `${new Date().toLocaleTimeString()} - ${message}`;
    console.log("[Predictor]", line);
    setLogs((prev) => [line, ...prev].slice(0, 8));
  }

  async function runPrediction() {
    setLoading(true);
    setResult(null);
    setAlertRes(null);
    setError("");
    pushLog("Run AI Prediction clicked");

    try {
      const response = await predictDisasterRisk(preparedPayload);
      const output = response.result || response;
      setResult(output);
      pushLog(`Prediction complete: ${output.risk_level || output.level} (${output.method || "Unknown"})`);
    } catch (err) {
      setError(err.message || "Prediction failed");
      pushLog("Prediction failed");
    } finally {
      setLoading(false);
    }
  }

  async function createAlert() {
    setError("");
    try {
      pushLog("Manual alert check triggered");
      const res = await runAlertCheck({ ...preparedPayload, threshold: 70 });
      setAlertRes(res);
      pushLog(res.alert_created ? "Alert created" : "No alert created");
    } catch (err) {
      setError(err.message || "Alert creation failed");
      pushLog("Alert generation failed");
    }
  }

  const levelText = result?.risk_level || result?.level || "Medium";

  return (
    <div className="p-6 text-white space-y-5">
      <div>
        <h1 className="text-3xl font-bold flex items-center gap-2">
          <Brain size={28} /> AI Predictor
        </h1>
        <p className="text-gray-400">ML-driven multi-hazard risk prediction with explainability.</p>
      </div>

      <div className="bg-white/5 border border-white/10 rounded-2xl p-5">
        <div className="flex flex-wrap gap-3 items-center mb-5">
          <select
            value={disaster}
            onChange={(e) => setDisaster(e.target.value)}
            className="bg-black/30 border border-white/10 rounded-xl px-3 py-2"
          >
            <option value="flood">Flood</option>
            <option value="landslide">Landslide</option>
            <option value="earthquake">Earthquake</option>
          </select>

          <button
            onClick={runPrediction}
            disabled={loading}
            className="px-4 py-2 bg-blue-600 rounded-xl hover:bg-blue-700 disabled:opacity-60"
          >
            {loading ? "Running AI..." : "Run AI Prediction"}
          </button>

          <button onClick={createAlert} className="px-4 py-2 bg-red-600 rounded-xl hover:bg-red-700">
            Trigger Alert Check
          </button>
        </div>

        <div className="grid md:grid-cols-2 gap-4">
          <Slider label="Latitude" min={6} max={38} step={0.01} value={payload.latitude} onChange={(v) => setField("latitude", v)} icon={Activity} />
          <Slider label="Longitude" min={67} max={98} step={0.01} value={payload.longitude} onChange={(v) => setField("longitude", v)} icon={Activity} />
          <Slider label="Rainfall 24h (mm)" min={0} max={350} step={1} value={payload.rainfall_24h_mm} onChange={(v) => setField("rainfall_24h_mm", v)} icon={Waves} />
          <Slider label="Soil Moisture" min={0} max={1} step={0.01} value={payload.soil_moisture} onChange={(v) => setField("soil_moisture", v)} icon={Gauge} />
          <Slider label="Slope (deg)" min={0} max={60} step={0.1} value={payload.slope_deg} onChange={(v) => setField("slope_deg", v)} icon={Mountain} />
          <Slider label="NDVI" min={0} max={1} step={0.01} value={payload.ndvi} onChange={(v) => setField("ndvi", v)} icon={Gauge} />
          <Slider label="Plant Density" min={0} max={1} step={0.01} value={payload.plant_density} onChange={(v) => setField("plant_density", v)} icon={Gauge} />
          <Slider label="Seismic Magnitude" min={0} max={8} step={0.1} value={payload.seismic_mag} onChange={(v) => setField("seismic_mag", v)} icon={Activity} />
          <Slider label="Depth (km)" min={0} max={300} step={1} value={payload.depth_km} onChange={(v) => setField("depth_km", v)} icon={Activity} />
        </div>

        {error && <p className="text-red-400 mt-4">{error}</p>}
      </div>

      {result && (
        <div className="grid xl:grid-cols-2 gap-4">
          <div className="bg-white/5 border border-white/10 rounded-2xl p-5 space-y-3">
            <h2 className="text-xl font-semibold">Prediction Result</h2>
            <div className={`inline-flex border rounded-xl px-3 py-2 font-semibold ${COLORS[levelText] || COLORS.Medium}`}>
              Risk Level: {levelText}
            </div>
            <p>Method Used: <b>{result.method || "Unknown"}</b></p>
            <p>
              Confidence: <b>{result.confidence !== null && result.confidence !== undefined ? `${(Number(result.confidence) * 100).toFixed(1)}%` : "N/A"}</b>
            </p>
            <p>Risk Score (0-100): <b>{result.risk_score}</b></p>
            <p className="text-gray-300">{result.human_explanation || (result.explanation || [])[0]}</p>

            <div>
              <p className="font-semibold mb-1">Top 3 Features</p>
              <ul className="list-disc pl-5 text-gray-300">
                {(result.top_features || []).slice(0, 3).map((item) => (
                  <li key={item.feature}>{item.feature}: {item.importance}</li>
                ))}
              </ul>
            </div>

            <div className="text-sm text-gray-400">
              <p>Equation: {result.risk_equation}</p>
              <p>Equation Score: {result.equation_score}</p>
            </div>
          </div>

          <div className="bg-white/5 border border-white/10 rounded-2xl p-5">
            <h2 className="text-xl font-semibold mb-2">Feature Importance Chart</h2>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={fiRows}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                  <XAxis dataKey="feature" stroke="#CBD5E1" interval={0} angle={-20} textAnchor="end" height={80} />
                  <YAxis stroke="#CBD5E1" />
                  <Tooltip />
                  <Bar dataKey="importance" fill="#38bdf8" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      )}

      <div className="bg-white/5 border border-white/10 rounded-2xl p-4">
        <h3 className="font-semibold mb-2">Prediction Activity Log</h3>
        {logs.length === 0 ? <p className="text-gray-400">No activity yet.</p> : logs.map((l, i) => <p key={i} className="text-sm text-gray-300">{l}</p>)}
      </div>

      {alertRes && (
        <div className="bg-white/5 border border-white/10 rounded-2xl p-4">
          <p className="font-semibold">Alert Engine Response:</p>
          <p className="text-gray-300 mt-1">{alertRes.alert_created ? alertRes.alert.message : "No alert created."}</p>
        </div>
      )}
    </div>
  );
}

function Slider({ label, min, max, step, value, onChange, icon: Icon }) {
  return (
    <label className="block bg-black/20 border border-white/10 rounded-xl p-3">
      <div className="flex items-center justify-between mb-2 text-sm text-gray-300">
        <span className="flex items-center gap-1">{Icon ? <Icon size={14} /> : null} {label}</span>
        <span>{Number(value).toFixed(step < 1 ? 2 : 0)}</span>
      </div>
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        className="w-full"
      />
    </label>
  );
}
