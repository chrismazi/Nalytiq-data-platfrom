"""API Endpoints for Statistical, Forecasting, and Geospatial Features.

Comprehensive endpoints for:
- Statistical Disclosure Control (SDC)
- Time Series Forecasting
- Geospatial Analytics
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/analytics", tags=["Analytics"])


# ============================================
# SDC REQUEST/RESPONSE MODELS
# ============================================

class SDCAssessRequest(BaseModel):
    """Request for disclosure risk assessment."""
    data: List[Dict[str, Any]] = Field(..., min_items=1)
    quasi_identifiers: List[str] = Field(...)
    sensitive_attributes: List[str] = Field(default=[])
    k_threshold: int = Field(5, ge=2, le=100)


class SDCProtectRequest(BaseModel):
    """Request for data protection."""
    data: List[Dict[str, Any]] = Field(..., min_items=1)
    quasi_identifiers: List[str]
    sensitive_attributes: List[str] = []
    method: str = Field("suppression", pattern="^(suppression|noise_addition|micro_aggregation|rounding|synthetic)$")
    k_anonymity: int = Field(5, ge=2)
    suppress_threshold: int = Field(3, ge=1)
    noise_epsilon: float = Field(1.0, ge=0.1, le=10.0)


class KAnonymityRequest(BaseModel):
    """Request for k-anonymity check."""
    data: List[Dict[str, Any]]
    quasi_identifiers: List[str]
    k: int = Field(5, ge=2)


class SyntheticDataRequest(BaseModel):
    """Request for synthetic data generation."""
    data: List[Dict[str, Any]] = Field(..., min_items=10)
    n_synthetic: Optional[int] = None
    preserve_statistics: bool = True


# ============================================
# FORECASTING REQUEST/RESPONSE MODELS
# ============================================

class ForecastRequest(BaseModel):
    """Request for time series forecast."""
    data: List[Dict[str, Any]]
    value_column: str = "value"
    timestamp_column: str = "timestamp"
    horizon: int = Field(12, ge=1, le=60)
    method: str = Field("auto", pattern="^(auto|naive|seasonal_naive|exponential_smoothing|holt|holt_winters|arima)$")
    seasonal_period: Optional[int] = None
    confidence_level: float = Field(0.95, ge=0.5, le=0.99)


class SimpleTimeSeriesRequest(BaseModel):
    """Simplified request with just values."""
    values: List[float] = Field(..., min_items=4)
    horizon: int = Field(12, ge=1, le=60)
    method: str = "auto"


class SeasonalAdjustRequest(BaseModel):
    """Request for seasonal adjustment."""
    values: List[float] = Field(..., min_items=12)
    period: int = Field(12, ge=2, le=365)
    model: str = Field("additive", pattern="^(additive|multiplicative)$")


class PopulationProjectionRequest(BaseModel):
    """Request for population projection."""
    base_population: float = Field(..., ge=1000)
    base_year: Optional[int] = None
    projection_years: int = Field(30, ge=1, le=100)
    fertility_rate: float = Field(3.9, ge=1.0, le=8.0)
    mortality_rate: float = Field(0.005, ge=0.001, le=0.05)
    net_migration_rate: float = Field(0.001, ge=-0.05, le=0.05)
    fertility_decline_rate: float = Field(0.02, ge=0.0, le=0.1)
    mortality_decline_rate: float = Field(0.01, ge=0.0, le=0.1)


# ============================================
# GEOSPATIAL REQUEST/RESPONSE MODELS
# ============================================

class DistanceRequest(BaseModel):
    """Request for distance calculation."""
    point1: Dict[str, float]  # {latitude, longitude}
    point2: Dict[str, float]


class SpatialFilterRequest(BaseModel):
    """Request for spatial filtering."""
    data: List[Dict[str, Any]]
    center_latitude: float
    center_longitude: float
    radius_km: float = Field(..., ge=0.1, le=1000)
    lat_column: str = "latitude"
    lon_column: str = "longitude"


class SpatialAggregateRequest(BaseModel):
    """Request for spatial aggregation."""
    data: List[Dict[str, Any]]
    value_column: str
    admin_column: str = "district"
    admin_level: str = Field("district", pattern="^(province|district)$")
    aggregation: str = Field("sum", pattern="^(sum|mean|count|min|max)$")


class GeoJSONRequest(BaseModel):
    """Request for GeoJSON conversion."""
    data: List[Dict[str, Any]]
    lat_column: str = "latitude"
    lon_column: str = "longitude"
    properties: Optional[List[str]] = None


class ChoroplethRequest(BaseModel):
    """Request for choropleth generation."""
    data: List[Dict[str, Any]]
    value_column: str
    admin_column: str = "district"
    color_scheme: str = Field("sequential", pattern="^(sequential|diverging|qualitative)$")
    num_classes: int = Field(5, ge=3, le=9)


# ============================================
# SDC ENDPOINTS
# ============================================

@router.post("/sdc/assess")
async def assess_disclosure_risk(request: SDCAssessRequest):
    """Assess disclosure risk of a dataset.
    
    Evaluates:
    - K-anonymity level
    - L-diversity
    - T-closeness
    - Unique record identification
    
    Returns comprehensive risk assessment with recommendations.
    """
    from statistical_disclosure_control import get_sdc_engine
    
    engine = get_sdc_engine()
    
    assessment = engine.assess_risk(
        data=request.data,
        quasi_identifiers=request.quasi_identifiers,
        sensitive_attributes=request.sensitive_attributes,
        k_threshold=request.k_threshold
    )
    
    return {
        "assessment": assessment.to_dict(),
        "interpretation": {
            "very_low": "< 1% records at risk - safe for release",
            "low": "1-5% records at risk - minor protection needed",
            "medium": "5-20% records at risk - protection required",
            "high": "20-50% records at risk - significant protection required",
            "very_high": "> 50% records at risk - do not release without protection"
        }
    }


@router.post("/sdc/protect")
async def apply_disclosure_protection(request: SDCProtectRequest):
    """Apply disclosure protection to dataset.
    
    Methods:
    - suppression: Remove records in small cells
    - noise_addition: Add Laplace noise to numeric values
    - micro_aggregation: Replace with group centroids
    - rounding: Round numeric values
    - synthetic: Generate synthetic data
    
    Returns protected data with utility metrics.
    """
    from statistical_disclosure_control import get_sdc_engine, SDCConfig, ProtectionMethod
    
    engine = get_sdc_engine()
    
    config = SDCConfig(
        k_anonymity=request.k_anonymity,
        suppress_threshold=request.suppress_threshold,
        noise_epsilon=request.noise_epsilon,
        quasi_identifiers=request.quasi_identifiers,
        sensitive_attributes=request.sensitive_attributes
    )
    
    method = ProtectionMethod(request.method)
    
    result = engine.protect(request.data, config, method)
    
    return {
        "result": result.to_dict(),
        "protected_data": result.protected_data[:100],  # Limit response size
        "total_records": len(result.protected_data)
    }


@router.post("/sdc/k-anonymity")
async def check_k_anonymity(request: KAnonymityRequest):
    """Check if dataset satisfies k-anonymity.
    
    K-anonymity ensures every combination of quasi-identifiers
    appears in at least k records.
    """
    from statistical_disclosure_control import KAnonymityChecker
    
    satisfies, current_k, violations = KAnonymityChecker.check(
        data=request.data,
        quasi_identifiers=request.quasi_identifiers,
        k=request.k
    )
    
    return {
        "satisfies_k_anonymity": satisfies,
        "current_k": current_k,
        "required_k": request.k,
        "violations": violations[:20],  # Limit
        "total_violations": len(violations),
        "recommendation": (
            f"Dataset satisfies {request.k}-anonymity" if satisfies
            else f"Protection needed: {len(violations)} violating combinations"
        )
    }


@router.post("/sdc/synthetic")
async def generate_synthetic_data(request: SyntheticDataRequest):
    """Generate synthetic data that preserves statistical properties.
    
    Creates privacy-safe synthetic records that maintain
    the same distributions as the original data.
    """
    from statistical_disclosure_control import SyntheticDataGenerator
    
    synthetic = SyntheticDataGenerator.generate_synthetic(
        data=request.data,
        n_synthetic=request.n_synthetic,
        preserve_correlations=request.preserve_statistics
    )
    
    return {
        "synthetic_data": synthetic[:100],  # Limit
        "total_generated": len(synthetic),
        "original_count": len(request.data),
        "note": "Synthetic data maintains statistical properties but no individual records are real"
    }


# ============================================
# FORECASTING ENDPOINTS
# ============================================

@router.post("/forecast")
async def generate_forecast(request: ForecastRequest):
    """Generate time series forecast.
    
    Supports multiple methods:
    - auto: Automatic method selection
    - naive: Last value
    - seasonal_naive: Last seasonal value
    - exponential_smoothing: Simple exponential smoothing
    - holt: Linear trend
    - holt_winters: Trend + seasonality
    - arima: ARIMA model
    
    Returns point forecasts with confidence intervals.
    """
    from time_series_forecasting import get_forecasting_engine, ForecastMethod
    
    engine = get_forecasting_engine()
    
    try:
        method = ForecastMethod(request.method) if request.method != "auto" else ForecastMethod.AUTO
        
        result = engine.forecast(
            series=request.data,
            horizon=request.horizon,
            method=method,
            seasonal_period=request.seasonal_period,
            confidence_level=request.confidence_level,
            value_column=request.value_column,
            timestamp_column=request.timestamp_column
        )
        
        return {
            "forecast": result.to_dict(),
            "interpretation": {
                "rmse": f"Average forecast error: {result.metrics.get('rmse', 0):.2f}",
                "mape": f"Average percentage error: {result.metrics.get('mape', 0):.1f}%"
            }
        }
        
    except Exception as e:
        logger.error(f"Forecasting error: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/forecast/simple")
async def simple_forecast(request: SimpleTimeSeriesRequest):
    """Generate forecast from simple value list.
    
    Convenience endpoint for quick forecasting.
    """
    from time_series_forecasting import get_forecasting_engine, ForecastMethod
    import numpy as np
    
    engine = get_forecasting_engine()
    
    method = ForecastMethod(request.method) if request.method != "auto" else ForecastMethod.AUTO
    
    result = engine.forecast(
        series=np.array(request.values),
        horizon=request.horizon,
        method=method
    )
    
    return {
        "input_length": len(request.values),
        "forecast_horizon": request.horizon,
        "method_used": result.method.value,
        "forecasts": result.forecast.tolist(),
        "lower_bound": result.lower_bound.tolist(),
        "upper_bound": result.upper_bound.tolist(),
        "metrics": result.metrics
    }


@router.post("/forecast/seasonal-adjust")
async def seasonal_adjustment(request: SeasonalAdjustRequest):
    """Apply seasonal adjustment to time series.
    
    Decomposes series into:
    - Trend component
    - Seasonal component
    - Residual component
    
    Returns seasonally adjusted values.
    """
    from time_series_forecasting import get_forecasting_engine
    
    engine = get_forecasting_engine()
    
    result = engine.seasonal_adjust(
        series=request.values,
        period=request.period,
        model=request.model
    )
    
    return result.to_dict()


@router.post("/forecast/population")
async def population_projection(request: PopulationProjectionRequest):
    """Generate population projection.
    
    Uses cohort-component method based on:
    - Fertility rates
    - Mortality rates
    - Migration patterns
    
    Includes projections by age group.
    """
    from time_series_forecasting import get_forecasting_engine
    
    engine = get_forecasting_engine()
    
    result = engine.population_projection(
        base_population=request.base_population,
        base_year=request.base_year,
        projection_years=request.projection_years,
        fertility_rate=request.fertility_rate,
        mortality_rate=request.mortality_rate,
        net_migration_rate=request.net_migration_rate,
        fertility_decline_rate=request.fertility_decline_rate,
        mortality_decline_rate=request.mortality_decline_rate
    )
    
    return result.to_dict()


@router.get("/forecast/methods")
async def list_forecast_methods():
    """List available forecasting methods with descriptions."""
    return {
        "methods": [
            {
                "id": "auto",
                "name": "Automatic",
                "description": "Automatically selects best method based on data characteristics"
            },
            {
                "id": "naive",
                "name": "Naive",
                "description": "Uses last observed value for all forecasts"
            },
            {
                "id": "seasonal_naive",
                "name": "Seasonal Naive",
                "description": "Uses last value from same season"
            },
            {
                "id": "exponential_smoothing",
                "name": "Exponential Smoothing",
                "description": "Weighted average with exponentially decreasing weights"
            },
            {
                "id": "holt",
                "name": "Holt's Linear Trend",
                "description": "Smoothing with linear trend component"
            },
            {
                "id": "holt_winters",
                "name": "Holt-Winters",
                "description": "Smoothing with trend and seasonal components"
            },
            {
                "id": "arima",
                "name": "ARIMA",
                "description": "AutoRegressive Integrated Moving Average"
            }
        ],
        "recommendation": "Use 'auto' for automatic selection based on your data"
    }


# ============================================
# GEOSPATIAL ENDPOINTS
# ============================================

@router.get("/geo/provinces")
async def get_provinces():
    """Get all Rwanda provinces with demographics."""
    from geospatial_analytics import get_geo_engine
    
    engine = get_geo_engine()
    provinces = engine.get_provinces()
    
    return {
        "provinces": [p.to_dict() for p in provinces],
        "count": len(provinces)
    }


@router.get("/geo/districts")
async def get_districts(province: Optional[str] = None):
    """Get districts, optionally filtered by province."""
    from geospatial_analytics import get_geo_engine
    
    engine = get_geo_engine()
    districts = engine.get_districts(province)
    
    return {
        "districts": [d.to_dict() for d in districts],
        "count": len(districts),
        "filter": {"province": province} if province else None
    }


@router.get("/geo/statistics")
async def get_geographic_statistics():
    """Get Rwanda geographic statistics."""
    from geospatial_analytics import get_geo_engine
    
    engine = get_geo_engine()
    return engine.get_statistics()


@router.post("/geo/distance")
async def calculate_distance(request: DistanceRequest):
    """Calculate distance between two points.
    
    Uses Haversine formula for great-circle distance.
    Returns distance in kilometers.
    """
    from geospatial_analytics import get_geo_engine
    
    engine = get_geo_engine()
    
    distance = engine.distance(request.point1, request.point2)
    
    return {
        "point1": request.point1,
        "point2": request.point2,
        "distance_km": round(distance, 2),
        "distance_miles": round(distance * 0.621371, 2)
    }


@router.post("/geo/filter-by-radius")
async def filter_by_radius(request: SpatialFilterRequest):
    """Filter data points within radius of a center point.
    
    Returns records sorted by distance from center.
    """
    from geospatial_analytics import get_geo_engine
    
    engine = get_geo_engine()
    
    filtered = engine.points_within_distance(
        data=request.data,
        center=(request.center_latitude, request.center_longitude),
        radius_km=request.radius_km,
        lat_column=request.lat_column,
        lon_column=request.lon_column
    )
    
    return {
        "center": {
            "latitude": request.center_latitude,
            "longitude": request.center_longitude
        },
        "radius_km": request.radius_km,
        "results": filtered,
        "count": len(filtered),
        "original_count": len(request.data)
    }


@router.post("/geo/aggregate")
async def spatial_aggregate(request: SpatialAggregateRequest):
    """Aggregate data by administrative unit.
    
    Supports aggregation by province or district.
    """
    from geospatial_analytics import get_geo_engine
    
    engine = get_geo_engine()
    
    if request.admin_level == "province":
        result = engine.aggregate_by_province(
            data=request.data,
            value_column=request.value_column,
            province_column=request.admin_column,
            aggregation=request.aggregation
        )
    else:
        result = engine.aggregate_by_district(
            data=request.data,
            value_column=request.value_column,
            district_column=request.admin_column,
            aggregation=request.aggregation
        )
    
    return result.to_dict()


@router.post("/geo/choropleth")
async def generate_choropleth(request: ChoroplethRequest):
    """Generate choropleth map configuration.
    
    Creates color-coded map data for visualization.
    """
    from geospatial_analytics import get_geo_engine
    
    engine = get_geo_engine()
    
    # First aggregate the data
    aggregation = engine.aggregate_by_district(
        data=request.data,
        value_column=request.value_column,
        district_column=request.admin_column,
        aggregation="sum"
    )
    
    # Generate choropleth
    choropleth = engine.choropleth(
        aggregation=aggregation,
        value_key=request.value_column,
        color_scheme=request.color_scheme,
        num_classes=request.num_classes
    )
    
    return choropleth


@router.post("/geo/to-geojson")
async def convert_to_geojson(request: GeoJSONRequest):
    """Convert point data to GeoJSON format.
    
    Returns standard GeoJSON FeatureCollection.
    """
    from geospatial_analytics import get_geo_engine
    
    engine = get_geo_engine()
    
    geojson = engine.to_geojson(
        data=request.data,
        lat_column=request.lat_column,
        lon_column=request.lon_column,
        properties=request.properties
    )
    
    return geojson


@router.get("/geo/boundaries/{level}")
async def get_admin_boundaries(level: str = "province"):
    """Get administrative boundaries as GeoJSON.
    
    Levels: province, district
    """
    from geospatial_analytics import get_geo_engine, AdminLevel
    
    engine = get_geo_engine()
    
    try:
        admin_level = AdminLevel(level)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid level: {level}. Use 'province' or 'district'")
    
    return engine.admin_boundaries(admin_level)


@router.post("/geo/is-in-rwanda")
async def check_in_rwanda(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180)
):
    """Check if coordinates are within Rwanda."""
    from geospatial_analytics import get_geo_engine
    
    engine = get_geo_engine()
    
    is_in = engine.is_in_rwanda((latitude, longitude))
    
    return {
        "latitude": latitude,
        "longitude": longitude,
        "is_in_rwanda": is_in
    }


@router.get("/geo/district/{name}")
async def get_district_info(name: str):
    """Get information about a specific district."""
    from geospatial_analytics import get_geo_engine
    
    engine = get_geo_engine()
    
    province = engine.get_province_for_district(name)
    
    if not province:
        raise HTTPException(status_code=404, detail=f"District not found: {name}")
    
    # Get all districts to find this one
    districts = engine.get_districts()
    district = next((d for d in districts if d.name.lower() == name.lower()), None)
    
    if district:
        return {
            "district": district.to_dict(),
            "province": province
        }
    
    return {"name": name, "province": province}
