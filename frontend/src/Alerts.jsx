import React, { useEffect, useState } from "react";

import {
  clearAlertPhone,
  getSavedAlertPhone,
  isAlertEnabled,
  requestNotificationPermission,
  saveAlertPhone,
  triggerAlertNotification,
} from "./alertNotifications.js";
import { generateAlerts, getAlerts, getValidationMetrics } from "./api/disasterApi.js";

export default function Alerts() {
  const [alerts, setAlerts] = useState([]);
  const [validation, setValidation] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [phoneNumber, setPhoneNumber] = useState("");
  const [otp, setOtp] = useState("");
  const [sentOtp, setSentOtp] = useState("");
  const [otpStage, setOtpStage] = useState("idle");
  const [alertEnabled, setAlertEnabled] = useState(false);
  const [popupMessage, setPopupMessage] = useState("");

  useEffect(() => {
    const savedPhone = getSavedAlertPhone();
    if (savedPhone) {
      setPhoneNumber(savedPhone);
      setAlertEnabled(isAlertEnabled());
      setOtpStage("verified");
    }
  }, []);

  useEffect(() => {
    if (!popupMessage) {
      return undefined;
    }
    const timeout = window.setTimeout(() => setPopupMessage(""), 3200);
    return () => window.clearTimeout(timeout);
  }, [popupMessage]);

  async function loadData() {
    try {
      setLoading(true);
      const [alertResponse, validationResponse] = await Promise.all([getAlerts(), getValidationMetrics()]);
      setAlerts(Array.isArray(alertResponse) ? alertResponse : []);
      setValidation(validationResponse);
      setError("");
    } catch (err) {
      setError(err.message || "Unable to load alerts.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadData();
  }, []);

  function handleSendOtp() {
    if (!phoneNumber.trim()) {
      setError("Enter a phone number before sending OTP.");
      return;
    }

    const generatedOtp = String(Math.floor(1000 + Math.random() * 9000));
    console.log(`[DisasterGuard AI] Demo OTP for ${phoneNumber}: ${generatedOtp}`);
    setSentOtp(generatedOtp);
    setOtp("");
    setOtpStage("sent");
    setError("");
    setPopupMessage("OTP generated. Check the browser console for demo OTP.");
  }

  async function handleVerifyOtp() {
    if (otp.trim() !== sentOtp) {
      setError("Incorrect OTP. Please enter the demo OTP from the console.");
      return;
    }

    saveAlertPhone(phoneNumber.trim());
    setAlertEnabled(true);
    setOtpStage("verified");
    setError("");
    await requestNotificationPermission();
    setPopupMessage("Phone alert setup complete.");
  }

  function handleDisableAlerts() {
    clearAlertPhone();
    setAlertEnabled(false);
    setPhoneNumber("");
    setOtp("");
    setSentOtp("");
    setOtpStage("idle");
    setPopupMessage("Phone alert setup removed.");
  }

  async function handleGenerate() {
    try {
      const response = await generateAlerts();
      await loadData();
      if (Number(response?.count || 0) > 0) {
        const firstAlert = response.alerts?.[0];
        await triggerAlertNotification({
          title: "Disaster Alert!",
          body: firstAlert
            ? `${firstAlert.region}: ${firstAlert.message}`
            : "High hazard risk detected in the monitoring system.",
          onPopup: setPopupMessage,
        });
      }
    } catch (err) {
      setError(err.message || "Unable to generate alerts.");
    }
  }

  return (
    <section className="page">
      <div className="page-header">
        <div>
          <p className="eyebrow">Threshold-Based Alerts</p>
          <h2>Alerts</h2>
          <p className="page-copy">
            Alerts are created automatically when the predicted risk score crosses the configured threshold.
          </p>
        </div>

        <button type="button" className="primary-button" onClick={handleGenerate}>
          Generate Current Alerts
        </button>
      </div>

      {error ? <div className="card error-text">{error}</div> : null}
      {popupMessage ? <div className="alert-popup">🚨 {popupMessage}</div> : null}

      <div className="premium-card">
        <div className="card-topline">
          <span className="pill-label">Mobile Alert Setup</span>
          <span className={`risk-badge ${alertEnabled ? "low" : "medium"}`}>
            {alertEnabled ? "Alert Enabled" : "Setup Required"}
          </span>
        </div>

        <div className="otp-grid">
          <label className="field">
            <span>Enter Phone Number</span>
            <input
              className="text-input"
              value={phoneNumber}
              onChange={(event) => setPhoneNumber(event.target.value)}
              placeholder="+91 9876543210"
            />
          </label>

          <div className="button-row otp-actions">
            <button type="button" className="primary-button" onClick={handleSendOtp}>
              Send OTP
            </button>
            {alertEnabled ? (
              <button type="button" className="secondary-button" onClick={handleDisableAlerts}>
                Disable Alerts
              </button>
            ) : null}
          </div>
        </div>

        {otpStage === "sent" ? (
          <div className="otp-grid otp-verify-block">
            <label className="field">
              <span>Enter OTP</span>
              <input
                className="text-input"
                value={otp}
                onChange={(event) => setOtp(event.target.value)}
                placeholder="4-digit OTP"
              />
            </label>

            <div className="button-row otp-actions">
              <button type="button" className="primary-button" onClick={handleVerifyOtp}>
                Verify OTP
              </button>
            </div>
          </div>
        ) : null}

        <p className="body-copy">
          Demo mode: a 4-digit OTP is generated locally and shown in the browser console for evaluation.
        </p>
      </div>

      <div className="grid three-column">
        <div className="card">
          <h3>Accuracy</h3>
          <p className="stat">{((validation?.accuracy || 0) * 100).toFixed(1)}%</p>
        </div>
        <div className="card">
          <h3>Precision</h3>
          <p className="stat">{((validation?.precision || 0) * 100).toFixed(1)}%</p>
        </div>
        <div className="card">
          <h3>Recall</h3>
          <p className="stat">{((validation?.recall || 0) * 100).toFixed(1)}%</p>
        </div>
      </div>

      <div className="card">
        <h3>Stored Alerts</h3>
        {loading ? <p className="body-copy">Loading alerts...</p> : null}
        {!loading && alerts.length === 0 ? <p className="body-copy">No alerts have been stored yet.</p> : null}

        <div className="list">
          {alerts.map((alert) => (
            <div className="list-item" key={alert.id}>
              <div>
                <p className="list-title">{alert.region}</p>
                <p className="body-copy">{alert.message}</p>
              </div>
              <div className="list-meta">
                <span className={`risk-badge ${String(alert.level).toLowerCase()}`}>{alert.level}</span>
                <span>{Number(alert.risk_score).toFixed(2)}</span>
                <span>{new Date(alert.created_at).toLocaleString()}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
