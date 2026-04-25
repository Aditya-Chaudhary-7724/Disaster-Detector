import React, { useEffect, useMemo, useState } from "react";
import { MapPinned } from "lucide-react";
import { useNavigate } from "react-router-dom";

import { getDisasterData } from "./api/disasterApi.js";

function normalizeRecords(records, disaster) {
  return (records || []).map((item) => ({
    id: item.id,
    disaster,
    location: item.place || item.location || item.zone_name || item.region || "Unknown",
    region: item.region || item.place || "Unknown",
    lat: item.latitude ?? item.lat,
    lon: item.longitude ?? item.lon,
    timestamp: item.timestamp,
    risk: item.risk_level || item.risk || "Unknown",
    value:
      disaster === "earthquake"
        ? Number(item.magnitude || item.seismic_activity || 0).toFixed(2)
        : disaster === "flood"
        ? `${Number(item.rainfall || 0).toFixed(0)} mm`
        : Number(item.risk_score || item.soil_moisture || 0).toFixed(2),
    valueLabel: disaster === "earthquake" ? "Magnitude" : disaster === "flood" ? "Rainfall" : "Risk",
  }));
}

function buildMapLink(record) {
  const params = new URLSearchParams({
    disaster: record.disaster,
    lat: String(record.lat),
    lon: String(record.lon),
    label: record.location,
    region: record.region,
    value: `${record.valueLabel}: ${record.value}`,
  });
  return `/map?${params.toString()}`;
}

export default function LiveData() {
  const [records, setRecords] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const navigate = useNavigate();

  useEffect(() => {
    async function loadRecords() {
      try {
        setLoading(true);
        const [earthquakes, floods, landslides] = await Promise.all([
          getDisasterData("earthquake"),
          getDisasterData("flood"),
          getDisasterData("landslide"),
        ]);

        const merged = [
          ...normalizeRecords(earthquakes, "earthquake"),
          ...normalizeRecords(floods, "flood"),
          ...normalizeRecords(landslides, "landslide"),
        ].sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));

        setRecords(merged.slice(0, 15));
      } catch (err) {
        setError(err.message || "Unable to load live disaster data.");
      } finally {
        setLoading(false);
      }
    }

    loadRecords();
  }, []);

  const mobileRecords = useMemo(() => records, [records]);

  return (
    <section className="page">
      <div className="page-header">
        <div>
          <p className="eyebrow">Interactive API Data</p>
          <h2>Live Data</h2>
          <p className="page-copy">
            Click any record to open the map, zoom to the selected location, and inspect the related disaster data.
          </p>
        </div>
      </div>

      {error ? <div className="premium-card error-text">{error}</div> : null}

      <div className="premium-card desktop-table-card">
        <h3>Latest Disaster Records</h3>
        {loading ? <div className="skeleton-card tall" /> : null}
        {!loading ? (
          <div className="table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Disaster</th>
                  <th>Location</th>
                  <th>Latitude / Longitude</th>
                  <th>Magnitude / Rainfall / Risk</th>
                  <th>Date &amp; Time</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {records.map((record) => (
                  <tr key={`${record.disaster}-${record.id}`}>
                    <td className="capitalize-text">{record.disaster}</td>
                    <td>{record.location}</td>
                    <td>
                      {Number(record.lat).toFixed(3)}, {Number(record.lon).toFixed(3)}
                    </td>
                    <td>
                      {record.valueLabel}: {record.value}
                    </td>
                    <td>{new Date(record.timestamp).toLocaleString()}</td>
                    <td>
                      <button
                        type="button"
                        className="secondary-button compact-button"
                        onClick={() => navigate(buildMapLink(record))}
                      >
                        <MapPinned size={15} />
                        View on Map
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : null}
      </div>

      <div className="mobile-record-list">
        {mobileRecords.map((record) => (
          <button
            type="button"
            className="data-card mobile-record-card"
            key={`mobile-${record.disaster}-${record.id}`}
            onClick={() => navigate(buildMapLink(record))}
          >
            <div className="card-topline">
              <span className="pill-label">{record.disaster}</span>
              <span className={`risk-badge ${String(record.risk).toLowerCase()}`}>{record.risk}</span>
            </div>
            <p className="list-title">{record.location}</p>
            <p className="metric">
              {Number(record.lat).toFixed(3)}, {Number(record.lon).toFixed(3)}
            </p>
            <p className="metric">
              {record.valueLabel}: {record.value}
            </p>
            <p className="body-copy">{new Date(record.timestamp).toLocaleString()}</p>
          </button>
        ))}
      </div>
    </section>
  );
}
