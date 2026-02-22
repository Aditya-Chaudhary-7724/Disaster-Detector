import React, { useState } from "react";
import { predictDisasterRisk, runAlertCheck } from "../api/disasterApi";

export default function Predictor() {
  const [disaster, setDisaster] = useState("flood");
  const [payload, setPayload] = useState({
    rainfall_24h_mm: 0,
    rainfall_7d_mm: 0,
    soil_moisture: 0.5,
    slope_deg: 10,
    ndvi: 0.5,
    plant_density: 0.5,
    seismic_mag: 0,
    depth_km: 0,
  });

  const [result, setResult] = useState(null);
  const [alertRes, setAlertRes] = useState(null);
  const [error, setError] = useState("");

  function handleChange(e) {
    const { name, value } = e.target;
    setPayload((p) => ({ ...p, [name]: value }));
  }

  async function handlePredict() {
    setError("");
    setResult(null);
    setAlertRes(null);

    try {
      const res = await predictDisasterRisk({
        disaster,
        ...payload,
        rainfall_24h_mm: Number(payload.rainfall_24h_mm),
        rainfall_7d_mm: Number(payload.rainfall_7d_mm),
        soil_moisture: Number(payload.soil_moisture),
        slope_deg: Number(payload.slope_deg),
        ndvi: Number(payload.ndvi),
        plant_density: Number(payload.plant_density),
        seismic_mag: Number(payload.seismic_mag),
        depth_km: Number(payload.depth_km),
      });

      setResult(res.result);
    } catch (err) {
      setError(err.message || "Prediction failed");
    }
  }

  async function handleCreateAlert() {
    setError("");
    setAlertRes(null);

    try {
      const res = await runAlertCheck({
        disaster,
        ...payload,
        threshold: 70,
        rainfall_24h_mm: Number(payload.rainfall_24h_mm),
        rainfall_7d_mm: Number(payload.rainfall_7d_mm),
        soil_moisture: Number(payload.soil_moisture),
        slope_deg: Number(payload.slope_deg),
        ndvi: Number(payload.ndvi),
        plant_density: Number(payload.plant_density),
        seismic_mag: Number(payload.seismic_mag),
        depth_km: Number(payload.depth_km),
      });

      setAlertRes(res);
    } catch (err) {
      setError(err.message || "Alert creation failed");
    }
  }

  return (
    <div className="p-6 text-white">
      <h1 className="text-3xl font-bold mb-2">AI Predictor (Risk Forecast)</h1>
      <p className="text-gray-400 mb-6">
        This does not "see the future". It generates a <b>risk probability</b> using scientific rules.
      </p>

      <div className="bg-white/5 border border-white/10 rounded-2xl p-5 max-w-3xl">
        <div className="flex gap-3 mb-4">
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
            onClick={handlePredict}
            className="px-4 py-2 bg-blue-600 rounded-xl hover:bg-blue-700 transition"
          >
            Predict Risk
          </button>

          <button
            onClick={handleCreateAlert}
            className="px-4 py-2 bg-red-600 rounded-xl hover:bg-red-700 transition"
          >
            Create Alert (if HIGH)
          </button>
        </div>

        <div className="grid grid-cols-2 gap-3">
          {disaster !== "earthquake" && (
            <>
              <Input label="Rainfall 24h (mm)" name="rainfall_24h_mm" value={payload.rainfall_24h_mm} onChange={handleChange} />
              <Input label="Rainfall 7d (mm)" name="rainfall_7d_mm" value={payload.rainfall_7d_mm} onChange={handleChange} />
              <Input label="Soil Moisture (0-1)" name="soil_moisture" value={payload.soil_moisture} onChange={handleChange} />
              <Input label="Slope (deg)" name="slope_deg" value={payload.slope_deg} onChange={handleChange} />
              <Input label="NDVI (0-1)" name="ndvi" value={payload.ndvi} onChange={handleChange} />
              <Input label="Plant Density (0-1)" name="plant_density" value={payload.plant_density} onChange={handleChange} />
            </>
          )}

          {disaster === "earthquake" && (
            <>
              <Input label="Seismic Magnitude" name="seismic_mag" value={payload.seismic_mag} onChange={handleChange} />
              <Input label="Depth (km)" name="depth_km" value={payload.depth_km} onChange={handleChange} />
            </>
          )}
        </div>

        {error && <p className="text-red-400 mt-4">{error}</p>}

        {result && (
          <div className="mt-5 bg-black/30 border border-white/10 rounded-xl p-4">
            <p className="text-lg font-semibold">
              Risk Score: <span className="text-yellow-300">{result.risk_score}/100</span> —{" "}
              <span className="text-green-300">{result.level}</span>
            </p>

            <ul className="mt-2 text-gray-300 list-disc pl-5">
              {result.reasons.map((r, i) => (
                <li key={i}>{r}</li>
              ))}
            </ul>
          </div>
        )}

        {alertRes && (
          <div className="mt-4 bg-black/40 border border-white/10 rounded-xl p-4">
            <p className="font-semibold">
              Alert Engine:{" "}
              {alertRes.alert_created ? (
                <span className="text-green-400">✅ Alert Created</span>
              ) : (
                <span className="text-gray-400">No alert (risk below threshold)</span>
              )}
            </p>

            {alertRes.alert_created && (
              <p className="text-gray-300 mt-2">{alertRes.alert.message}</p>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

function Input({ label, name, value, onChange }) {
  return (
    <div>
      <p className="text-sm text-gray-400 mb-1">{label}</p>
      <input
        name={name}
        value={value}
        onChange={onChange}
        className="w-full bg-black/30 border border-white/10 rounded-xl px-3 py-2 outline-none"
      />
    </div>
  );
}
