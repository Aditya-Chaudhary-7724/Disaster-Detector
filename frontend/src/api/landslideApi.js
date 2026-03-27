import { BASE_URL } from "./disasterApi";

export async function getLandslides() {
  try {
    const res = await fetch(`${BASE_URL}/api/landslides`);
    if (!res.ok) throw new Error("Failed to fetch landslides");
    return await res.json();
  } catch (err) {
    console.error("API FAILED:", err);
    throw err;
  }
}

export async function syncLandslides() {
  try {
    const res = await fetch(`${BASE_URL}/api/fetch-landslides`);
    if (!res.ok) throw new Error("Failed to sync landslides");
    return await res.json();
  } catch (err) {
    console.error("API FAILED:", err);
    throw err;
  }
}
