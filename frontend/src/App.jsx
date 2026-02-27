import React from "react";
import { Routes, Route, Navigate } from "react-router-dom";

import Layout from "./components/Layout.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import Earthquakes from "./pages/Earthquakes.jsx";
import Floods from "./pages/Floods.jsx";
import Landslides from "./pages/Landslides.jsx";
import Mitigation from "./pages/Mitigation.jsx";
import Predictor from "./pages/Predictor.jsx";
import AutoAIPredictor from "./pages/AutoAIPredictor.jsx";
import SpatialRiskMap from "./pages/SpatialRiskMap.jsx";
import Alerts from "./pages/Alerts.jsx";
import ResearchPredictor from "./pages/ResearchPredictor.jsx";

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<Navigate to="/dashboard" />} />

        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/earthquakes" element={<Earthquakes />} />
        <Route path="/floods" element={<Floods />} />
        <Route path="/landslides" element={<Landslides />} />
        <Route path="/mitigation" element={<Mitigation />} />

        <Route path="/predictor" element={<Predictor />} />
        <Route path="/auto-ai-predictor" element={<AutoAIPredictor />} />
        <Route path="/spatial-risk-map" element={<SpatialRiskMap />} />
        <Route path="/research-predictor" element={<ResearchPredictor />} />
        <Route path="/alerts" element={<Alerts />} />
      </Route>
    </Routes>
  );
}
