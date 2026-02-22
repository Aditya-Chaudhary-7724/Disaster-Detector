import React, { useState } from "react";
import { CheckCircle, TrendingUp } from "lucide-react";

export default function PredictionPage() {
  const [formData, setFormData] = useState({
    magnitude: "",
    depth_km: "",
    frequency_hz: "",
    p_wave_speed: "",
    s_wave_speed: "",
    station_distance_km: "",
  });

  const [prediction, setPrediction] = useState(null);
  const [loading, setLoading] = useState(false);

  const getRiskRecommendations = (level) => {
    const recommendations = {
      High: [
        "Evacuate to designated safe zones immediately",
        "Alert emergency services and local authorities",
        "Secure heavy furniture and equipment",
        "Prepare emergency supplies and evacuation kit",
      ],
      Medium: ["Stay alert and monitor seismic activity", "Review emergency plan", "Charge devices and keep kit ready"],
      Low: ["Continue normal activities with awareness", "Keep emergency kit accessible", "Stay informed about updates"],
    };
    return recommendations[level] || [];
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    setLoading(true);

    setTimeout(() => {
      const riskScore = Math.random();
      const riskLevel = riskScore > 0.7 ? "High" : riskScore > 0.4 ? "Medium" : "Low";

      setPrediction({
        riskLevel,
        probability: (riskScore * 100).toFixed(1),
        recommendations: getRiskRecommendations(riskLevel),
      });

      setLoading(false);
    }, 1200);
  };

  return (
    <div>
      <h1 className="text-3xl font-bold text-white mb-8">Earthquake Risk Prediction</h1>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <div className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl p-6">
          <h2 className="text-xl font-bold text-white mb-6">Input Seismic Data</h2>

          <form onSubmit={handleSubmit} className="space-y-4">
            {[
              { key: "magnitude", label: "Magnitude", step: "0.1", placeholder: "e.g., 3.5" },
              { key: "depth_km", label: "Depth (km)", step: "0.1", placeholder: "e.g., 25" },
              { key: "frequency_hz", label: "Frequency (Hz)", step: "0.1", placeholder: "e.g., 4.5" },
              { key: "p_wave_speed", label: "P-Wave Speed (km/s)", step: "0.1", placeholder: "e.g., 6.5" },
              { key: "s_wave_speed", label: "S-Wave Speed (km/s)", step: "0.1", placeholder: "e.g., 3.5" },
              { key: "station_distance_km", label: "Station Distance (km)", step: "0.1", placeholder: "e.g., 150" },
            ].map((f) => (
              <div key={f.key}>
                <label className="block text-gray-300 mb-2">{f.label}</label>
                <input
                  type="number"
                  step={f.step}
                  value={formData[f.key]}
                  onChange={(e) => setFormData({ ...formData, [f.key]: e.target.value })}
                  className="w-full px-4 py-2 bg-white/5 border border-white/20 rounded-lg text-white focus:outline-none focus:border-blue-400"
                  placeholder={f.placeholder}
                  required
                />
              </div>
            ))}

            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition font-semibold disabled:opacity-50"
            >
              {loading ? "Analyzing..." : "Predict Risk Level"}
            </button>
          </form>
        </div>

        <div className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl p-6">
          <h2 className="text-xl font-bold text-white mb-6">Prediction Results</h2>

          {!prediction ? (
            <div className="flex flex-col items-center justify-center h-64 text-gray-400">
              <TrendingUp className="w-14 h-14 mb-4" />
              <p>Enter data and click predict</p>
            </div>
          ) : (
            <div>
              <div className="mb-6">
                <h3 className="text-gray-300 mb-2">Risk Level</h3>
                <div
                  className={`text-3xl font-bold p-4 rounded-lg text-center ${
                    prediction.riskLevel === "High"
                      ? "bg-red-500/20 text-red-400 border border-red-500/30"
                      : prediction.riskLevel === "Medium"
                      ? "bg-yellow-500/20 text-yellow-400 border border-yellow-500/30"
                      : "bg-green-500/20 text-green-400 border border-green-500/30"
                  }`}
                >
                  {prediction.riskLevel}
                </div>
              </div>

              <div className="mb-6">
                <h3 className="text-gray-300 mb-2">Probability</h3>
                <div className="bg-white/5 rounded-lg p-4">
                  <span className="text-white font-semibold">{prediction.probability}%</span>
                  <div className="w-full bg-gray-700 rounded-full h-3 mt-2">
                    <div className="h-3 rounded-full bg-blue-500" style={{ width: `${prediction.probability}%` }} />
                  </div>
                </div>
              </div>

              <div>
                <h3 className="text-gray-300 mb-3">Recommended Actions</h3>
                <div className="space-y-2">
                  {prediction.recommendations.map((rec, idx) => (
                    <div key={idx} className="flex items-start gap-3 bg-white/5 p-3 rounded-lg">
                      <CheckCircle className="w-5 h-5 text-blue-400 flex-shrink-0 mt-0.5" />
                      <span className="text-gray-300 text-sm">{rec}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>

      </div>
    </div>
  );
}
