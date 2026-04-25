import React, { useEffect, useMemo } from "react";
import { Circle, CircleMarker, MapContainer, Popup, TileLayer, useMap } from "react-leaflet";
import "leaflet/dist/leaflet.css";

function zoneStyle(level) {
  if (level === "High") {
    return { color: "#a84f5b", fillColor: "#cc7b86", fillOpacity: 0.34 };
  }
  if (level === "Medium") {
    return { color: "#9f8747", fillColor: "#d8c27a", fillOpacity: 0.28 };
  }
  return { color: "#517a63", fillColor: "#81a88c", fillOpacity: 0.24 };
}

function FocusController({ focusItem, disaster, zones }) {
  const map = useMap();

  useEffect(() => {
    if (focusItem?.lat && focusItem?.lon) {
      map.setView([Number(focusItem.lat), Number(focusItem.lon)], 7, { animate: true });
      return;
    }

    if (zones.length > 0) {
      const avgLat = zones.reduce((sum, zone) => sum + zone.lat, 0) / zones.length;
      const avgLon = zones.reduce((sum, zone) => sum + zone.lon, 0) / zones.length;
      map.setView([avgLat, avgLon], 5, { animate: true });
      return;
    }

    map.setView([22.9734, 78.6569], 5, { animate: true });
  }, [map, focusItem, disaster, zones]);

  return null;
}

export default function HazardZoneMap({ disaster, zones, focusItem, className = "leaflet-map", heightClass = "" }) {
  const center = useMemo(() => {
    if (focusItem?.lat && focusItem?.lon) {
      return [Number(focusItem.lat), Number(focusItem.lon)];
    }
    if (!zones.length) {
      return [22.9734, 78.6569];
    }
    const avgLat = zones.reduce((sum, zone) => sum + zone.lat, 0) / zones.length;
    const avgLon = zones.reduce((sum, zone) => sum + zone.lon, 0) / zones.length;
    return [avgLat, avgLon];
  }, [focusItem, zones]);

  return (
    <MapContainer key={`${disaster}-${focusItem?.lat || "base"}-${focusItem?.lon || "base"}`} center={center} zoom={5} scrollWheelZoom className={`${className} ${heightClass}`.trim()}>
      <TileLayer
        attribution='&copy; OpenStreetMap contributors'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      <FocusController focusItem={focusItem} disaster={disaster} zones={zones} />

      {zones.map((zone) => (
        <Circle
          key={zone.id}
          center={[zone.lat, zone.lon]}
          radius={zone.radius_km * 1000}
          pathOptions={zoneStyle(zone.risk_level)}
        >
          <Popup>
            <strong>{zone.zone_name}</strong>
            <br />
            Region: {zone.region}
            <br />
            Risk Level: {zone.risk_level}
            <br />
            Risk Score: {Number(zone.risk_score).toFixed(2)}
          </Popup>
        </Circle>
      ))}

      {focusItem?.lat && focusItem?.lon ? (
        <CircleMarker
          center={[Number(focusItem.lat), Number(focusItem.lon)]}
          radius={10}
          pathOptions={{ color: "#bfdbfe", fillColor: "#60a5fa", fillOpacity: 0.85 }}
        >
          <Popup>
            <strong>{focusItem.label || "Selected Location"}</strong>
            <br />
            Disaster: {focusItem.disaster || disaster}
            <br />
            {focusItem.region ? `Region: ${focusItem.region}` : null}
            {focusItem.value ? (
              <>
                <br />
                {focusItem.value}
              </>
            ) : null}
          </Popup>
        </CircleMarker>
      ) : null}
    </MapContainer>
  );
}
