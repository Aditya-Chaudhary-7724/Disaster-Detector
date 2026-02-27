import React, { useEffect, useMemo, useState } from 'react';
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';

import {
  fetchResearchDatasetSummary,
  predictResearchRisk,
} from '../api/researchPredictorApi';

const LEVEL_STYLES = {
  Low: 'text-green-300 bg-green-500/20 border-green-400/40',
  Medium: 'text-yellow-300 bg-yellow-500/20 border-yellow-400/40',
  High: 'text-red-300 bg-red-500/20 border-red-400/40',
};

const PIE_COLORS = ['#3b82f6', '#14b8a6', '#f59e0b'];

const INITIAL_FORM = {
  disaster_type: 'flood',
  seismic_mag: 2.5,
  depth_km: 25,
  rainfall_24h_mm: 90,
  soil_moisture: 0.62,
  slope_deg: 12,
  ndvi: 0.52,
  plant_density: 0.55,
  past_event_count: 4,
};

export default function ResearchPredictor() {
  const [form, setForm] = useState(INITIAL_FORM);
  const [prediction, setPrediction] = useState(null);
  const [summary, setSummary] = useState(null);
  const [loadingPredict, setLoadingPredict] = useState(false);
  const [loadingCharts, setLoadingCharts] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    async function loadCharts() {
      try {
        const data = await fetchResearchDatasetSummary();
        setSummary(data);
      } catch (err) {
        setError(err.message || 'Failed to load research chart data');
      } finally {
        setLoadingCharts(false);
      }
    }

    loadCharts();
  }, []);

  const contributionRows = useMemo(() => {
    if (!prediction?.contributions) return [];

    return Object.entries(prediction.contributions)
      .map(([feature, value]) => ({
        feature,
        contribution: Number(value),
      }))
      .sort((a, b) => b.contribution - a.contribution);
  }, [prediction]);

  const timeseries = summary?.risk_score_timeseries || [];
  const frequency = summary?.frequency_distribution || [];

  const onChange = (event) => {
    const { name, value } = event.target;
    setForm((prev) => ({
      ...prev,
      [name]: ['disaster_type'].includes(name) ? value : Number(value),
    }));
  };

  const onPredict = async () => {
    setError('');
    setLoadingPredict(true);
    try {
      const result = await predictResearchRisk(form);
      setPrediction(result);
    } catch (err) {
      setError(err.message || 'Prediction request failed');
    } finally {
      setLoadingPredict(false);
    }
  };

  return (
    <div className="p-6 text-white space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Research Predictor</h1>
        <p className="text-white/70 mt-1">
          Hybrid risk inference (rule-based + ML-ready features) for multi-hazard analysis.
        </p>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        <section className="bg-white/5 border border-white/10 rounded-2xl p-5 space-y-4">
          <h2 className="text-xl font-semibold">Input Parameters</h2>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <FieldSelect label="Disaster Type" name="disaster_type" value={form.disaster_type} onChange={onChange} options={['earthquake', 'flood', 'landslide']} />
            <Field label="Seismic Magnitude" name="seismic_mag" value={form.seismic_mag} onChange={onChange} step="0.1" />
            <Field label="Depth (km)" name="depth_km" value={form.depth_km} onChange={onChange} step="0.1" />
            <Field label="Rainfall 24h (mm)" name="rainfall_24h_mm" value={form.rainfall_24h_mm} onChange={onChange} step="0.1" />
            <Field label="Soil Moisture (0-1)" name="soil_moisture" value={form.soil_moisture} onChange={onChange} step="0.01" min="0" max="1" />
            <Field label="Slope (deg)" name="slope_deg" value={form.slope_deg} onChange={onChange} step="0.1" />
            <Field label="NDVI (0-1)" name="ndvi" value={form.ndvi} onChange={onChange} step="0.01" min="0" max="1" />
            <Field label="Plant Density (0-1)" name="plant_density" value={form.plant_density} onChange={onChange} step="0.01" min="0" max="1" />
            <Field label="Past Event Count" name="past_event_count" value={form.past_event_count} onChange={onChange} step="1" min="0" />
          </div>

          <button
            onClick={onPredict}
            disabled={loadingPredict}
            className="px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 disabled:opacity-50 transition"
          >
            {loadingPredict ? 'Predicting...' : 'Run Research Prediction'}
          </button>
        </section>

        <section className="bg-white/5 border border-white/10 rounded-2xl p-5 space-y-4">
          <h2 className="text-xl font-semibold">Prediction Output</h2>

          {!prediction ? (
            <p className="text-white/60">Submit inputs to generate risk score and explanations.</p>
          ) : (
            <>
              <div className={`inline-flex items-center px-4 py-2 border rounded-xl font-semibold ${LEVEL_STYLES[prediction.risk_level] || LEVEL_STYLES.Medium}`}>
                Risk Level: {prediction.risk_level}
              </div>
              <p className="text-lg">
                Risk Score: <span className="font-bold text-cyan-300">{prediction.risk_score}</span>
              </p>
              <div>
                <h3 className="font-semibold mb-2">Explanation</h3>
                <ul className="list-disc pl-5 text-white/80 space-y-1">
                  {prediction.explanation?.map((line, index) => (
                    <li key={index}>{line}</li>
                  ))}
                </ul>
              </div>
            </>
          )}
        </section>
      </div>

      {error && <p className="text-red-400">{error}</p>}

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        <section className="bg-white/5 border border-white/10 rounded-2xl p-5">
          <h2 className="text-lg font-semibold mb-3">Risk Score vs Time</h2>
          {loadingCharts ? (
            <p className="text-white/60">Loading chart...</p>
          ) : (
            <div className="h-72">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={timeseries}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                  <XAxis dataKey="date" stroke="#cbd5e1" hide={timeseries.length > 18} />
                  <YAxis stroke="#cbd5e1" domain={[0, 1]} />
                  <Tooltip />
                  <Legend />
                  <Line type="monotone" dataKey="risk_score" name="Risk Score" stroke="#38bdf8" strokeWidth={2} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}
        </section>

        <section className="bg-white/5 border border-white/10 rounded-2xl p-5">
          <h2 className="text-lg font-semibold mb-3">Feature Contribution</h2>
          {contributionRows.length === 0 ? (
            <p className="text-white/60">Run a prediction to view feature contributions.</p>
          ) : (
            <div className="h-72">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={contributionRows} layout="vertical" margin={{ left: 24 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                  <XAxis type="number" stroke="#cbd5e1" />
                  <YAxis type="category" dataKey="feature" stroke="#cbd5e1" width={130} />
                  <Tooltip />
                  <Bar dataKey="contribution" fill="#22d3ee" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
        </section>

        <section className="bg-white/5 border border-white/10 rounded-2xl p-5">
          <h2 className="text-lg font-semibold mb-3">Disaster Frequency Distribution</h2>
          {loadingCharts ? (
            <p className="text-white/60">Loading chart...</p>
          ) : (
            <div className="h-72">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie data={frequency} dataKey="count" nameKey="disaster_type" outerRadius={95} label>
                    {frequency.map((item, index) => (
                      <Cell key={item.disaster_type} fill={PIE_COLORS[index % PIE_COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            </div>
          )}
        </section>
      </div>
    </div>
  );
}

function Field({ label, ...props }) {
  return (
    <label className="block">
      <span className="text-sm text-white/70">{label}</span>
      <input
        {...props}
        type="number"
        className="mt-1 w-full bg-black/30 border border-white/10 rounded-lg px-3 py-2 outline-none"
      />
    </label>
  );
}

function FieldSelect({ label, options, ...props }) {
  return (
    <label className="block">
      <span className="text-sm text-white/70">{label}</span>
      <select
        {...props}
        className="mt-1 w-full bg-black/30 border border-white/10 rounded-lg px-3 py-2 outline-none"
      >
        {options.map((option) => (
          <option key={option} value={option}>
            {option}
          </option>
        ))}
      </select>
    </label>
  );
}
