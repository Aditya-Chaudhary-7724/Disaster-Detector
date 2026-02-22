export async function getFloods() {
  const res = await fetch("/api/floods");
  if (!res.ok) throw new Error("Failed to fetch floods");
  return res.json();
}

export async function syncFloods() {
  const res = await fetch("/api/fetch-floods");
  if (!res.ok) throw new Error("Failed to sync floods");
  return res.json();
}
