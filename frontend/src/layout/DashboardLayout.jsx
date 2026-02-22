import React, { useState } from "react";
import { NavLink, Outlet } from "react-router-dom";
import { Activity, Home, Menu, X, Droplets, Mountain, Shield } from "lucide-react";

export default function DashboardLayout() {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const menuItems = [
    { path: "/app", icon: <Home className="w-5 h-5" />, label: "Dashboard" },
    { path: "/app/earthquakes", icon: <Activity className="w-5 h-5" />, label: "Earthquakes" },
    { path: "/app/floods", icon: <Droplets className="w-5 h-5" />, label: "Floods" },
    { path: "/app/landslides", icon: <Mountain className="w-5 h-5" />, label: "Landslides" },
    { path: "/app/mitigation", icon: <Shield className="w-5 h-5" />, label: "Mitigation" },
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 to-slate-800">
      {/* Top bar */}
      <nav className="bg-slate-800/50 border-b border-white/10 fixed top-0 w-full z-30">
        <div className="px-4 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className="lg:hidden text-white"
            >
              {sidebarOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </button>

            <span className="text-xl font-bold text-white">Disaster Detector</span>
          </div>

          <span className="text-gray-400 text-sm hidden sm:block">
            India Monitoring + Mitigation
          </span>
        </div>
      </nav>

      {/* Sidebar */}
      <aside
        className={`fixed top-16 left-0 h-[calc(100vh-4rem)] w-64 bg-slate-800/50 border-r border-white/10 transform transition-transform duration-300 z-20 ${
          sidebarOpen ? "translate-x-0" : "-translate-x-full"
        } lg:translate-x-0`}
      >
        <nav className="p-4 space-y-2">
          {menuItems.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              onClick={() => setSidebarOpen(false)}
              className={({ isActive }) =>
                `w-full flex items-center gap-3 px-4 py-3 rounded-lg transition ${
                  isActive
                    ? "bg-blue-600 text-white"
                    : "text-gray-300 hover:bg-white/5 hover:text-white"
                }`
              }
            >
              {item.icon}
              <span className="font-medium">{item.label}</span>
            </NavLink>
          ))}
        </nav>
      </aside>

      {/* Main content */}
      <main className="lg:ml-64 pt-16 min-h-screen">
        <Outlet />
      </main>
    </div>
  );
}
