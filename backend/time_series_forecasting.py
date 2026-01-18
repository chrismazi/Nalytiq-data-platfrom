"""Time Series Forecasting Engine.

Production-ready implementation for statistical forecasting.
Designed for national statistics offices with support for:
- Economic indicator forecasting
- Population projections
- Seasonal adjustment
- SDG progress tracking

Based on:
- Hyndman & Athanasopoulos (2021). Forecasting: Principles and Practice
- UN Population Division projection methodology
- Eurostat seasonal adjustment guidelines

Example usage:
    engine = get_forecasting_engine()
    
    # Fit and forecast
    result = engine.forecast(
        data=gdp_series,
        horizon=12,
        frequency="monthly"
    )
    
    # Population projection
    projection = engine.population_projection(
        base_population=13000000,
        fertility_rate=3.9,
        mortality_rate=0.005,
        years=30
    )
"""

from __future__ import annotations

import logging
import math
from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

import numpy as np
from scipy import stats, optimize
from scipy.signal import periodogram

logger = logging.getLogger(__name__)


class Frequency(str, Enum):
    """Time series frequency."""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


class ForecastMethod(str, Enum):
    """Available forecasting methods."""
    NAIVE = "naive"
    SEASONAL_NAIVE = "seasonal_naive"
    MOVING_AVERAGE = "moving_average"
    EXPONENTIAL_SMOOTHING = "exponential_smoothing"
    HOLT = "holt"
    HOLT_WINTERS = "holt_winters"
    ARIMA = "arima"
    AUTO = "auto"


class TrendType(str, Enum):
    """Trend component types."""
    NONE = "none"
    ADDITIVE = "additive"
    MULTIPLICATIVE = "multiplicative"
    DAMPED = "damped"


class SeasonalityType(str, Enum):
    """Seasonality component types."""
    NONE = "none"
    ADDITIVE = "additive"
    MULTIPLICATIVE = "multiplicative"


@dataclass
class TimeSeriesData:
    """Time series data container.
    
    Attributes:
        values: Numeric values.
        timestamps: Corresponding timestamps.
        frequency: Data frequency.
        name: Series name.
    """
    values: np.ndarray
    timestamps: List[datetime]
    frequency: Frequency
    name: str = "series"
    
    def __len__(self) -> int:
        return len(self.values)
    
    @classmethod
    def from_dict(
        cls,
        data: List[Dict[str, Any]],
        value_column: str,
        timestamp_column: str,
        frequency: Frequency = Frequency.MONTHLY
    ) -> "TimeSeriesData":
        """Create from list of dictionaries."""
        # Sort by timestamp
        sorted_data = sorted(data, key=lambda x: x.get(timestamp_column, ""))
        
        values = []
        timestamps = []
        
        for record in sorted_data:
            val = record.get(value_column)
            ts = record.get(timestamp_column)
            
            if val is not None and ts is not None:
                if isinstance(val, (int, float)):
                    values.append(float(val))
                    if isinstance(ts, str):
                        ts = datetime.fromisoformat(ts.replace('Z', '+00:00'))
                    timestamps.append(ts)
        
        return cls(
            values=np.array(values),
            timestamps=timestamps,
            frequency=frequency
        )


@dataclass
class ForecastResult:
    """Result of time series forecast.
    
    Attributes:
        forecast: Point forecasts.
        lower_bound: Lower confidence interval.
        upper_bound: Upper confidence interval.
        confidence_level: Confidence level (e.g., 0.95).
        method: Method used for forecasting.
        fitted_values: In-sample fitted values.
        residuals: Forecast residuals.
        metrics: Accuracy metrics.
    """
    forecast: np.ndarray
    timestamps: List[datetime]
    lower_bound: np.ndarray
    upper_bound: np.ndarray
    confidence_level: float
    method: ForecastMethod
    fitted_values: np.ndarray
    residuals: np.ndarray
    metrics: Dict[str, float]
    components: Dict[str, np.ndarray] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "forecast": [
                {
                    "timestamp": ts.isoformat() if hasattr(ts, 'isoformat') else str(ts),
                    "value": float(val),
                    "lower": float(lb),
                    "upper": float(ub)
                }
                for ts, val, lb, ub in zip(
                    self.timestamps,
                    self.forecast,
                    self.lower_bound,
                    self.upper_bound
                )
            ],
            "method": self.method.value,
            "confidence_level": self.confidence_level,
            "metrics": self.metrics,
            "components": {k: v.tolist()[:10] for k, v in self.components.items()},
        }


