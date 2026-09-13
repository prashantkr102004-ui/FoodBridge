from math import asin, cos, radians, sin, sqrt


def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Return approximate straight-line distance between two coordinates."""
    earth_radius_km = 6371.0

    lat1_rad = radians(lat1)
    lon1_rad = radians(lon1)
    lat2_rad = radians(lat2)
    lon2_rad = radians(lon2)

    lat_delta = lat2_rad - lat1_rad
    lon_delta = lon2_rad - lon1_rad

    a = sin(lat_delta / 2) ** 2 + cos(lat1_rad) * cos(lat2_rad) * sin(lon_delta / 2) ** 2
    c = 2 * asin(sqrt(a))
    return earth_radius_km * c
