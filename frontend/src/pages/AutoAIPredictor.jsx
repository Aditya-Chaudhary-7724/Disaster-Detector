import React, { useState } from "react";
import { BrainCircuit, Loader2, Radar, Satellite } from "lucide-react";
import { Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { runAutomaticPrediction, runAutoPrediction } from "../api/autoPredictorApi";

const BADGE = {
  Low: "bg-green-500/20 text-green-300 border-green-400/30",
  Medium: "bg-orange-500/20 text-orange-300 border-orange-400/30",
  High: "bg-red-500/20 text-red-300 border-red-400/30",
};

function asPercent(value, scale = 1) {
  return `${(Number(value || 0) * scale).toFixed(1)}%`;
}

export default function AutoAIPredictor() {
  const [disasterType, setDisasterType] = useState("flood");
  const [loadingAuto, setLoadingAuto] = useState(false);
  const [loadingFocused, setLoadingFocused] = useState(false);
  const [error, setError] = useState("");
  const [autoResult, setAutoResult] = useState(null);
  const [focusedResult, setFocusedResult] = useState(null);

  async function onRunAuto() {
    setLoadingAuto(true);
    setError("");
    try {
      const data = await runAutomaticPrediction();
      setAutoResult(data);
    } catch (e) {
      setError(e.message || "Automatic prediction failed");
      setAutoResult(null);
    } finally {
      setLoadingAuto(false);
    }
  }

  async function onRunFocused() {
    setLoadingFocused(true);
    setError("");
    try {
      const data = await runAutoPrediction(disasterType);
      setFocusedResult(data);
    } catch (e) {
      setError(e.message || "Focused prediction failed");
      setFocusedResult(null);
    } finally {
      setLoadingFocused(false);
    }
  }

  const best = autoResult?.details || null;
  const level = autoResult?.risk_level || best?.risk_level || "Medium";
  const focusedLevel = focusedResult?.risk_level || "Medium";
  const forecastData = (focusedResult?.future_risk_7_days || autoResult?.future_risk_7_days || []).map((value, index) => ({
    day: `D+${index + 1}`,
    risk: Number(value || 0) * 100,
  }));

  return (
    <div className="p-6 text-white space-y-6">
      <div>
        <h1 className="text-3xl font-bold flex items-center gap-2">
          <BrainCircuit size={30} /> Auto Predictor
        </h1>
        <p className="text-gray-400">No manual input required. The backend scans recent DB events, rolling averages, ML output, and simulated satellite signals.</p>
      </div>

      <div className="grid xl:grid-cols-2 gap-4">
        <div className="bg-white/5 border border-white/10 rounded-2xl p-5 space-y-4">
          <div className="flex items-start justify-between gap-3">
            <div>
              <h2 className="text-xl font-semibold">Automatic AI Scan</h2>
              <p className="text-sm text-gray-400">Find the highest current disaster risk with one click.</p>
            </div>
            <button
              onClick={onRunAuto}
              disabled={loadingAuto}
              className="px-5 py-2.5 rounded-xl bg-cyan-600 hover:bg-cyan-700 disabled:opacity-60 inline-flex items-center gap-2 font-semibold"
            >
              {loadingAuto ? <><Loader2 size={16} className="animate-spin" /> Running...</> : <><Radar size={16} /> Run AI Prediction</>}
            </button>
          </div>

          {autoResult && (
            <div className="space-y-3">
              <div className={`inline-flex border rounded-xl px-3 py-2 font-semibold ${BADGE[level] || BADGE.Medium}`}>
                {level} Risk
              </div>
              <p>Priority hazard: <b className="capitalize">{autoResult.disaster_type}</b></p>
              <p>Risk score: <b>{asPercent(autoResult.risk_score)}</b></p>
              <p>Confidence: <b>{asPercent(autoResult.confidence)}</b></p>
              <p>Trend: <b className="capitalize">{autoResult.trend || best?.trend || "stable"}</b></p>
              <div className="grid md:grid-cols-3 gap-3">
                {(autoResult.evaluated_disasters || []).map((item) => (
                  <div key={item.disaster_type} className="rounded-xl border border-white/10 bg-black/20 p-3">
                    <p className="font-semibold capitalize">{item.disaster_type}</p>
                    <p className="text-sm text-gray-300">Risk: {asPercent(item.risk_score)}</p>
                    <p className="text-sm text-gray-400">{item.risk_level} • {item.trend || "stable"}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        <div className="bg-white/5 border border-white/10 rounded-2xl p-5 space-y-4">
          <div className="flex flex-wrap items-center gap-3">
            <div>
              <h2 className="text-xl font-semibold">Focused Hazard Check</h2>
              <p className="text-sm text-gray-400">Run the same no-input pipeline for one selected disaster type.</p>
            </div>
          </div>
          <div className="flex flex-wrap gap-3 items-center">
            <select
              value={disasterType}
              onChange={(e) => setDisasterType(e.target.value)}
              className="bg-black/30 border border-white/10 rounded-xl px-3 py-2"
            >
              <option value="earthquake">Earthquake</option>
              <option value="flood">Flood</option>
              <option value="landslide">Landslide</option>
            </select>
            <button
              onClick={onRunFocused}
              disabled={loadingFocused}
              className="px-5 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 disabled:opacity-60 inline-flex items-center gap-2 font-semibold"
            >
              {loadingFocused ? <><Loader2 size={16} className="animate-spin" /> Running...</> : <><Satellite size={16} /> Run Selected Hazard</>}
            </button>
          </div>

          {focusedResult && (
            <div className="space-y-2">
              <div className={`inline-flex border rounded-xl px-3 py-2 font-semibold ${BADGE[focusedLevel] || BADGE.Medium}`}>
                {focusedLevel} Risk
              </div>
              <p>Final risk: <b>{asPercent(focusedResult.final_risk)}</b></p>
              <p>Confidence: <b>{asPercent(focusedResult.confidence, 1)}</b></p>
              <p>Rule score: <b>{asPercent(focusedResult.rule_score)}</b></p>
              <p>ML score: <b>{asPercent(focusedResult.ml_score)}</b></p>
              <p>Satellite score: <b>{asPercent(focusedResult.satellite_score)}</b></p>
              <p>CNN score: <b>{asPercent(focusedResult.cnn_score)}</b></p>
              <p>Trend: <b className="capitalize">{focusedResult.trend || "stable"}</b></p>
            </div>
          )}
        </div>
      </div>

      {(best || focusedResult) && (
        <div className="grid xl:grid-cols-3 gap-4">
          {best && (
            <div className="bg-white/5 border border-white/10 rounded-2xl p-5 space-y-2">
              <h3 className="text-lg font-semibold">Automatic Scan Details</h3>
              <p>Rolling window: <b>{best.explanation?.rolling_window || "Last 7 days"}</b></p>
              <p>Data source: <b>{best.explanation?.dataset_source || "db"}</b></p>
              <p>Weather source: <b>{best.explanation?.weather_source || "fallback"}</b></p>
              <p>Latency: <b>{best.explanation?.latency_ms || 0} ms</b></p>
              <p>Explanation: <b className="capitalize">{autoResult?.explanation?.trend || best?.trend || "stable"} trend from recent records</b></p>
            </div>
          )}

          {focusedResult && (
            <div className="bg-white/5 border border-white/10 rounded-2xl p-5 space-y-2">
              <h3 className="text-lg font-semibold">Derived Signals</h3>
              <p>7-day rainfall: <b>{Number(focusedResult.explanation?.derived_features?.rainfall_accumulation_7d || 0).toFixed(2)} mm</b></p>
              <p>Soil moisture trend: <b>{Number(focusedResult.explanation?.derived_features?.soil_moisture_trend || 0).toFixed(3)}</b></p>
              <p>Slope instability index: <b>{Number(focusedResult.explanation?.derived_features?.slope_instability_index || 0).toFixed(3)}</b></p>
              <p>Seismic activity frequency: <b>{Number(focusedResult.explanation?.derived_features?.seismic_activity_frequency || 0).toFixed(3)}</b></p>
            </div>
          )}

          {forecastData.length > 0 && (
            <div className="bg-white/5 border border-white/10 rounded-2xl p-5">
              <h3 className="text-lg font-semibold mb-3">Next 7 Days Forecast</h3>
              <div className="h-56">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={forecastData}>
                    <XAxis dataKey="day" stroke="#CBD5E1" />
                    <YAxis stroke="#CBD5E1" domain={[0, 100]} />
                    <Tooltip />
                    <Line type="monotone" dataKey="risk" stroke="#22d3ee" strokeWidth={2} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>
          )}
        </div>
      )}

      {error && <p className="text-red-400">{error}</p>}
    </div>
  );
}
