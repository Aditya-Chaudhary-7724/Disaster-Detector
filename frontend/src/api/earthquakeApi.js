import { BASE_URL } from "./disasterApi";

export async function getEarthquakes() {
  try {
    const res = await fetch(`${BASE_URL}/api/earthquakes`);
    if (!res.ok) throw new Error("HTTP error " + res.status);
    return await res.json();
  } catch (err) {
    console.error("API FAILED:", err);
    throw err;
  }
}

export async function fetchIndiaEarthquakesToDB() {
  try {
    const res = await fetch(`${BASE_URL}/api/fetch-india`);
    if (!res.ok) throw new Error("Sync failed: " + res.status);
    return await res.json();
  } catch (err) {
    console.error("API FAILED:", err);
    throw err;
  }
}
