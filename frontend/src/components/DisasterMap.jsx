import React, { useEffect } from "react";
import {
  MapContainer,
  TileLayer,
  Marker,
  Popup,
  useMap,
} from "react-leaflet";
import "leaflet/dist/leaflet.css";

import L from "leaflet";

// ✅ FIX: Leaflet marker icon issue in Vite
import markerIcon2x from "leaflet/dist/images/marker-icon-2x.png";
import markerIcon from "leaflet/dist/images/marker-icon.png";
import markerShadow from "leaflet/dist/images/marker-shadow.png";

delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: markerIcon2x,
  iconUrl: markerIcon,
  shadowUrl: markerShadow,
});

// ✅ Small helper: map auto fly to selected coordinate
function FlyTo({ lat, lon }) {
  const map = useMap();

  useEffect(() => {
    if (!lat || !lon) return;
    map.flyTo([lat, lon], 6, { duration: 0.8 });
  }, [lat, lon]);

  return null;
}

export default function DisasterMap({ selected, title = "Live Map" }) {
  const lat = selected?.latitude ?? selected?.lat;
  const lon = selected?.longitude ?? selected?.lon;
  const disaster = (selected?.disaster || selected?.type || title || "").toLowerCase();

  // default center India
  const center = lat && lon ? [lat, lon] : [22.9734, 78.6569];
  const markerIcon = new L.Icon({
    iconUrl: disaster.includes("flood")
      ? "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-blue.png"
      : disaster.includes("landslide")
      ? "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-orange.png"
      : "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-red.png",
    shadowUrl: markerShadow,
    iconSize: [25, 41],
    iconAnchor: [12, 41],
    popupAnchor: [1, -34],
    shadowSize: [41, 41],
  });

  return (
    <div className="bg-white/5 border border-white/10 rounded-xl p-4">
      <h2 className="text-lg font-bold text-white mb-3">{title}</h2>

      <div className="h-[320px] w-full rounded-lg overflow-hidden border border-white/10">
        <MapContainer
          center={center}
          zoom={lat && lon ? 6 : 4}
          scrollWheelZoom={true}
          className="h-full w-full"
        >
          <TileLayer
            attribution='&copy; OpenStreetMap contributors'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />

          {/* ✅ Auto fly when selected changes */}
          {lat && lon && <FlyTo lat={lat} lon={lon} />}

          {/* ✅ Marker (blue locator) */}
          {lat && lon && (
            <Marker position={[lat, lon]} icon={markerIcon}>
              <Popup>
                <div className="text-sm">
                  <p className="font-bold">{selected.place || "Selected Location"}</p>
                  {selected.magnitude !== undefined && (
                    <p>Magnitude: {selected.magnitude}</p>
                  )}
                  {(selected.risk || selected.severity) && <p>Severity: {selected.risk || selected.severity}</p>}
                </div>
              </Popup>
            </Marker>
          )}
        </MapContainer>
      </div>

      {!lat || !lon ? (
        <p className="text-gray-400 text-sm mt-3">
          Click a row from the table to show the marker 📍
        </p>
      ) : (
        <p className="text-green-400 text-sm mt-3">
          Marker updated ✅ ({lat.toFixed(2)}, {lon.toFixed(2)})
        </p>
      )}
    </div>
  );
}
