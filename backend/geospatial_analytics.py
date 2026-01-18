"""Geospatial Analytics Engine.

Production-ready geospatial analysis for Rwanda's administrative
structure and beyond.

Features:
- Rwanda administrative boundaries (5 provinces, 30 districts, 416 sectors)
- Spatial queries and filtering
- Choropleth data preparation
- Distance calculations
- Spatial aggregation
- GeoJSON generation

Based on:
- Rwanda administrative divisions (2024)
- OpenStreetMap data
- ISO 3166-2:RW standards

Example usage:
    engine = get_geo_engine()
    
    # Get provinces
    provinces = engine.get_provinces()
    
    # Spatial aggregation
    result = engine.aggregate_by_district(data, value_column="population")
    
    # Generate GeoJSON
    geojson = engine.to_geojson(data, lat_col="latitude", lon_col="longitude")
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

import numpy as np

logger = logging.getLogger(__name__)


class AdminLevel(str, Enum):
    """Rwanda administrative levels."""
    COUNTRY = "country"
    PROVINCE = "province"
    DISTRICT = "district"
    SECTOR = "sector"
    CELL = "cell"
    VILLAGE = "village"


@dataclass
class Coordinate:
    """Geographic coordinate."""
    latitude: float
    longitude: float
    
    def __post_init__(self):
        if not -90 <= self.latitude <= 90:
            raise ValueError(f"Invalid latitude: {self.latitude}")
        if not -180 <= self.longitude <= 180:
            raise ValueError(f"Invalid longitude: {self.longitude}")
    
    def to_tuple(self) -> Tuple[float, float]:
        return (self.latitude, self.longitude)
    
    def to_geojson_coords(self) -> List[float]:
        """GeoJSON uses [lon, lat] order."""
        return [self.longitude, self.latitude]


@dataclass
class BoundingBox:
    """Geographic bounding box."""
    min_lat: float
    max_lat: float
    min_lon: float
    max_lon: float
    
    def contains(self, coord: Coordinate) -> bool:
        """Check if coordinate is within bounding box."""
        return (
            self.min_lat <= coord.latitude <= self.max_lat and
            self.min_lon <= coord.longitude <= self.max_lon
        )
    
    def center(self) -> Coordinate:
        """Get center point of bounding box."""
        return Coordinate(
            latitude=(self.min_lat + self.max_lat) / 2,
            longitude=(self.min_lon + self.max_lon) / 2
        )


@dataclass
class AdminUnit:
    """Administrative unit (province, district, sector, etc.)."""
    code: str
    name: str
    name_local: Optional[str]  # Kinyarwanda name
    level: AdminLevel
    parent_code: Optional[str]
    population: Optional[int]
    area_km2: Optional[float]
    centroid: Optional[Coordinate]
    bbox: Optional[BoundingBox]
    geometry: Optional[List[List[float]]] = None  # Polygon coordinates
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "code": self.code,
            "name": self.name,
            "name_local": self.name_local,
            "level": self.level.value,
            "parent_code": self.parent_code,
            "population": self.population,
            "area_km2": self.area_km2,
            "centroid": self.centroid.to_tuple() if self.centroid else None,
        }
    
    def to_geojson_feature(self, properties: Dict = None) -> Dict[str, Any]:
        """Convert to GeoJSON Feature."""
        return {
            "type": "Feature",
            "properties": {
                **self.to_dict(),
                **(properties or {})
            },
            "geometry": {
                "type": "Polygon" if self.geometry else "Point",
                "coordinates": self.geometry or (
                    self.centroid.to_geojson_coords() if self.centroid else [0, 0]
                )
            }
        }


@dataclass
class SpatialAggregation:
    """Result of spatial aggregation."""
    admin_level: AdminLevel
    aggregations: Dict[str, Dict[str, Any]]  # {unit_code: {metric: value}}
    summary: Dict[str, float]
    timestamp: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "admin_level": self.admin_level.value,
            "units": [
                {"code": code, **values}
                for code, values in self.aggregations.items()
            ],
            "summary": self.summary,
            "timestamp": self.timestamp,
        }


class RwandaAdminRegistry:
    """Rwanda administrative unit registry.
    
    Contains official administrative divisions of Rwanda.
    """
    
    # Rwanda bounding box
    RWANDA_BBOX = BoundingBox(
        min_lat=-2.840,
        max_lat=-1.047,
        min_lon=28.856,
        max_lon=30.899
    )
    
    # Province data
    PROVINCES = {
        "RW-01": {
            "name": "Kigali", "name_local": "Umujyi wa Kigali",
            "population": 1745433, "area_km2": 730,
            "centroid": (-1.9403, 30.0588)
        },
        "RW-02": {
            "name": "Eastern", "name_local": "Intara y'Iburasirazuba",
            "population": 2715257, "area_km2": 9392,
            "centroid": (-1.9000, 30.5000)
        },
        "RW-03": {
            "name": "Northern", "name_local": "Intara y'Amajyaruguru",
            "population": 2015376, "area_km2": 3293,
            "centroid": (-1.6500, 29.8000)
        },
        "RW-04": {
            "name": "Western", "name_local": "Intara y'Iburengerazuba",
            "population": 2558119, "area_km2": 5883,
            "centroid": (-2.2000, 29.2500)
        },
        "RW-05": {
            "name": "Southern", "name_local": "Intara y'Amajyepfo",
            "population": 2866289, "area_km2": 5963,
            "centroid": (-2.5000, 29.7500)
        }
    }
    
    # District to province mapping
    DISTRICTS = {
        # Kigali City
        "RW-01-01": {"name": "Gasabo", "province": "RW-01", "population": 746219, "area_km2": 429},
        "RW-01-02": {"name": "Kicukiro", "province": "RW-01", "population": 456329, "area_km2": 167},
        "RW-01-03": {"name": "Nyarugenge", "province": "RW-01", "population": 355873, "area_km2": 134},
        
        # Eastern Province
        "RW-02-01": {"name": "Bugesera", "province": "RW-02", "population": 422009, "area_km2": 1337},
        "RW-02-02": {"name": "Gatsibo", "province": "RW-02", "population": 434937, "area_km2": 1585},
        "RW-02-03": {"name": "Kayonza", "province": "RW-02", "population": 386049, "area_km2": 1938},
        "RW-02-04": {"name": "Kirehe", "province": "RW-02", "population": 382756, "area_km2": 1192},
        "RW-02-05": {"name": "Ngoma", "province": "RW-02", "population": 345375, "area_km2": 862},
        "RW-02-06": {"name": "Nyagatare", "province": "RW-02", "population": 486685, "area_km2": 1747},
        "RW-02-07": {"name": "Rwamagana", "province": "RW-02", "population": 326046, "area_km2": 731},
        
        # Northern Province
        "RW-03-01": {"name": "Burera", "province": "RW-03", "population": 362204, "area_km2": 646},
        "RW-03-02": {"name": "Gakenke", "province": "RW-03", "population": 358748, "area_km2": 704},
        "RW-03-03": {"name": "Gicumbi", "province": "RW-03", "population": 417656, "area_km2": 867},
        "RW-03-04": {"name": "Musanze", "province": "RW-03", "population": 426392, "area_km2": 530},
        "RW-03-05": {"name": "Rulindo", "province": "RW-03", "population": 318886, "area_km2": 546},
        
        # Western Province
        "RW-04-01": {"name": "Karongi", "province": "RW-04", "population": 370379, "area_km2": 993},
        "RW-04-02": {"name": "Ngororero", "province": "RW-04", "population": 343575, "area_km2": 678},
        "RW-04-03": {"name": "Nyabihu", "province": "RW-04", "population": 306227, "area_km2": 532},
        "RW-04-04": {"name": "Nyamasheke", "province": "RW-04", "population": 408390, "area_km2": 1068},
        "RW-04-05": {"name": "Rubavu", "province": "RW-04", "population": 513315, "area_km2": 388},
        "RW-04-06": {"name": "Rusizi", "province": "RW-04", "population": 443455, "area_km2": 977},
        "RW-04-07": {"name": "Rutsiro", "province": "RW-04", "population": 336655, "area_km2": 1157},
        
        # Southern Province
        "RW-05-01": {"name": "Gisagara", "province": "RW-05", "population": 337494, "area_km2": 679},
        "RW-05-02": {"name": "Huye", "province": "RW-05", "population": 368257, "area_km2": 582},
        "RW-05-03": {"name": "Kamonyi", "province": "RW-05", "population": 358182, "area_km2": 655},
        "RW-05-04": {"name": "Muhanga", "province": "RW-05", "population": 347908, "area_km2": 647},
        "RW-05-05": {"name": "Nyamagabe", "province": "RW-05", "population": 371214, "area_km2": 1099},
        "RW-05-06": {"name": "Nyanza", "province": "RW-05", "population": 301587, "area_km2": 672},
        "RW-05-07": {"name": "Nyaruguru", "province": "RW-05", "population": 324368, "area_km2": 1012},
        "RW-05-08": {"name": "Ruhango", "province": "RW-05", "population": 334185, "area_km2": 627},
    }
    
    # District name to code mapping
    DISTRICT_BY_NAME = {
        info["name"]: code for code, info in DISTRICTS.items()
    }
    
    @classmethod
    def get_provinces(cls) -> List[AdminUnit]:
        """Get all provinces."""
        return [
            AdminUnit(
                code=code,
                name=info["name"],
                name_local=info.get("name_local"),
                level=AdminLevel.PROVINCE,
                parent_code="RW",
                population=info.get("population"),
                area_km2=info.get("area_km2"),
                centroid=Coordinate(*info["centroid"]) if "centroid" in info else None,
                bbox=None
            )
            for code, info in cls.PROVINCES.items()
        ]
    
    @classmethod
    def get_districts(cls, province_code: str = None) -> List[AdminUnit]:
        """Get districts, optionally filtered by province."""
        districts = []
        for code, info in cls.DISTRICTS.items():
            if province_code and info["province"] != province_code:
                continue
            
            province_info = cls.PROVINCES.get(info["province"], {})
            
            districts.append(AdminUnit(
                code=code,
                name=info["name"],
                name_local=None,
                level=AdminLevel.DISTRICT,
                parent_code=info["province"],
                population=info.get("population"),
                area_km2=info.get("area_km2"),
                centroid=None,
                bbox=None
            ))
        
        return districts
    
    @classmethod
    def get_district_by_name(cls, name: str) -> Optional[AdminUnit]:
        """Get district by name."""
        code = cls.DISTRICT_BY_NAME.get(name)
        if code:
            info = cls.DISTRICTS[code]
            return AdminUnit(
                code=code,
                name=info["name"],
                name_local=None,
                level=AdminLevel.DISTRICT,
                parent_code=info["province"],
                population=info.get("population"),
                area_km2=info.get("area_km2"),
                centroid=None,
                bbox=None
            )
        return None
    
    @classmethod
    def get_province_for_district(cls, district_name: str) -> Optional[str]:
        """Get province name for a district."""
        code = cls.DISTRICT_BY_NAME.get(district_name)
        if code:
            province_code = cls.DISTRICTS[code]["province"]
            return cls.PROVINCES.get(province_code, {}).get("name")
        return None


class GeoCalculator:
    """Geographic calculations."""
    
    # Earth's radius in km
    EARTH_RADIUS_KM = 6371.0
    
    @staticmethod
    def haversine_distance(
        coord1: Coordinate,
        coord2: Coordinate
    ) -> float:
        """Calculate great-circle distance between two points.
        
        Uses the Haversine formula.
        
        Args:
            coord1: First coordinate.
            coord2: Second coordinate.
            
        Returns:
            Distance in kilometers.
        """
        lat1 = math.radians(coord1.latitude)
        lat2 = math.radians(coord2.latitude)
        dlat = math.radians(coord2.latitude - coord1.latitude)
        dlon = math.radians(coord2.longitude - coord1.longitude)
        
        a = (
            math.sin(dlat / 2) ** 2 +
            math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
        )
        c = 2 * math.asin(math.sqrt(a))
        
        return GeoCalculator.EARTH_RADIUS_KM * c
    
    @staticmethod
    def bearing(
        coord1: Coordinate,
        coord2: Coordinate
    ) -> float:
        """Calculate initial bearing from coord1 to coord2.
        
        Returns:
            Bearing in degrees (0-360).
        """
        lat1 = math.radians(coord1.latitude)
        lat2 = math.radians(coord2.latitude)
        dlon = math.radians(coord2.longitude - coord1.longitude)
        
        x = math.sin(dlon) * math.cos(lat2)
        y = (
            math.cos(lat1) * math.sin(lat2) -
            math.sin(lat1) * math.cos(lat2) * math.cos(dlon)
        )
        
        bearing = math.atan2(x, y)
        return (math.degrees(bearing) + 360) % 360
    
    @staticmethod
    def destination(
        start: Coordinate,
        bearing_degrees: float,
        distance_km: float
    ) -> Coordinate:
        """Calculate destination point given start, bearing, and distance.
        
        Args:
            start: Starting coordinate.
            bearing_degrees: Bearing in degrees.
            distance_km: Distance in kilometers.
            
        Returns:
            Destination coordinate.
        """
        lat1 = math.radians(start.latitude)
        lon1 = math.radians(start.longitude)
        bearing = math.radians(bearing_degrees)
        
        d = distance_km / GeoCalculator.EARTH_RADIUS_KM
        
        lat2 = math.asin(
            math.sin(lat1) * math.cos(d) +
            math.cos(lat1) * math.sin(d) * math.cos(bearing)
        )
        
        lon2 = lon1 + math.atan2(
            math.sin(bearing) * math.sin(d) * math.cos(lat1),
            math.cos(d) - math.sin(lat1) * math.sin(lat2)
        )
        
        return Coordinate(
            latitude=math.degrees(lat2),
            longitude=math.degrees(lon2)
        )
    
    @staticmethod
    def point_in_polygon(
        coord: Coordinate,
        polygon: List[List[float]]
    ) -> bool:
        """Check if point is inside polygon using ray casting.
        
        Args:
            coord: Point to check.
            polygon: List of [lon, lat] coordinates forming polygon.
            
        Returns:
            True if point is inside.
        """
        x, y = coord.longitude, coord.latitude
        n = len(polygon)
        inside = False
        
        j = n - 1
        for i in range(n):
            xi, yi = polygon[i]
            xj, yj = polygon[j]
            
            if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi) + xi):
                inside = not inside
            j = i
        
        return inside
    
    @staticmethod
    def centroid(points: List[Coordinate]) -> Coordinate:
        """Calculate centroid of points."""
        if not points:
            raise ValueError("Cannot calculate centroid of empty list")
        
        avg_lat = sum(p.latitude for p in points) / len(points)
        avg_lon = sum(p.longitude for p in points) / len(points)
        
        return Coordinate(latitude=avg_lat, longitude=avg_lon)
    
    @staticmethod
    def bounding_box(points: List[Coordinate]) -> BoundingBox:
        """Calculate bounding box containing all points."""
        if not points:
            raise ValueError("Cannot calculate bounding box of empty list")
        
        lats = [p.latitude for p in points]
        lons = [p.longitude for p in points]
        
        return BoundingBox(
            min_lat=min(lats),
            max_lat=max(lats),
            min_lon=min(lons),
            max_lon=max(lons)
        )


class SpatialAggregator:
    """Aggregate data by administrative units."""
    
    @staticmethod
    def aggregate_by_admin(
        data: List[Dict[str, Any]],
        admin_column: str,
        value_column: str,
        aggregation: str = "sum",
        admin_level: AdminLevel = AdminLevel.DISTRICT
    ) -> SpatialAggregation:
        """Aggregate data by administrative unit.
        
        Args:
            data: Data records with admin unit column.
            admin_column: Column containing admin unit names.
            value_column: Column to aggregate.
            aggregation: sum, mean, count, min, max.
            admin_level: Administrative level.
            
        Returns:
            Spatial aggregation result.
        """
        # Group by admin unit
        groups = {}
        for record in data:
            admin = record.get(admin_column)
            value = record.get(value_column)
            
            if admin is not None:
                if admin not in groups:
                    groups[admin] = []
                if isinstance(value, (int, float)):
                    groups[admin].append(value)
        
        # Aggregate
        aggregations = {}
        for admin, values in groups.items():
            if not values:
                continue
            
            if aggregation == "sum":
                agg_value = sum(values)
            elif aggregation == "mean":
                agg_value = sum(values) / len(values)
            elif aggregation == "count":
                agg_value = len(values)
            elif aggregation == "min":
                agg_value = min(values)
            elif aggregation == "max":
                agg_value = max(values)
            else:
                agg_value = sum(values)
            
            aggregations[admin] = {
                value_column: agg_value,
                "count": len(values),
                "aggregation": aggregation
            }
        
        # Summary statistics
        all_values = [v[value_column] for v in aggregations.values()]
        summary = {}
        if all_values:
            summary = {
                "total": sum(all_values),
                "mean": sum(all_values) / len(all_values),
                "min": min(all_values),
                "max": max(all_values),
                "units": len(all_values)
            }
        
        return SpatialAggregation(
            admin_level=admin_level,
            aggregations=aggregations,
            summary=summary,
            timestamp=datetime.utcnow().isoformat()
        )


class ChoroplethGenerator:
    """Generate choropleth map data."""
    
    @staticmethod
    def generate(
        aggregation: SpatialAggregation,
        value_key: str,
        color_scheme: str = "sequential",
        num_classes: int = 5
    ) -> Dict[str, Any]:
        """Generate choropleth configuration.
        
        Args:
            aggregation: Spatial aggregation result.
            value_key: Key for value to visualize.
            color_scheme: sequential, diverging, or qualitative.
            num_classes: Number of color classes.
            
        Returns:
            Choropleth configuration with breaks and colors.
        """
        values = [
            v.get(value_key, 0)
            for v in aggregation.aggregations.values()
        ]
        
        if not values:
            return {"error": "No values to visualize"}
        
        # Calculate class breaks (Jenks natural breaks approximation)
        sorted_values = sorted(values)
        n = len(sorted_values)
        
        if n < num_classes:
            breaks = sorted_values
        else:
            # Simple quantile-based breaks
            breaks = [
                sorted_values[int(i * n / num_classes)]
                for i in range(num_classes)
            ]
            breaks.append(sorted_values[-1])
        
        # Color schemes
        schemes = {
            "sequential": [
                "#f7fbff", "#deebf7", "#c6dbef", "#9ecae1",
                "#6baed6", "#4292c6", "#2171b5", "#084594"
            ],
            "diverging": [
                "#d73027", "#f46d43", "#fdae61", "#fee08b",
                "#d9ef8b", "#a6d96a", "#66bd63", "#1a9850"
            ],
            "qualitative": [
                "#e41a1c", "#377eb8", "#4daf4a", "#984ea3",
                "#ff7f00", "#ffff33", "#a65628", "#f781bf"
            ]
        }
        
        colors = schemes.get(color_scheme, schemes["sequential"])[:num_classes]
        
        # Assign colors to each unit
        unit_colors = {}
        for unit, data in aggregation.aggregations.items():
            value = data.get(value_key, 0)
            # Find class
            color_idx = 0
            for i, brk in enumerate(breaks[:-1]):
                if value >= brk:
                    color_idx = min(i, len(colors) - 1)
            unit_colors[unit] = colors[color_idx]
        
        return {
            "type": "choropleth",
            "value_key": value_key,
            "color_scheme": color_scheme,
            "breaks": breaks,
            "colors": colors,
            "unit_colors": unit_colors,
            "legend": [
                {"min": breaks[i], "max": breaks[i+1], "color": colors[i]}
                for i in range(len(colors))
            ]
        }


class GeoJSONGenerator:
    """Generate GeoJSON from data."""
    
    @staticmethod
    def points_to_geojson(
        data: List[Dict[str, Any]],
        lat_column: str = "latitude",
        lon_column: str = "longitude",
        properties: List[str] = None
    ) -> Dict[str, Any]:
        """Convert point data to GeoJSON FeatureCollection.
        
        Args:
            data: Records with lat/lon columns.
            lat_column: Latitude column name.
            lon_column: Longitude column name.
            properties: Additional properties to include.
            
        Returns:
            GeoJSON FeatureCollection.
        """
        features = []
        
        for record in data:
            lat = record.get(lat_column)
            lon = record.get(lon_column)
            
            if lat is None or lon is None:
                continue
            
            try:
                lat = float(lat)
                lon = float(lon)
            except (ValueError, TypeError):
                continue
            
            # Build properties
            props = {}
            if properties:
                for key in properties:
                    if key in record:
                        props[key] = record[key]
            else:
                props = {
                    k: v for k, v in record.items()
                    if k not in [lat_column, lon_column]
                }
            
            features.append({
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [lon, lat]
                },
                "properties": props
            })
        
        return {
            "type": "FeatureCollection",
            "features": features,
            "crs": {
                "type": "name",
                "properties": {"name": "EPSG:4326"}
            }
        }
    
    @staticmethod
    def admin_boundaries_geojson(
        admin_level: AdminLevel = AdminLevel.PROVINCE
    ) -> Dict[str, Any]:
        """Generate GeoJSON for Rwanda administrative boundaries.
        
        Note: Returns centroids as points since full polygons
        would require external shapefile data.
        """
        features = []
        
        if admin_level == AdminLevel.PROVINCE:
            for province in RwandaAdminRegistry.get_provinces():
                features.append(province.to_geojson_feature())
        
        elif admin_level == AdminLevel.DISTRICT:
            for district in RwandaAdminRegistry.get_districts():
                features.append(district.to_geojson_feature())
        
        return {
            "type": "FeatureCollection",
            "features": features,
            "properties": {
                "admin_level": admin_level.value,
                "country": "Rwanda",
                "source": "NISR"
            }
        }


class GeospatialEngine:
    """Main geospatial analytics engine.
    
    Provides unified interface for:
    - Administrative boundary queries
    - Distance calculations
    - Spatial aggregation
    - Choropleth generation
    - GeoJSON export
    
    Example:
        engine = GeospatialEngine()
        
        # Aggregate by district
        agg = engine.aggregate_by_district(data, "population")
        
        # Generate choropleth
        choropleth = engine.choropleth(agg, "population")
    """
    
    def __init__(self):
        self._registry = RwandaAdminRegistry()
        self._calculator = GeoCalculator()
        self._aggregator = SpatialAggregator()
        self._choropleth = ChoroplethGenerator()
        self._geojson = GeoJSONGenerator()
    
    def get_provinces(self) -> List[AdminUnit]:
        """Get all Rwanda provinces."""
        return self._registry.get_provinces()
    
    def get_districts(
        self,
        province: str = None
    ) -> List[AdminUnit]:
        """Get districts, optionally filtered by province.
        
        Args:
            province: Province name or code to filter by.
            
        Returns:
            List of districts.
        """
        province_code = None
        
        if province:
            # Check if it's a code or name
            if province.startswith("RW-"):
                province_code = province
            else:
                # Find by name
                for code, info in self._registry.PROVINCES.items():
                    if info["name"].lower() == province.lower():
                        province_code = code
                        break
        
        return self._registry.get_districts(province_code)
    
    def get_province_for_district(
        self,
        district_name: str
    ) -> Optional[str]:
        """Get province name for a district."""
        return self._registry.get_province_for_district(district_name)
    
    def distance(
        self,
        point1: Union[Coordinate, Tuple[float, float], Dict],
        point2: Union[Coordinate, Tuple[float, float], Dict]
    ) -> float:
        """Calculate distance between two points in km.
        
        Args:
            point1: First point (Coordinate, (lat, lon), or dict).
            point2: Second point.
            
        Returns:
            Distance in kilometers.
        """
        coord1 = self._to_coordinate(point1)
        coord2 = self._to_coordinate(point2)
        
        return self._calculator.haversine_distance(coord1, coord2)
    
    def _to_coordinate(
        self,
        point: Union[Coordinate, Tuple[float, float], Dict]
    ) -> Coordinate:
        """Convert various point formats to Coordinate."""
        if isinstance(point, Coordinate):
            return point
        elif isinstance(point, tuple):
            return Coordinate(latitude=point[0], longitude=point[1])
        elif isinstance(point, dict):
            return Coordinate(
                latitude=point.get("latitude", point.get("lat", 0)),
                longitude=point.get("longitude", point.get("lon", point.get("lng", 0)))
            )
        else:
            raise ValueError(f"Cannot convert {type(point)} to Coordinate")
    
    def points_within_distance(
        self,
        data: List[Dict[str, Any]],
        center: Union[Coordinate, Tuple[float, float]],
        radius_km: float,
        lat_column: str = "latitude",
        lon_column: str = "longitude"
    ) -> List[Dict[str, Any]]:
        """Filter points within distance of center.
        
        Args:
            data: Records with location data.
            center: Center point.
            radius_km: Radius in kilometers.
            lat_column: Latitude column name.
            lon_column: Longitude column name.
            
        Returns:
            Filtered records within radius.
        """
        center_coord = self._to_coordinate(center)
        
        results = []
        for record in data:
            try:
                point = Coordinate(
                    latitude=float(record[lat_column]),
                    longitude=float(record[lon_column])
                )
                dist = self._calculator.haversine_distance(center_coord, point)
                
                if dist <= radius_km:
                    results.append({
                        **record,
                        "_distance_km": round(dist, 2)
                    })
            except (KeyError, ValueError, TypeError):
                continue
        
        return sorted(results, key=lambda x: x.get("_distance_km", 0))
    
    def aggregate_by_district(
        self,
        data: List[Dict[str, Any]],
        value_column: str,
        district_column: str = "district",
        aggregation: str = "sum"
    ) -> SpatialAggregation:
        """Aggregate data by district.
        
        Args:
            data: Data records.
            value_column: Column to aggregate.
            district_column: Column with district names.
            aggregation: Aggregation function.
            
        Returns:
            Spatial aggregation result.
        """
        return self._aggregator.aggregate_by_admin(
            data=data,
            admin_column=district_column,
            value_column=value_column,
            aggregation=aggregation,
            admin_level=AdminLevel.DISTRICT
        )
    
    def aggregate_by_province(
        self,
        data: List[Dict[str, Any]],
        value_column: str,
        province_column: str = "province",
        aggregation: str = "sum"
    ) -> SpatialAggregation:
        """Aggregate data by province."""
        return self._aggregator.aggregate_by_admin(
            data=data,
            admin_column=province_column,
            value_column=value_column,
            aggregation=aggregation,
            admin_level=AdminLevel.PROVINCE
        )
    
    def choropleth(
        self,
        aggregation: SpatialAggregation,
        value_key: str,
        color_scheme: str = "sequential",
        num_classes: int = 5
    ) -> Dict[str, Any]:
        """Generate choropleth map configuration.
        
        Args:
            aggregation: Spatial aggregation result.
            value_key: Value to visualize.
            color_scheme: Color scheme type.
            num_classes: Number of color classes.
            
        Returns:
            Choropleth configuration.
        """
        return self._choropleth.generate(
            aggregation, value_key, color_scheme, num_classes
        )
    
    def to_geojson(
        self,
        data: List[Dict[str, Any]],
        lat_column: str = "latitude",
        lon_column: str = "longitude",
        properties: List[str] = None
    ) -> Dict[str, Any]:
        """Convert data to GeoJSON.
        
        Args:
            data: Records with location data.
            lat_column: Latitude column.
            lon_column: Longitude column.
            properties: Properties to include.
            
        Returns:
            GeoJSON FeatureCollection.
        """
        return self._geojson.points_to_geojson(
            data, lat_column, lon_column, properties
        )
    
    def admin_boundaries(
        self,
        level: AdminLevel = AdminLevel.PROVINCE
    ) -> Dict[str, Any]:
        """Get administrative boundaries as GeoJSON.
        
        Args:
            level: Administrative level.
            
        Returns:
            GeoJSON FeatureCollection.
        """
        return self._geojson.admin_boundaries_geojson(level)
    
    def is_in_rwanda(
        self,
        point: Union[Coordinate, Tuple[float, float]]
    ) -> bool:
        """Check if a point is within Rwanda's borders."""
        coord = self._to_coordinate(point)
        return self._registry.RWANDA_BBOX.contains(coord)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get Rwanda geographic statistics."""
        provinces = self.get_provinces()
        districts = self.get_districts()
        
        return {
            "country": "Rwanda",
            "iso_code": "RW",
            "total_population": sum(p.population or 0 for p in provinces),
            "total_area_km2": sum(p.area_km2 or 0 for p in provinces),
            "num_provinces": len(provinces),
            "num_districts": len(districts),
            "provinces": [
                {
                    "name": p.name,
                    "population": p.population,
                    "area_km2": p.area_km2
                }
                for p in provinces
            ],
            "bounding_box": {
                "min_lat": self._registry.RWANDA_BBOX.min_lat,
                "max_lat": self._registry.RWANDA_BBOX.max_lat,
                "min_lon": self._registry.RWANDA_BBOX.min_lon,
                "max_lon": self._registry.RWANDA_BBOX.max_lon
            }
        }


# Module singleton
_engine: Optional[GeospatialEngine] = None


def get_geo_engine() -> GeospatialEngine:
    """Get the global geospatial engine instance."""
    global _engine
    if _engine is None:
        _engine = GeospatialEngine()
    return _engine
