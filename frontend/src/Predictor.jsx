import React, { useEffect, useState } from "react";

import { shouldTriggerAlert, triggerAlertNotification } from "./alertNotifications.js";
import { getModelInfo, getRegions, predictDisasterRisk } from "./api/disasterApi.js";

const THEORY_ITEMS = [
  {
    title: "Ensemble Learning Principle",
    text: "Random Forest combines many decision trees and uses their shared vote to reduce single-model bias.",
  },
  {
    title: "Spatial Correlation Principle",
    text: "Nearby regions often share monsoon systems, river basins, and terrain effects, so local risk is compared with surrounding rainfall averages.",
  },
  {
    title: "Temporal Trend Analysis",
    text: "A seven-record rolling rainfall average smooths short spikes and highlights sustained wet conditions.",
  },
];

function formatScore(value) {
  return Number(value || 0).toFixed(2);
}

function formatPercent(value) {
  return `${(Number(value || 0) * 100).toFixed(1)}%`;
}

function featureLabel(name) {
  return String(name)
    .replaceAll("_", " ")
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

export default function Predictor() {
  const [regions, setRegions] = useState([]);
  const [selectedRegion, setSelectedRegion] = useState("Chennai");
  const [result, setResult] = useState(null);
  const [modelInfo, setModelInfo] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [popupMessage, setPopupMessage] = useState("");

  useEffect(() => {
    if (!popupMessage) {
      return undefined;
    }
    const timeout = window.setTimeout(() => setPopupMessage(""), 3200);
    return () => window.clearTimeout(timeout);
  }, [popupMessage]);

  useEffect(() => {
    async function loadInitialData() {
      try {
        const [regionResponse, infoResponse] = await Promise.all([getRegions(), getModelInfo()]);
        const loadedRegions = regionResponse.regions || [];
        setRegions(loadedRegions);
        if (loadedRegions[0]?.region) {
          setSelectedRegion(loadedRegions[0].region);
        }
        setModelInfo(infoResponse);
      } catch (err) {
        setError(err.message || "Unable to load project data.");
      }
    }

    loadInitialData();
  }, []);

  async function handlePredict() {
    setLoading(true);
    setError("");
    try {
      const response = await predictDisasterRisk({ region: selectedRegion });
      setResult(response);
      if (response.alert_created || shouldTriggerAlert(response.risk_score)) {
        await triggerAlertNotification({
          title: "Disaster Alert!",
          body: `High ${selectedRegion} risk detected with score ${Number(response.risk_score).toFixed(2)}`,
          onPopup: setPopupMessage,
        });
      }
    } catch (err) {
      setError(err.message || "Prediction failed.");
    } finally {
      setLoading(false);
    }
  }

  const featureImportance = Object.entries(result?.feature_importance || {})
    .sort((first, second) => Number(second[1]) - Number(first[1]))
    .slice(0, 8);
  const inputFeatures = result?.input_features || {};

  return (
    <section className="page">
      <div className="page-header">
        <div>
          <p className="eyebrow">CSV Data to ML Risk Analysis</p>
          <h2>Predictor</h2>
          <p className="page-copy">
            Random Forest prediction with rainfall history, nearby-region context, and explainable feature weights.
          </p>
        </div>
      </div>

      <div className="card form-card">
        <label className="field">
          <span>Region</span>
          <select value={selectedRegion} onChange={(event) => setSelectedRegion(event.target.value)}>
            {regions.map((region) => (
              <option key={region.region} value={region.region}>
                {region.region}
              </option>
            ))}
          </select>
        </label>

        <button type="button" className="primary-button" onClick={handlePredict} disabled={loading}>
          {loading ? "Predicting..." : "Predict Risk"}
        </button>
      </div>

      {error ? <div className="card error-text">{error}</div> : null}
      {popupMessage ? <div className="alert-popup">{popupMessage}</div> : null}

      {result ? (
        <div className="grid two-column predictor-results">
          <div className="card">
            <h3>Prediction Result</h3>
            <div className={`risk-badge ${String(result.risk_level).toLowerCase()}`}>{result.risk_level} Risk</div>
            <p className="stat">{formatScore(result.risk_score)}</p>
            <p className="metric">Model Used: {result.algorithm || result.method || "Random Forest"}</p>
            <p className="metric">Formula: Final Risk = {result.formula || "0.5*ML + 0.3*Temporal + 0.2*Spatial"}</p>
            <p className="metric">
              Validation Accuracy: {formatPercent(result.validation?.accuracy)}
            </p>
            <p className="body-copy">{result.analysis || result.human_explanation}</p>
          </div>

          <div className="card">
            <h3>Score Breakdown</h3>
            <div className="score-grid">
              <div className="score-tile">
                <span>ML Score</span>
                <strong>{formatScore(result.ml_score ?? result.ml_probability)}</strong>
              </div>
              <div className="score-tile">
                <span>Temporal Score</span>
                <strong>{formatScore(result.temporal_score ?? result.temporal_factor)}</strong>
              </div>
              <div className="score-tile">
                <span>Spatial Score</span>
                <strong>{formatScore(result.spatial_score ?? result.spatial_influence)}</strong>
              </div>
            </div>
          </div>

          <div className="card">
            <h3>Feature Importance</h3>
            <div className="importance-list">
              {featureImportance.map(([feature, importance]) => (
                <div className="importance-row" key={feature}>
                  <div className="importance-row-header">
                    <span>{featureLabel(feature)}</span>
                    <strong>{formatPercent(importance)}</strong>
                  </div>
                  <div className="importance-track">
                    <span style={{ width: `${Math.min(Number(importance || 0) * 100, 100)}%` }} />
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="card">
            <h3>Selected Region Features</h3>
            <div className="metric-list">
              <p>Rainfall: {formatScore(inputFeatures.rainfall)} mm</p>
              <p>Temperature: {formatScore(inputFeatures.temperature)} C</p>
              <p>Humidity: {formatScore(inputFeatures.humidity)}%</p>
              <p>Water Level: {formatScore(inputFeatures.water_level)} m</p>
              <p>Soil Moisture: {formatScore(inputFeatures.soil_moisture)}</p>
              <p>Seismic Activity: {formatScore(inputFeatures.seismic_activity)}</p>
            </div>
          </div>
        </div>
      ) : null}

      <div className="grid three-column">
        {THEORY_ITEMS.map((item) => (
          <div className="card theory-card" key={item.title}>
            <h3>{item.title}</h3>
            <p className="body-copy">{item.text}</p>
          </div>
        ))}
      </div>

      <div className="grid two-column">
        <div className="card">
          <h3>Validation Summary</h3>
          {result ? (
            <div className="metric-list">
              <p>Stored Predictions: {result.validation?.total_predictions || 0}</p>
              <p>Accuracy: {formatPercent(result.validation?.accuracy)}</p>
              <p>Precision: {formatPercent(result.validation?.precision)}</p>
              <p>Recall: {formatPercent(result.validation?.recall)}</p>
            </div>
          ) : (
            <p className="body-copy">Run a prediction to see validation metrics.</p>
          )}
        </div>

        <div className="card">
          <h3>Model Summary</h3>
          {modelInfo ? (
            <div className="metric-list">
              <p>Algorithm: {modelInfo.algorithm || modelInfo.model}</p>
              <p>Formula: Final Risk = {modelInfo.formula}</p>
              <p>Training Accuracy: {formatPercent(modelInfo.training_metrics?.accuracy)}</p>
              <p>Training Precision: {formatPercent(modelInfo.training_metrics?.precision)}</p>
              <p>Training Recall: {formatPercent(modelInfo.training_metrics?.recall)}</p>
              <p>Training Rows: {modelInfo.datasets?.rows?.training || 0}</p>
            </div>
          ) : (
            <p className="body-copy">Loading model details...</p>
          )}
        </div>
      </div>
    </section>
  );
}
