import React, { useEffect, useState } from "react";
import { Activity, BarChart3, Gauge } from "lucide-react";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { getPerformanceSnapshot } from "../api/disasterApi";

export default function PerformanceDashboard() {
  const [data, setData] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    getPerformanceSnapshot()
      .then(setData)
      .catch((err) => setError(err.message || "Failed to load performance dashboard"));
  }, []);

  const hybrid = data?.models?.hybrid_ml || {};
  const metrics = data?.system_metrics || {};
  const chartData = [
    { name: "Accuracy", value: Number(hybrid.accuracy || 0) * 100 },
    { name: "Precision", value: Number(hybrid.precision || 0) * 100 },
    { name: "Recall", value: Number(hybrid.recall || 0) * 100 },
  ];

  return (
    <div className="p-6 text-white space-y-6">
      <div>
        <h1 className="text-3xl font-bold flex items-center gap-2">
          <BarChart3 size={30} /> Performance Dashboard
        </h1>
        <p className="text-gray-400">Model quality, system throughput, and backend prediction activity in one place.</p>
      </div>

      {error && <p className="text-red-400">{error}</p>}

      <div className="grid md:grid-cols-4 gap-4">
        <MetricCard title="Predictions" value={metrics.prediction_count ?? 0} icon={Activity} />
        <MetricCard title="Alerts" value={metrics.alert_count ?? 0} icon={Gauge} />
        <MetricCard title="Failures" value={metrics.failure_count ?? 0} icon={Activity} />
        <MetricCard title="Rows Trained" value={hybrid.dataset_rows ?? 0} icon={BarChart3} />
      </div>

      <div className="grid xl:grid-cols-[1.15fr,0.85fr] gap-4">
        <div className="rounded-2xl border border-white/10 bg-white/5 p-5">
          <h2 className="text-xl font-semibold mb-4">Hybrid Model Quality</h2>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis dataKey="name" stroke="#CBD5E1" />
                <YAxis stroke="#CBD5E1" domain={[0, 100]} />
                <Tooltip />
                <Bar dataKey="value" fill="#22d3ee" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="rounded-2xl border border-white/10 bg-white/5 p-5 space-y-3">
          <h2 className="text-xl font-semibold">Model Details</h2>
          <Info label="Hybrid Accuracy" value={`${(Number(hybrid.accuracy || 0) * 100).toFixed(1)}%`} />
          <Info label="Hybrid Precision" value={`${(Number(hybrid.precision || 0) * 100).toFixed(1)}%`} />
          <Info label="Hybrid Recall" value={`${(Number(hybrid.recall || 0) * 100).toFixed(1)}%`} />
          <Info label="Satellite Accuracy" value={data?.models?.satellite_model?.accuracy != null ? `${(Number(data.models.satellite_model.accuracy) * 100).toFixed(1)}%` : "N/A"} />
          <Info label="CNN Accuracy" value={data?.models?.cnn_model?.accuracy != null ? `${(Number(data.models.cnn_model.accuracy) * 100).toFixed(1)}%` : "Heuristic / N/A"} />
        </div>
      </div>
    </div>
  );
}

function MetricCard({ title, value, icon: Icon }) {
  return (
    <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
      <div className="flex items-center gap-3">
        <div className="rounded-xl bg-white/10 p-2">
          <Icon size={18} />
        </div>
        <div>
          <p className="text-sm text-gray-400">{title}</p>
          <p className="text-2xl font-bold">{value}</p>
        </div>
      </div>
    </div>
  );
}

function Info({ label, value }) {
  return (
    <div className="rounded-xl border border-white/10 bg-black/20 p-3">
      <p className="text-gray-400">{label}</p>
      <p className="font-semibold mt-1">{value}</p>
    </div>
  );
}