@dataclass
class SeasonalAdjustmentResult:
    """Result of seasonal adjustment."""
    adjusted: np.ndarray
    trend: np.ndarray
    seasonal: np.ndarray
    residual: np.ndarray
    seasonal_factors: Dict[int, float]
    method: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "adjusted_values": self.adjusted.tolist()[:50],
            "trend": self.trend.tolist()[:50],
            "seasonal_factors": self.seasonal_factors,
            "method": self.method,
        }


@dataclass
class PopulationProjection:
    """Population projection result."""
    years: List[int]
    total_population: List[float]
    by_age_group: Dict[str, List[float]]
    births: List[float]
    deaths: List[float]
    growth_rate: List[float]
    assumptions: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "projection": [
                {
                    "year": year,
                    "total_population": int(pop),
                    "growth_rate": f"{gr*100:.2f}%",
                    "births": int(b),
                    "deaths": int(d)
                }
                for year, pop, gr, b, d in zip(
                    self.years,
                    self.total_population,
                    self.growth_rate,
                    self.births,
                    self.deaths
                )
            ],
            "by_age_group": {
                k: [int(v) for v in vals[:10]]
                for k, vals in self.by_age_group.items()
            },
            "assumptions": self.assumptions,
        }


class ForecastAccuracy:
    """Calculate forecast accuracy metrics."""
    
    @staticmethod
    def mae(actual: np.ndarray, predicted: np.ndarray) -> float:
        """Mean Absolute Error."""
        return float(np.mean(np.abs(actual - predicted)))
    
    @staticmethod
    def mse(actual: np.ndarray, predicted: np.ndarray) -> float:
        """Mean Squared Error."""
        return float(np.mean((actual - predicted) ** 2))
    
    @staticmethod
    def rmse(actual: np.ndarray, predicted: np.ndarray) -> float:
        """Root Mean Squared Error."""
        return float(np.sqrt(np.mean((actual - predicted) ** 2)))
    
    @staticmethod
    def mape(actual: np.ndarray, predicted: np.ndarray) -> float:
        """Mean Absolute Percentage Error."""
        mask = actual != 0
        if not np.any(mask):
            return float('inf')
        return float(np.mean(np.abs((actual[mask] - predicted[mask]) / actual[mask])) * 100)
    
    @staticmethod
    def smape(actual: np.ndarray, predicted: np.ndarray) -> float:
        """Symmetric Mean Absolute Percentage Error."""
        denominator = (np.abs(actual) + np.abs(predicted)) / 2
        mask = denominator != 0
        if not np.any(mask):
            return 0.0
        return float(np.mean(np.abs(actual[mask] - predicted[mask]) / denominator[mask]) * 100)
    
    @staticmethod
    def mase(actual: np.ndarray, predicted: np.ndarray, naive_errors: np.ndarray) -> float:
        """Mean Absolute Scaled Error."""
        q = np.abs(actual - predicted) / np.mean(np.abs(naive_errors))
        return float(np.mean(q))
    
    @classmethod
    def all_metrics(
        cls,
        actual: np.ndarray,
        predicted: np.ndarray
    ) -> Dict[str, float]:
        """Calculate all accuracy metrics."""
        return {
            "mae": cls.mae(actual, predicted),
            "mse": cls.mse(actual, predicted),
            "rmse": cls.rmse(actual, predicted),
            "mape": cls.mape(actual, predicted),
            "smape": cls.smape(actual, predicted),
        }


