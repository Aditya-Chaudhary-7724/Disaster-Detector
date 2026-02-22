import React from "react";
import { ShieldCheck } from "lucide-react";

export default function Mitigation() {
  const tips = [
    { title: "Earthquake", points: ["Drop, Cover, Hold", "Stay away from glass/windows", "Keep emergency kit ready"] },
    { title: "Flood", points: ["Move to higher ground", "Avoid driving through water", "Keep documents waterproof"] },
    { title: "Landslide", points: ["Avoid steep slopes during heavy rain", "Watch for cracks in ground", "Evacuate if warnings issued"] },
  ];

  return (
    <div className="p-6 text-white">
      <div className="flex items-center gap-3 mb-6">
        <ShieldCheck className="w-8 h-8 text-green-400" />
        <h1 className="text-3xl font-bold">Mitigation & Safety Guide</h1>
      </div>

      <p className="text-gray-400 mb-8">
        These are recommended actions to reduce risk and improve safety during disasters.
      </p>

      <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
        {tips.map((t, idx) => (
          <div key={idx} className="bg-white/5 border border-white/10 rounded-xl p-6 hover:bg-white/10 transition">
            <h2 className="text-xl font-bold mb-3">{t.title}</h2>
            <ul className="list-disc ml-5 text-gray-300 space-y-2">
              {t.points.map((p, i) => (
                <li key={i}>{p}</li>
              ))}
            </ul>
          </div>
        ))}
      </div>

      <div className="mt-8 bg-blue-600/10 border border-blue-500/20 rounded-xl p-6">
        <h2 className="text-xl font-bold mb-2 text-blue-300">Next Upgrade ✅</h2>
        <p className="text-gray-300">
          We will later connect this to real-time alerts + auto generated mitigation checklist for each warning level.
        </p>
      </div>
    </div>
  );
}
