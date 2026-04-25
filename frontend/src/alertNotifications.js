const ALERT_PHONE_KEY = "disasterguard-alert-phone";
const ALERT_ENABLED_KEY = "disasterguard-alert-enabled";
const ALERT_THRESHOLD = 0.7;

export function getSavedAlertPhone() {
  return localStorage.getItem(ALERT_PHONE_KEY) || "";
}

export function isAlertEnabled() {
  return localStorage.getItem(ALERT_ENABLED_KEY) === "true";
}

export function saveAlertPhone(phone) {
  localStorage.setItem(ALERT_PHONE_KEY, phone);
  localStorage.setItem(ALERT_ENABLED_KEY, "true");
}

export function clearAlertPhone() {
  localStorage.removeItem(ALERT_PHONE_KEY);
  localStorage.removeItem(ALERT_ENABLED_KEY);
}

export async function requestNotificationPermission() {
  if (typeof Notification === "undefined") {
    return "unsupported";
  }
  if (Notification.permission === "granted") {
    return "granted";
  }
  return Notification.requestPermission();
}

export async function triggerAlertNotification({ title, body, onPopup }) {
  if (!isAlertEnabled()) {
    return false;
  }

  onPopup?.("ALERT SENT TO YOUR PHONE");
  const permission = await requestNotificationPermission();
  if (permission === "granted") {
    new Notification(title, { body });
  }
  return true;
}

export function shouldTriggerAlert(riskScore) {
  return Number(riskScore || 0) > ALERT_THRESHOLD;
}
