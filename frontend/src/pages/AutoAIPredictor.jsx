import React, { useState } from "react";
import { BrainCircuit, Loader2, Satellite } from "lucide-react";

import { runAutoPrediction } from "../api/autoPredictorApi";

const BADGE = {
  Low: "bg-green-500/20 text-green-300 border-green-400/30",
  Medium: "bg-orange-500/20 text-orange-300 border-orange-400/30",
  High: "bg-red-500/20 text-red-300 border-red-400/30",
};

export default function AutoAIPredictor() {
  const [disasterType, setDisasterType] = useState("flood");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState(null);

  async function onRun() {
    setLoading(true);
    setError("");
    try {
      const data = await runAutoPrediction(disasterType);
      setResult(data);
    } catch (e) {
      setError(e.message || "Auto prediction failed");
      setResult(null);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="p-6 text-white space-y-6">
      <div>
        <h1 className="text-3xl font-bold flex items-center gap-2">
          <BrainCircuit size={30} /> Auto AI Predictor
        </h1>
        <p className="text-gray-400">No manual inputs. Uses DB + weather + satellite + hybrid ML.</p>
      </div>

      <div className="bg-white/5 border border-white/10 rounded-2xl p-5 flex flex-wrap items-center gap-3">
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
          onClick={onRun}
          disabled={loading}
          className="px-5 py-2.5 rounded-xl bg-cyan-600 hover:bg-cyan-700 disabled:opacity-60 inline-flex items-center gap-2 font-semibold"
        >
          {loading ? (
            <>
              <Loader2 size={16} className="animate-spin" /> Running...
            </>
          ) : (
            <>
              <Satellite size={16} /> Run Auto Prediction
            </>
          )}
        </button>
      </div>

      {error && <p className="text-red-400">{error}</p>}

      {result && (
        <div className="grid lg:grid-cols-2 gap-4">
          <div className="bg-white/5 border border-white/10 rounded-2xl p-5 space-y-3">
            <h2 className="text-xl font-semibold">Auto Prediction Output</h2>
            <p>
              Disaster: <b className="capitalize">{result.disaster}</b>
            </p>
            <div className={`inline-flex border rounded-xl px-3 py-2 font-semibold ${BADGE[result.risk_level] || BADGE.Medium}`}>
              Risk Level: {result.risk_level}
            </div>
            <p>
              Final Risk: <b>{(Number(result.final_risk || 0) * 100).toFixed(1)}%</b>
            </p>
            <p>
              Confidence: <b>{Number(result.confidence || 0).toFixed(1)}%</b>
            </p>
            <p>
              Rule Score: <b>{(Number(result.rule_score || 0) * 100).toFixed(1)}%</b>
            </p>
            <p>
              ML Score: <b>{(Number(result.ml_score || 0) * 100).toFixed(1)}%</b>
            </p>
            <p>
              Satellite Score: <b>{(Number(result.satellite_score || 0) * 100).toFixed(1)}%</b>
            </p>
          </div>

          <div className="bg-white/5 border border-white/10 rounded-2xl p-5 space-y-3">
            <h2 className="text-xl font-semibold">Risk Explanation</h2>
            <p>Formula: <b>{result.explanation?.fusion_formula}</b></p>
            <p>Rolling: <b>{result.explanation?.rolling_window}</b></p>
            <p>Weather Source: <b>{result.explanation?.weather_source || "fallback"}</b></p>
            <p>Data Source: <b>{result.explanation?.dataset_source || "db"}</b></p>
            <p>Latency: <b>{result.explanation?.latency_ms} ms</b></p>
            <div className="text-gray-300 text-sm">
              <p>Seismic Activity Frequency: {Number(result.explanation?.derived_features?.seismic_activity_frequency || 0).toFixed(3)}</p>
              <p>Rainfall Accumulation (7d): {Number(result.explanation?.derived_features?.rainfall_accumulation_7d || 0).toFixed(2)} mm</p>
              <p>Soil Moisture Trend: {Number(result.explanation?.derived_features?.soil_moisture_trend || 0).toFixed(3)}</p>
              <p>Slope Instability Index: {Number(result.explanation?.derived_features?.slope_instability_index || 0).toFixed(3)}</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
