import React, { useState } from "react";

export default function SettingsPage() {
  const [emailNotif, setEmailNotif] = useState(true);
  const [smsNotif, setSmsNotif] = useState(false);

  return (
    <div>
      <h1 className="text-3xl font-bold text-white mb-8">Settings</h1>

      <div className="bg-white/5 border border-white/10 rounded-xl p-6 mb-8">
        <h2 className="text-xl font-bold text-white mb-6">Notification Preferences</h2>

        <div className="space-y-4">
          <div className="flex items-center justify-between p-4 bg-white/5 rounded-lg">
            <div>
              <h3 className="text-white font-semibold mb-1">Email Notifications</h3>
              <p className="text-gray-400 text-sm">Receive alerts and updates via email</p>
            </div>

            <button
              onClick={() => setEmailNotif(!emailNotif)}
              className={`relative w-14 h-8 rounded-full transition ${emailNotif ? "bg-blue-600" : "bg-gray-600"}`}
            >
              <div
                className={`absolute top-1 left-1 w-6 h-6 bg-white rounded-full transition transform ${
                  emailNotif ? "translate-x-6" : ""
                }`}
              />
            </button>
          </div>

          <div className="flex items-center justify-between p-4 bg-white/5 rounded-lg">
            <div>
              <h3 className="text-white font-semibold mb-1">SMS Notifications</h3>
              <p className="text-gray-400 text-sm">Receive critical alerts via SMS</p>
            </div>

            <button
              onClick={() => setSmsNotif(!smsNotif)}
              className={`relative w-14 h-8 rounded-full transition ${smsNotif ? "bg-blue-600" : "bg-gray-600"}`}
            >
              <div
                className={`absolute top-1 left-1 w-6 h-6 bg-white rounded-full transition transform ${
                  smsNotif ? "translate-x-6" : ""
                }`}
              />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
