const configuredUrl = import.meta.env.VITE_API_URL?.trim() || "";
export const BASE_URL = configuredUrl || "http://127.0.0.1:5050";

async function apiRequest(path, options = {}) {
  const response = await fetch(`${BASE_URL}${path}`, options);
  if (!response.ok) {
    let message = `API error (${response.status})`;
    try {
      const body = await response.json();
      message = body.error || body.message || message;
    } catch {
      // Keep fallback message.
    }
    throw new Error(message);
  }
  return response.json();
}

export function getRegions() {
  return apiRequest("/api/regions");
}
export function getDashboardData(disaster = "flood") {
  return apiRequest(`/api/dashboard?disaster=${encodeURIComponent(disaster)}`);
}

export function getMapData(disaster = "flood") {
  return apiRequest(`/api/map?disaster=${encodeURIComponent(disaster)}`);
}

export function getDisasterData(disaster) {
  const routeMap = {
    earthquake: "/api/earthquakes",
    flood: "/api/floods",
    landslide: "/api/landslides",
  };
  return apiRequest(routeMap[disaster]);
}

export function predictDisasterRisk(payload) {
  return apiRequest("/api/predict", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export function getAlerts() {
  return apiRequest("/api/alerts");
}

export function generateAlerts() {
  return apiRequest("/api/alerts/generate", { method: "POST" });
}

export function getValidationMetrics() {
  return apiRequest("/api/validation");
}

export function getMitigationGuidance() {
  return apiRequest("/api/mitigation");
}

export function getModelInfo() {
  return apiRequest("/api/model-info");
}
