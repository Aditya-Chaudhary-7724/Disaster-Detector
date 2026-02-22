import React from "react";
import { Download } from "lucide-react";
import { mockRecentEvents } from "../data/mockEarthquakeData";

export default function ReportsPage() {
  return (
    <div>
      <h1 className="text-3xl font-bold text-white mb-8">Reports & Analytics</h1>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="bg-gradient-to-br from-red-500/20 to-red-600/20 border border-red-500/30 rounded-xl p-6">
          <h3 className="text-gray-300 mb-2">Total Critical Alerts</h3>
          <p className="text-4xl font-bold text-white">24</p>
          <p className="text-red-400 text-sm mt-2">Last 30 days</p>
        </div>

        <div className="bg-gradient-to-br from-blue-500/20 to-blue-600/20 border border-blue-500/30 rounded-xl p-6">
          <h3 className="text-gray-300 mb-2">Average Magnitude</h3>
          <p className="text-4xl font-bold text-white">3.2M</p>
          <p className="text-blue-400 text-sm mt-2">Last 30 days</p>
        </div>

        <div className="bg-gradient-to-br from-purple-500/20 to-purple-600/20 border border-purple-500/30 rounded-xl p-6">
          <h3 className="text-gray-300 mb-2">Peak Activity Time</h3>
          <p className="text-4xl font-bold text-white">14:00</p>
          <p className="text-purple-400 text-sm mt-2">2:00 PM - 4:00 PM</p>
        </div>
      </div>

      <div className="bg-white/5 border border-white/10 rounded-xl p-6 mb-8">
        <h2 className="text-xl font-bold text-white mb-4">Export Reports</h2>
        <div className="flex gap-4 flex-wrap">
          <button className="flex items-center gap-2 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition">
            <Download className="w-5 h-5" />
            Download PDF Report
          </button>

          <button className="flex items-center gap-2 px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 transition">
            <Download className="w-5 h-5" />
            Export as CSV
          </button>
        </div>
      </div>

      <div className="bg-white/5 border border-white/10 rounded-xl p-6">
        <h2 className="text-xl font-bold text-white mb-4">Historical Events</h2>

        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-white/10">
                <th className="text-left text-gray-400 py-3 px-4">Time</th>
                <th className="text-left text-gray-400 py-3 px-4">Location</th>
                <th className="text-left text-gray-400 py-3 px-4">Magnitude</th>
                <th className="text-left text-gray-400 py-3 px-4">Depth</th>
                <th className="text-left text-gray-400 py-3 px-4">Severity</th>
              </tr>
            </thead>
            <tbody>
              {mockRecentEvents.map((event) => (
                <tr key={event.id} className="border-b border-white/5 hover:bg-white/5">
                  <td className="py-3 px-4 text-gray-400">{event.time}</td>
                  <td className="py-3 px-4 text-white">{event.location}</td>
                  <td className="py-3 px-4 text-white">{event.magnitude}M</td>
                  <td className="py-3 px-4 text-white">{event.depth} km</td>
                  <td className="py-3 px-4 text-gray-300">{event.severity}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

      </div>
    </div>
  );
}