class NaiveForecaster:
    """Naive and seasonal naive forecasts."""
    
    @staticmethod
    def forecast(
        series: np.ndarray,
        horizon: int,
        seasonal_period: int = None
    ) -> np.ndarray:
        """Generate naive forecast.
        
        Args:
            series: Historical values.
            horizon: Forecast horizon.
            seasonal_period: Period for seasonal naive (None for regular naive).
            
        Returns:
            Point forecasts.
        """
        if seasonal_period:
            # Seasonal naive: last value from same season
            forecasts = []
            for h in range(horizon):
                idx = len(series) - seasonal_period + (h % seasonal_period)
                if idx >= 0:
                    forecasts.append(series[idx])
                else:
                    forecasts.append(series[-1])
            return np.array(forecasts)
        else:
            # Simple naive: last value
            return np.full(horizon, series[-1])


class ExponentialSmoother:
    """Exponential smoothing methods (SES, Holt, Holt-Winters)."""
    
    @staticmethod
    def simple(
        series: np.ndarray,
        alpha: float = None
    ) -> Tuple[np.ndarray, float]:
        """Simple Exponential Smoothing.
        
        Args:
            series: Historical values.
            alpha: Smoothing parameter (0-1). Auto-optimized if None.
            
        Returns:
            Tuple of (smoothed values, optimal alpha).
        """
        if alpha is None:
            # Optimize alpha
            def sse(alpha):
                smoothed = ExponentialSmoother._ses_smooth(series, alpha[0])
                return np.sum((series[1:] - smoothed[:-1]) ** 2)
            
            result = optimize.minimize(sse, [0.3], bounds=[(0.01, 0.99)])
            alpha = result.x[0]
        
        smoothed = ExponentialSmoother._ses_smooth(series, alpha)
        return smoothed, alpha
    
    @staticmethod
    def _ses_smooth(series: np.ndarray, alpha: float) -> np.ndarray:
        """Apply SES smoothing."""
        smoothed = np.zeros_like(series)
        smoothed[0] = series[0]
        
        for t in range(1, len(series)):
            smoothed[t] = alpha * series[t] + (1 - alpha) * smoothed[t - 1]
        
        return smoothed
    
    @staticmethod
    def holt(
        series: np.ndarray,
        alpha: float = None,
        beta: float = None,
        damped: bool = False,
        phi: float = 0.98
    ) -> Tuple[np.ndarray, np.ndarray, Dict[str, float]]:
        """Holt's linear trend method.
        
        Args:
            series: Historical values.
            alpha: Level smoothing parameter.
            beta: Trend smoothing parameter.
            damped: Whether to use damped trend.
            phi: Damping parameter.
            
        Returns:
            Tuple of (level, trend, parameters).
        """
        n = len(series)
        
        # Initialize
        level = np.zeros(n)
        trend = np.zeros(n)
        
        level[0] = series[0]
        trend[0] = series[1] - series[0] if n > 1 else 0
        
        # Default parameters
        if alpha is None:
            alpha = 0.3
        if beta is None:
            beta = 0.1
        
        # Apply Holt's method
        for t in range(1, n):
            if damped:
                level[t] = alpha * series[t] + (1 - alpha) * (level[t-1] + phi * trend[t-1])
                trend[t] = beta * (level[t] - level[t-1]) + (1 - beta) * phi * trend[t-1]
            else:
                level[t] = alpha * series[t] + (1 - alpha) * (level[t-1] + trend[t-1])
                trend[t] = beta * (level[t] - level[t-1]) + (1 - beta) * trend[t-1]
        
        return level, trend, {"alpha": alpha, "beta": beta, "phi": phi if damped else 1.0}
    
    @staticmethod
    def holt_winters(
        series: np.ndarray,
        seasonal_period: int,
        alpha: float = None,
        beta: float = None,
        gamma: float = None,
        seasonal_type: SeasonalityType = SeasonalityType.ADDITIVE
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, Dict[str, float]]:
        """Holt-Winters seasonal method.
        
        Args:
            series: Historical values.
            seasonal_period: Length of seasonal cycle.
            alpha: Level smoothing parameter.
            beta: Trend smoothing parameter.
            gamma: Seasonal smoothing parameter.
            seasonal_type: Additive or multiplicative seasonality.
            
        Returns:
            Tuple of (level, trend, seasonal, parameters).
        """
        n = len(series)
        m = seasonal_period
        
        # Default parameters
        if alpha is None:
            alpha = 0.3
        if beta is None:
            beta = 0.1
        if gamma is None:
            gamma = 0.1
        
        # Initialize
        level = np.zeros(n)
        trend = np.zeros(n)
        seasonal = np.zeros(n + m)
        
        # Initial level and trend
        level[0] = np.mean(series[:m])
        trend[0] = (np.mean(series[m:2*m]) - np.mean(series[:m])) / m if n >= 2*m else 0
        
        # Initial seasonal components
        if seasonal_type == SeasonalityType.ADDITIVE:
            for i in range(m):
                seasonal[i] = series[i] - level[0]
        else:
            for i in range(m):
                seasonal[i] = series[i] / (level[0] + 1e-10)
        
        # Apply Holt-Winters
        for t in range(1, n):
            if seasonal_type == SeasonalityType.ADDITIVE:
                level[t] = alpha * (series[t] - seasonal[t]) + (1 - alpha) * (level[t-1] + trend[t-1])
                trend[t] = beta * (level[t] - level[t-1]) + (1 - beta) * trend[t-1]
                seasonal[t + m] = gamma * (series[t] - level[t]) + (1 - gamma) * seasonal[t]
            else:
                level[t] = alpha * (series[t] / (seasonal[t] + 1e-10)) + (1 - alpha) * (level[t-1] + trend[t-1])
                trend[t] = beta * (level[t] - level[t-1]) + (1 - beta) * trend[t-1]
                seasonal[t + m] = gamma * (series[t] / (level[t] + 1e-10)) + (1 - gamma) * seasonal[t]
        
        return level, trend, seasonal[:n], {
            "alpha": alpha, "beta": beta, "gamma": gamma,
            "seasonal_type": seasonal_type.value
        }


