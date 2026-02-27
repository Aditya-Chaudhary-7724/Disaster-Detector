import React, { useMemo, useState } from "react";
import { AlertTriangle, Ambulance, Flame, Phone, ShieldCheck } from "lucide-react";

const ADVICE = {
  earthquake: {
    Low: ["Secure heavy furniture.", "Review household emergency kit.", "Practice drop-cover-hold drills."],
    Medium: ["Move away from windows and hanging objects.", "Keep power bank and emergency radio charged.", "Identify nearest open evacuation point."],
    High: ["Evacuate unsafe structures immediately.", "Follow district disaster authority broadcasts.", "Do not use elevators; assist vulnerable people first."],
  },
  flood: {
    Low: ["Monitor local rain forecast.", "Keep drainage paths clear.", "Store documents in waterproof covers."],
    Medium: ["Move vehicles to higher elevation.", "Prepare 24-hour emergency supplies.", "Avoid crossing waterlogged roads."],
    High: ["Evacuate to higher ground now.", "Switch off main electricity if water enters premises.", "Avoid all road travel in floodplains."],
  },
  landslide: {
    Low: ["Inspect slope drains and retaining walls.", "Avoid unnecessary slope cutting.", "Track rainfall accumulation."],
    Medium: ["Watch for fresh cracks or tilted trees.", "Prepare rapid evacuation bags.", "Restrict movement near steep embankments."],
    High: ["Evacuate slope-facing homes immediately.", "Avoid valleys/channels with active debris flow.", "Follow geologist/authority evacuation orders."],
  },
};

const RESPONSE_NODES = [
  { name: "District Emergency Operations Center", lat: 28.61, lon: 77.21 },
  { name: "National Disaster Response Unit", lat: 19.07, lon: 72.88 },
  { name: "Regional Medical Rapid Team", lat: 22.57, lon: 88.36 },
  { name: "State Fire & Rescue HQ", lat: 13.08, lon: 80.27 },
];

function nearestService(lat, lon) {
  let best = RESPONSE_NODES[0];
  let bestD = Number.POSITIVE_INFINITY;
  for (const node of RESPONSE_NODES) {
    const d = Math.hypot(lat - node.lat, lon - node.lon);
    if (d < bestD) {
      bestD = d;
      best = node;
    }
  }
  return `${best.name} (mock distance index: ${bestD.toFixed(2)})`;
}

export default function Mitigation() {
  const [disaster, setDisaster] = useState("flood");
  const [severity, setSeverity] = useState("Medium");
  const [lat, setLat] = useState(26.14);
  const [lon, setLon] = useState(91.73);

  const tips = ADVICE[disaster][severity];
  const isHigh = severity === "High";
  const nearest = useMemo(() => nearestService(Number(lat), Number(lon)), [lat, lon]);

  return (
    <div className="p-6 text-white space-y-6">
      <div className="flex items-center gap-3">
        <ShieldCheck className="w-8 h-8 text-green-400" />
        <h1 className="text-3xl font-bold">Smart Mitigation & Emergency Response</h1>
      </div>

      <div className="bg-white/5 border border-white/10 rounded-2xl p-5 grid md:grid-cols-4 gap-4">
        <label className="block">
          <span className="text-sm text-gray-300">Disaster</span>
          <select value={disaster} onChange={(e) => setDisaster(e.target.value)} className="mt-1 w-full bg-black/30 border border-white/10 rounded-lg px-3 py-2">
            <option value="earthquake">Earthquake</option>
            <option value="flood">Flood</option>
            <option value="landslide">Landslide</option>
          </select>
        </label>

        <label className="block">
          <span className="text-sm text-gray-300">Severity</span>
          <select value={severity} onChange={(e) => setSeverity(e.target.value)} className="mt-1 w-full bg-black/30 border border-white/10 rounded-lg px-3 py-2">
            <option value="Low">Low</option>
            <option value="Medium">Medium</option>
            <option value="High">High</option>
          </select>
        </label>

        <label className="block">
          <span className="text-sm text-gray-300">Latitude</span>
          <input value={lat} onChange={(e) => setLat(e.target.value)} className="mt-1 w-full bg-black/30 border border-white/10 rounded-lg px-3 py-2" />
        </label>

        <label className="block">
          <span className="text-sm text-gray-300">Longitude</span>
          <input value={lon} onChange={(e) => setLon(e.target.value)} className="mt-1 w-full bg-black/30 border border-white/10 rounded-lg px-3 py-2" />
        </label>
      </div>

      <div className={`rounded-2xl p-5 border ${isHigh ? "bg-red-500/10 border-red-500/30" : "bg-white/5 border-white/10"}`}>
        <h2 className="text-xl font-bold flex items-center gap-2">
          <AlertTriangle className={isHigh ? "text-red-300" : "text-yellow-300"} />
          Severity-Based Action Plan ({severity})
        </h2>
        <ul className="list-disc ml-5 mt-3 text-gray-200 space-y-2">
          {tips.map((tip, i) => (
            <li key={i}>{tip}</li>
          ))}
        </ul>

        {isHigh && (
          <div className="mt-4 p-4 rounded-xl bg-red-500/20 border border-red-400/30">
            <p className="font-semibold text-red-200">Immediate High-Risk Protocol</p>
            <p className="text-red-100 mt-1">Evacuation is recommended. Nearest response service (mock geo): {nearest}</p>
          </div>
        )}
      </div>

      <div className="bg-white/5 border border-white/10 rounded-2xl p-5">
        <h2 className="text-xl font-bold mb-3">Emergency Contact Panel</h2>
        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-3">
          <ContactCard title="Police" number="100" icon={ShieldCheck} color="bg-blue-600" />
          <ContactCard title="Ambulance" number="108" icon={Ambulance} color="bg-green-600" />
          <ContactCard title="Fire Dept" number="101" icon={Flame} color="bg-orange-600" />
          <ContactCard title="Disaster Helpline" number="112" icon={Phone} color="bg-red-600" />
        </div>
      </div>
    </div>
  );
}

function ContactCard({ title, number, icon: Icon, color }) {
  return (
    <div className="rounded-xl border border-white/10 bg-black/20 p-4">
      <div className="flex items-center justify-between mb-3">
        <p className="font-semibold">{title}</p>
        <span className={`p-2 rounded-lg ${color}`}><Icon size={16} /></span>
      </div>
      <a href={`tel:${number}`} className="text-lg font-bold text-cyan-300 hover:underline">
        {number}
      </a>
    </div>
  );
}
