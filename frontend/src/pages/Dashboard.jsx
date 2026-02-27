import React, { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  Activity,
  Waves,
  Mountain,
  Radar,
  ShieldCheck,
  BellRing,
  TrendingUp,
} from "lucide-react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import {
  getEarthquakes,
  getFloods,
  getLandslides,
  getRiskTrend,
  getDisasterFrequency,
  getPredictionConfidenceSeries,
} from "../api/disasterApi";

function StatCard({ title, subtitle, icon: Icon, onClick, rightText }) {
  return (
    <button
      onClick={onClick}
      className="w-full text-left p-5 rounded-2xl border border-white/10 bg-white/5 hover:bg-white/10 transition shadow"
    >
      <div className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-xl bg-white/10">
            <Icon size={20} />
          </div>
          <div>
            <h3 className="text-lg font-semibold">{title}</h3>
            <p className="text-sm text-white/60">{subtitle}</p>
          </div>
        </div>
        {rightText && (
          <div className="text-sm px-3 py-1 rounded-full bg-white/10 text-white/70">
            {rightText}
          </div>
        )}
      </div>
    </button>
  );
}

function MiniBox({ title, value, hint }) {
  return (
    <div className="p-4 rounded-2xl border border-white/10 bg-white/5">
      <p className="text-sm text-white/60">{title}</p>
      <p className="text-2xl font-bold mt-1">{value}</p>
      {hint && <p className="text-xs text-white/50 mt-1">{hint}</p>}
    </div>
  );
}

