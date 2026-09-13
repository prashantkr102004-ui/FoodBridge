import { useState } from "react";

async function reverseGeocode(latitude, longitude) {
  const response = await fetch(
    `https://nominatim.openstreetmap.org/reverse?format=jsonv2&lat=${latitude}&lon=${longitude}`
  );
  if (!response.ok) return "";
  const data = await response.json();
  return data.display_name || "";
}

export default function LocationPicker({ onLocation, addressKey = "location" }) {
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);

  function useCurrentLocation() {
    setMessage("");
    if (!navigator.geolocation) {
      setMessage("Browser geolocation is not supported.");
      return;
    }

    setLoading(true);
    navigator.geolocation.getCurrentPosition(
      async (position) => {
        const latitude = position.coords.latitude;
        const longitude = position.coords.longitude;
        onLocation({
          latitude,
          longitude
        });
        try {
          const address = await reverseGeocode(latitude, longitude);
          if (address) {
            onLocation({ latitude, longitude, [addressKey]: address });
            setMessage("Current location and address added. You can edit the address before saving.");
          } else {
            setMessage("Current location added. Please check the address before saving.");
          }
        } catch {
          setMessage("Current location added. Please check the address before saving.");
        } finally {
          setLoading(false);
        }
      },
      (error) => {
        const messages = {
          1: "Location permission was denied.",
          2: "Location is currently unavailable.",
          3: "Location request timed out."
        };
        setMessage(messages[error.code] || "Could not get your current location.");
        setLoading(false);
      },
      { enableHighAccuracy: true, timeout: 10000 }
    );
  }

  return (
    <div className="location-picker">
      <button className="button secondary" type="button" onClick={useCurrentLocation} disabled={loading}>
        {loading ? "Detecting..." : "Use My Current Location"}
      </button>
      {message && <p className="muted">{message}</p>}
    </div>
  );
}
