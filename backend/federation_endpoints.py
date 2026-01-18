"""
Federation API Endpoints

FastAPI router for data federation:
- Data catalog operations
- Dataset sharing
- Federated queries
- Access management
"""

from fastapi import APIRouter, HTTPException, Query, Body
from typing import Optional, List, Dict
from datetime import datetime
from pydantic import BaseModel, Field
import logging

from federation.data_catalog import (
    get_data_catalog, 
    DataAccessLevel, 
    DatasetType
)
from federation.dataset_sharing import get_dataset_sharing_manager
from federation.federated_query import get_federated_query_engine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/federation", tags=["Data Federation"])


# ============================================
# PYDANTIC MODELS
# ============================================

class DatasetRegistration(BaseModel):
    name: str = Field(..., description="Dataset name")
    description: str = Field(..., description="Dataset description")
    dataset_type: str = Field(..., description="Type: statistical, survey, census, etc.")
    access_level: str = Field("restricted", description="Access level: public, restricted, internal")
    schema: Optional[Dict] = Field(None, description="Column schema")
    tags: Optional[List[str]] = Field(None, description="Searchable tags")
    temporal_coverage: Optional[Dict] = Field(None, description="Time period covered")
    geographic_coverage: Optional[str] = Field("Rwanda", description="Geographic scope")
    update_frequency: Optional[str] = Field(None, description="How often updated")
    row_count: Optional[int] = Field(None, description="Number of records")
    column_count: Optional[int] = Field(None, description="Number of columns")
    documentation_url: Optional[str] = Field(None, description="Documentation link")
    contact_email: Optional[str] = Field(None, description="Contact email")


class AccessRequest(BaseModel):
    requester_name: str = Field(..., description="Name of requester")
    requester_email: str = Field(..., description="Contact email")
    purpose: str = Field(..., description="Purpose of access")
    duration_days: int = Field(365, description="Requested access duration")
    access_type: str = Field("read", description="Type of access: read, download, query")


class FederatedQuery(BaseModel):
    dataset_ids: List[str] = Field(..., description="Datasets to query")
    query_type: str = Field(..., description="Query type: describe, aggregate, count, sample")
    parameters: Dict = Field(default_factory=dict, description="Query parameters")


# ============================================
# DATA CATALOG ENDPOINTS
# ============================================

