import React from "react";
import { Activity, Bell, Gauge, Radio } from "lucide-react";
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { mockSeismicData, mockRecentEvents } from "../data/mockDashboardData";

export default function DashboardHome() {
  const stats = [
    { label: "Current Risk Level", value: "Medium", icon: <Gauge className="w-6 h-6" />, color: "bg-yellow-500" },
    { label: "Last Seismic Reading", value: "4.2M", icon: <Activity className="w-6 h-6" />, color: "bg-blue-500" },
    { label: "Total Alerts Today", value: "7", icon: <Bell className="w-6 h-6" />, color: "bg-red-500" },
    { label: "Active Sensors", value: "42", icon: <Radio className="w-6 h-6" />, color: "bg-green-500" },
  ];

  return (
    <div className="p-6">
      <h1 className="text-3xl font-bold text-white mb-8">Dashboard Overview</h1>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {stats.map((stat, idx) => (
          <div key={idx} className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl p-6 hover:bg-white/10 transition">
            <div className="flex items-center justify-between mb-4">
              <div className={`${stat.color} p-3 rounded-lg text-white`}>{stat.icon}</div>
            </div>
            <h3 className="text-gray-400 text-sm mb-1">{stat.label}</h3>
            <p className="text-2xl font-bold text-white">{stat.value}</p>
          </div>
        ))}
      </div>

      {/* Chart */}
      <div className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl p-6 mb-8">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-bold text-white">Seismic Activity (Last 24 Hours)</h2>
          <span className="text-green-400 text-sm flex items-center gap-2">
            <span className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></span>
            Live
          </span>
        </div>

        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={mockSeismicData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
            <XAxis dataKey="time" stroke="#9CA3AF" />
            <YAxis stroke="#9CA3AF" />
            <Tooltip contentStyle={{ backgroundColor: "#1F2937", border: "1px solid #374151" }} />
            <Legend />
            <Line type="monotone" dataKey="magnitude" stroke="#3B82F6" strokeWidth={2} name="Magnitude" />
            <Line type="monotone" dataKey="depth" stroke="#8B5CF6" strokeWidth={2} name="Depth (km)" />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Recent Events */}
      <div className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl p-6">
        <h2 className="text-xl font-bold text-white mb-4">Recent Seismic Events</h2>

        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-white/10">
                <th className="text-left text-gray-400 py-3 px-4">Location</th>
                <th className="text-left text-gray-400 py-3 px-4">Magnitude</th>
                <th className="text-left text-gray-400 py-3 px-4">Depth</th>
                <th className="text-left text-gray-400 py-3 px-4">Time</th>
                <th className="text-left text-gray-400 py-3 px-4">Severity</th>
              </tr>
            </thead>
            <tbody>
              {mockRecentEvents.map((event) => (
                <tr key={event.id} className="border-b border-white/5 hover:bg-white/5">
                  <td className="py-3 px-4 text-white">{event.location}</td>
                  <td className="py-3 px-4 text-white">{event.magnitude}M</td>
                  <td className="py-3 px-4 text-white">{event.depth} km</td>
                  <td className="py-3 px-4 text-gray-400">{event.time}</td>
                  <td className="py-3 px-4">
                    <span
                      className={`px-3 py-1 rounded-full text-xs font-semibold ${
                        event.severity === "high"
                          ? "bg-red-500/20 text-red-400"
                          : event.severity === "medium"
                          ? "bg-yellow-500/20 text-yellow-400"
                          : "bg-green-500/20 text-green-400"
                      }`}
                    >
                      {event.severity}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <p className="text-gray-500 text-xs mt-3">
          *This dashboard view is currently demo-styled. Earthquake module fetches real data.
        </p>
      </div>
    </div>
  );
}
