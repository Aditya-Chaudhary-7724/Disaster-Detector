export async function getEarthquakes() {
  const res = await fetch("/api/earthquakes");
  if (!res.ok) throw new Error("Failed to fetch earthquakes");
  return res.json();
}

export async function fetchIndiaEarthquakesToDB() {
  const res = await fetch("/api/fetch-india");
  if (!res.ok) throw new Error("Failed to sync earthquakes");
  return res.json();
}

// Floods
export async function getFloods() {
  const res = await fetch("/api/floods");
  if (!res.ok) throw new Error("Failed to fetch floods");
  return res.json();
}

export async function fetchFloodsToDB() {
  const res = await fetch("/api/fetch-floods");
  if (!res.ok) throw new Error("Failed to sync floods");
  return res.json();
}

// Landslides
export async function getLandslides() {
  const res = await fetch("/api/landslides");
  if (!res.ok) throw new Error("Failed to fetch landslides");
  return res.json();
}

export async function fetchLandslidesToDB() {
  const res = await fetch("/api/fetch-landslides");
  if (!res.ok) throw new Error("Failed to sync landslides");
  return res.json();
}

// Predictor
export async function predictDisasterRisk(payload) {
  const res = await fetch("/api/predict", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!res.ok) throw new Error("Prediction failed");
  return res.json();
}

// Auto Alerts
export async function runAlertCheck(payload) {
  const res = await fetch("/api/run-alert-check", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!res.ok) throw new Error("Alert check failed");
  return res.json();
}

export async function getAlerts() {
  const res = await fetch("/api/alerts");
  if (!res.ok) throw new Error("Failed to fetch alerts");
  return res.json();
}
