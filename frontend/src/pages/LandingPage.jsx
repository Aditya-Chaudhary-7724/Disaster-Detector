import React from "react";
import { Link } from "react-router-dom";
import { Activity, Bell, Radio, Shield, TrendingUp } from "lucide-react";

export default function LandingPage() {
  const features = [
    { icon: <Radio className="w-8 h-8" />, title: "Live Monitoring", description: "Real-time disaster tracking & updates" },
    { icon: <TrendingUp className="w-8 h-8" />, title: "Risk Prediction", description: "AI-style prediction modules (coming soon)" },
    { icon: <Bell className="w-8 h-8" />, title: "Instant Alerts", description: "Critical warnings & safety notifications" },
    { icon: <Shield className="w-8 h-8" />, title: "Mitigation Steps", description: "Safety protocols and preparedness guidance" },
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-blue-950 to-slate-950 text-white">
      <nav className="border-b border-white/10 bg-black/20 backdrop-blur-sm">
        <div className="max-w-7xl mx-auto px-4 py-4 flex justify-between items-center">
          <div className="flex items-center gap-2">
            <Activity className="w-8 h-8 text-blue-400" />
            <span className="text-xl font-bold">Disaster Detector</span>
          </div>

          <div className="flex gap-4">
            <Link to="/login" className="px-4 py-2 text-white hover:text-blue-400 transition">
              Login
            </Link>
            <Link to="/signup" className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition">
              Sign Up
            </Link>
          </div>
        </div>
      </nav>

      <div className="max-w-7xl mx-auto px-4 py-20">
        <div className="text-center mb-16">
          <h1 className="text-5xl md:text-7xl font-bold mb-6 leading-tight">
            Disaster Early Warning <br />
            <span className="text-blue-400">& Monitoring System</span>
          </h1>
          <p className="text-xl text-gray-300 mb-8 max-w-3xl mx-auto">
            Track disasters in India starting with earthquakes. Landslides & cyclones coming soon.
          </p>

          <div className="flex gap-4 justify-center flex-wrap">
            <Link
              to="/dashboard"
              className="px-8 py-4 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition transform hover:scale-105 text-lg font-semibold"
            >
              Go to Dashboard
            </Link>

            <Link
              to="/alerts"
              className="px-8 py-4 bg-white/10 text-white rounded-lg hover:bg-white/20 transition backdrop-blur-sm text-lg font-semibold"
            >
              View Alerts
            </Link>
          </div>
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6 mb-16">
          {features.map((feature, idx) => (
            <div key={idx} className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl p-6 hover:bg-white/10 transition transform hover:scale-105">
              <div className="text-blue-400 mb-4">{feature.icon}</div>
              <h3 className="text-xl font-bold mb-2">{feature.title}</h3>
              <p className="text-gray-400 text-sm">{feature.description}</p>
            </div>
          ))}
        </div>

        <div className="bg-gradient-to-r from-blue-600 to-purple-600 rounded-2xl p-8 text-center">
          <h2 className="text-3xl font-bold mb-4">Stay Protected. Stay Informed.</h2>
          <p className="text-white/90 mb-6">
            Build safer communities with real-time disaster intelligence.
          </p>
          <Link
            to="/signup"
            className="px-8 py-3 bg-white text-blue-600 rounded-lg hover:bg-gray-100 transition font-semibold inline-block"
          >
            Get Started Free
          </Link>
        </div>
      </div>

      <footer className="border-t border-white/10 bg-black/20 backdrop-blur-sm mt-20">
        <div className="max-w-7xl mx-auto px-4 py-8 text-center text-gray-400">
          <p>&copy; 2026 Disaster Detector. India Monitoring System.</p>
        </div>
      </footer>
    </div>
  );
}
