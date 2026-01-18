"""
Organization Registry Module

Manages X-Road member organizations:
- Organization registration and verification
- Subsystem management
- Status management
- Organization search and discovery
"""

import os
import json
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
import uuid

from xroad.models import (
    Organization, OrganizationCreate, OrganizationUpdate,
    Subsystem, SubsystemCreate,
    OrganizationStatus, MemberClass
)

logger = logging.getLogger(__name__)


class OrganizationRegistry:
    """
    Registry for X-Road member organizations.
    
    Manages:
    - Organization registration
    - Organization verification
    - Subsystem management
    - Status tracking
    """
    
    REGISTRY_FILE = os.path.join(os.path.dirname(__file__), '..', 'data', 'organizations.json')
    SUBSYSTEMS_FILE = os.path.join(os.path.dirname(__file__), '..', 'data', 'subsystems.json')
    
    def __init__(self):
        """Initialize organization registry"""
        self._organizations: Dict[str, Dict] = {}
        self._subsystems: Dict[str, Dict] = {}
        self._load_data()
        logger.info("OrganizationRegistry initialized")
    
    def _load_data(self):
        """Load registry data from files"""
        # Ensure data directory exists
        os.makedirs(os.path.dirname(self.REGISTRY_FILE), exist_ok=True)
        
        # Load organizations
        if os.path.exists(self.REGISTRY_FILE):
            try:
                with open(self.REGISTRY_FILE, 'r') as f:
                    self._organizations = json.load(f)
                logger.info(f"Loaded {len(self._organizations)} organizations")
            except Exception as e:
                logger.warning(f"Failed to load organizations: {e}")
        
        # Load subsystems
        if os.path.exists(self.SUBSYSTEMS_FILE):
            try:
                with open(self.SUBSYSTEMS_FILE, 'r') as f:
                    self._subsystems = json.load(f)
                logger.info(f"Loaded {len(self._subsystems)} subsystems")
            except Exception as e:
                logger.warning(f"Failed to load subsystems: {e}")
    
    def _save_organizations(self):
        """Save organizations to file"""
        try:
            with open(self.REGISTRY_FILE, 'w') as f:
                json.dump(self._organizations, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save organizations: {e}")
    
    def _save_subsystems(self):
        """Save subsystems to file"""
        try:
            with open(self.SUBSYSTEMS_FILE, 'w') as f:
                json.dump(self._subsystems, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save subsystems: {e}")
    
    # ==================== ORGANIZATION OPERATIONS ====================
    
    def register_organization(self, org_data: OrganizationCreate) -> Dict:
        """
        Register a new organization.
        
        Args:
            org_data: Organization creation data
            
        Returns:
            Created organization data
            
        Raises:
            ValueError: If organization code already exists
        """
        # Check for duplicate code
        for org in self._organizations.values():
            if org["code"] == org_data.code:
                raise ValueError(f"Organization with code '{org_data.code}' already exists")
        
        # Create organization
        org_id = str(uuid.uuid4())
        now = datetime.utcnow()
        
        organization = {
            "id": org_id,
            "code": org_data.code,
            "name": org_data.name,
            "member_class": org_data.member_class.value,
            "status": OrganizationStatus.PENDING.value,
            "contact_email": org_data.contact_email,
            "contact_phone": org_data.contact_phone,
            "address": org_data.address,
            "website": org_data.website,
            "description": org_data.description,
            "metadata": org_data.metadata or {},
            "certificate_id": None,
            "registration_date": now.isoformat(),
            "verified_at": None,
            "verified_by": None,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat()
        }
        
        self._organizations[org_id] = organization
        self._save_organizations()
        
        logger.info(f"Organization registered: {org_data.code}")
        return organization
    
    def get_organization(self, org_id: str) -> Optional[Dict]:
        """Get organization by ID"""
        return self._organizations.get(org_id)
    
    def get_organization_by_code(self, code: str) -> Optional[Dict]:
        """Get organization by code"""
        for org in self._organizations.values():
            if org["code"] == code:
                return org
        return None
    
    def update_organization(self, org_id: str, update_data: OrganizationUpdate) -> Optional[Dict]:
        """
        Update organization details.
        
        Args:
            org_id: Organization ID
            update_data: Fields to update
            
        Returns:
            Updated organization or None if not found
        """
        if org_id not in self._organizations:
            return None
        
        org = self._organizations[org_id]
        
        # Update only provided fields
        if update_data.name is not None:
            org["name"] = update_data.name
        if update_data.contact_email is not None:
            org["contact_email"] = update_data.contact_email
        if update_data.contact_phone is not None:
            org["contact_phone"] = update_data.contact_phone
        if update_data.address is not None:
            org["address"] = update_data.address
        if update_data.website is not None:
            org["website"] = update_data.website
        if update_data.description is not None:
            org["description"] = update_data.description
        if update_data.metadata is not None:
            org["metadata"] = update_data.metadata
        
        org["updated_at"] = datetime.utcnow().isoformat()
        
        self._organizations[org_id] = org
        self._save_organizations()
        
        logger.info(f"Organization updated: {org['code']}")
        return org
    
    def verify_organization(
        self, 
        org_id: str, 
        verified_by: str,
        certificate_id: str = None
    ) -> Optional[Dict]:
        """
        Verify an organization (activate it).
        
        Args:
            org_id: Organization ID
            verified_by: User who verified
            certificate_id: Optional certificate ID to associate
            
        Returns:
            Updated organization or None
        """
        if org_id not in self._organizations:
            return None
        
        org = self._organizations[org_id]
        org["status"] = OrganizationStatus.ACTIVE.value
        org["verified_at"] = datetime.utcnow().isoformat()
        org["verified_by"] = verified_by
        org["updated_at"] = datetime.utcnow().isoformat()
        
        if certificate_id:
            org["certificate_id"] = certificate_id
        
        self._organizations[org_id] = org
        self._save_organizations()
        
        logger.info(f"Organization verified: {org['code']}")
        return org
    
    def suspend_organization(self, org_id: str, reason: str = None) -> Optional[Dict]:
        """
        Suspend an organization.
        
        Args:
            org_id: Organization ID
            reason: Reason for suspension
            
        Returns:
            Updated organization or None
        """
        if org_id not in self._organizations:
            return None
        
        org = self._organizations[org_id]
        org["status"] = OrganizationStatus.SUSPENDED.value
        org["updated_at"] = datetime.utcnow().isoformat()
        if reason:
            org["metadata"]["suspension_reason"] = reason
            org["metadata"]["suspended_at"] = datetime.utcnow().isoformat()
        
        self._organizations[org_id] = org
        self._save_organizations()
        
        logger.info(f"Organization suspended: {org['code']}")
        return org
    
    def reactivate_organization(self, org_id: str) -> Optional[Dict]:
        """Reactivate a suspended organization"""
        if org_id not in self._organizations:
            return None
        
        org = self._organizations[org_id]
        if org["status"] != OrganizationStatus.SUSPENDED.value:
            return org
        
        org["status"] = OrganizationStatus.ACTIVE.value
        org["updated_at"] = datetime.utcnow().isoformat()
        org["metadata"]["reactivated_at"] = datetime.utcnow().isoformat()
        
        self._organizations[org_id] = org
        self._save_organizations()
        
        logger.info(f"Organization reactivated: {org['code']}")
        return org
    
    def list_organizations(
        self,
        status: OrganizationStatus = None,
        member_class: MemberClass = None,
        search: str = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict]:
        """
        List organizations with filters.
        
        Args:
            status: Filter by status
            member_class: Filter by member class
            search: Search in name or code
            limit: Maximum results
            offset: Skip first N results
            
        Returns:
            List of matching organizations
        """
        results = []
        
        for org in self._organizations.values():
            # Apply filters
            if status and org["status"] != status.value:
                continue
            if member_class and org["member_class"] != member_class.value:
                continue
            if search:
                search_lower = search.lower()
                if search_lower not in org["code"].lower() and \
                   search_lower not in org["name"].lower():
                    continue
            
            results.append(org)
        
        # Sort by name
        results.sort(key=lambda x: x["name"])
        
        # Apply pagination
        return results[offset:offset + limit]
    
    def delete_organization(self, org_id: str) -> bool:
        """
        Delete an organization (only if pending).
        
        Args:
            org_id: Organization ID
            
        Returns:
            True if deleted, False otherwise
        """
        if org_id not in self._organizations:
            return False
        
        org = self._organizations[org_id]
        if org["status"] != OrganizationStatus.PENDING.value:
            logger.warning(f"Cannot delete active organization: {org['code']}")
            return False
        
        # Delete associated subsystems
        for sub_id in list(self._subsystems.keys()):
            if self._subsystems[sub_id]["organization_id"] == org_id:
                del self._subsystems[sub_id]
        self._save_subsystems()
        
        del self._organizations[org_id]
        self._save_organizations()
        
        logger.info(f"Organization deleted: {org['code']}")
        return True
    
    # ==================== SUBSYSTEM OPERATIONS ====================
    
    def create_subsystem(self, org_id: str, subsystem_data: SubsystemCreate) -> Dict:
        """
        Create a subsystem for an organization.
        
        Args:
            org_id: Organization ID
            subsystem_data: Subsystem creation data
            
        Returns:
            Created subsystem data
            
        Raises:
            ValueError: If organization not found or subsystem code exists
        """
        if org_id not in self._organizations:
            raise ValueError(f"Organization not found: {org_id}")
        
        org = self._organizations[org_id]
        
        # Check for duplicate code within organization
        for sub in self._subsystems.values():
            if sub["organization_id"] == org_id and sub["code"] == subsystem_data.code:
                raise ValueError(
                    f"Subsystem '{subsystem_data.code}' already exists in organization"
                )
        
        # Create subsystem
        sub_id = str(uuid.uuid4())
        now = datetime.utcnow()
        
        subsystem = {
            "id": sub_id,
            "organization_id": org_id,
            "organization_code": org["code"],
            "code": subsystem_data.code,
            "name": subsystem_data.name,
            "description": subsystem_data.description,
            "api_base_url": subsystem_data.api_base_url,
            "status": "active",
            "created_at": now.isoformat(),
            "updated_at": now.isoformat()
        }
        
        self._subsystems[sub_id] = subsystem
        self._save_subsystems()
        
        logger.info(f"Subsystem created: {org['code']}/{subsystem_data.code}")
        return subsystem
    
    def get_subsystem(self, subsystem_id: str) -> Optional[Dict]:
        """Get subsystem by ID"""
        return self._subsystems.get(subsystem_id)
    
    def get_subsystem_by_code(self, org_code: str, subsystem_code: str) -> Optional[Dict]:
        """Get subsystem by organization code and subsystem code"""
        for sub in self._subsystems.values():
            if sub["organization_code"] == org_code and sub["code"] == subsystem_code:
                return sub
        return None
    
    def list_subsystems(self, org_id: str = None) -> List[Dict]:
        """
        List subsystems, optionally filtered by organization.
        
        Args:
            org_id: Filter by organization ID
            
        Returns:
            List of subsystems
        """
        if org_id:
            return [s for s in self._subsystems.values() if s["organization_id"] == org_id]
        return list(self._subsystems.values())
    
    def update_subsystem(
        self, 
        subsystem_id: str,
        name: str = None,
        description: str = None,
        api_base_url: str = None
    ) -> Optional[Dict]:
        """Update a subsystem"""
        if subsystem_id not in self._subsystems:
            return None
        
        sub = self._subsystems[subsystem_id]
        
        if name is not None:
            sub["name"] = name
        if description is not None:
            sub["description"] = description
        if api_base_url is not None:
            sub["api_base_url"] = api_base_url
        
        sub["updated_at"] = datetime.utcnow().isoformat()
        
        self._subsystems[subsystem_id] = sub
        self._save_subsystems()
        
        return sub
    
    def delete_subsystem(self, subsystem_id: str) -> bool:
        """Delete a subsystem"""
        if subsystem_id not in self._subsystems:
            return False
        
        del self._subsystems[subsystem_id]
        self._save_subsystems()
        
        return True
    
    # ==================== STATISTICS ====================
    
    def get_statistics(self) -> Dict:
        """Get registry statistics"""
        stats = {
            "organizations": {
                "total": len(self._organizations),
                "by_status": {},
                "by_class": {}
            },
            "subsystems": {
                "total": len(self._subsystems)
            }
        }
        
        for org in self._organizations.values():
            status = org["status"]
            member_class = org["member_class"]
            
            stats["organizations"]["by_status"][status] = \
                stats["organizations"]["by_status"].get(status, 0) + 1
            stats["organizations"]["by_class"][member_class] = \
                stats["organizations"]["by_class"].get(member_class, 0) + 1
        
        return stats


# Singleton instance
_organization_registry: Optional[OrganizationRegistry] = None


def get_organization_registry() -> OrganizationRegistry:
    """Get the global OrganizationRegistry instance"""
    global _organization_registry
    if _organization_registry is None:
        _organization_registry = OrganizationRegistry()
    return _organization_registry
