import React from "react";
import { NavLink, Outlet } from "react-router-dom";
import {
  LayoutDashboard,
  Activity,
  Waves,
  Mountain,
  Brain,
  BrainCircuit,
  Flame,
  Radar,
  Bell,
  Shield
} from "lucide-react";

export default function Layout() {
  const linkClass = ({ isActive }) =>
    "flex items-center gap-3 px-4 py-3 rounded-xl transition " +
    (isActive ? "bg-blue-600 text-white" : "text-gray-200 hover:bg-white/10");

  return (
    <div className="min-h-screen bg-[#0B1220] text-white flex">
      {/* Sidebar */}
      <aside className="w-64 border-r border-white/10 p-4">
        <div className="text-xl font-bold mb-6 flex items-center gap-2">
          <Activity size={22} /> Disaster Detector
        </div>

        <nav className="flex flex-col gap-2">
          <NavLink to="/dashboard" className={linkClass}>
            <LayoutDashboard size={18} /> Dashboard
          </NavLink>

          <NavLink to="/earthquakes" className={linkClass}>
            <Activity size={18} /> Earthquakes
          </NavLink>

          <NavLink to="/floods" className={linkClass}>
            <Waves size={18} /> Floods
          </NavLink>

          <NavLink to="/landslides" className={linkClass}>
            <Mountain size={18} /> Landslides
          </NavLink>

          <NavLink to="/predictor" className={linkClass}>
            <Brain size={18} /> Predictor
          </NavLink>

          <NavLink to="/auto-ai-predictor" className={linkClass}>
            <BrainCircuit size={18} /> Auto AI Predictor
          </NavLink>

          <NavLink to="/spatial-risk-map" className={linkClass}>
            <Flame size={18} /> Spatial Risk Map
          </NavLink>

          <NavLink to="/research-predictor" className={linkClass}>
            <Radar size={18} /> Research Predictor
          </NavLink>

          <NavLink to="/mitigation" className={linkClass}>
            <Shield size={18} /> Mitigation
          </NavLink>

          <NavLink to="/alerts" className={linkClass}>
            <Bell size={18} /> Alerts
          </NavLink>
        </nav>
      </aside>

      {/* Main */}
      <main className="flex-1">
        <div className="p-4 border-b border-white/10 flex justify-end">
          <button className="px-4 py-2 rounded-xl bg-red-600 hover:bg-red-700 transition">
            Logout
          </button>
        </div>
        <Outlet />
      </main>
    </div>
  );
}
