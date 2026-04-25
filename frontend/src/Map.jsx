import React, { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";

import HazardZoneMap from "./HazardZoneMap.jsx";
import { getMapData } from "./api/disasterApi.js";

export default function Map() {
  const [items, setItems] = useState([]);
  const [error, setError] = useState("");
  const [searchParams, setSearchParams] = useSearchParams();

  const disaster = searchParams.get("disaster") || "flood";
  const focusItem = useMemo(() => {
    const lat = searchParams.get("lat");
    const lon = searchParams.get("lon");
    if (!lat || !lon) {
      return null;
    }
    return {
      lat: Number(lat),
      lon: Number(lon),
      label: searchParams.get("label") || "Selected Location",
      region: searchParams.get("region") || "",
      value: searchParams.get("value") || "",
      disaster,
    };
  }, [disaster, searchParams]);

  useEffect(() => {
    async function loadMapData() {
      try {
        const response = await getMapData(disaster);
        setItems(response.items || []);
      } catch (err) {
        setError(err.message || "Unable to load map data.");
      }
    }

    loadMapData();
  }, [disaster]);

  return (
    <section className="page">
      <div className="page-header">
        <div>
          <p className="eyebrow">Interactive Map View</p>
          <h2>Map</h2>
          <p className="page-copy">
            Select a disaster type or open a record from Live Data to zoom directly to the chosen location.
          </p>
        </div>
      </div>

      {error ? <div className="premium-card error-text">{error}</div> : null}

      <div className="premium-card form-card map-filter-card">
        <label className="field">
          <span>Disaster Type</span>
          <select value={disaster} onChange={(event) => setSearchParams({ disaster: event.target.value })}>
            <option value="flood">Flood</option>
            <option value="earthquake">Earthquake</option>
            <option value="landslide">Landslide</option>
          </select>
        </label>
      </div>

      <div className="premium-card map-panel">
        <HazardZoneMap disaster={disaster} zones={items} focusItem={focusItem} className="leaflet-map" />
      </div>

      <div className="grid three-column">
        {items.map((item) => (
          <div className="premium-card" key={item.id}>
            <h3>{item.zone_name}</h3>
            <p className="body-copy">{item.region}</p>
            <p className="metric">Risk Score: {Number(item.risk_score).toFixed(2)}</p>
            <span className={`risk-badge ${String(item.risk_level).toLowerCase()}`}>{item.risk_level}</span>
          </div>
        ))}
      </div>
    </section>
  );
}
