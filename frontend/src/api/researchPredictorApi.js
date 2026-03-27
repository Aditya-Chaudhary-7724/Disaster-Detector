import { BASE_URL } from "./disasterApi";

export async function predictResearchRisk(payload) {
  try {
    const res = await fetch(`${BASE_URL}/api/research/predict`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    const body = await res.json();
    if (!res.ok) {
      throw new Error(body.error || "Research prediction failed");
    }
    return body;
  } catch (err) {
    console.error("API FAILED:", err);
    throw err;
  }
}

export async function fetchResearchDatasetSummary() {
  try {
    const res = await fetch(`${BASE_URL}/api/research/dataset-summary`);
    const body = await res.json();
    if (!res.ok) {
      throw new Error(body.error || "Failed to load research charts");
    }
    return body;
  } catch (err) {
    console.error("API FAILED:", err);
    throw err;
  }
}
