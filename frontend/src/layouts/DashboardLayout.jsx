import React, { useState } from "react";
import { NavLink, useNavigate } from "react-router-dom";
import {
  Activity,
  Bell,
  FileText,
  Home,
  LogOut,
  Menu,
  Radio,
  Settings,
  TrendingUp,
  User,
  X,
} from "lucide-react";

export default function DashboardLayout({ children }) {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const navigate = useNavigate();

  const menuItems = [
    { to: "/dashboard", icon: <Home className="w-5 h-5" />, label: "Dashboard" },
    { to: "/monitoring", icon: <Radio className="w-5 h-5" />, label: "Live Monitoring" },
    { to: "/predictions", icon: <TrendingUp className="w-5 h-5" />, label: "Predictions" },
    { to: "/alerts", icon: <Bell className="w-5 h-5" />, label: "Alerts" },
    { to: "/reports", icon: <FileText className="w-5 h-5" />, label: "Reports" },
    { to: "/settings", icon: <Settings className="w-5 h-5" />, label: "Settings" },
  ];

  const handleLogout = () => {
    localStorage.removeItem("auth");
    navigate("/");
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 to-slate-900 text-white">
      {/* Top Navbar */}
      <nav className="bg-slate-900/60 backdrop-blur-sm border-b border-white/10 fixed top-0 w-full z-30">
        <div className="px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center gap-4">
              <button onClick={() => setSidebarOpen(!sidebarOpen)} className="lg:hidden text-white">
                {sidebarOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
              </button>

              <div className="flex items-center gap-2">
                <Activity className="w-8 h-8 text-blue-400" />
                <span className="text-xl font-bold hidden sm:block">Disaster Detector</span>
              </div>
            </div>

            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2 px-4 py-2 bg-white/5 rounded-lg">
                <User className="w-5 h-5 text-gray-400" />
                <span className="hidden sm:block">Aditya</span>
              </div>

              <button
                onClick={handleLogout}
                className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition flex items-center gap-2"
              >
                <LogOut className="w-4 h-4" />
                <span className="hidden sm:block">Logout</span>
              </button>
            </div>
          </div>
        </div>
      </nav>

      {/* Sidebar */}
      <aside
        className={`fixed top-16 left-0 h-[calc(100vh-4rem)] w-64 bg-slate-900/60 backdrop-blur-sm border-r border-white/10 transform transition-transform duration-300 z-20 ${
          sidebarOpen ? "translate-x-0" : "-translate-x-full"
        } lg:translate-x-0`}
      >
        <nav className="p-4">
          {menuItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              onClick={() => setSidebarOpen(false)}
              className={({ isActive }) =>
                `w-full flex items-center gap-3 px-4 py-3 rounded-lg transition mb-2 ${
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

      {/* Main */}
      <main className="lg:ml-64 pt-16 min-h-screen">
        <div className="p-4 sm:p-6 lg:p-8">{children}</div>
      </main>
    </div>
  );
}
