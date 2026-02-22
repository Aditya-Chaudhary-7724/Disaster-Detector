export const mockSeismicData = [
  { time: "00:00", magnitude: 2.1, depth: 15 },
  { time: "04:00", magnitude: 2.5, depth: 18 },
  { time: "08:00", magnitude: 1.8, depth: 12 },
  { time: "12:00", magnitude: 3.2, depth: 25 },
  { time: "16:00", magnitude: 2.9, depth: 20 },
  { time: "20:00", magnitude: 2.3, depth: 16 },
];

export const mockRecentEvents = [
  { id: 1, location: "Assam, India", magnitude: 4.2, depth: 10, time: "2 mins ago", severity: "medium" },
  { id: 2, location: "Gujarat, India", magnitude: 3.1, depth: 15, time: "1 hour ago", severity: "low" },
  { id: 3, location: "Arunachal Pradesh, India", magnitude: 5.1, depth: 10, time: "5 hours ago", severity: "high" },
  { id: 4, location: "Andaman, India", magnitude: 4.8, depth: 35, time: "12 hours ago", severity: "medium" },
];

export const mockAlerts = [
  { id: 1, severity: "critical", location: "North East India", time: "10 mins ago", message: "High seismic activity detected. Drop, Cover, Hold.", resolved: false },
  { id: 2, severity: "high", location: "Himalayan Belt", time: "2 hours ago", message: "Moderate earthquake risk. Stay alert.", resolved: false },
  { id: 3, severity: "medium", location: "Gujarat Region", time: "5 hours ago", message: "Increased tremor frequency observed.", resolved: true },
  { id: 4, severity: "low", location: "South India", time: "1 day ago", message: "Minor activity detected. No action required.", resolved: true },
];