@router.post("/catalog/datasets")
async def register_dataset(
    organization_code: str,
    dataset: DatasetRegistration
):
    """Register a new dataset in the catalog"""
    catalog = get_data_catalog()
    
    try:
        result = catalog.register_dataset(
            organization_code=organization_code,
            name=dataset.name,
            description=dataset.description,
            dataset_type=DatasetType(dataset.dataset_type),
            access_level=DataAccessLevel(dataset.access_level),
            schema=dataset.schema,
            tags=dataset.tags,
            temporal_coverage=dataset.temporal_coverage,
            geographic_coverage=dataset.geographic_coverage,
            update_frequency=dataset.update_frequency,
            row_count=dataset.row_count,
            column_count=dataset.column_count,
            documentation_url=dataset.documentation_url,
            contact_email=dataset.contact_email
        )
        
        return {
            "success": True,
            "message": "Dataset registered",
            "dataset": result
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/catalog/datasets")
async def search_datasets(
    query: Optional[str] = None,
    organization_code: Optional[str] = None,
    dataset_type: Optional[str] = None,
    access_level: Optional[str] = None,
    tags: Optional[str] = None,  # Comma-separated
    limit: int = 50,
    offset: int = 0
):
    """Search the data catalog"""
    catalog = get_data_catalog()
    
    tag_list = tags.split(",") if tags else None
    dtype = DatasetType(dataset_type) if dataset_type else None
    level = DataAccessLevel(access_level) if access_level else None
    
    datasets = catalog.search(
        query=query,
        organization_code=organization_code,
        dataset_type=dtype,
        access_level=level,
        tags=tag_list,
        limit=limit,
        offset=offset
    )
    
    return {
        "datasets": datasets,
        "count": len(datasets),
        "limit": limit,
        "offset": offset
    }


@router.get("/catalog/datasets/{dataset_id}")
async def get_dataset(dataset_id: str):
    """Get dataset details"""
    catalog = get_data_catalog()
    dataset = catalog.get_dataset(dataset_id)
    
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    return dataset


@router.get("/catalog/datasets/public")
async def get_public_datasets():
    """Get all public datasets"""
    catalog = get_data_catalog()
    return {
        "datasets": catalog.get_public_datasets()
    }


@router.get("/catalog/datasets/popular")
async def get_popular_datasets(limit: int = 10):
    """Get most popular datasets"""
    catalog = get_data_catalog()
    return {
        "datasets": catalog.get_popular_datasets(limit)
    }


@router.get("/catalog/statistics")
async def get_catalog_statistics():
    """Get catalog statistics"""
    catalog = get_data_catalog()
    return catalog.get_catalog_statistics()


@router.get("/catalog/organizations/{org_code}/datasets")
async def get_organization_datasets(org_code: str):
    """Get all datasets owned by an organization"""
    catalog = get_data_catalog()
    return {
        "organization": org_code,
        "datasets": catalog.get_organization_datasets(org_code)
    }


# ============================================
# DATASET SHARING ENDPOINTS
# ============================================

@router.post("/sharing/request/{dataset_id}")
async def request_dataset_access(
    dataset_id: str,
    requester_org: str,
    request: AccessRequest
):
    """Request access to a dataset"""
    sharing = get_dataset_sharing_manager()
    
    try:
        result = sharing.request_access(
            dataset_id=dataset_id,
            requester_org=requester_org,
            requester_name=request.requester_name,
            requester_email=request.requester_email,
            purpose=request.purpose,
            duration_days=request.duration_days,
            access_type=request.access_type
        )
        
        return {
            "success": True,
            "message": "Access request submitted",
            "request": result
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/sharing/approve/{request_id}")
async def approve_access_request(
    request_id: str,
    reviewer_name: str,
    notes: Optional[str] = None,
    custom_duration_days: Optional[int] = None
):
    """Approve an access request"""
    sharing = get_dataset_sharing_manager()
    
    try:
        result = sharing.approve_request(
            request_id=request_id,
            reviewer_name=reviewer_name,
            notes=notes,
            custom_duration_days=custom_duration_days
        )
        
        return {
            "success": True,
            "message": "Request approved",
            "request": result
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/sharing/reject/{request_id}")
async def reject_access_request(
    request_id: str,
    reviewer_name: str,
    reason: str
):
    """Reject an access request"""
    sharing = get_dataset_sharing_manager()
    
    try:
        result = sharing.reject_request(
            request_id=request_id,
            reviewer_name=reviewer_name,
            reason=reason
        )
        
        return {
            "success": True,
            "message": "Request rejected",
            "request": result
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/sharing/pending/{organization_code}")
async def get_pending_requests(organization_code: str):
    """Get pending access requests for an organization"""
    sharing = get_dataset_sharing_manager()
    requests = sharing.get_pending_requests(organization_code)
    
    return {
        "pending_requests": requests,
        "count": len(requests)
    }


@router.get("/sharing/access/{organization_code}")
async def get_organization_shares(organization_code: str):
    """Get all shares for an organization"""
    sharing = get_dataset_sharing_manager()
    return sharing.get_organization_shares(organization_code)


@router.get("/sharing/check")
async def check_dataset_access(
    dataset_id: str,
    organization_code: str
):
    """Check if organization has access to a dataset"""
    sharing = get_dataset_sharing_manager()
    return sharing.check_access(dataset_id, organization_code)


@router.post("/sharing/revoke/{share_id}")
async def revoke_share(share_id: str, reason: Optional[str] = None):
    """Revoke a dataset share"""
    sharing = get_dataset_sharing_manager()
    
    if not sharing.revoke_share(share_id, reason):
        raise HTTPException(status_code=404, detail="Share not found")
    
    return {
        "success": True,
        "message": "Share revoked"
    }


@router.get("/sharing/statistics")
async def get_sharing_statistics():
    """Get sharing statistics"""
    sharing = get_dataset_sharing_manager()
    return sharing.get_statistics()


# ============================================
# FEDERATED QUERY ENDPOINTS
# ============================================

@router.post("/query")
async def execute_federated_query(
    organization_code: str,
    query: FederatedQuery,
    user_id: Optional[str] = None
):
    """
    Execute a federated query across datasets.
    
    Query types:
    - describe: Get dataset metadata
    - columns: Get column information
    - count: Get record counts
    - aggregate: Run aggregation (requires column and function)
    - sample: Get sample records
    """
    engine = get_federated_query_engine()
    
    result = engine.execute_query(
        organization_code=organization_code,
        dataset_ids=query.dataset_ids,
        query_type=query.query_type,
        parameters=query.parameters,
        user_id=user_id
    )
    
    if not result["success"]:
        raise HTTPException(
            status_code=400,
            detail={
                "error": result.get("error"),
                "denied_datasets": result.get("denied_datasets")
            }
        )
    
    return result


@router.get("/query/accessible/{organization_code}")
async def get_accessible_datasets(organization_code: str):
    """Get all datasets accessible to an organization"""
    engine = get_federated_query_engine()
    datasets = engine.get_accessible_datasets(organization_code)
    
    return {
        "organization": organization_code,
        "accessible_datasets": datasets,
        "count": len(datasets)
    }


@router.get("/query/history")
async def get_query_history(
    organization_code: Optional[str] = None,
    limit: int = 50
):
    """Get query execution history"""
    engine = get_federated_query_engine()
    return {
        "history": engine.get_query_history(organization_code, limit)
    }


@router.get("/query/statistics")
async def get_query_statistics():
    """Get query engine statistics"""
    engine = get_federated_query_engine()
    return engine.get_statistics()
