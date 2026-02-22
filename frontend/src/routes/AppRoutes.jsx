import React from "react";
import { Routes, Route, Navigate } from "react-router-dom";

import DashboardLayout from "../layout/DashboardLayout";
import DashboardHome from "../pages/DashboardHome";
import Earthquakes from "../pages/Earthquakes";
import Floods from "../pages/Floods";
import Landslides from "../pages/Landslides";
import Mitigation from "../pages/Mitigation";

export default function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/app" replace />} />

      <Route path="/app" element={<DashboardLayout />}>
        <Route index element={<DashboardHome />} />
        <Route path="earthquakes" element={<Earthquakes />} />
        <Route path="floods" element={<Floods />} />
        <Route path="landslides" element={<Landslides />} />
        <Route path="mitigation" element={<Mitigation />} />
      </Route>

      <Route path="*" element={<Navigate to="/app" replace />} />
    </Routes>
  );
}
