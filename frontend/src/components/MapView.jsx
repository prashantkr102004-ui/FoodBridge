import L from "leaflet";
import { MapContainer, Marker, Popup, TileLayer } from "react-leaflet";
import { Link } from "react-router-dom";
import { formatDistance, formatQuantity } from "../utils/format";

const pickupIcon = L.divIcon({
  className: "map-marker pickup-marker",
  html: "<span></span>",
  iconSize: [22, 22],
  iconAnchor: [11, 11]
});

const userIcon = L.divIcon({
  className: "map-marker user-marker",
  html: "<span></span>",
  iconSize: [24, 24],
  iconAnchor: [12, 12]
});

function hasCoordinates(item) {
  return (
    item?.latitude !== null &&
    item?.latitude !== undefined &&
    item?.longitude !== null &&
    item?.longitude !== undefined &&
    Number.isFinite(Number(item.latitude)) &&
    Number.isFinite(Number(item.longitude))
  );
}

export function DonationMap({ donation }) {
  if (!hasCoordinates(donation)) {
    return null;
  }

  const position = [Number(donation.latitude), Number(donation.longitude)];
  return (
    <div className="map-panel" data-testid="pickup-map">
      <MapContainer center={position} zoom={14} scrollWheelZoom={false}>
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <Marker position={position} icon={pickupIcon}>
          <Popup>
            <strong>{donation.food_name}</strong>
            <br />
            {donation.pickup_address}
          </Popup>
        </Marker>
      </MapContainer>
    </div>
  );
}

export function NearbyDonationsMap({ user, donations }) {
  if (!hasCoordinates(user) || !donations?.length) {
    return null;
  }

  const userPosition = [Number(user.latitude), Number(user.longitude)];
  return (
    <div className="map-panel large" data-testid="nearby-map">
      <MapContainer center={userPosition} zoom={12} scrollWheelZoom={false}>
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <Marker position={userPosition} icon={userIcon}>
          <Popup>Your saved location</Popup>
        </Marker>
        {donations.filter(hasCoordinates).map((donation) => (
          <Marker key={donation.id} position={[Number(donation.latitude), Number(donation.longitude)]} icon={pickupIcon}>
            <Popup>
              <strong>{donation.food_name}</strong>
              <br />
              {formatQuantity(donation.quantity, donation.quantity_unit)}
              <br />
              {formatDistance(donation.distance_km)}
              <br />
              <Link to={`/receiver/donations/${donation.id}`}>View Donation</Link>
            </Popup>
          </Marker>
        ))}
      </MapContainer>
    </div>
  );
}