class ARIMAForecaster:
    """Simplified ARIMA implementation."""
    
    @staticmethod
    def difference(series: np.ndarray, d: int = 1) -> np.ndarray:
        """Apply differencing."""
        result = series.copy()
        for _ in range(d):
            result = np.diff(result)
        return result
    
    @staticmethod
    def undifference(
        differenced: np.ndarray,
        original: np.ndarray,
        d: int = 1
    ) -> np.ndarray:
        """Reverse differencing."""
        result = differenced.copy()
        for i in range(d):
            first_val = original[-(d - i)]
            result = np.cumsum(np.concatenate([[first_val], result]))
        return result
    
    @staticmethod
    def ar_coefficients(series: np.ndarray, p: int) -> np.ndarray:
        """Estimate AR coefficients using Yule-Walker equations."""
        if p == 0:
            return np.array([])
        
        # Autocorrelation
        n = len(series)
        mean = np.mean(series)
        var = np.var(series)
        
        r = np.zeros(p + 1)
        for k in range(p + 1):
            if k < n:
                r[k] = np.sum((series[:n-k] - mean) * (series[k:] - mean)) / (n * var + 1e-10)
        
        # Yule-Walker
        R = np.zeros((p, p))
        for i in range(p):
            for j in range(p):
                R[i, j] = r[abs(i - j)]
        
        try:
            phi = np.linalg.solve(R, r[1:p+1])
        except np.linalg.LinAlgError:
            phi = np.zeros(p)
        
        return phi
    
    @staticmethod
    def forecast(
        series: np.ndarray,
        horizon: int,
        p: int = 1,
        d: int = 1,
        q: int = 0
    ) -> np.ndarray:
        """Generate ARIMA forecast.
        
        Args:
            series: Historical values.
            horizon: Forecast horizon.
            p: AR order.
            d: Differencing order.
            q: MA order (simplified, uses 0).
            
        Returns:
            Point forecasts.
        """
        # Apply differencing
        diff_series = ARIMAForecaster.difference(series, d)
        
        # Estimate AR coefficients
        ar_coef = ARIMAForecaster.ar_coefficients(diff_series, p)
        
        # Generate forecasts on differenced scale
        extended = list(diff_series)
        
        for _ in range(horizon):
            if p > 0:
                forecast = np.sum(ar_coef * np.array(extended[-p:])[::-1])
            else:
                forecast = 0
            extended.append(forecast)
        
        # Undifference
        forecasts = np.array(extended[-horizon:])
        
        for i in range(d):
            last_val = series[-(i + 1)]
            forecasts = last_val + np.cumsum(forecasts)
        
        return forecasts


