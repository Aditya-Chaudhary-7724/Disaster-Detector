import { BASE_URL } from "./disasterApi";

export async function getFloods() {
  try {
    const res = await fetch(`${BASE_URL}/api/floods`);
    if (!res.ok) throw new Error("Failed to fetch floods");
    return await res.json();
  } catch (err) {
    console.error("API FAILED:", err);
    throw err;
  }
}

export async function syncFloods() {
  try {
    const res = await fetch(`${BASE_URL}/api/fetch-floods`);
    if (!res.ok) throw new Error("Failed to sync floods");
    return await res.json();
  } catch (err) {
    console.error("API FAILED:", err);
    throw err;
  }
}
