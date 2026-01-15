"""
Geographic utilities for Google Maps integration and spatial operations.
"""

import logging
from typing import Optional, Tuple, Dict, Any
from django.conf import settings
from geopy.geocoders import GoogleV3
from geopy.distance import geodesic
from shapely.geometry import Point, Polygon
import json

logger = logging.getLogger(__name__)


class GeographicService:
    """Service for geographic operations using Google Maps API"""

    def __init__(self):
        self.api_key = getattr(settings, 'GOOGLE_MAPS_GEOCODING_API_KEY', '')
        self.geolocator = GoogleV3(api_key=self.api_key) if self.api_key else None

    def geocode_location(self, location_string: str) -> Optional[Dict[str, Any]]:
        """
        Geocode a location string to coordinates using Google Maps API.

        Args:
            location_string: Location to geocode (e.g., "Nairobi, Kenya")

        Returns:
            Dict with 'latitude', 'longitude', 'address' or None if failed
        """
        if not self.geolocator:
            logger.warning("Google Maps API key not configured")
            return None

        try:
            location = self.geolocator.geocode(location_string, timeout=10)
            if location:
                return {
                    'latitude': location.latitude,
                    'longitude': location.longitude,
                    'address': location.address,
                    'raw_location': location.raw
                }
        except Exception as e:
            logger.error(f"Geocoding failed for '{location_string}': {str(e)}")

        return None

    def reverse_geocode(self, latitude: float, longitude: float) -> Optional[str]:
        """
        Reverse geocode coordinates to address.

        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate

        Returns:
            Address string or None if failed
        """
        if not self.geolocator:
            logger.warning("Google Maps API key not configured")
            return None

        try:
            location = self.geolocator.reverse((latitude, longitude), timeout=10)
            if location:
                return location.address
        except Exception as e:
            logger.error(f"Reverse geocoding failed for ({latitude}, {longitude}): {str(e)}")

        return None

    def calculate_distance(self, point1: Tuple[float, float], point2: Tuple[float, float]) -> float:
        """
        Calculate distance between two points in kilometers.

        Args:
            point1: (latitude, longitude) tuple
            point2: (latitude, longitude) tuple

        Returns:
            Distance in kilometers
        """
        return geodesic(point1, point2).kilometers

    def is_point_in_polygon(self, latitude: float, longitude: float, polygon_geojson: Dict) -> bool:
        """
        Check if a point is inside a polygon defined by GeoJSON.

        Args:
            latitude: Point latitude
            longitude: Point longitude
            polygon_geojson: GeoJSON polygon object

        Returns:
            True if point is inside polygon
        """
        try:
            # Extract coordinates from GeoJSON (assuming Polygon type)
            if polygon_geojson.get('type') == 'Polygon':
                coordinates = polygon_geojson['coordinates'][0]  # Outer ring
                # GeoJSON uses [lng, lat], shapely uses [lng, lat] but we need to be careful
                polygon_coords = [(coord[0], coord[1]) for coord in coordinates]
                polygon = Polygon(polygon_coords)
                point = Point(longitude, latitude)  # Note: Point takes (x, y) = (lng, lat)
                return polygon.contains(point)
        except Exception as e:
            logger.error(f"Point-in-polygon check failed: {str(e)}")

        return False

    def is_point_in_circle(self, latitude: float, longitude: float,
                          center_lat: float, center_lng: float, radius_km: float) -> bool:
        """
        Check if a point is within a circle.

        Args:
            latitude: Point latitude
            longitude: Point longitude
            center_lat: Circle center latitude
            center_lng: Circle center longitude
            radius_km: Circle radius in kilometers

        Returns:
            True if point is within circle
        """
        distance = self.calculate_distance(
            (latitude, longitude),
            (center_lat, center_lng)
        )
        return distance <= radius_km

    def find_nearest_service_area(self, latitude: float, longitude: float, service_areas) -> Optional[Dict]:
        """
        Find the nearest service area to a given point.

        Args:
            latitude: Point latitude
            longitude: Point longitude
            service_areas: QuerySet of ServiceArea objects

        Returns:
            Dict with 'area', 'distance_km' or None
        """
        nearest_area = None
        min_distance = float('inf')

        for area in service_areas:
            if area.latitude and area.longitude:
                distance = self.calculate_distance(
                    (latitude, longitude),
                    (area.latitude, area.longitude)
                )
                if distance < min_distance:
                    min_distance = distance
                    nearest_area = area

        if nearest_area:
            return {
                'area': nearest_area,
                'distance_km': min_distance
            }

        return None


def get_geographic_service() -> GeographicService:
    """Get a configured GeographicService instance"""
    return GeographicService()


def enhance_service_area_with_coordinates(service_area):
    """
    Enhance a ServiceArea object with geocoding if coordinates are missing.

    Args:
        service_area: ServiceArea instance

    Returns:
        True if coordinates were updated, False otherwise
    """
    if service_area.latitude and service_area.longitude:
        return False  # Already has coordinates

    geo_service = get_geographic_service()
    location_string = f"{service_area.name}, Kenya"

    # Try to geocode
    geo_result = geo_service.geocode_location(location_string)
    if geo_result:
        service_area.latitude = geo_result['latitude']
        service_area.longitude = geo_result['longitude']
        service_area.save(update_fields=['latitude', 'longitude'])
        logger.info(f"Geocoded {service_area.name}: {service_area.latitude}, {service_area.longitude}")
        return True

    return False


def batch_geocode_service_areas():
    """
    Batch geocode all service areas that don't have coordinates.
    This should be run as a management command or background task.
    """
    from .models import ServiceArea

    areas_without_coords = ServiceArea.objects.filter(
        latitude__isnull=True,
        longitude__isnull=True,
        is_active=True
    )

    geo_service = get_geographic_service()
    updated_count = 0

    for area in areas_without_coords:
        location_string = f"{area.name}, Kenya"
        geo_result = geo_service.geocode_location(location_string)

        if geo_result:
            area.latitude = geo_result['latitude']
            area.longitude = geo_result['longitude']
            area.save(update_fields=['latitude', 'longitude'])
            updated_count += 1
            logger.info(f"Geocoded {area.name}: {area.latitude}, {area.longitude}")

    logger.info(f"Batch geocoding completed: {updated_count} areas updated")
    return updated_count
