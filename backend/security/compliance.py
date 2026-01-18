"""
Compliance Management Module

Regulatory compliance for data operations:
- GDPR compliance tracking
- Rwanda Data Protection Law compliance
- Consent management
- Data retention policies
- Compliance reporting
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from enum import Enum
import uuid

logger = logging.getLogger(__name__)


class ComplianceRegulation(str, Enum):
    """Supported compliance regulations"""
    GDPR = "gdpr"                           # EU General Data Protection Regulation
    RWANDA_DPL = "rwanda_dpl"               # Rwanda Data Protection Law
    STATISTICS_ACT = "statistics_act"       # Rwanda Statistics Act
    HEALTH_DATA = "health_data"             # Health data regulations
    FINANCIAL_DATA = "financial_data"       # Financial data regulations


class ConsentType(str, Enum):
    """Types of data consent"""
    DATA_PROCESSING = "data_processing"
    DATA_SHARING = "data_sharing"
    ANALYTICS = "analytics"
    RESEARCH = "research"
    MARKETING = "marketing"


class DataRetentionCategory(str, Enum):
    """Data retention categories"""
    TEMPORARY = "temporary"       # 30 days
    SHORT_TERM = "short_term"     # 1 year
    MEDIUM_TERM = "medium_term"   # 5 years
    LONG_TERM = "long_term"       # 10 years
    PERMANENT = "permanent"       # No expiry
    LEGAL_HOLD = "legal_hold"     # Until released


RETENTION_PERIODS = {
    DataRetentionCategory.TEMPORARY: timedelta(days=30),
    DataRetentionCategory.SHORT_TERM: timedelta(days=365),
    DataRetentionCategory.MEDIUM_TERM: timedelta(days=365 * 5),
    DataRetentionCategory.LONG_TERM: timedelta(days=365 * 10),
    DataRetentionCategory.PERMANENT: None,
    DataRetentionCategory.LEGAL_HOLD: None,
}


class ComplianceManager:
    """
    Compliance management for R-NDIP.
    
    Features:
    - Regulation tracking
    - Consent management
    - Data retention policies
    - Compliance auditing
    - Breach reporting
    """
    
    COMPLIANCE_FILE = os.path.join(os.path.dirname(__file__), '..', 'data', 'compliance.json')
    
    def __init__(self):
        """Initialize ComplianceManager"""
        self._consents: Dict[str, Dict] = {}           # subject_id -> consents
        self._retention_policies: Dict[str, Dict] = {} # dataset_id -> policy
        self._data_processing_records: List[Dict] = []
        self._breaches: List[Dict] = []
        self._load_data()
        logger.info("ComplianceManager initialized")
    
    def _load_data(self):
        """Load compliance data"""
        os.makedirs(os.path.dirname(self.COMPLIANCE_FILE), exist_ok=True)
        
        if os.path.exists(self.COMPLIANCE_FILE):
            try:
                with open(self.COMPLIANCE_FILE, 'r') as f:
                    data = json.load(f)
                    self._consents = data.get("consents", {})
                    self._retention_policies = data.get("retention_policies", {})
                    self._data_processing_records = data.get("processing_records", [])
                    self._breaches = data.get("breaches", [])
            except Exception as e:
                logger.warning(f"Failed to load compliance data: {e}")
    
    def _save_data(self):
        """Save compliance data"""
        try:
            data = {
                "consents": self._consents,
                "retention_policies": self._retention_policies,
                "processing_records": self._data_processing_records[-1000:],
                "breaches": self._breaches
            }
            with open(self.COMPLIANCE_FILE, 'w') as f:
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save compliance data: {e}")
    
    # ==========================================
    # CONSENT MANAGEMENT
    # ==========================================
    
    def record_consent(
        self,
        subject_id: str,
        consent_type: ConsentType,
        purpose: str,
        granted: bool,
        expiry_days: int = 365,
        organization_code: str = None,
        collected_by: str = None
    ) -> Dict:
        """
        Record consent from a data subject.
        
        Args:
            subject_id: Data subject identifier
            consent_type: Type of consent
            purpose: Purpose of data processing
            granted: Whether consent was granted
            expiry_days: Days until consent expires
            organization_code: Collecting organization
            collected_by: Who collected the consent
            
        Returns:
            Consent record
        """
        consent_id = str(uuid.uuid4())
        now = datetime.utcnow()
        
        if subject_id not in self._consents:
            self._consents[subject_id] = {}
        
        consent_record = {
            "id": consent_id,
            "type": consent_type.value,
            "purpose": purpose,
            "granted": granted,
            "collected_at": now.isoformat(),
            "expires_at": (now + timedelta(days=expiry_days)).isoformat() if granted else None,
            "organization_code": organization_code,
            "collected_by": collected_by,
            "status": "active" if granted else "denied",
            "withdrawal_date": None
        }
        
        self._consents[subject_id][consent_id] = consent_record
        self._save_data()
        
        logger.info(f"Consent recorded for subject {subject_id}: {consent_type.value} = {granted}")
        
        return consent_record
    
    def withdraw_consent(
        self,
        subject_id: str,
        consent_id: str,
        reason: str = None
    ) -> bool:
        """Withdraw a previously granted consent"""
        if subject_id not in self._consents:
            return False
        
        if consent_id not in self._consents[subject_id]:
            return False
        
        consent = self._consents[subject_id][consent_id]
        consent["status"] = "withdrawn"
        consent["withdrawal_date"] = datetime.utcnow().isoformat()
        consent["withdrawal_reason"] = reason
        
        self._save_data()
        
        logger.info(f"Consent withdrawn: {consent_id}")
        return True
    
    def check_consent(
        self,
        subject_id: str,
        consent_type: ConsentType,
        organization_code: str = None
    ) -> Dict:
        """
        Check if valid consent exists for a subject.
        
        Args:
            subject_id: Data subject identifier
            consent_type: Type of consent needed
            organization_code: Organization checking consent
            
        Returns:
            Consent status
        """
        if subject_id not in self._consents:
            return {
                "has_consent": False,
                "reason": "no_consent_records"
            }
        
        now = datetime.utcnow()
        
        for consent_id, consent in self._consents[subject_id].items():
            if consent["type"] != consent_type.value:
                continue
            
            if consent["status"] != "active":
                continue
            
            if consent["expires_at"]:
                expires = datetime.fromisoformat(consent["expires_at"])
                if expires < now:
                    consent["status"] = "expired"
                    continue
            
            if organization_code and consent.get("organization_code"):
                if consent["organization_code"] != organization_code:
                    continue
            
            return {
                "has_consent": True,
                "consent_id": consent_id,
                "expires_at": consent["expires_at"],
                "purpose": consent["purpose"]
            }
        
        return {
            "has_consent": False,
            "reason": "no_valid_consent"
        }
    
    def get_subject_consents(self, subject_id: str) -> List[Dict]:
        """Get all consent records for a subject"""
        if subject_id not in self._consents:
            return []
        
        return list(self._consents[subject_id].values())
    
    # ==========================================
    # DATA RETENTION
    # ==========================================
    
    def set_retention_policy(
        self,
        dataset_id: str,
        category: DataRetentionCategory,
        regulation: ComplianceRegulation,
        justification: str = None
    ) -> Dict:
        """Set data retention policy for a dataset"""
        policy = {
            "dataset_id": dataset_id,
            "category": category.value,
            "regulation": regulation.value,
            "retention_period": str(RETENTION_PERIODS.get(category)),
            "justification": justification,
            "created_at": datetime.utcnow().isoformat()
        }
        
        self._retention_policies[dataset_id] = policy
        self._save_data()
        
        return policy
    
    def check_retention(self, dataset_id: str, created_at: datetime) -> Dict:
        """Check if data should be retained or deleted"""
        policy = self._retention_policies.get(dataset_id)
        
        if not policy:
            return {
                "should_retain": True,
                "reason": "no_policy_defined"
            }
        
        category = DataRetentionCategory(policy["category"])
        retention_period = RETENTION_PERIODS.get(category)
        
        if retention_period is None:
            return {
                "should_retain": True,
                "reason": "permanent_or_legal_hold"
            }
        
        expiry_date = created_at + retention_period
        now = datetime.utcnow()
        
        if now > expiry_date:
            return {
                "should_retain": False,
                "reason": "retention_period_expired",
                "expired_on": expiry_date.isoformat()
            }
        
        return {
            "should_retain": True,
            "expires_on": expiry_date.isoformat(),
            "days_remaining": (expiry_date - now).days
        }
    
    # ==========================================
    # DATA PROCESSING RECORDS (Article 30 GDPR)
    # ==========================================
    
    def record_processing_activity(
        self,
        dataset_id: str,
        activity_type: str,
        purpose: str,
        data_categories: List[str],
        recipients: List[str] = None,
        transfers_outside_rw: bool = False,
        legal_basis: str = None,
        organization_code: str = None,
        user_id: str = None
    ) -> Dict:
        """
        Record a data processing activity for compliance.
        
        This maintains the required records under GDPR Article 30 and
        Rwanda Data Protection Law.
        """
        record = {
            "id": str(uuid.uuid4()),
            "timestamp": datetime.utcnow().isoformat(),
            "dataset_id": dataset_id,
            "activity_type": activity_type,
            "purpose": purpose,
            "data_categories": data_categories,
            "recipients": recipients or [],
            "transfers_outside_rw": transfers_outside_rw,
            "legal_basis": legal_basis,
            "organization_code": organization_code,
            "user_id": user_id
        }
        
        self._data_processing_records.append(record)
        
        # Trim old records (keep last 10000)
        if len(self._data_processing_records) > 10000:
            self._data_processing_records = self._data_processing_records[-10000:]
        
        self._save_data()
        
        return record
    
    # ==========================================
    # BREACH MANAGEMENT
    # ==========================================
    
    def report_breach(
        self,
        description: str,
        severity: str,  # low, medium, high, critical
        affected_datasets: List[str],
        affected_subjects_count: int,
        data_categories_affected: List[str],
        detected_by: str,
        organization_code: str = None
    ) -> Dict:
        """
        Report a data breach incident.
        
        Under GDPR and Rwanda DPL, breaches must be reported within 72 hours.
        """
        breach_id = str(uuid.uuid4())
        now = datetime.utcnow()
        
        breach = {
            "id": breach_id,
            "description": description,
            "severity": severity,
            "affected_datasets": affected_datasets,
            "affected_subjects_count": affected_subjects_count,
            "data_categories_affected": data_categories_affected,
            "detected_at": now.isoformat(),
            "detected_by": detected_by,
            "organization_code": organization_code,
            "status": "open",
            "notification_deadline": (now + timedelta(hours=72)).isoformat(),
            "authority_notified": False,
            "subjects_notified": False,
            "remediation_steps": [],
            "closed_at": None
        }
        
        self._breaches.append(breach)
        self._save_data()
        
        logger.critical(f"DATA BREACH REPORTED: {breach_id} - {severity} severity")
        
        return breach
    
    def update_breach(
        self,
        breach_id: str,
        status: str = None,
        remediation_step: str = None,
        authority_notified: bool = None,
        subjects_notified: bool = None
    ) -> Optional[Dict]:
        """Update a breach record"""
        for breach in self._breaches:
            if breach["id"] == breach_id:
                if status:
                    breach["status"] = status
                    if status == "closed":
                        breach["closed_at"] = datetime.utcnow().isoformat()
                
                if remediation_step:
                    breach["remediation_steps"].append({
                        "step": remediation_step,
                        "added_at": datetime.utcnow().isoformat()
                    })
                
                if authority_notified is not None:
                    breach["authority_notified"] = authority_notified
                
                if subjects_notified is not None:
                    breach["subjects_notified"] = subjects_notified
                
                self._save_data()
                return breach
        
        return None
    
    # ==========================================
    # COMPLIANCE REPORTING
    # ==========================================
    
    def generate_compliance_report(
        self,
        regulation: ComplianceRegulation = None,
        organization_code: str = None,
        start_date: datetime = None,
        end_date: datetime = None
    ) -> Dict:
        """
        Generate a compliance report.
        
        Args:
            regulation: Filter by regulation
            organization_code: Filter by organization
            start_date: Report start date
            end_date: Report end date
            
        Returns:
            Comprehensive compliance report
        """
        end_date = end_date or datetime.utcnow()
        start_date = start_date or (end_date - timedelta(days=30))
        
        # Filter processing records
        processing = [
            r for r in self._data_processing_records
            if start_date <= datetime.fromisoformat(r["timestamp"]) <= end_date
        ]
        
        if organization_code:
            processing = [r for r in processing if r.get("organization_code") == organization_code]
        
        # Consent statistics
        total_consents = sum(len(c) for c in self._consents.values())
        active_consents = sum(
            1 for consents in self._consents.values()
            for c in consents.values()
            if c["status"] == "active"
        )
        
        # Breach summary
        open_breaches = [b for b in self._breaches if b["status"] == "open"]
        
        # Retention policy coverage
        datasets_with_policy = len(self._retention_policies)
        
        report = {
            "report_id": str(uuid.uuid4()),
            "generated_at": datetime.utcnow().isoformat(),
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "organization_code": organization_code,
            "regulation": regulation.value if regulation else "all",
            
            "summary": {
                "processing_activities": len(processing),
                "total_consent_records": total_consents,
                "active_consents": active_consents,
                "datasets_with_retention_policy": datasets_with_policy,
                "open_breaches": len(open_breaches)
            },
            
            "processing_activities": {
                "total": len(processing),
                "by_type": {},
                "by_purpose": {},
                "cross_border_transfers": sum(1 for p in processing if p.get("transfers_outside_rw"))
            },
            
            "consent_status": {
                "total": total_consents,
                "active": active_consents,
                "withdrawn": sum(
                    1 for consents in self._consents.values()
                    for c in consents.values()
                    if c["status"] == "withdrawn"
                ),
                "expired": sum(
                    1 for consents in self._consents.values()
                    for c in consents.values()
                    if c["status"] == "expired"
                )
            },
            
            "breaches": {
                "total": len(self._breaches),
                "open": len(open_breaches),
                "critical": sum(1 for b in self._breaches if b["severity"] == "critical"),
                "pending_notification": sum(
                    1 for b in open_breaches
                    if not b["authority_notified"]
                )
            },
            
            "recommendations": []
        }
        
        # Add recommendations
        if open_breaches:
            report["recommendations"].append({
                "priority": "high",
                "category": "breach",
                "message": f"There are {len(open_breaches)} open breach incidents requiring attention"
            })
        
        for b in open_breaches:
            if not b["authority_notified"]:
                deadline = datetime.fromisoformat(b["notification_deadline"])
                if datetime.utcnow() > deadline:
                    report["recommendations"].append({
                        "priority": "critical",
                        "category": "breach",
                        "message": f"Breach {b['id'][:8]} has exceeded 72-hour notification deadline"
                    })
        
        return report
    
    def get_statistics(self) -> Dict:
        """Get compliance statistics"""
        return {
            "total_consent_records": sum(len(c) for c in self._consents.values()),
            "total_subjects_with_consent": len(self._consents),
            "datasets_with_retention_policy": len(self._retention_policies),
            "processing_records": len(self._data_processing_records),
            "total_breaches": len(self._breaches),
            "open_breaches": sum(1 for b in self._breaches if b["status"] == "open")
        }


# Singleton instance
_compliance_manager: Optional[ComplianceManager] = None


def get_compliance_manager() -> ComplianceManager:
    """Get the global ComplianceManager instance"""
    global _compliance_manager
    if _compliance_manager is None:
        _compliance_manager = ComplianceManager()
    return _compliance_manager