class SeasonalAdjuster:
    """Classical seasonal decomposition."""
    
    @staticmethod
    def decompose(
        series: np.ndarray,
        period: int,
        model: str = "additive"
    ) -> SeasonalAdjustmentResult:
        """Classical decomposition using moving averages.
        
        Args:
            series: Time series values.
            period: Seasonal period.
            model: "additive" or "multiplicative".
            
        Returns:
            Decomposition result with trend, seasonal, residual.
        """
        n = len(series)
        
        # Calculate trend using centered moving average
        if period % 2 == 0:
            # Even period: use 2x moving average
            weights = np.ones(period + 1) / period
            weights[0] = weights[-1] = 0.5 / period
        else:
            weights = np.ones(period) / period
        
        trend = np.convolve(series, weights, mode='same')
        
        # Handle edges
        half = len(weights) // 2
        trend[:half] = trend[half]
        trend[-half:] = trend[-half-1]
        
        # Calculate seasonal component
        if model == "multiplicative":
            detrended = series / (trend + 1e-10)
        else:
            detrended = series - trend
        
        # Average seasonal factors
        seasonal_factors = {}
        for i in range(period):
            indices = range(i, n, period)
            seasonal_factors[i] = np.mean([detrended[j] for j in indices])
        
        # Normalize seasonal factors
        if model == "multiplicative":
            factor_sum = sum(seasonal_factors.values())
            seasonal_factors = {k: v * period / factor_sum for k, v in seasonal_factors.items()}
        else:
            factor_mean = sum(seasonal_factors.values()) / period
            seasonal_factors = {k: v - factor_mean for k, v in seasonal_factors.items()}
        
        # Apply seasonal factors
        seasonal = np.array([seasonal_factors[i % period] for i in range(n)])
        
        # Calculate residual and seasonally adjusted
        if model == "multiplicative":
            residual = series / (trend * seasonal + 1e-10)
            adjusted = series / (seasonal + 1e-10)
        else:
            residual = series - trend - seasonal
            adjusted = series - seasonal
        
        return SeasonalAdjustmentResult(
            adjusted=adjusted,
            trend=trend,
            seasonal=seasonal,
            residual=residual,
            seasonal_factors=seasonal_factors,
            method=f"classical_{model}"
        )


