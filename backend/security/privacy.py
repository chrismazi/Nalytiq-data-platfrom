"""
Privacy Guard Module

Data privacy and PII protection for federated queries:
- PII detection and classification
- Data masking and anonymization
- Redaction policies
- Privacy-preserving transformations
"""

import re
import hashlib
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any, Set
from enum import Enum
import json

logger = logging.getLogger(__name__)


class PIIType(str, Enum):
    """Types of Personally Identifiable Information"""
    NAME = "name"
    EMAIL = "email"
    PHONE = "phone"
    ID_NUMBER = "id_number"
    ADDRESS = "address"
    DATE_OF_BIRTH = "date_of_birth"
    FINANCIAL = "financial"
    HEALTH = "health"
    BIOMETRIC = "biometric"
    LOCATION = "location"
    IP_ADDRESS = "ip_address"
    DEVICE_ID = "device_id"


class MaskingStrategy(str, Enum):
    """Data masking strategies"""
    REDACT = "redact"           # Replace with [REDACTED]
    HASH = "hash"               # One-way hash
    PARTIAL = "partial"         # Show partial (e.g., ***1234)
    GENERALIZE = "generalize"   # Generalize (e.g., age -> age range)
    NOISE = "noise"             # Add statistical noise
    SUPPRESS = "suppress"       # Remove entirely
    ENCRYPT = "encrypt"         # Reversible encryption


# PII detection patterns
PII_PATTERNS = {
    PIIType.EMAIL: r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
    PIIType.PHONE: r'\b(?:\+?250|0)?7[2-9]\d{7}\b',  # Rwanda phone format
    PIIType.ID_NUMBER: r'\b1\d{15}\b',  # Rwanda National ID format
    PIIType.IP_ADDRESS: r'\b(?:\d{1,3}\.){3}\d{1,3}\b',
    PIIType.DATE_OF_BIRTH: r'\b\d{4}[-/]\d{2}[-/]\d{2}\b',
}

# Sensitive column name patterns
SENSITIVE_COLUMNS = {
    PIIType.NAME: ['name', 'first_name', 'last_name', 'full_name', 'surname', 'izina'],
    PIIType.EMAIL: ['email', 'e_mail', 'email_address'],
    PIIType.PHONE: ['phone', 'telephone', 'mobile', 'telefone', 'tefoni'],
    PIIType.ID_NUMBER: ['national_id', 'nid', 'id_number', 'passport', 'indangamuntu'],
    PIIType.ADDRESS: ['address', 'street', 'city', 'district', 'sector', 'cell', 'village', 'aderesi'],
    PIIType.DATE_OF_BIRTH: ['dob', 'date_of_birth', 'birth_date', 'birthday', 'itariki_yavutse'],
    PIIType.FINANCIAL: ['salary', 'income', 'bank_account', 'credit_card', 'payment'],
    PIIType.HEALTH: ['diagnosis', 'condition', 'medical', 'treatment', 'medication', 'blood_type'],
    PIIType.LOCATION: ['latitude', 'longitude', 'gps', 'coordinates', 'geolocation'],
}


