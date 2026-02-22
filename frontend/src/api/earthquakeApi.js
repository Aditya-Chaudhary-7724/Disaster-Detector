export async function getEarthquakes() {
  const res = await fetch("/api/earthquakes");
  if (!res.ok) throw new Error("HTTP error " + res.status);
  return res.json();
}

export async function fetchIndiaEarthquakesToDB() {
  const res = await fetch("/api/fetch-india");
  if (!res.ok) throw new Error("Sync failed: " + res.status);
  return res.json();
}