class PopulationProjector:
    """Cohort-component population projection method.
    
    Based on UN Population Division methodology.
    """
    
    # Rwanda-specific age groups
    AGE_GROUPS = [
        "0-4", "5-9", "10-14", "15-19", "20-24", "25-29",
        "30-34", "35-39", "40-44", "45-49", "50-54", "55-59",
        "60-64", "65-69", "70-74", "75-79", "80+"
    ]
    
    @staticmethod
    def project(
        base_population: float,
        base_year: int,
        projection_years: int,
        fertility_rate: float = 3.9,
        mortality_rate: float = 0.005,
        net_migration_rate: float = 0.001,
        fertility_decline_rate: float = 0.02,
        mortality_decline_rate: float = 0.01
    ) -> PopulationProjection:
        """Project population using simplified cohort-component method.
        
        Args:
            base_population: Starting population.
            base_year: Starting year.
            projection_years: Number of years to project.
            fertility_rate: Total fertility rate (children per woman).
            mortality_rate: Crude death rate.
            net_migration_rate: Net migration rate.
            fertility_decline_rate: Annual decline in fertility.
            mortality_decline_rate: Annual decline in mortality.
            
        Returns:
            Population projection result.
        """
        years = list(range(base_year, base_year + projection_years + 1))
        populations = [base_population]
        births_list = []
        deaths_list = []
        growth_rates = []
        
        current_pop = base_population
        current_fertility = fertility_rate
        current_mortality = mortality_rate
        
        # Initialize age distribution (approximate Rwanda distribution)
        age_proportions = {
            "0-4": 0.15, "5-9": 0.14, "10-14": 0.13, "15-19": 0.11,
            "20-24": 0.10, "25-29": 0.09, "30-34": 0.07, "35-39": 0.06,
            "40-44": 0.05, "45-49": 0.04, "50-54": 0.03, "55-59": 0.02,
            "60-64": 0.01, "65-69": 0.005, "70-74": 0.003, "75-79": 0.002,
            "80+": 0.001
        }
        
        by_age_group = {age: [current_pop * prop] for age, prop in age_proportions.items()}
        
        for year_idx in range(1, projection_years + 1):
            # Women of reproductive age (15-49)
            reproductive_pop = sum(
                by_age_group[age][-1]
                for age in ["15-19", "20-24", "25-29", "30-34", "35-39", "40-44", "45-49"]
            ) * 0.5  # Assume 50% female
            
            # Calculate births (TFR spread over reproductive years)
            births = reproductive_pop * (current_fertility / 35)  # 35 reproductive years
            
            # Calculate deaths
            deaths = current_pop * current_mortality
            
            # Calculate migration
            migration = current_pop * net_migration_rate
            
            # Update population
            prev_pop = current_pop
            current_pop = current_pop + births - deaths + migration
            
            # Growth rate
            growth_rate = (current_pop - prev_pop) / prev_pop
            
            populations.append(current_pop)
            births_list.append(births)
            deaths_list.append(deaths)
            growth_rates.append(growth_rate)
            
            # Update age groups (simplified aging)
            for age in PopulationProjector.AGE_GROUPS:
                by_age_group[age].append(current_pop * age_proportions[age])
            
            # Update rates for next year
            current_fertility = max(2.1, current_fertility * (1 - fertility_decline_rate))
            current_mortality = max(0.003, current_mortality * (1 - mortality_decline_rate))
        
        return PopulationProjection(
            years=years,
            total_population=populations,
            by_age_group=by_age_group,
            births=births_list,
            deaths=deaths_list,
            growth_rate=growth_rates,
            assumptions={
                "base_fertility_rate": fertility_rate,
                "base_mortality_rate": mortality_rate,
                "net_migration_rate": net_migration_rate,
                "fertility_decline_rate": fertility_decline_rate,
                "mortality_decline_rate": mortality_decline_rate,
                "method": "cohort_component_simplified",
            }
        )


