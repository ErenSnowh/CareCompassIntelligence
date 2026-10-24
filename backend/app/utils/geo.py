"""
CareCompass AI — Geographic Utilities
Haversine distance calculation and geo-filtering for caregiver matching.
"""

from __future__ import annotations

import math


def haversine_distance(
    lat1: float, lng1: float, lat2: float, lng2: float
) -> float:
    """
    Calculate the great-circle distance between two points (in km)
    using the Haversine formula.

    Args:
        lat1, lng1: Coordinates of point 1 (user location)
        lat2, lng2: Coordinates of point 2 (caregiver base)

    Returns:
        Distance in kilometers
    """
    R = 6371.0  # Earth's radius in km

    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlng / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c


def is_within_radius(
    user_lat: float,
    user_lng: float,
    base_lat: float,
    base_lng: float,
    max_radius_km: float,
) -> bool:
    """Check if user is within the caregiver's service radius."""
    distance = haversine_distance(user_lat, user_lng, base_lat, base_lng)
    return distance <= max_radius_km


def distance_score(distance_km: float, max_radius_km: float) -> float:
    """
    Convert distance to a 0-1 score (closer = higher score).
    Uses linear decay within the service radius.

    Args:
        distance_km: Actual distance to caregiver
        max_radius_km: Caregiver's maximum service radius

    Returns:
        Score from 0.0 (at radius edge) to 1.0 (same location)
    """
    if max_radius_km <= 0:
        return 0.0
    if distance_km <= 0:
        return 1.0
    if distance_km >= max_radius_km:
        return 0.0

    return 1.0 - (distance_km / max_radius_km)
