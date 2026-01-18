"""
Data Catalog Module

Central catalog for discoverable datasets across organizations:
- Dataset registration
- Metadata management
- Search and discovery
- Access level tagging
"""

import os
import json
import logging
from datetime import datetime
from typing import Optional, List, Dict
from enum import Enum
import uuid

logger = logging.getLogger(__name__)


class DataAccessLevel(str, Enum):
    """Data access levels"""
    PUBLIC = "public"           # Available to all members
    RESTRICTED = "restricted"   # Requires approval
    INTERNAL = "internal"       # Organization-only
    CONFIDENTIAL = "confidential"  # Special clearance needed


class DatasetType(str, Enum):
    """Types of datasets"""
    STATISTICAL = "statistical"
    ADMINISTRATIVE = "administrative"
    SURVEY = "survey"
    CENSUS = "census"
    GEOSPATIAL = "geospatial"
    TIME_SERIES = "time_series"
    AGGREGATE = "aggregate"
    MICRODATA = "microdata"


class DataCatalog:
    """
    Central data catalog for the federation.
    
    Features:
    - Dataset registration
    - Metadata management
    - Search and discovery
    - Schema information
    """
    
    CATALOG_FILE = os.path.join(os.path.dirname(__file__), '..', 'data', 'data_catalog.json')
    
    def __init__(self):
        """Initialize data catalog"""
        self._datasets: Dict[str, Dict] = {}
        self._load_data()
        logger.info("DataCatalog initialized")
    
    def _load_data(self):
        """Load catalog from file"""
        os.makedirs(os.path.dirname(self.CATALOG_FILE), exist_ok=True)
        
        if os.path.exists(self.CATALOG_FILE):
            try:
                with open(self.CATALOG_FILE, 'r') as f:
                    self._datasets = json.load(f)
                logger.info(f"Loaded {len(self._datasets)} datasets from catalog")
            except Exception as e:
                logger.warning(f"Failed to load catalog: {e}")
    
    def _save_data(self):
        """Save catalog to file"""
        try:
            with open(self.CATALOG_FILE, 'w') as f:
                json.dump(self._datasets, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save catalog: {e}")
    
    def register_dataset(
        self,
        organization_code: str,
        name: str,
        description: str,
        dataset_type: DatasetType,
        access_level: DataAccessLevel,
        schema: Dict = None,
        tags: List[str] = None,
        temporal_coverage: Dict = None,
        geographic_coverage: str = None,
        update_frequency: str = None,
        row_count: int = None,
        column_count: int = None,
        file_format: str = None,
        documentation_url: str = None,
        contact_email: str = None
    ) -> Dict:
        """
        Register a dataset in the catalog.
        
        Args:
            organization_code: Owning organization
            name: Dataset name
            description: Description
            dataset_type: Type of dataset
            access_level: Access level
            schema: Column schemas
            tags: Searchable tags
            temporal_coverage: Time period covered
            geographic_coverage: Geographic scope
            update_frequency: How often updated
            row_count: Number of records
            column_count: Number of columns
            file_format: Data format
            documentation_url: Documentation link
            contact_email: Contact for inquiries
            
        Returns:
            Registered dataset
        """
        dataset_id = str(uuid.uuid4())
        now = datetime.utcnow()
        
        dataset = {
            "id": dataset_id,
            "organization_code": organization_code,
            "name": name,
            "description": description,
            "dataset_type": dataset_type.value,
            "access_level": access_level.value,
            "schema": schema or {},
            "tags": tags or [],
            "temporal_coverage": temporal_coverage,
            "geographic_coverage": geographic_coverage or "Rwanda",
            "update_frequency": update_frequency,
            "statistics": {
                "row_count": row_count,
                "column_count": column_count
            },
            "file_format": file_format or "CSV",
            "documentation_url": documentation_url,
            "contact_email": contact_email,
            "status": "active",
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
            "version": "1.0.0",
            "download_count": 0,
            "query_count": 0
        }
        
        self._datasets[dataset_id] = dataset
        self._save_data()
        
        logger.info(f"Dataset registered: {name} by {organization_code}")
        return dataset
    
    def get_dataset(self, dataset_id: str) -> Optional[Dict]:
        """Get dataset by ID"""
        return self._datasets.get(dataset_id)
    
    def search(
        self,
        query: str = None,
        organization_code: str = None,
        dataset_type: DatasetType = None,
        access_level: DataAccessLevel = None,
        tags: List[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict]:
        """
        Search the data catalog.
        
        Args:
            query: Text search in name and description
            organization_code: Filter by organization
            dataset_type: Filter by type
            access_level: Filter by access level
            tags: Filter by tags
            limit: Maximum results
            offset: Skip first N results
            
        Returns:
            Matching datasets
        """
        results = []
        
        for dataset in self._datasets.values():
            # Skip inactive datasets
            if dataset.get("status") != "active":
                continue
            
            # Apply filters
            if organization_code and dataset["organization_code"] != organization_code:
                continue
            if dataset_type and dataset["dataset_type"] != dataset_type.value:
                continue
            if access_level and dataset["access_level"] != access_level.value:
                continue
            
            # Tag filter
            if tags:
                dataset_tags = set(dataset.get("tags", []))
                if not dataset_tags.intersection(set(tags)):
                    continue
            
            # Text search
            if query:
                query_lower = query.lower()
                name_match = query_lower in dataset["name"].lower()
                desc_match = query_lower in dataset["description"].lower()
                tag_match = any(query_lower in t.lower() for t in dataset.get("tags", []))
                
                if not (name_match or desc_match or tag_match):
                    continue
            
            results.append(dataset)
        
        # Sort by name
        results.sort(key=lambda x: x["name"])
        
        return results[offset:offset + limit]
    
    def get_organization_datasets(self, organization_code: str) -> List[Dict]:
        """Get all datasets owned by an organization"""
        return [
            d for d in self._datasets.values()
            if d["organization_code"] == organization_code
        ]
    
    def get_public_datasets(self) -> List[Dict]:
        """Get all public datasets"""
        return [
            d for d in self._datasets.values()
            if d["access_level"] == DataAccessLevel.PUBLIC.value and d["status"] == "active"
        ]
    
    def update_dataset(
        self,
        dataset_id: str,
        updates: Dict
    ) -> Optional[Dict]:
        """Update dataset metadata"""
        if dataset_id not in self._datasets:
            return None
        
        dataset = self._datasets[dataset_id]
        
        allowed_updates = [
            "name", "description", "tags", "schema", "temporal_coverage",
            "geographic_coverage", "update_frequency", "documentation_url",
            "contact_email", "status"
        ]
        
        for key, value in updates.items():
            if key in allowed_updates:
                dataset[key] = value
        
        dataset["updated_at"] = datetime.utcnow().isoformat()
        
        # Increment version on significant updates
        if any(k in updates for k in ["schema", "name"]):
            version_parts = dataset["version"].split(".")
            version_parts[1] = str(int(version_parts[1]) + 1)
            dataset["version"] = ".".join(version_parts)
        
        self._datasets[dataset_id] = dataset
        self._save_data()
        
        return dataset
    
    def increment_stats(self, dataset_id: str, stat_type: str):
        """Increment usage statistics"""
        if dataset_id not in self._datasets:
            return
        
        if stat_type == "download":
            self._datasets[dataset_id]["download_count"] += 1
        elif stat_type == "query":
            self._datasets[dataset_id]["query_count"] += 1
        
        self._save_data()
    
    def get_popular_datasets(self, limit: int = 10) -> List[Dict]:
        """Get most popular datasets by usage"""
        active = [d for d in self._datasets.values() if d["status"] == "active"]
        
        # Sort by combined usage
        active.sort(
            key=lambda x: x.get("download_count", 0) + x.get("query_count", 0),
            reverse=True
        )
        
        return active[:limit]
    
    def get_catalog_statistics(self) -> Dict:
        """Get catalog statistics"""
        stats = {
            "total_datasets": len(self._datasets),
            "by_type": {},
            "by_access_level": {},
            "by_organization": {},
            "total_downloads": 0,
            "total_queries": 0
        }
        
        for dataset in self._datasets.values():
            # By type
            dtype = dataset["dataset_type"]
            stats["by_type"][dtype] = stats["by_type"].get(dtype, 0) + 1
            
            # By access level
            level = dataset["access_level"]
            stats["by_access_level"][level] = stats["by_access_level"].get(level, 0) + 1
            
            # By organization
            org = dataset["organization_code"]
            stats["by_organization"][org] = stats["by_organization"].get(org, 0) + 1
            
            # Usage stats
            stats["total_downloads"] += dataset.get("download_count", 0)
            stats["total_queries"] += dataset.get("query_count", 0)
        
        return stats


# Singleton instance
_data_catalog: Optional[DataCatalog] = None


def get_data_catalog() -> DataCatalog:
    """Get the global DataCatalog instance"""
    global _data_catalog
    if _data_catalog is None:
        _data_catalog = DataCatalog()
    return _data_catalog