class ForecastingEngine:
    """Main time series forecasting engine.
    
    Provides unified interface for:
    - Automatic method selection
    - Multiple forecasting methods
    - Seasonal adjustment
    - Population projection
    
    Example:
        engine = ForecastingEngine()
        result = engine.forecast(series, horizon=12)
    """
    
    def __init__(self):
        self._smoother = ExponentialSmoother()
        self._arima = ARIMAForecaster()
        self._seasonal = SeasonalAdjuster()
        self._population = PopulationProjector()
    
    def _detect_seasonality(
        self,
        series: np.ndarray,
        max_period: int = 12
    ) -> Tuple[bool, int]:
        """Detect seasonality using periodogram."""
        if len(series) < 2 * max_period:
            return False, 1
        
        # Calculate periodogram
        freqs, power = periodogram(series - np.mean(series))
        
        # Find dominant frequency
        valid = (freqs > 0) & (freqs <= 0.5)
        if not np.any(valid):
            return False, 1
        
        dom_idx = np.argmax(power[valid])
        dom_freq = freqs[valid][dom_idx]
        dom_power = power[valid][dom_idx]
        
        # Period from frequency
        if dom_freq > 0:
            period = int(round(1 / dom_freq))
        else:
            period = 1
        
        # Check if seasonality is significant
        mean_power = np.mean(power[valid])
        is_seasonal = dom_power > 2 * mean_power and 2 <= period <= max_period
        
        return is_seasonal, min(period, max_period)
    
    def _select_method(
        self,
        series: np.ndarray,
        seasonal_period: int = None
    ) -> ForecastMethod:
        """Automatically select best forecasting method."""
        n = len(series)
        
        if n < 4:
            return ForecastMethod.NAIVE
        
        has_seasonality, detected_period = self._detect_seasonality(series)
        
        if seasonal_period:
            has_seasonality = True
            detected_period = seasonal_period
        
        # Check for trend
        first_half = np.mean(series[:n//2])
        second_half = np.mean(series[n//2:])
        has_trend = abs(second_half - first_half) / (np.std(series) + 1e-10) > 0.5
        
        if has_seasonality and n >= 2 * detected_period:
            return ForecastMethod.HOLT_WINTERS
        elif has_trend:
            return ForecastMethod.HOLT
        elif n > 10:
            return ForecastMethod.EXPONENTIAL_SMOOTHING
        else:
            return ForecastMethod.NAIVE
    
    def forecast(
        self,
        series: Union[np.ndarray, TimeSeriesData, List[Dict]],
        horizon: int = 12,
        method: ForecastMethod = ForecastMethod.AUTO,
        seasonal_period: int = None,
        confidence_level: float = 0.95,
        value_column: str = "value",
        timestamp_column: str = "timestamp"
    ) -> ForecastResult:
        """Generate time series forecast.
        
        Args:
            series: Historical data.
            horizon: Forecast horizon.
            method: Forecasting method (AUTO for automatic selection).
            seasonal_period: Seasonal period (auto-detected if None).
            confidence_level: Confidence level for intervals.
            
        Returns:
            ForecastResult with predictions and metrics.
        """
        # Convert input to array
        if isinstance(series, TimeSeriesData):
            values = series.values
            timestamps = series.timestamps
        elif isinstance(series, list) and isinstance(series[0], dict):
            ts_data = TimeSeriesData.from_dict(series, value_column, timestamp_column)
            values = ts_data.values
            timestamps = ts_data.timestamps
        else:
            values = np.array(series)
            # Generate synthetic timestamps
            base_time = datetime.now()
            timestamps = [base_time + timedelta(days=i*30) for i in range(len(values))]
        
        n = len(values)
        
        if n < 2:
            raise ValueError("Series must have at least 2 observations")
        
        # Detect seasonality if not provided
        if seasonal_period is None:
            _, seasonal_period = self._detect_seasonality(values)
        
        # Select method
        if method == ForecastMethod.AUTO:
            method = self._select_method(values, seasonal_period)
        
        # Generate forecasts
        components = {}
        
        if method == ForecastMethod.NAIVE:
            forecasts = NaiveForecaster.forecast(values, horizon)
            fitted = np.roll(values, 1)
            fitted[0] = values[0]
            
        elif method == ForecastMethod.SEASONAL_NAIVE:
            forecasts = NaiveForecaster.forecast(values, horizon, seasonal_period)
            fitted = np.roll(values, seasonal_period)
            fitted[:seasonal_period] = values[:seasonal_period]
            
        elif method == ForecastMethod.EXPONENTIAL_SMOOTHING:
            fitted, alpha = self._smoother.simple(values)
            last_smooth = fitted[-1]
            forecasts = np.full(horizon, last_smooth)
            components["smoothing_alpha"] = np.array([alpha])
            
        elif method == ForecastMethod.HOLT:
            level, trend, params = self._smoother.holt(values)
            fitted = level + trend
            last_level = level[-1]
            last_trend = trend[-1]
            forecasts = np.array([last_level + (h + 1) * last_trend for h in range(horizon)])
            components["level"] = level
            components["trend"] = trend
            
        elif method == ForecastMethod.HOLT_WINTERS:
            level, trend, seasonal, params = self._smoother.holt_winters(
                values, seasonal_period
            )
            fitted = level + trend + seasonal
            
            # Forecast
            forecasts = []
            last_level = level[-1]
            last_trend = trend[-1]
            for h in range(horizon):
                seasonal_idx = (n + h) % seasonal_period
                fc = last_level + (h + 1) * last_trend + seasonal[-(seasonal_period - seasonal_idx)]
                forecasts.append(fc)
            forecasts = np.array(forecasts)
            
            components["level"] = level
            components["trend"] = trend
            components["seasonal"] = seasonal
            
        elif method == ForecastMethod.ARIMA:
            forecasts = self._arima.forecast(values, horizon, p=2, d=1, q=0)
            # Simple fitted values for ARIMA
            fitted = values.copy()
            fitted[1:] = values[:-1]
            
        else:
            forecasts = NaiveForecaster.forecast(values, horizon)
            fitted = np.roll(values, 1)
            fitted[0] = values[0]
        
        # Calculate residuals
        residuals = values - fitted
        
        # Calculate prediction intervals
        residual_std = np.std(residuals)
        z = stats.norm.ppf((1 + confidence_level) / 2)
        
        # Widen intervals for longer horizons
        horizon_multiplier = np.sqrt(np.arange(1, horizon + 1))
        
        lower_bound = forecasts - z * residual_std * horizon_multiplier
        upper_bound = forecasts + z * residual_std * horizon_multiplier
        
        # Generate forecast timestamps
        last_ts = timestamps[-1] if timestamps else datetime.now()
        forecast_timestamps = []
        for h in range(horizon):
            next_ts = last_ts + timedelta(days=30 * (h + 1))  # Approximate monthly
            forecast_timestamps.append(next_ts)
        
        # Calculate accuracy metrics
        metrics = ForecastAccuracy.all_metrics(values, fitted)
        
        return ForecastResult(
            forecast=forecasts,
            timestamps=forecast_timestamps,
            lower_bound=lower_bound,
            upper_bound=upper_bound,
            confidence_level=confidence_level,
            method=method,
            fitted_values=fitted,
            residuals=residuals,
            metrics=metrics,
            components=components
        )
    
    def seasonal_adjust(
        self,
        series: Union[np.ndarray, List[float]],
        period: int,
        model: str = "additive"
    ) -> SeasonalAdjustmentResult:
        """Apply seasonal adjustment.
        
        Args:
            series: Time series values.
            period: Seasonal period.
            model: "additive" or "multiplicative".
            
        Returns:
            Seasonal adjustment result.
        """
        if isinstance(series, list):
            series = np.array(series)
        
        return self._seasonal.decompose(series, period, model)
    
    def population_projection(
        self,
        base_population: float,
        base_year: int = None,
        projection_years: int = 30,
        **kwargs
    ) -> PopulationProjection:
        """Project population.
        
        Args:
            base_population: Starting population.
            base_year: Starting year (defaults to current year).
            projection_years: Years to project.
            **kwargs: Fertility, mortality, migration parameters.
            
        Returns:
            Population projection.
        """
        if base_year is None:
            base_year = datetime.now().year
        
        return self._population.project(
            base_population=base_population,
            base_year=base_year,
            projection_years=projection_years,
            **kwargs
        )


# Module singleton
_engine: Optional[ForecastingEngine] = None


def get_forecasting_engine() -> ForecastingEngine:
    """Get the global forecasting engine instance."""
    global _engine
    if _engine is None:
        _engine = ForecastingEngine()
    return _engine