class PrivacyGuard:
    """
    Privacy protection for data operations.
    
    Features:
    - PII detection in data and schemas
    - Configurable masking strategies
    - Column-level privacy policies
    - Audit trail for privacy operations
    """
    
    def __init__(self):
        """Initialize PrivacyGuard"""
        self._policies: Dict[str, Dict] = {}  # dataset_id -> column policies
        self._default_strategy = MaskingStrategy.REDACT
        self._privacy_log: List[Dict] = []
        logger.info("PrivacyGuard initialized")
    
    def detect_pii_in_column(self, column_name: str) -> List[PIIType]:
        """Detect potential PII types based on column name"""
        detected = []
        column_lower = column_name.lower()
        
        for pii_type, patterns in SENSITIVE_COLUMNS.items():
            for pattern in patterns:
                if pattern in column_lower:
                    detected.append(pii_type)
                    break
        
        return detected
    
    def detect_pii_in_value(self, value: str) -> List[PIIType]:
        """Detect PII in a string value using regex patterns"""
        detected = []
        
        for pii_type, pattern in PII_PATTERNS.items():
            if re.search(pattern, str(value), re.IGNORECASE):
                detected.append(pii_type)
        
        return detected
    
    def scan_schema(self, schema: Dict[str, Dict]) -> Dict[str, List[PIIType]]:
        """
        Scan a dataset schema for potential PII columns.
        
        Args:
            schema: Column name -> column info mapping
            
        Returns:
            Column name -> detected PII types
        """
        results = {}
        
        for column_name, column_info in schema.items():
            detected = self.detect_pii_in_column(column_name)
            
            # Also check column description if available
            description = column_info.get("description", "")
            if description:
                for pii_type, patterns in SENSITIVE_COLUMNS.items():
                    for pattern in patterns:
                        if pattern in description.lower() and pii_type not in detected:
                            detected.append(pii_type)
            
            if detected:
                results[column_name] = detected
        
        return results
    
    def set_policy(
        self,
        dataset_id: str,
        column_name: str,
        pii_types: List[PIIType],
        strategy: MaskingStrategy,
        config: Dict = None
    ):
        """
        Set privacy policy for a dataset column.
        
        Args:
            dataset_id: Dataset identifier
            column_name: Column name
            pii_types: Types of PII in this column
            strategy: Masking strategy to apply
            config: Strategy-specific configuration
        """
        if dataset_id not in self._policies:
            self._policies[dataset_id] = {}
        
        self._policies[dataset_id][column_name] = {
            "pii_types": [p.value for p in pii_types],
            "strategy": strategy.value,
            "config": config or {},
            "created_at": datetime.utcnow().isoformat()
        }
        
        logger.info(f"Privacy policy set for {dataset_id}.{column_name}: {strategy.value}")
    
    def mask_value(
        self,
        value: Any,
        strategy: MaskingStrategy,
        pii_type: PIIType = None,
        config: Dict = None
    ) -> Any:
        """
        Apply masking strategy to a value.
        
        Args:
            value: Value to mask
            strategy: Masking strategy
            pii_type: Type of PII (for strategy-specific handling)
            config: Strategy configuration
            
        Returns:
            Masked value
        """
        if value is None:
            return None
        
        config = config or {}
        str_value = str(value)
        
        if strategy == MaskingStrategy.REDACT:
            return "[REDACTED]"
        
        elif strategy == MaskingStrategy.HASH:
            salt = config.get("salt", "r-ndip-privacy")
            hashed = hashlib.sha256(f"{salt}{str_value}".encode()).hexdigest()
            return hashed[:16]  # Truncated hash
        
        elif strategy == MaskingStrategy.PARTIAL:
            visible_chars = config.get("visible_chars", 4)
            if len(str_value) <= visible_chars:
                return "*" * len(str_value)
            return "*" * (len(str_value) - visible_chars) + str_value[-visible_chars:]
        
        elif strategy == MaskingStrategy.GENERALIZE:
            # Type-specific generalization
            if pii_type == PIIType.DATE_OF_BIRTH:
                # Convert to age range
                try:
                    from datetime import datetime
                    birth_year = int(str_value[:4])
                    age = datetime.now().year - birth_year
                    if age < 18:
                        return "Under 18"
                    elif age < 30:
                        return "18-29"
                    elif age < 45:
                        return "30-44"
                    elif age < 60:
                        return "45-59"
                    else:
                        return "60+"
                except:
                    return "[GENERALIZED]"
            
            elif pii_type == PIIType.ADDRESS:
                # Keep only district level
                return config.get("generalized_value", "[LOCATION]")
            
            return "[GENERALIZED]"
        
        elif strategy == MaskingStrategy.NOISE:
            # Add noise to numeric values
            try:
                import random
                num_value = float(value)
                noise_percent = config.get("noise_percent", 0.1)
                noise = num_value * noise_percent * (random.random() * 2 - 1)
                return round(num_value + noise, 2)
            except:
                return value
        
        elif strategy == MaskingStrategy.SUPPRESS:
            return None
        
        else:
            return "[PROTECTED]"
    
    def apply_privacy(
        self,
        dataset_id: str,
        data: List[Dict],
        requesting_org: str = None,
        user_id: str = None
    ) -> Dict:
        """
        Apply privacy policies to dataset records.
        
        Args:
            dataset_id: Dataset identifier
            data: List of records
            requesting_org: Organization requesting data
            user_id: User requesting data
            
        Returns:
            Protected data with privacy applied
        """
        start_time = datetime.utcnow()
        
        policies = self._policies.get(dataset_id, {})
        
        if not policies:
            # No policies - return as-is but log
            self._log_privacy_operation(
                dataset_id=dataset_id,
                operation="passthrough",
                records_processed=len(data),
                columns_masked=0,
                requesting_org=requesting_org,
                user_id=user_id
            )
            return {
                "data": data,
                "privacy_applied": False,
                "message": "No privacy policies defined for this dataset"
            }
        
        # Apply policies
        protected_data = []
        columns_masked = set()
        
        for record in data:
            protected_record = {}
            
            for column, value in record.items():
                if column in policies:
                    policy = policies[column]
                    strategy = MaskingStrategy(policy["strategy"])
                    pii_types = [PIIType(t) for t in policy["pii_types"]]
                    
                    protected_record[column] = self.mask_value(
                        value=value,
                        strategy=strategy,
                        pii_type=pii_types[0] if pii_types else None,
                        config=policy.get("config")
                    )
                    columns_masked.add(column)
                else:
                    protected_record[column] = value
            
            protected_data.append(protected_record)
        
        duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        
        # Log operation
        self._log_privacy_operation(
            dataset_id=dataset_id,
            operation="mask",
            records_processed=len(data),
            columns_masked=len(columns_masked),
            masked_columns=list(columns_masked),
            requesting_org=requesting_org,
            user_id=user_id,
            duration_ms=duration_ms
        )
        
        return {
            "data": protected_data,
            "privacy_applied": True,
            "records_processed": len(data),
            "columns_masked": list(columns_masked),
            "duration_ms": duration_ms
        }
    
    def _log_privacy_operation(self, **kwargs):
        """Log privacy operation for audit"""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            **kwargs
        }
        self._privacy_log.append(log_entry)
        
        # Trim log
        if len(self._privacy_log) > 5000:
            self._privacy_log = self._privacy_log[-5000:]
    
    def get_dataset_policies(self, dataset_id: str) -> Dict:
        """Get all privacy policies for a dataset"""
        return self._policies.get(dataset_id, {})
    
    def auto_configure_policies(
        self,
        dataset_id: str,
        schema: Dict[str, Dict],
        default_strategy: MaskingStrategy = MaskingStrategy.REDACT
    ) -> Dict:
        """
        Automatically configure privacy policies based on schema scan.
        
        Args:
            dataset_id: Dataset identifier
            schema: Dataset schema
            default_strategy: Default masking strategy
            
        Returns:
            Configuration results
        """
        detected = self.scan_schema(schema)
        configured = []
        
        for column_name, pii_types in detected.items():
            self.set_policy(
                dataset_id=dataset_id,
                column_name=column_name,
                pii_types=pii_types,
                strategy=default_strategy
            )
            configured.append({
                "column": column_name,
                "pii_types": [p.value for p in pii_types],
                "strategy": default_strategy.value
            })
        
        return {
            "dataset_id": dataset_id,
            "columns_configured": len(configured),
            "policies": configured
        }
    
    def get_privacy_report(self, dataset_id: str = None) -> Dict:
        """Generate privacy report"""
        log = self._privacy_log
        
        if dataset_id:
            log = [l for l in log if l.get("dataset_id") == dataset_id]
        
        return {
            "total_operations": len(log),
            "total_records_processed": sum(l.get("records_processed", 0) for l in log),
            "datasets_protected": len(self._policies),
            "columns_protected": sum(len(cols) for cols in self._policies.values()),
            "recent_operations": log[-20:]
        }


# Singleton instance
_privacy_guard: Optional[PrivacyGuard] = None


def get_privacy_guard() -> PrivacyGuard:
    """Get the global PrivacyGuard instance"""
    global _privacy_guard
    if _privacy_guard is None:
        _privacy_guard = PrivacyGuard()
    return _privacy_guard
