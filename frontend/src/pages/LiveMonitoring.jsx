import React, { useEffect, useState } from "react";
import { Activity, Clock, MapPin, Radio } from "lucide-react";

export default function LiveMonitoring() {
  const [liveData, setLiveData] = useState({
    magnitude: 2.8,
    depth: 18,
    frequency: 4.5,
    timestamp: new Date().toLocaleTimeString(),
  });

  useEffect(() => {
    const interval = setInterval(() => {
      setLiveData({
        magnitude: (Math.random() * 4 + 1).toFixed(1),
        depth: Math.floor(Math.random() * 40 + 10),
        frequency: (Math.random() * 10 + 1).toFixed(1),
        timestamp: new Date().toLocaleTimeString(),
      });
    }, 3000);

    return () => clearInterval(interval);
  }, []);

  return (
    <div>
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold text-white">Live Monitoring</h1>

        <div className="flex items-center gap-2 px-4 py-2 bg-green-500/20 text-green-400 rounded-lg border border-green-500/30">
          <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
          <span>Live</span>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <div className="bg-gradient-to-br from-blue-500/20 to-blue-600/20 backdrop-blur-sm border border-blue-500/30 rounded-xl p-6">
          <div className="flex items-center gap-2 mb-2">
            <Activity className="w-5 h-5 text-blue-400" />
            <h3 className="text-gray-300 text-sm">Magnitude</h3>
          </div>
          <p className="text-3xl font-bold text-white">{liveData.magnitude}M</p>
        </div>

        <div className="bg-gradient-to-br from-purple-500/20 to-purple-600/20 backdrop-blur-sm border border-purple-500/30 rounded-xl p-6">
          <div className="flex items-center gap-2 mb-2">
            <MapPin className="w-5 h-5 text-purple-400" />
            <h3 className="text-gray-300 text-sm">Depth</h3>
          </div>
          <p className="text-3xl font-bold text-white">{liveData.depth} km</p>
        </div>

        <div className="bg-gradient-to-br from-green-500/20 to-green-600/20 backdrop-blur-sm border border-green-500/30 rounded-xl p-6">
          <div className="flex items-center gap-2 mb-2">
            <Radio className="w-5 h-5 text-green-400" />
            <h3 className="text-gray-300 text-sm">Frequency</h3>
          </div>
          <p className="text-3xl font-bold text-white">{liveData.frequency} Hz</p>
        </div>

        <div className="bg-gradient-to-br from-orange-500/20 to-orange-600/20 backdrop-blur-sm border border-orange-500/30 rounded-xl p-6">
          <div className="flex items-center gap-2 mb-2">
            <Clock className="w-5 h-5 text-orange-400" />
            <h3 className="text-gray-300 text-sm">Last Update</h3>
          </div>
          <p className="text-2xl font-bold text-white">{liveData.timestamp}</p>
        </div>
      </div>

      <div className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl p-6">
        <h2 className="text-xl font-bold text-white mb-4">India Map (Coming Soon)</h2>
        <div className="bg-slate-800/50 rounded-lg h-80 flex items-center justify-center border-2 border-dashed border-white/20">
          <div className="text-center">
            <MapPin className="w-14 h-14 text-gray-500 mx-auto mb-4" />
            <p className="text-gray-400">Map Integration Placeholder</p>
            <p className="text-gray-500 text-sm">We'll add Mapbox / Google Maps later</p>
          </div>
        </div>
      </div>
    </div>
  );
}
