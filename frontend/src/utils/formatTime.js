export function formatTime(ms) {
  if (!ms) return "Unknown";
  const d = new Date(ms);
  return d.toLocaleString();
}
