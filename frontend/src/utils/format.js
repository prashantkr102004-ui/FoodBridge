export function formatDate(value) {
  if (!value) return "Not yet";
  return new Intl.DateTimeFormat("en-IN", {
    dateStyle: "medium",
    timeStyle: "short"
  }).format(new Date(value));
}

export function formatQuantity(quantity, unit) {
  return `${Number(quantity).toLocaleString("en-IN")} ${unit}`;
}

export function formatDistance(distanceKm) {
  if (distanceKm === null || distanceKm === undefined) return "";
  return `Approx. ${Number(distanceKm).toFixed(1)} km away`;
}

export function formatTimeRemaining(value) {
  if (!value) return "";
  const minutes = Math.max(0, Math.round((new Date(value).getTime() - Date.now()) / 60000));
  if (minutes < 60) return `Expires in ${minutes} min`;
  const hours = Math.floor(minutes / 60);
  const remainingMinutes = minutes % 60;
  if (remainingMinutes === 0) return `Expires in ${hours} hr`;
  return `Expires in ${hours} hr ${remainingMinutes} min`;
}

export function roleHome(role) {
  if (role === "DONOR") return "/donor";
  if (role === "NGO" || role === "VOLUNTEER") return "/receiver";
  if (role === "ADMIN") return "/admin";
  return "/";
}

export function toLocalDateTimeInput(value) {
  if (!value) return "";
  const date = new Date(value);
  const offset = date.getTimezoneOffset();
  const local = new Date(date.getTime() - offset * 60000);
  return local.toISOString().slice(0, 16);
}

export function fromLocalDateTimeInput(value) {
  return value ? new Date(value).toISOString() : "";
}

export function isValidCoordinatePair(latitude, longitude) {
  if (latitude === "" && longitude === "") return true;
  if (latitude === null && longitude === null) return true;
  if (latitude === undefined && longitude === undefined) return true;
  if (latitude === "" || longitude === "" || latitude === null || longitude === null || latitude === undefined || longitude === undefined) {
    return false;
  }
  const lat = Number(latitude);
  const lon = Number(longitude);
  return Number.isFinite(lat) && Number.isFinite(lon) && lat >= -90 && lat <= 90 && lon >= -180 && lon <= 180;
}
