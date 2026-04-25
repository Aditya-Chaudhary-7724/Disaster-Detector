import React, { useState } from "react";
import { createUserWithEmailAndPassword } from "firebase/auth";
import { Link, useNavigate } from "react-router-dom";

import { auth } from "./firebase.js";

export default function Signup() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  async function handleSubmit(event) {
    event.preventDefault();
    if (!email.trim() || !password.trim()) {
      setError("Email and password are required.");
      return;
    }
    if (password.length < 6) {
      setError("Password must be at least 6 characters.");
      return;
    }

    try {
      setLoading(true);
      setError("");
      await createUserWithEmailAndPassword(auth, email.trim(), password);
      navigate("/dashboard", { replace: true });
    } catch (err) {
      setError(err.message || "Unable to create account.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="auth-page">
      <form className="auth-card" onSubmit={handleSubmit}>
        <img src="/logo.png" alt="DisasterGuard AI shield logo" className="auth-logo" />
        <p className="eyebrow">Create Account</p>
        <h1 className="auth-title">Signup for DisasterGuard AI</h1>
        <p className="page-copy">Create an account to unlock the protected hazard monitoring tools.</p>

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
            placeholder="At least 6 characters"
          />
        </label>

        {error ? <div className="error-text">{error}</div> : null}

        <button type="submit" className="primary-button auth-button" disabled={loading}>
          {loading ? "Creating Account..." : "Signup"}
        </button>

        <p className="body-copy auth-link-copy">
          Already have an account? <Link to="/login" className="inline-link">Log in</Link>
        </p>
      </form>
    </section>
  );
}
