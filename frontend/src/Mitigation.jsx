import React, { useEffect, useState } from "react";

import { getMitigationGuidance } from "./api/disasterApi.js";

export default function Mitigation() {
  const [items, setItems] = useState([]);
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadGuidance() {
      try {
        const response = await getMitigationGuidance();
        setItems(response.items || []);
      } catch (err) {
        setError(err.message || "Unable to load mitigation guidance.");
      }
    }

    loadGuidance();
  }, []);

  return (
    <section className="page">
      <div className="page-header">
        <div>
          <p className="eyebrow">Practical Safety Guidance</p>
          <h2>Mitigation</h2>
          <p className="page-copy">
            Each region includes simple precautions based on its main disaster exposure.
          </p>
        </div>
      </div>

      {error ? <div className="card error-text">{error}</div> : null}

      <div className="grid two-column">
        {items.map((item) => (
          <div className="card" key={item.region}>
            <h3>{item.region}</h3>
            <p className="body-copy">Primary Hazard: {item.primary_hazard}</p>
            <div className="metric-list">
              {item.tips.map((tip) => (
                <p key={tip}>{tip}</p>
              ))}
            </div>
            <div className="button-row">
              {(item.emergency_contacts || []).map((contact) => (
                <a key={contact.number} className="secondary-button" href={`tel:${contact.number}`}>
                  {contact.label} ({contact.number})
                </a>
              ))}
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
