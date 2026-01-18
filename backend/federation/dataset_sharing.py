"""
Dataset Sharing Module

Manages dataset sharing between organizations:
- Sharing requests
- Approval workflow
- Access tracking
- Revocation
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict
from enum import Enum
import uuid

from .data_catalog import get_data_catalog, DataAccessLevel

logger = logging.getLogger(__name__)


class RequestStatus(str, Enum):
    """Status of access requests"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"
    REVOKED = "revoked"


class DatasetSharingManager:
    """
    Manages dataset sharing between organizations.
    
    Features:
    - Access request workflow
    - Approval management
    - Share tracking
    - Revocation
    """
    
    SHARES_FILE = os.path.join(os.path.dirname(__file__), '..', 'data', 'dataset_shares.json')
    REQUESTS_FILE = os.path.join(os.path.dirname(__file__), '..', 'data', 'share_requests.json')
    
    def __init__(self):
        """Initialize sharing manager"""
        self._shares: Dict[str, Dict] = {}
        self._requests: Dict[str, Dict] = {}
        self._load_data()
        logger.info("DatasetSharingManager initialized")
    
    def _load_data(self):
        """Load data from files"""
        os.makedirs(os.path.dirname(self.SHARES_FILE), exist_ok=True)
        
        if os.path.exists(self.SHARES_FILE):
            try:
                with open(self.SHARES_FILE, 'r') as f:
                    self._shares = json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load shares: {e}")
        
        if os.path.exists(self.REQUESTS_FILE):
            try:
                with open(self.REQUESTS_FILE, 'r') as f:
                    self._requests = json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load requests: {e}")
    
    def _save_shares(self):
        """Save shares to file"""
        try:
            with open(self.SHARES_FILE, 'w') as f:
                json.dump(self._shares, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save shares: {e}")
    
    def _save_requests(self):
        """Save requests to file"""
        try:
            with open(self.REQUESTS_FILE, 'w') as f:
                json.dump(self._requests, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save requests: {e}")
    
    def request_access(
        self,
        dataset_id: str,
        requester_org: str,
        requester_name: str,
        requester_email: str,
        purpose: str,
        duration_days: int = 365,
        access_type: str = "read"
    ) -> Dict:
        """
        Request access to a dataset.
        
        Args:
            dataset_id: Target dataset ID
            requester_org: Requesting organization code
            requester_name: Name of requester
            requester_email: Contact email
            purpose: Purpose of access
            duration_days: Requested access duration
            access_type: Type of access (read, download, query)
            
        Returns:
            Access request record
        """
        catalog = get_data_catalog()
        dataset = catalog.get_dataset(dataset_id)
        
        if not dataset:
            raise ValueError(f"Dataset not found: {dataset_id}")
        
        # Check if access level allows requesting
        if dataset["access_level"] == DataAccessLevel.INTERNAL.value:
            if requester_org != dataset["organization_code"]:
                raise ValueError("Internal datasets cannot be shared externally")
        
        request_id = str(uuid.uuid4())
        now = datetime.utcnow()
        
        request = {
            "id": request_id,
            "dataset_id": dataset_id,
            "dataset_name": dataset["name"],
            "owner_org": dataset["organization_code"],
            "requester_org": requester_org,
            "requester_name": requester_name,
            "requester_email": requester_email,
            "purpose": purpose,
            "access_type": access_type,
            "duration_days": duration_days,
            "status": RequestStatus.PENDING.value,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
            "reviewed_at": None,
            "reviewed_by": None,
            "review_notes": None
        }
        
        # Auto-approve public datasets
        if dataset["access_level"] == DataAccessLevel.PUBLIC.value:
            request["status"] = RequestStatus.APPROVED.value
            request["reviewed_at"] = now.isoformat()
            request["reviewed_by"] = "system"
            request["review_notes"] = "Auto-approved (public dataset)"
            
            # Create share immediately
            self._create_share(request)
        
        self._requests[request_id] = request
        self._save_requests()
        
        logger.info(f"Access request submitted: {requester_org} -> {dataset['name']}")
        return request
    
    def approve_request(
        self,
        request_id: str,
        reviewer_name: str,
        notes: str = None,
        custom_duration_days: int = None
    ) -> Dict:
        """
        Approve an access request.
        
        Args:
            request_id: Request ID
            reviewer_name: Name of approver
            notes: Optional review notes
            custom_duration_days: Override requested duration
            
        Returns:
            Updated request
        """
        if request_id not in self._requests:
            raise ValueError(f"Request not found: {request_id}")
        
        request = self._requests[request_id]
        
        if request["status"] != RequestStatus.PENDING.value:
            raise ValueError(f"Request is not pending: {request['status']}")
        
        now = datetime.utcnow()
        
        request["status"] = RequestStatus.APPROVED.value
        request["reviewed_at"] = now.isoformat()
        request["reviewed_by"] = reviewer_name
        request["review_notes"] = notes
        request["updated_at"] = now.isoformat()
        
        if custom_duration_days:
            request["duration_days"] = custom_duration_days
        
        # Create share
        self._create_share(request)
        
        self._requests[request_id] = request
        self._save_requests()
        
        logger.info(f"Request approved: {request_id}")
        return request
    
    def reject_request(
        self,
        request_id: str,
        reviewer_name: str,
        reason: str
    ) -> Dict:
        """
        Reject an access request.
        
        Args:
            request_id: Request ID
            reviewer_name: Name of reviewer
            reason: Rejection reason
            
        Returns:
            Updated request
        """
        if request_id not in self._requests:
            raise ValueError(f"Request not found: {request_id}")
        
        request = self._requests[request_id]
        
        if request["status"] != RequestStatus.PENDING.value:
            raise ValueError(f"Request is not pending: {request['status']}")
        
        now = datetime.utcnow()
        
        request["status"] = RequestStatus.REJECTED.value
        request["reviewed_at"] = now.isoformat()
        request["reviewed_by"] = reviewer_name
        request["review_notes"] = reason
        request["updated_at"] = now.isoformat()
        
        self._requests[request_id] = request
        self._save_requests()
        
        logger.info(f"Request rejected: {request_id}")
        return request
    
    def _create_share(self, request: Dict):
        """Create a share from an approved request"""
        share_id = str(uuid.uuid4())
        now = datetime.utcnow()
        expires_at = now + timedelta(days=request["duration_days"])
        
        share = {
            "id": share_id,
            "request_id": request["id"],
            "dataset_id": request["dataset_id"],
            "dataset_name": request["dataset_name"],
            "owner_org": request["owner_org"],
            "shared_with_org": request["requester_org"],
            "access_type": request["access_type"],
            "granted_at": now.isoformat(),
            "expires_at": expires_at.isoformat(),
            "status": "active",
            "access_count": 0,
            "last_accessed": None
        }
        
        self._shares[share_id] = share
        self._save_shares()
        
        logger.info(f"Share created: {share_id}")
    
    def check_access(
        self,
        dataset_id: str,
        organization_code: str
    ) -> Dict:
        """
        Check if an organization has access to a dataset.
        
        Args:
            dataset_id: Dataset ID
            organization_code: Organization code
            
        Returns:
            Access status
        """
        catalog = get_data_catalog()
        dataset = catalog.get_dataset(dataset_id)
        
        if not dataset:
            return {"has_access": False, "reason": "dataset_not_found"}
        
        # Owner always has access
        if dataset["organization_code"] == organization_code:
            return {
                "has_access": True,
                "access_type": "owner",
                "expires_at": None
            }
        
        # Public datasets are accessible
        if dataset["access_level"] == DataAccessLevel.PUBLIC.value:
            return {
                "has_access": True,
                "access_type": "public",
                "expires_at": None
            }
        
        # Check for active share
        now = datetime.utcnow()
        
        for share in self._shares.values():
            if (share["dataset_id"] == dataset_id and
                share["shared_with_org"] == organization_code and
                share["status"] == "active"):
                
                expires = datetime.fromisoformat(share["expires_at"])
                if expires > now:
                    return {
                        "has_access": True,
                        "access_type": share["access_type"],
                        "share_id": share["id"],
                        "expires_at": share["expires_at"]
                    }
                else:
                    # Expired
                    share["status"] = "expired"
                    self._save_shares()
        
        return {
            "has_access": False,
            "reason": "no_access_grant"
        }
    
    def record_access(self, share_id: str):
        """Record dataset access for tracking"""
        if share_id in self._shares:
            self._shares[share_id]["access_count"] += 1
            self._shares[share_id]["last_accessed"] = datetime.utcnow().isoformat()
            self._save_shares()
    
    def revoke_share(self, share_id: str, reason: str = None) -> bool:
        """Revoke a share"""
        if share_id not in self._shares:
            return False
        
        share = self._shares[share_id]
        share["status"] = "revoked"
        share["revoked_at"] = datetime.utcnow().isoformat()
        share["revoke_reason"] = reason
        
        self._shares[share_id] = share
        self._save_shares()
        
        logger.info(f"Share revoked: {share_id}")
        return True
    
    def get_pending_requests(self, organization_code: str) -> List[Dict]:
        """Get pending requests for an organization to review"""
        return [
            r for r in self._requests.values()
            if r["owner_org"] == organization_code and r["status"] == RequestStatus.PENDING.value
        ]
    
    def get_organization_shares(self, organization_code: str) -> Dict:
        """Get shares for an organization (granted and received)"""
        granted = []
        received = []
        
        for share in self._shares.values():
            if share["status"] != "active":
                continue
            
            if share["owner_org"] == organization_code:
                granted.append(share)
            elif share["shared_with_org"] == organization_code:
                received.append(share)
        
        return {
            "granted": granted,
            "received": received
        }
    
    def get_statistics(self) -> Dict:
        """Get sharing statistics"""
        stats = {
            "total_shares": len(self._shares),
            "active_shares": 0,
            "total_requests": len(self._requests),
            "pending_requests": 0,
            "by_status": {}
        }
        
        for share in self._shares.values():
            status = share["status"]
            stats["by_status"][status] = stats["by_status"].get(status, 0) + 1
            if status == "active":
                stats["active_shares"] += 1
        
        for req in self._requests.values():
            if req["status"] == RequestStatus.PENDING.value:
                stats["pending_requests"] += 1
        
        return stats


# Singleton instance
_dataset_sharing_manager: Optional[DatasetSharingManager] = None


def get_dataset_sharing_manager() -> DatasetSharingManager:
    """Get the global DatasetSharingManager instance"""
    global _dataset_sharing_manager
    if _dataset_sharing_manager is None:
        _dataset_sharing_manager = DatasetSharingManager()
    return _dataset_sharing_manager
