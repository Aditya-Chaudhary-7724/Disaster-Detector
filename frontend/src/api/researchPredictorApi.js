export async function predictResearchRisk(payload) {
  const res = await fetch('/api/research/predict', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });

  const body = await res.json();
  if (!res.ok) {
    throw new Error(body.error || 'Research prediction failed');
  }
  return body;
}

export async function fetchResearchDatasetSummary() {
  const res = await fetch('/api/research/dataset-summary');
  const body = await res.json();
  if (!res.ok) {
    throw new Error(body.error || 'Failed to load research charts');
  }
  return body;
}
