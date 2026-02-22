import React, { useEffect } from "react";
import {
  MapContainer,
  TileLayer,
  Marker,
  Popup,
  useMap,
} from "react-leaflet";
import L from "leaflet";

// ✅ Fix marker icon
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl:
    "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
  iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
  shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
});

function FixMapResize() {
  const map = useMap();

  useEffect(() => {
    const t = setTimeout(() => {
      map.invalidateSize();
    }, 200);

    return () => clearTimeout(t);
  }, [map]);

  return null;
}

function MapFocus({ selected }) {
  const map = useMap();

  useEffect(() => {
    if (selected?.latitude && selected?.longitude) {
      map.setView([selected.latitude, selected.longitude], 6, {
        animate: true,
      });
    }
  }, [selected, map]);

  return null;
}

export default function EarthquakeMap({ data = [], selected }) {
  const defaultCenter = [22.5, 79];

  return (
    <div className="w-full h-[360px] rounded-xl overflow-hidden border border-white/10 bg-white/5">
      <MapContainer
        center={defaultCenter}
        zoom={5}
        style={{ height: "100%", width: "100%" }}
        scrollWheelZoom={false}
      >
        <FixMapResize />
        <TileLayer
          attribution='&copy; OpenStreetMap contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        <MapFocus selected={selected} />

        {data.map((q) => (
          <Marker key={q.id} position={[q.latitude, q.longitude]}>
            <Popup>
              <div className="text-sm">
                <p className="font-bold">{q.place}</p>
                <p>Magnitude: {q.magnitude}</p>
                <p>Depth: {q.depth} km</p>
                <p className="text-gray-500">
                  {new Date(q.time).toLocaleString()}
                </p>
              </div>
            </Popup>
          </Marker>
        ))}
      </MapContainer>
    </div>
  );
}
