export const BASE_URL = "http://127.0.0.1:5050";

async function apiRequest(path, options = {}) {
  try {
    const res = await fetch(`${BASE_URL}${path}`, options);
    if (!res.ok) {
      let message = `API error (${res.status})`;
      try {
        const body = await res.json();
        message = body?.error || body?.message || message;
      } catch {
        // keep fallback message
      }
      throw new Error(message);
    }
    return await res.json();
  } catch (err) {
    console.error("API FAILED:", err);
    throw err;
  }
}

export async function getEarthquakes() {
  return apiRequest("/api/earthquakes");
}

export async function fetchIndiaEarthquakesToDB() {
  return apiRequest("/api/fetch-india");
}

export async function getFloods() {
  return apiRequest("/api/floods");
}

export async function fetchFloodsToDB() {
  return apiRequest("/api/fetch-floods");
}

export async function getLandslides() {
  return apiRequest("/api/landslides");
}

export async function fetchLandslidesToDB() {
  return apiRequest("/api/fetch-landslides");
}

export async function predictDisasterRisk(payload) {
  return apiRequest("/api/predict", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export async function runAlertCheck(payload) {
  return apiRequest("/api/run-alert-check", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export async function getAlerts() {
  return apiRequest("/api/alerts");
}

export async function generateAlerts() {
  return apiRequest("/api/alerts/generate", { method: "POST" });
}

export async function getRiskTrend() {
  return apiRequest("/api/analytics/risk-trend");
}

export async function getDisasterFrequency() {
  return apiRequest("/api/analytics/disaster-frequency");
}

export async function getPredictionConfidenceSeries() {
  return apiRequest("/api/analytics/prediction-confidence");
}

export async function runAutoPredict(disasterType) {
  return apiRequest(`/api/auto-predict/${disasterType}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({}),
  });
}
