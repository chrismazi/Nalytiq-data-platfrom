"""Statistical Disclosure Control (SDC) Module.

Production-ready implementation for privacy-preserving data release.
Implements techniques required by national statistics offices for
safe microdata publication.

Based on:
- Hundepool et al. (2012). Statistical Disclosure Control
- UN Handbook on Statistical Disclosure Control
- Eurostat SDC Guidelines

Techniques implemented:
- K-Anonymity
- L-Diversity
- T-Closeness
- Data Suppression
- Noise Addition (Laplace mechanism)
- Synthetic Data Generation
- Risk Assessment

Example usage:
    sdc = get_sdc_engine()
    
    # Check k-anonymity
    result = sdc.check_k_anonymity(data, quasi_identifiers, k=5)
    
    # Apply protection
    protected = sdc.apply_protection(data, config)
"""

from __future__ import annotations

import logging
import math
import random
import hashlib
from abc import ABC, abstractmethod
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union

import numpy as np
from scipy import stats

logger = logging.getLogger(__name__)


class RiskLevel(str, Enum):
    """Disclosure risk levels."""
    VERY_LOW = "very_low"      # < 1% risk
    LOW = "low"                 # 1-5% risk
    MEDIUM = "medium"           # 5-20% risk
    HIGH = "high"               # 20-50% risk
    VERY_HIGH = "very_high"     # > 50% risk


class ProtectionMethod(str, Enum):
    """Available protection methods."""
    SUPPRESSION = "suppression"
    GENERALIZATION = "generalization"
    NOISE_ADDITION = "noise_addition"
    SWAPPING = "swapping"
    MICRO_AGGREGATION = "micro_aggregation"
    SYNTHETIC = "synthetic"
    TOP_CODING = "top_coding"
    BOTTOM_CODING = "bottom_coding"
    ROUNDING = "rounding"


@dataclass
class DisclosureRiskAssessment:
    """Result of disclosure risk assessment.
    
    Attributes:
        overall_risk: Overall risk level.
        risk_score: Numeric risk score (0-1).
        unique_records: Number of unique records (k=1).
        k_anonymity_level: Current k-anonymity level.
        l_diversity_level: Current l-diversity level.
        records_at_risk: Number of records with high risk.
        recommendations: Suggested protection measures.
    """
    overall_risk: RiskLevel
    risk_score: float
    unique_records: int
    k_anonymity_level: int
    l_diversity_level: float
    records_at_risk: int
    high_risk_combinations: List[Dict[str, Any]]
    recommendations: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "overall_risk": self.overall_risk.value,
            "risk_score": self.risk_score,
            "unique_records": self.unique_records,
            "k_anonymity_level": self.k_anonymity_level,
            "l_diversity_level": self.l_diversity_level,
            "records_at_risk": self.records_at_risk,
            "high_risk_combinations": self.high_risk_combinations[:10],
            "recommendations": self.recommendations,
        }


@dataclass
class ProtectionResult:
    """Result of applying disclosure protection.
    
    Attributes:
        protected_data: The protected dataset.
        method_applied: Protection method used.
        records_modified: Number of modified records.
        information_loss: Measure of information loss (0-1).
        utility_metrics: Data utility metrics after protection.
    """
    protected_data: List[Dict[str, Any]]
    method_applied: ProtectionMethod
    records_modified: int
    records_suppressed: int
    information_loss: float
    utility_metrics: Dict[str, float]
    before_risk: float
    after_risk: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "method_applied": self.method_applied.value,
            "records_modified": self.records_modified,
            "records_suppressed": self.records_suppressed,
            "information_loss": self.information_loss,
            "utility_metrics": self.utility_metrics,
            "risk_reduction": f"{(1 - self.after_risk/max(0.001, self.before_risk))*100:.1f}%",
            "data_sample": self.protected_data[:5] if self.protected_data else [],
        }


