export async function getLandslides() {
  const res = await fetch("/api/landslides");
  if (!res.ok) throw new Error("Failed to fetch landslides");
  return res.json();
}

export async function syncLandslides() {
  const res = await fetch("/api/fetch-landslides");
  if (!res.ok) throw new Error("Failed to sync landslides");
  return res.json();
}
