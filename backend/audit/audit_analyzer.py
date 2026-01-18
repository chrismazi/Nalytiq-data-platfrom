"""
Audit Analyzer Module

Analytics and insights from audit logs:
- Usage patterns
- Security analysis
- Compliance reports
- Anomaly detection
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from collections import defaultdict

from .audit_logger import AuditLogger, get_audit_logger, AuditEventType, AuditSeverity

logger = logging.getLogger(__name__)


class AuditAnalyzer:
    """
    Analyzes audit logs for insights and reporting.
    
    Features:
    - Usage analytics
    - Security monitoring
    - Compliance reporting
    - Trend analysis
    """
    
    def __init__(self, audit_logger: AuditLogger = None):
        """Initialize audit analyzer"""
        self.audit_logger = audit_logger or get_audit_logger()
        logger.info("AuditAnalyzer initialized")
    
    def get_usage_summary(self, days: int = 30) -> Dict:
        """
        Get usage summary for the specified period.
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Usage summary with metrics
        """
        start_date = datetime.utcnow() - timedelta(days=days)
        entries = self.audit_logger.query(start_date=start_date, limit=10000)
        
        summary = {
            "period_days": days,
            "total_events": len(entries),
            "transactions": {
                "total": 0,
                "successful": 0,
                "failed": 0
            },
            "authentications": {
                "total": 0,
                "successful": 0,
                "failed": 0
            },
            "top_services": {},
            "top_organizations": {},
            "daily_activity": {}
        }
        
        for entry in entries:
            event_type = entry.get("event_type")
            timestamp = entry.get("timestamp", "")[:10]  # Date only
            
            # Track daily activity
            summary["daily_activity"][timestamp] = \
                summary["daily_activity"].get(timestamp, 0) + 1
            
            # Transaction metrics
            if event_type == AuditEventType.TRANSACTION_COMPLETED.value:
                summary["transactions"]["total"] += 1
                summary["transactions"]["successful"] += 1
                
                service = entry.get("resource_id")
                if service:
                    summary["top_services"][service] = \
                        summary["top_services"].get(service, 0) + 1
                
            elif event_type == AuditEventType.TRANSACTION_FAILED.value:
                summary["transactions"]["total"] += 1
                summary["transactions"]["failed"] += 1
            
            # Auth metrics
            elif event_type == AuditEventType.AUTH_LOGIN_SUCCESS.value:
                summary["authentications"]["total"] += 1
                summary["authentications"]["successful"] += 1
            elif event_type == AuditEventType.AUTH_LOGIN_FAILED.value:
                summary["authentications"]["total"] += 1
                summary["authentications"]["failed"] += 1
            
            # Organization activity
            org = entry.get("organization_code")
            if org:
                summary["top_organizations"][org] = \
                    summary["top_organizations"].get(org, 0) + 1
        
        # Calculate success rates
        if summary["transactions"]["total"] > 0:
            summary["transactions"]["success_rate"] = round(
                summary["transactions"]["successful"] / summary["transactions"]["total"] * 100, 2
            )
        
        if summary["authentications"]["total"] > 0:
            summary["authentications"]["success_rate"] = round(
                summary["authentications"]["successful"] / summary["authentications"]["total"] * 100, 2
            )
        
        # Sort top lists
        summary["top_services"] = dict(
            sorted(summary["top_services"].items(), key=lambda x: x[1], reverse=True)[:10]
        )
        summary["top_organizations"] = dict(
            sorted(summary["top_organizations"].items(), key=lambda x: x[1], reverse=True)[:10]
        )
        
        return summary
    
    def get_security_report(self, days: int = 7) -> Dict:
        """
        Generate security-focused report.
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Security report with alerts and metrics
        """
        start_date = datetime.utcnow() - timedelta(days=days)
        entries = self.audit_logger.query(start_date=start_date, limit=10000)
        
        report = {
            "period_days": days,
            "security_events": {
                "signature_failures": 0,
                "access_denied": 0,
                "auth_failures": 0,
                "system_errors": 0
            },
            "certificates": {
                "issued": 0,
                "revoked": 0,
                "renewed": 0,
                "expired": 0
            },
            "failed_auth_by_ip": {},
            "access_denied_details": [],
            "alerts": []
        }
        
        for entry in entries:
            event_type = entry.get("event_type")
            
            # Security events
            if event_type == AuditEventType.SECURITY_SIGNATURE_FAILED.value:
                report["security_events"]["signature_failures"] += 1
            elif event_type == AuditEventType.ACCESS_DENIED.value:
                report["security_events"]["access_denied"] += 1
                report["access_denied_details"].append({
                    "timestamp": entry.get("timestamp"),
                    "actor": entry.get("actor_id"),
                    "action": entry.get("action")
                })
            elif event_type == AuditEventType.AUTH_LOGIN_FAILED.value:
                report["security_events"]["auth_failures"] += 1
                ip = entry.get("client_ip", "unknown")
                report["failed_auth_by_ip"][ip] = \
                    report["failed_auth_by_ip"].get(ip, 0) + 1
            elif event_type == AuditEventType.SYSTEM_ERROR.value:
                report["security_events"]["system_errors"] += 1
            
            # Certificate events
            elif event_type == AuditEventType.CERT_ISSUED.value:
                report["certificates"]["issued"] += 1
            elif event_type == AuditEventType.CERT_REVOKED.value:
                report["certificates"]["revoked"] += 1
            elif event_type == AuditEventType.CERT_RENEWED.value:
                report["certificates"]["renewed"] += 1
            elif event_type == AuditEventType.CERT_EXPIRED.value:
                report["certificates"]["expired"] += 1
        
        # Generate alerts
        if report["security_events"]["signature_failures"] > 5:
            report["alerts"].append({
                "level": "high",
                "message": f"High signature failure rate: {report['security_events']['signature_failures']} failures"
            })
        
        if report["security_events"]["auth_failures"] > 10:
            report["alerts"].append({
                "level": "medium",
                "message": f"Multiple authentication failures: {report['security_events']['auth_failures']} attempts"
            })
        
        # Check for potential brute force (many failures from same IP)
        for ip, count in report["failed_auth_by_ip"].items():
            if count > 5:
                report["alerts"].append({
                    "level": "high",
                    "message": f"Potential brute force from IP {ip}: {count} failed attempts"
                })
        
        # Limit access denied details
        report["access_denied_details"] = report["access_denied_details"][-20:]
        
        return report
    
    def get_organization_activity(
        self,
        organization_code: str,
        days: int = 30
    ) -> Dict:
        """
        Get activity report for a specific organization.
        
        Args:
            organization_code: Organization to analyze
            days: Number of days
            
        Returns:
            Organization activity report
        """
        start_date = datetime.utcnow() - timedelta(days=days)
        entries = self.audit_logger.query(
            organization_code=organization_code,
            start_date=start_date,
            limit=10000
        )
        
        activity = {
            "organization_code": organization_code,
            "period_days": days,
            "total_events": len(entries),
            "event_breakdown": {},
            "services_used": {},
            "services_provided": {},
            "daily_activity": {},
            "error_count": 0
        }
        
        for entry in entries:
            event_type = entry.get("event_type")
            timestamp = entry.get("timestamp", "")[:10]
            
            # Event breakdown
            activity["event_breakdown"][event_type] = \
                activity["event_breakdown"].get(event_type, 0) + 1
            
            # Daily activity
            activity["daily_activity"][timestamp] = \
                activity["daily_activity"].get(timestamp, 0) + 1
            
            # Track services
            if entry.get("resource_type") == "service":
                service = entry.get("resource_id")
                if service:
                    # Check if providing or consuming
                    if entry.get("actor_id") == organization_code:
                        activity["services_used"][service] = \
                            activity["services_used"].get(service, 0) + 1
                    else:
                        activity["services_provided"][service] = \
                            activity["services_provided"].get(service, 0) + 1
            
            # Count errors
            if entry.get("severity") in ["error", "critical"]:
                activity["error_count"] += 1
        
        return activity
    
    def detect_anomalies(self, baseline_days: int = 30) -> List[Dict]:
        """
        Detect potential anomalies in activity patterns.
        
        Args:
            baseline_days: Days to use for baseline calculation
            
        Returns:
            List of detected anomalies
        """
        anomalies = []
        
        # Get baseline stats
        baseline_end = datetime.utcnow() - timedelta(days=1)
        baseline_start = baseline_end - timedelta(days=baseline_days)
        baseline_entries = self.audit_logger.query(
            start_date=baseline_start,
            end_date=baseline_end,
            limit=50000
        )
        
        # Get today's stats
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        today_entries = self.audit_logger.query(
            start_date=today_start,
            limit=10000
        )
        
        if not baseline_entries:
            return anomalies
        
        # Calculate baseline averages
        daily_avg = len(baseline_entries) / baseline_days
        
        # Organization activity baselines
        org_activity = defaultdict(list)
        for entry in baseline_entries:
            org = entry.get("organization_code")
            date = entry.get("timestamp", "")[:10]
            if org:
                org_activity[(org, date)] = org_activity.get((org, date), 0) + 1
        
        org_daily_avg = defaultdict(float)
        for (org, _), count in org_activity.items():
            org_daily_avg[org] = org_daily_avg.get(org, 0) + count / baseline_days
        
        # Check for volume anomalies
        if len(today_entries) > daily_avg * 3:
            anomalies.append({
                "type": "volume_spike",
                "severity": "medium",
                "message": f"Today's activity ({len(today_entries)}) is 3x higher than average ({daily_avg:.0f})"
            })
        
        # Check for unusual organization activity
        today_org_activity = defaultdict(int)
        for entry in today_entries:
            org = entry.get("organization_code")
            if org:
                today_org_activity[org] += 1
        
        for org, count in today_org_activity.items():
            avg = org_daily_avg.get(org, daily_avg / 10)  # Default to small fraction
            if count > avg * 5 and avg > 0:
                anomalies.append({
                    "type": "org_activity_spike",
                    "severity": "low",
                    "message": f"Organization {org} activity ({count}) unusually high vs average ({avg:.0f})"
                })
        
        # Check for new organizations
        baseline_orgs = set(org for org, _ in org_activity.keys())
        today_orgs = set(today_org_activity.keys())
        new_orgs = today_orgs - baseline_orgs
        
        for org in new_orgs:
            if today_org_activity[org] > 10:
                anomalies.append({
                    "type": "new_org_activity",
                    "severity": "low",
                    "message": f"New organization {org} with {today_org_activity[org]} events"
                })
        
        return anomalies
    
    def generate_compliance_report(
        self,
        start_date: datetime,
        end_date: datetime,
        organization_code: str = None
    ) -> Dict:
        """
        Generate a compliance report for auditors.
        
        Args:
            start_date: Report period start
            end_date: Report period end
            organization_code: Optional organization filter
            
        Returns:
            Comprehensive compliance report
        """
        entries = self.audit_logger.export_for_compliance(
            start_date=start_date,
            end_date=end_date,
            organization_code=organization_code
        )
        
        report = {
            "report_generated": datetime.utcnow().isoformat(),
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
                "days": (end_date - start_date).days
            },
            "organization_filter": organization_code,
            "summary": {
                "total_events": len(entries),
                "unique_actors": len(set(e.get("actor_id") for e in entries if e.get("actor_id"))),
                "unique_organizations": len(set(e.get("organization_code") for e in entries if e.get("organization_code"))),
                "security_incidents": 0,
                "access_control_events": 0,
                "data_access_events": 0
            },
            "event_distribution": {},
            "security_summary": {
                "signature_verifications": 0,
                "signature_failures": 0,
                "access_granted": 0,
                "access_denied": 0
            },
            "integrity_verified": True,
            "sample_entries": []
        }
        
        # Analyze entries
        for entry in entries:
            event_type = entry.get("event_type")
            
            # Event distribution
            report["event_distribution"][event_type] = \
                report["event_distribution"].get(event_type, 0) + 1
            
            # Security metrics
            if event_type == AuditEventType.SECURITY_SIGNATURE_VERIFIED.value:
                report["security_summary"]["signature_verifications"] += 1
            elif event_type == AuditEventType.SECURITY_SIGNATURE_FAILED.value:
                report["security_summary"]["signature_failures"] += 1
                report["summary"]["security_incidents"] += 1
            elif event_type == AuditEventType.ACCESS_GRANTED.value:
                report["security_summary"]["access_granted"] += 1
                report["summary"]["access_control_events"] += 1
            elif event_type == AuditEventType.ACCESS_DENIED.value:
                report["security_summary"]["access_denied"] += 1
                report["summary"]["access_control_events"] += 1
                report["summary"]["security_incidents"] += 1
            elif event_type == AuditEventType.DATA_ACCESSED.value:
                report["summary"]["data_access_events"] += 1
        
        # Add sample entries (first and last 5)
        report["sample_entries"] = entries[:5] + entries[-5:] if len(entries) > 10 else entries
        
        # Verify a sample of entries for integrity
        sample_size = min(10, len(entries))
        for entry in entries[:sample_size]:
            result = self.audit_logger.verify_integrity(entry.get("id"))
            if not result.get("valid"):
                report["integrity_verified"] = False
                break
        
        return report


# Singleton instance
_audit_analyzer: Optional[AuditAnalyzer] = None


def get_audit_analyzer() -> AuditAnalyzer:
    """Get the global AuditAnalyzer instance"""
    global _audit_analyzer
    if _audit_analyzer is None:
        _audit_analyzer = AuditAnalyzer()
    return _audit_analyzer