export default function Dashboard() {
  const nav = useNavigate();

  const [eq, setEq] = useState([]);
  const [floods, setFloods] = useState([]);
  const [landslides, setLandslides] = useState([]);

  const [loading, setLoading] = useState(true);
  const [riskTrend, setRiskTrend] = useState([]);
  const [frequency, setFrequency] = useState([]);
  const [confidenceSeries, setConfidenceSeries] = useState([]);

  useEffect(() => {
    async function loadAll() {
      try {
        setLoading(true);
        const [a, b, c, trend, freq, conf] = await Promise.all([
          getEarthquakes(),
          getFloods(),
          getLandslides(),
          getRiskTrend(),
          getDisasterFrequency(),
          getPredictionConfidenceSeries(),
        ]);
        setEq(Array.isArray(a) ? a : []);
        setFloods(Array.isArray(b) ? b : []);
        setLandslides(Array.isArray(c) ? c : []);
        setRiskTrend(Array.isArray(trend) ? trend : []);
        setFrequency(Array.isArray(freq) ? freq : []);
        setConfidenceSeries(Array.isArray(conf) ? conf : []);
      } catch (e) {
        console.error("Dashboard load error:", e);
      } finally {
        setLoading(false);
      }
    }

    loadAll();
    const t = setInterval(loadAll, 15000);
    return () => clearInterval(t);
  }, []);

  const stats = useMemo(() => {
    const eqToday = eq.filter((x) => Date.now() - x.time < 24 * 60 * 60 * 1000);
    const maxMag = eqToday.reduce((m, x) => Math.max(m, Number(x.magnitude || 0)), 0);

    const floodsToday = floods.filter((x) => Date.now() - (x.time || 0) < 24 * 60 * 60 * 1000);
    const landsToday = landslides.filter((x) => Date.now() - (x.time || 0) < 24 * 60 * 60 * 1000);

    return {
      eqCount: eq.length,
      eqTodayCount: eqToday.length,
      maxMag: maxMag ? maxMag.toFixed(1) : "0.0",
      floodCount: floods.length,
      floodTodayCount: floodsToday.length,
      landsCount: landslides.length,
      landsTodayCount: landsToday.length,
    };
  }, [eq, floods, landslides]);

  return (
    <div className="p-6 text-white">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold">Dashboard</h1>
          <p className="text-white/60 mt-1">
            Disaster monitoring system (Earthquake + Flood + Landslide)
          </p>
        </div>

        <div className="flex items-center gap-2">
          <div className="px-3 py-2 rounded-xl bg-white/5 border border-white/10 text-sm text-white/70">
            {loading ? "Syncing…" : "Live ✅"}
          </div>
        </div>
      </div>

      {/* Top Cards */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 mt-6">
        <StatCard
          title="Earthquakes"
          subtitle="USGS + India region sync"
          icon={Activity}
          onClick={() => nav("/earthquakes")}
          rightText={`${stats.eqTodayCount} today`}
        />
        <StatCard
          title="Floods"
          subtitle="DB stored alerts/events (sync supported)"
          icon={Waves}
          onClick={() => nav("/floods")}
          rightText={`${stats.floodTodayCount} today`}
        />
        <StatCard
          title="Landslides"
          subtitle="DB stored risk events (sync supported)"
          icon={Mountain}
          onClick={() => nav("/landslides")}
          rightText={`${stats.landsTodayCount} today`}
        />
      </div>

      {/* Live Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mt-6">
        <MiniBox title="Earthquakes in DB" value={stats.eqCount} hint="Auto-refresh: 15s" />
        <MiniBox title="Max Magnitude (24h)" value={stats.maxMag} hint="Latest 24 hours" />
        <MiniBox title="Flood Events in DB" value={stats.floodCount} hint="Simulated for now" />
        <MiniBox title="Landslide Events in DB" value={stats.landsCount} hint="Simulated for now" />
      </div>

      {/* System Status + AI Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mt-6">
        <div className="p-6 rounded-2xl border border-white/10 bg-white/5">
          <h2 className="text-xl font-semibold mb-3 flex items-center gap-2">
            <ShieldCheck size={18} /> System Status
          </h2>
          <div className="space-y-2 text-white/80">
            <p>✅ Backend: Flask API</p>
            <p>✅ Frontend: React + Vite + Router</p>
            <p>✅ Auto refresh: supported in each disaster page</p>
            <p className="text-yellow-300">⚠ Mitigation + Alerts AI section coming next 🚀</p>
          </div>
        </div>

        <div className="p-6 rounded-2xl border border-white/10 bg-white/5">
          <h2 className="text-xl font-semibold mb-3 flex items-center gap-2">
            <Radar size={18} /> AI Prediction & Alerts
          </h2>

          <p className="text-white/70 text-sm">
            Your AI module will forecast <b>7-day & 30-day risk</b> using hybrid logic (rules + ML later).
          </p>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mt-4">
            <button
              onClick={() => nav("/predictor")}
              className="p-4 rounded-2xl bg-blue-600 hover:bg-blue-700 transition flex items-center justify-between"
            >
              <div>
                <p className="font-semibold flex items-center gap-2">
                  <TrendingUp size={18} /> Open Predictor
                </p>
                <p className="text-xs text-white/80 mt-1">
                  Forecast risk levels (next 7 / 30 days)
                </p>
              </div>
              <span className="text-sm bg-white/20 px-3 py-1 rounded-full">NEW</span>
            </button>

            <button
              onClick={() => nav("/alerts")}
              className="p-4 rounded-2xl bg-red-600 hover:bg-red-700 transition flex items-center justify-between"
            >
              <div>
                <p className="font-semibold flex items-center gap-2">
                  <BellRing size={18} /> Alerts Center
                </p>
                <p className="text-xs text-white/80 mt-1">
                  Real-time alerts & mitigation actions
                </p>
              </div>
              <span className="text-sm bg-white/20 px-3 py-1 rounded-full">Live</span>
            </button>
          </div>

          <div className="mt-4 p-4 rounded-2xl bg-white/5 border border-white/10 text-sm text-white/70">
            💡 Upcoming: Chain-reaction prediction (Earthquake → Landslide risk), plus notification system
            like “presidential alert” (SMS / Push).
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-4 mt-6">
        <div className="p-4 rounded-2xl border border-white/10 bg-white/5">
          <h3 className="font-semibold mb-2">Risk Trend (7 Days)</h3>
          <div className="h-60">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={riskTrend.slice(-40).map((d) => ({ ...d, t: new Date(d.timestamp).toLocaleDateString() }))}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis dataKey="t" stroke="#CBD5E1" hide />
                <YAxis stroke="#CBD5E1" domain={[0, 100]} />
                <Tooltip />
                <Line dataKey="risk_score" stroke="#38bdf8" dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="p-4 rounded-2xl border border-white/10 bg-white/5">
          <h3 className="font-semibold mb-2">Disaster Frequency</h3>
          <div className="h-60">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={frequency}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis dataKey="name" stroke="#CBD5E1" />
                <YAxis stroke="#CBD5E1" />
                <Tooltip />
                <Bar dataKey="count" fill="#22d3ee" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="p-4 rounded-2xl border border-white/10 bg-white/5">
          <h3 className="font-semibold mb-2">Prediction Confidence</h3>
          <div className="h-60">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={confidenceSeries.slice(-40).map((d) => ({ ...d, t: new Date(d.timestamp).toLocaleDateString() }))}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis dataKey="t" stroke="#CBD5E1" hide />
                <YAxis stroke="#CBD5E1" domain={[0, 1]} />
                <Tooltip />
                <Line dataKey="confidence" stroke="#f97316" dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
}
