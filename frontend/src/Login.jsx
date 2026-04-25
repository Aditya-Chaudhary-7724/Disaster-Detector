import React, { useState } from "react";
import { signInWithEmailAndPassword } from "firebase/auth";
import { Link, useLocation, useNavigate } from "react-router-dom";

import { auth } from "./firebase.js";

export default function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();

  async function handleSubmit(event) {
    event.preventDefault();
    if (!email.trim() || !password.trim()) {
      setError("Email and password are required.");
      return;
    }

    try {
      setLoading(true);
      setError("");
      await signInWithEmailAndPassword(auth, email.trim(), password);
      const nextPath = location.state?.from?.pathname || "/dashboard";
      navigate(nextPath, { replace: true });
    } catch (err) {
      setError(err.message || "Unable to log in.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="auth-page">
      <form className="auth-card" onSubmit={handleSubmit}>
        <img src="/logo.png" alt="DisasterGuard AI shield logo" className="auth-logo" />
        <p className="eyebrow">Welcome Back</p>
        <h1 className="auth-title">Login to DisasterGuard AI</h1>
        <p className="page-copy">Sign in to access the dashboard, alerts, map, mitigation, and live data modules.</p>

        <label className="field">
          <span>Email</span>
          <input
            className="text-input"
            type="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            placeholder="you@example.com"
          />
        </label>

        <label className="field">
          <span>Password</span>
          <input
            className="text-input"
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            placeholder="Enter your password"
          />
        </label>

        {error ? <div className="error-text">{error}</div> : null}

        <button type="submit" className="primary-button auth-button" disabled={loading}>
          {loading ? "Signing In..." : "Login"}
        </button>

        <p className="body-copy auth-link-copy">
          New here? <Link to="/signup" className="inline-link">Create an account</Link>
        </p>
      </form>
    </section>
  );
}