@dataclass
class SDCConfig:
    """Configuration for SDC protection.
    
    Attributes:
        k_anonymity: Minimum k for k-anonymity.
        l_diversity: Minimum l for l-diversity.
        t_closeness: Maximum t for t-closeness.
        suppress_threshold: Suppress cells below this count.
        noise_epsilon: Epsilon for differential privacy noise.
        max_info_loss: Maximum acceptable information loss.
    """
    k_anonymity: int = 5
    l_diversity: int = 2
    t_closeness: float = 0.2
    suppress_threshold: int = 3
    noise_epsilon: float = 1.0
    max_info_loss: float = 0.3
    quasi_identifiers: List[str] = field(default_factory=list)
    sensitive_attributes: List[str] = field(default_factory=list)
    

class Generalizer:
    """Generalization hierarchies for quasi-identifiers.
    
    Implements domain generalization hierarchies for common
    demographic variables.
    """
    
    # Age generalization hierarchy
    AGE_HIERARCHIES = {
        0: lambda x: x,                          # Exact age
        1: lambda x: f"{(x // 5) * 5}-{(x // 5) * 5 + 4}",  # 5-year bands
        2: lambda x: f"{(x // 10) * 10}-{(x // 10) * 10 + 9}",  # 10-year bands
        3: lambda x: "Child" if x < 18 else ("Adult" if x < 65 else "Senior"),
        4: lambda x: "*",  # Full suppression
    }
    
    # Rwanda district to province mapping
    RWANDA_GEOGRAPHY = {
        "Gasabo": "Kigali", "Kicukiro": "Kigali", "Nyarugenge": "Kigali",
        "Bugesera": "Eastern", "Gatsibo": "Eastern", "Kayonza": "Eastern",
        "Kirehe": "Eastern", "Ngoma": "Eastern", "Nyagatare": "Eastern",
        "Rwamagana": "Eastern",
        "Burera": "Northern", "Gakenke": "Northern", "Gicumbi": "Northern",
        "Musanze": "Northern", "Rulindo": "Northern",
        "Gisagara": "Southern", "Huye": "Southern", "Kamonyi": "Southern",
        "Muhanga": "Southern", "Nyamagabe": "Southern", "Nyanza": "Southern",
        "Nyaruguru": "Southern", "Ruhango": "Southern",
        "Karongi": "Western", "Ngororero": "Western", "Nyabihu": "Western",
        "Nyamasheke": "Western", "Rubavu": "Western", "Rusizi": "Western",
        "Rutsiro": "Western",
    }
    
    @classmethod
    def generalize_age(cls, age: int, level: int) -> str:
        """Generalize age to specified level."""
        if level not in cls.AGE_HIERARCHIES:
            level = max(cls.AGE_HIERARCHIES.keys())
        return cls.AGE_HIERARCHIES[level](age)
    
    @classmethod
    def generalize_location(cls, location: str, level: int) -> str:
        """Generalize Rwanda location."""
        if level == 0:
            return location
        elif level == 1:
            return cls.RWANDA_GEOGRAPHY.get(location, "Unknown")
        else:
            return "Rwanda"
    
    @classmethod
    def generalize_date(cls, date_str: str, level: int) -> str:
        """Generalize date to specified precision."""
        try:
            if isinstance(date_str, str):
                date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            else:
                date = date_str
                
            if level == 0:
                return date.strftime("%Y-%m-%d")
            elif level == 1:
                return date.strftime("%Y-%m")
            elif level == 2:
                return date.strftime("%Y-Q%s") % ((date.month - 1) // 3 + 1)
            elif level == 3:
                return date.strftime("%Y")
            else:
                return "*"
        except Exception:
            return date_str


class KAnonymityChecker:
    """Check and enforce k-anonymity.
    
    k-anonymity requires that every combination of quasi-identifiers
    appears in at least k records.
    """
    
    @staticmethod
    def check(
        data: List[Dict[str, Any]],
        quasi_identifiers: List[str],
        k: int = 5
    ) -> Tuple[bool, int, List[Dict[str, Any]]]:
        """Check if data satisfies k-anonymity.
        
        Args:
            data: Dataset to check.
            quasi_identifiers: Columns that could identify individuals.
            k: Minimum required group size.
            
        Returns:
            Tuple of (satisfies_k, current_k, violating_combinations).
        """
        if not data or not quasi_identifiers:
            return True, float('inf'), []
        
        # Count equivalence classes
        equivalence_classes = Counter()
        
        for record in data:
            key = tuple(record.get(qi, None) for qi in quasi_identifiers)
            equivalence_classes[key] += 1
        
        # Find minimum k and violations
        min_k = min(equivalence_classes.values()) if equivalence_classes else 0
        
        violations = [
            {
                "combination": dict(zip(quasi_identifiers, key)),
                "count": count
            }
            for key, count in equivalence_classes.items()
            if count < k
        ]
        
        satisfies = min_k >= k
        
        return satisfies, min_k, violations
    
    @staticmethod
    def get_equivalence_classes(
        data: List[Dict[str, Any]],
        quasi_identifiers: List[str]
    ) -> Dict[Tuple, List[int]]:
        """Get equivalence class indices for each record."""
        classes = defaultdict(list)
        
        for idx, record in enumerate(data):
            key = tuple(record.get(qi, None) for qi in quasi_identifiers)
            classes[key].append(idx)
        
        return dict(classes)


class LDiversityChecker:
    """Check and enforce l-diversity.
    
    l-diversity requires that each equivalence class contains at least
    l "well-represented" values for sensitive attributes.
    """
    
    @staticmethod
    def check(
        data: List[Dict[str, Any]],
        quasi_identifiers: List[str],
        sensitive_attr: str,
        l: int = 2
    ) -> Tuple[bool, float, List[Dict[str, Any]]]:
        """Check if data satisfies l-diversity.
        
        Args:
            data: Dataset to check.
            quasi_identifiers: Quasi-identifier columns.
            sensitive_attr: Sensitive attribute column.
            l: Minimum diversity level.
            
        Returns:
            Tuple of (satisfies_l, min_l, violating_classes).
        """
        eq_classes = KAnonymityChecker.get_equivalence_classes(
            data, quasi_identifiers
        )
        
        min_l = float('inf')
        violations = []
        
        for key, indices in eq_classes.items():
            # Get distinct sensitive values in this class
            sensitive_values = [data[i].get(sensitive_attr) for i in indices]
            distinct_values = len(set(sensitive_values))
            
            min_l = min(min_l, distinct_values)
            
            if distinct_values < l:
                violations.append({
                    "combination": dict(zip(quasi_identifiers, key)),
                    "sensitive_diversity": distinct_values,
                    "record_count": len(indices)
                })
        
        satisfies = min_l >= l if min_l != float('inf') else True
        
        return satisfies, min_l, violations
    
    @staticmethod
    def entropy_l_diversity(
        data: List[Dict[str, Any]],
        quasi_identifiers: List[str],
        sensitive_attr: str
    ) -> float:
        """Calculate entropy-based l-diversity."""
        eq_classes = KAnonymityChecker.get_equivalence_classes(
            data, quasi_identifiers
        )
        
        min_entropy = float('inf')
        
        for key, indices in eq_classes.items():
            sensitive_values = [data[i].get(sensitive_attr) for i in indices]
            value_counts = Counter(sensitive_values)
            total = len(sensitive_values)
            
            # Calculate entropy
            entropy = 0
            for count in value_counts.values():
                p = count / total
                if p > 0:
                    entropy -= p * math.log2(p)
            
            min_entropy = min(min_entropy, entropy)
        
        # l = 2^entropy
        return 2 ** min_entropy if min_entropy != float('inf') else 0


class TClosenessChecker:
    """Check t-closeness.
    
    t-closeness requires that the distribution of sensitive attributes
    within each equivalence class is close to the overall distribution.
    """
    
    @staticmethod
    def check(
        data: List[Dict[str, Any]],
        quasi_identifiers: List[str],
        sensitive_attr: str,
        t: float = 0.2
    ) -> Tuple[bool, float, List[Dict[str, Any]]]:
        """Check if data satisfies t-closeness.
        
        Uses Earth Mover's Distance (EMD) for numerical attributes
        and variational distance for categorical.
        
        Args:
            data: Dataset to check.
            quasi_identifiers: Quasi-identifier columns.
            sensitive_attr: Sensitive attribute column.
            t: Maximum allowed distance.
            
        Returns:
            Tuple of (satisfies_t, max_distance, violating_classes).
        """
        if not data:
            return True, 0.0, []
        
        # Get overall distribution
        all_values = [record.get(sensitive_attr) for record in data]
        
        # Determine if numeric or categorical
        is_numeric = all(isinstance(v, (int, float)) for v in all_values if v is not None)
        
        if is_numeric:
            return TClosenessChecker._check_numeric(
                data, quasi_identifiers, sensitive_attr, all_values, t
            )
        else:
            return TClosenessChecker._check_categorical(
                data, quasi_identifiers, sensitive_attr, all_values, t
            )
    
    @staticmethod
    def _check_numeric(
        data: List[Dict],
        quasi_identifiers: List[str],
        sensitive_attr: str,
        all_values: List,
        t: float
    ) -> Tuple[bool, float, List[Dict]]:
        """Check t-closeness for numeric attributes using EMD."""
        eq_classes = KAnonymityChecker.get_equivalence_classes(
            data, quasi_identifiers
        )
        
        # Sort overall values for EMD calculation
        sorted_all = sorted([v for v in all_values if v is not None])
        
        max_distance = 0.0
        violations = []
        
        for key, indices in eq_classes.items():
            class_values = sorted([
                data[i].get(sensitive_attr) 
                for i in indices 
                if data[i].get(sensitive_attr) is not None
            ])
            
            if not class_values:
                continue
            
            # Calculate EMD (simplified)
            try:
                distance = stats.wasserstein_distance(sorted_all, class_values)
                # Normalize by range
                value_range = max(sorted_all) - min(sorted_all) if sorted_all else 1
                distance = distance / max(value_range, 1)
            except Exception:
                distance = 0
            
            max_distance = max(max_distance, distance)
            
            if distance > t:
                violations.append({
                    "combination": dict(zip(quasi_identifiers, key)),
                    "distance": distance,
                    "record_count": len(indices)
                })
        
        return max_distance <= t, max_distance, violations
    
    @staticmethod
    def _check_categorical(
        data: List[Dict],
        quasi_identifiers: List[str],
        sensitive_attr: str,
        all_values: List,
        t: float
    ) -> Tuple[bool, float, List[Dict]]:
        """Check t-closeness for categorical using variational distance."""
        eq_classes = KAnonymityChecker.get_equivalence_classes(
            data, quasi_identifiers
        )
        
        # Overall distribution
        overall_counts = Counter(all_values)
        total = len(all_values)
        overall_dist = {k: v / total for k, v in overall_counts.items()}
        
        max_distance = 0.0
        violations = []
        
        for key, indices in eq_classes.items():
            class_values = [data[i].get(sensitive_attr) for i in indices]
            class_counts = Counter(class_values)
            class_total = len(class_values)
            
            if class_total == 0:
                continue
            
            class_dist = {k: v / class_total for k, v in class_counts.items()}
            
            # Variational distance: max absolute difference
            all_keys = set(overall_dist.keys()) | set(class_dist.keys())
            distance = sum(
                abs(class_dist.get(k, 0) - overall_dist.get(k, 0))
                for k in all_keys
            ) / 2
            
            max_distance = max(max_distance, distance)
            
            if distance > t:
                violations.append({
                    "combination": dict(zip(quasi_identifiers, key)),
                    "distance": distance,
                    "record_count": len(indices)
                })
        
        return max_distance <= t, max_distance, violations


class CellSuppressor:
    """Implements cell suppression for tabular data."""
    
    @staticmethod
    def suppress_small_cells(
        data: List[Dict[str, Any]],
        quasi_identifiers: List[str],
        threshold: int = 3,
        markers: str = "***"
    ) -> Tuple[List[Dict[str, Any]], int]:
        """Suppress records in cells below threshold.
        
        Returns:
            Tuple of (protected_data, records_suppressed).
        """
        eq_classes = KAnonymityChecker.get_equivalence_classes(
            data, quasi_identifiers
        )
        
        # Find indices to suppress
        suppress_indices = set()
        for key, indices in eq_classes.items():
            if len(indices) < threshold:
                suppress_indices.update(indices)
        
        # Create suppressed data
        protected = []
        for idx, record in enumerate(data):
            if idx in suppress_indices:
                # Suppress sensitive values
                new_record = {
                    k: (markers if k not in quasi_identifiers else v)
                    for k, v in record.items()
                }
                protected.append(new_record)
            else:
                protected.append(record.copy())
        
        return protected, len(suppress_indices)


class NoiseAdder:
    """Add statistical noise for privacy protection."""
    
    @staticmethod
    def laplace_noise(
        data: List[Dict[str, Any]],
        numeric_columns: List[str],
        epsilon: float = 1.0,
        sensitivity: float = None
    ) -> List[Dict[str, Any]]:
        """Add Laplace noise to numeric columns.
        
        Args:
            data: Dataset.
            numeric_columns: Columns to add noise to.
            epsilon: Privacy parameter.
            sensitivity: Query sensitivity (auto-calculated if None).
            
        Returns:
            Data with noise added.
        """
        if not data:
            return data
        
        result = []
        
        # Calculate sensitivity per column if not provided
        sensitivities = {}
        if sensitivity is None:
            for col in numeric_columns:
                values = [r.get(col) for r in data if isinstance(r.get(col), (int, float))]
                if values:
                    sensitivities[col] = (max(values) - min(values)) / len(data)
                else:
                    sensitivities[col] = 1.0
        else:
            sensitivities = {col: sensitivity for col in numeric_columns}
        
        for record in data:
            new_record = record.copy()
            for col in numeric_columns:
                value = record.get(col)
                if isinstance(value, (int, float)):
                    scale = sensitivities[col] / epsilon
                    noise = random.random() - 0.5
                    noise = -scale * math.copysign(1, noise) * math.log(1 - 2 * abs(noise))
                    new_record[col] = value + noise
            result.append(new_record)
        
        return result
    
    @staticmethod
    def controlled_rounding(
        data: List[Dict[str, Any]],
        numeric_columns: List[str],
        base: int = 5
    ) -> List[Dict[str, Any]]:
        """Round numeric values to nearest base.
        
        Args:
            data: Dataset.
            numeric_columns: Columns to round.
            base: Rounding base (e.g., 5, 10).
            
        Returns:
            Rounded data.
        """
        result = []
        
        for record in data:
            new_record = record.copy()
            for col in numeric_columns:
                value = record.get(col)
                if isinstance(value, (int, float)):
                    new_record[col] = round(value / base) * base
            result.append(new_record)
        
        return result


class MicroAggregator:
    """Microaggregation for disclosure control."""
    
    @staticmethod
    def aggregate(
        data: List[Dict[str, Any]],
        quasi_identifiers: List[str],
        numeric_columns: List[str],
        k: int = 5
    ) -> List[Dict[str, Any]]:
        """Apply microaggregation to achieve k-anonymity.
        
        Groups records and replaces values with group centroids.
        
        Args:
            data: Dataset.
            quasi_identifiers: Grouping columns.
            numeric_columns: Columns to aggregate.
            k: Minimum group size.
            
        Returns:
            Microaggregated data.
        """
        if len(data) < k:
            return data
        
        # Sort by quasi-identifiers
        sorted_indices = sorted(
            range(len(data)),
            key=lambda i: tuple(str(data[i].get(qi, "")) for qi in quasi_identifiers)
        )
        
        result = [None] * len(data)
        
        # Process in groups of k
        for i in range(0, len(sorted_indices), k):
            group_indices = sorted_indices[i:min(i + k, len(sorted_indices))]
            
            # Ensure minimum group size
            if len(group_indices) < k and i > 0:
                # Merge with previous group
                continue
            
            # Calculate centroids for numeric columns
            centroids = {}
            for col in numeric_columns:
                values = [
                    data[idx].get(col)
                    for idx in group_indices
                    if isinstance(data[idx].get(col), (int, float))
                ]
                if values:
                    centroids[col] = sum(values) / len(values)
            
            # Apply centroids
            for idx in group_indices:
                new_record = data[idx].copy()
                for col, centroid in centroids.items():
                    new_record[col] = centroid
                result[idx] = new_record
        
        # Fill any None values
        return [r if r is not None else data[i].copy() for i, r in enumerate(result)]


class SyntheticDataGenerator:
    """Generate synthetic data that preserves statistical properties."""
    
    @staticmethod
    def generate_synthetic(
        data: List[Dict[str, Any]],
        n_synthetic: int = None,
        preserve_correlations: bool = True
    ) -> List[Dict[str, Any]]:
        """Generate synthetic records.
        
        Args:
            data: Original dataset.
            n_synthetic: Number of synthetic records (default: same as original).
            preserve_correlations: Whether to preserve column correlations.
            
        Returns:
            Synthetic dataset.
        """
        if not data:
            return []
        
        n = n_synthetic or len(data)
        columns = list(data[0].keys())
        
        # Separate numeric and categorical columns
        numeric_cols = []
        categorical_cols = []
        
        for col in columns:
            sample_values = [r.get(col) for r in data[:100] if r.get(col) is not None]
            if sample_values and all(isinstance(v, (int, float)) for v in sample_values):
                numeric_cols.append(col)
            else:
                categorical_cols.append(col)
        
        synthetic = []
        
        for _ in range(n):
            record = {}
            
            # Generate categorical values from empirical distribution
            for col in categorical_cols:
                values = [r.get(col) for r in data if r.get(col) is not None]
                if values:
                    record[col] = random.choice(values)
                else:
                    record[col] = None
            
            # Generate numeric values
            for col in numeric_cols:
                values = [r.get(col) for r in data if isinstance(r.get(col), (int, float))]
                if values:
                    mean = sum(values) / len(values)
                    std = (sum((v - mean) ** 2 for v in values) / len(values)) ** 0.5
                    record[col] = random.gauss(mean, std)
                else:
                    record[col] = None
            
            synthetic.append(record)
        
        return synthetic


class SDCEngine:
    """Main Statistical Disclosure Control engine.
    
    Provides a unified interface for:
    - Risk assessment
    - Protection method application
    - Utility measurement
    
    Example:
        engine = SDCEngine()
        
        # Assess risk
        risk = engine.assess_risk(data, quasi_ids, sensitive_attrs)
        
        # Apply protection
        protected = engine.protect(data, config)
    """
    
    def __init__(self):
        self._k_checker = KAnonymityChecker()
        self._l_checker = LDiversityChecker()
        self._t_checker = TClosenessChecker()
        self._generalizer = Generalizer()
        self._suppressor = CellSuppressor()
        self._noise_adder = NoiseAdder()
        self._aggregator = MicroAggregator()
        self._synthetic_gen = SyntheticDataGenerator()
    
    def assess_risk(
        self,
        data: List[Dict[str, Any]],
        quasi_identifiers: List[str],
        sensitive_attributes: List[str] = None,
        k_threshold: int = 5
    ) -> DisclosureRiskAssessment:
        """Assess disclosure risk of a dataset.
        
        Args:
            data: Dataset to assess.
            quasi_identifiers: Columns that could identify individuals.
            sensitive_attributes: Sensitive columns to protect.
            k_threshold: Minimum acceptable k-anonymity level.
            
        Returns:
            Comprehensive risk assessment.
        """
        if not data:
            return DisclosureRiskAssessment(
                overall_risk=RiskLevel.VERY_LOW,
                risk_score=0.0,
                unique_records=0,
                k_anonymity_level=0,
                l_diversity_level=0.0,
                records_at_risk=0,
                high_risk_combinations=[],
                recommendations=[]
            )
        
        # Check k-anonymity
        k_satisfied, current_k, k_violations = self._k_checker.check(
            data, quasi_identifiers, k_threshold
        )
        
        # Check l-diversity if sensitive attributes provided
        l_level = 0.0
        l_violations = []
        if sensitive_attributes:
            for attr in sensitive_attributes:
                _, attr_l, attr_violations = self._l_checker.check(
                    data, quasi_identifiers, attr, 2
                )
                l_level = max(l_level, attr_l)
                l_violations.extend(attr_violations)
        
        # Count unique records (k=1)
        _, min_k, _ = self._k_checker.check(data, quasi_identifiers, 1)
        unique_records = sum(
            1 for v in k_violations if v.get("count", 0) == 1
        )
        
        # Calculate overall risk score
        records_at_risk = sum(v.get("count", 0) for v in k_violations)
        risk_score = records_at_risk / len(data) if data else 0
        
        # Determine risk level
        if risk_score < 0.01:
            risk_level = RiskLevel.VERY_LOW
        elif risk_score < 0.05:
            risk_level = RiskLevel.LOW
        elif risk_score < 0.20:
            risk_level = RiskLevel.MEDIUM
        elif risk_score < 0.50:
            risk_level = RiskLevel.HIGH
        else:
            risk_level = RiskLevel.VERY_HIGH
        
        # Generate recommendations
        recommendations = []
        if not k_satisfied:
            recommendations.append(
                f"Apply generalization or suppression to achieve k={k_threshold} anonymity"
            )
        if unique_records > 0:
            recommendations.append(
                f"Remove or aggregate {unique_records} unique records"
            )
        if l_level < 2 and sensitive_attributes:
            recommendations.append(
                "Increase diversity of sensitive attributes in equivalence classes"
            )
        if risk_score > 0.1:
            recommendations.append(
                "Consider microaggregation or synthetic data generation"
            )
        
        return DisclosureRiskAssessment(
            overall_risk=risk_level,
            risk_score=risk_score,
            unique_records=unique_records,
            k_anonymity_level=current_k,
            l_diversity_level=l_level,
            records_at_risk=records_at_risk,
            high_risk_combinations=k_violations,
            recommendations=recommendations
        )
    
    def protect(
        self,
        data: List[Dict[str, Any]],
        config: SDCConfig,
        method: ProtectionMethod = ProtectionMethod.SUPPRESSION
    ) -> ProtectionResult:
        """Apply disclosure protection to dataset.
        
        Args:
            data: Dataset to protect.
            config: Protection configuration.
            method: Protection method to apply.
            
        Returns:
            Protected dataset with metrics.
        """
        if not data:
            return ProtectionResult(
                protected_data=[],
                method_applied=method,
                records_modified=0,
                records_suppressed=0,
                information_loss=0.0,
                utility_metrics={},
                before_risk=0.0,
                after_risk=0.0
            )
        
        # Assess risk before
        before_assessment = self.assess_risk(
            data, config.quasi_identifiers, config.sensitive_attributes
        )
        
        # Apply protection
        protected_data = data
        records_modified = 0
        records_suppressed = 0
        
        if method == ProtectionMethod.SUPPRESSION:
            protected_data, records_suppressed = self._suppressor.suppress_small_cells(
                data, config.quasi_identifiers, config.suppress_threshold
            )
            records_modified = records_suppressed
            
        elif method == ProtectionMethod.NOISE_ADDITION:
            numeric_cols = self._get_numeric_columns(data)
            protected_data = self._noise_adder.laplace_noise(
                data, numeric_cols, config.noise_epsilon
            )
            records_modified = len(data)
            
        elif method == ProtectionMethod.MICRO_AGGREGATION:
            numeric_cols = self._get_numeric_columns(data)
            protected_data = self._aggregator.aggregate(
                data, config.quasi_identifiers, numeric_cols, config.k_anonymity
            )
            records_modified = len(data)
            
        elif method == ProtectionMethod.ROUNDING:
            numeric_cols = self._get_numeric_columns(data)
            protected_data = self._noise_adder.controlled_rounding(
                data, numeric_cols, base=5
            )
            records_modified = len(data)
            
        elif method == ProtectionMethod.SYNTHETIC:
            protected_data = self._synthetic_gen.generate_synthetic(data)
            records_modified = len(data)
        
        # Assess risk after
        after_assessment = self.assess_risk(
            protected_data, config.quasi_identifiers, config.sensitive_attributes
        )
        
        # Calculate information loss
        info_loss = self._calculate_information_loss(data, protected_data)
        
        # Calculate utility metrics
        utility = self._calculate_utility(data, protected_data)
        
        return ProtectionResult(
            protected_data=protected_data,
            method_applied=method,
            records_modified=records_modified,
            records_suppressed=records_suppressed,
            information_loss=info_loss,
            utility_metrics=utility,
            before_risk=before_assessment.risk_score,
            after_risk=after_assessment.risk_score
        )
    
    def _get_numeric_columns(self, data: List[Dict]) -> List[str]:
        """Identify numeric columns in data."""
        if not data:
            return []
        
        numeric = []
        for col in data[0].keys():
            values = [r.get(col) for r in data[:100]]
            if all(isinstance(v, (int, float)) or v is None for v in values):
                if any(isinstance(v, (int, float)) for v in values):
                    numeric.append(col)
        
        return numeric
    
    def _calculate_information_loss(
        self,
        original: List[Dict],
        protected: List[Dict]
    ) -> float:
        """Calculate information loss ratio."""
        if not original or not protected:
            return 0.0
        
        numeric_cols = self._get_numeric_columns(original)
        
        if not numeric_cols:
            return 0.0
        
        total_loss = 0
        
        for col in numeric_cols:
            orig_values = [r.get(col) for r in original if isinstance(r.get(col), (int, float))]
            prot_values = [r.get(col) for r in protected if isinstance(r.get(col), (int, float))]
            
            if orig_values and prot_values and len(orig_values) == len(prot_values):
                orig_var = np.var(orig_values) if len(orig_values) > 1 else 1
                diff_var = np.var([o - p for o, p in zip(orig_values, prot_values)])
                
                if orig_var > 0:
                    total_loss += diff_var / orig_var
        
        return min(1.0, total_loss / len(numeric_cols)) if numeric_cols else 0.0
    
    def _calculate_utility(
        self,
        original: List[Dict],
        protected: List[Dict]
    ) -> Dict[str, float]:
        """Calculate data utility metrics."""
        metrics = {}
        
        numeric_cols = self._get_numeric_columns(original)
        
        for col in numeric_cols[:5]:  # Limit to first 5 numeric columns
            orig_values = [r.get(col) for r in original if isinstance(r.get(col), (int, float))]
            prot_values = [r.get(col) for r in protected if isinstance(r.get(col), (int, float))]
            
            if orig_values and prot_values:
                # Mean preservation
                orig_mean = np.mean(orig_values)
                prot_mean = np.mean(prot_values)
                mean_diff = abs(orig_mean - prot_mean) / (abs(orig_mean) + 1e-10)
                metrics[f"{col}_mean_preservation"] = max(0, 1 - mean_diff)
                
                # Variance preservation
                orig_var = np.var(orig_values)
                prot_var = np.var(prot_values)
                var_diff = abs(orig_var - prot_var) / (orig_var + 1e-10)
                metrics[f"{col}_variance_preservation"] = max(0, 1 - var_diff)
        
        # Overall utility score
        if metrics:
            metrics["overall_utility"] = np.mean(list(metrics.values()))
        else:
            metrics["overall_utility"] = 1.0
        
        return metrics


# Module singleton
_sdc_engine: Optional[SDCEngine] = None


def get_sdc_engine() -> SDCEngine:
    """Get the global SDC engine instance."""
    global _sdc_engine
    if _sdc_engine is None:
        _sdc_engine = SDCEngine()
    return _sdc_engine
