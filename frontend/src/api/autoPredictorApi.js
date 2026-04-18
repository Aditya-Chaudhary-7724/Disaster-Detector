import { BASE_URL } from "./disasterApi";

async function parseResponse(res, fallbackMessage) {
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.error || err.message || fallbackMessage);
  }
  return res.json();
}

export async function runAutomaticPrediction() {
  try {
    const res = await fetch(`${BASE_URL}/api/auto-predict`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({}),
    });
    return await parseResponse(res, "Automatic prediction failed");
  } catch (err) {
    console.error("API FAILED:", err);
    throw err;
  }
}

export async function runAutoPrediction(disasterType) {
  try {
    const res = await fetch(`${BASE_URL}/api/auto-predict/${disasterType}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({}),
    });
    return await parseResponse(res, "Auto prediction failed");
  } catch (err) {
    console.error("API FAILED:", err);
    throw err;
  }
}

export async function runSatellitePrediction(disasterType) {
  try {
    const res = await fetch(`${BASE_URL}/api/satellite-predict`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ disaster_type: disasterType }),
    });
    return await parseResponse(res, "Satellite prediction failed");
  } catch (err) {
    console.error("API FAILED:", err);
    throw err;
  }
}

export async function runSpatialAutoPrediction(disasterType, options = {}) {
  const params = new URLSearchParams();
  if (options.method) params.set("method", options.method);
  if (options.k) params.set("k", String(options.k));
  const query = params.toString() ? `?${params.toString()}` : "";

  try {
    const res = await fetch(`${BASE_URL}/api/auto-predict-spatial/${disasterType}${query}`);
    if (!res.ok) {
      const text = await res.text().catch(() => "");
      let detail = "";
      try {
        const parsed = JSON.parse(text || "{}");
        detail = parsed.error || parsed.message || "";
      } catch {
        detail = text ? text.slice(0, 160) : "";
      }
      throw new Error(`Spatial auto prediction failed (${res.status})${detail ? `: ${detail}` : ""}`);
    }
    return await res.json();
  } catch (err) {
    console.error("API FAILED:", err);
    throw err;
  }
}
