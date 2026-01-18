"""
Federated Query Engine

Enables querying data across organizations:
- Distributed query execution
- Result aggregation
- Privacy-preserving operations
- Query optimization
"""

import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
import uuid
import pandas as pd

from .data_catalog import get_data_catalog
from .dataset_sharing import get_dataset_sharing_manager

logger = logging.getLogger(__name__)


class FederatedQueryEngine:
    """
    Federated query engine for cross-organization data access.
    
    Features:
    - Query authorized datasets
    - Aggregate results
    - Privacy-preserving analytics
    - Query history tracking
    """
    
    def __init__(self):
        """Initialize federated query engine"""
        self.catalog = get_data_catalog()
        self.sharing_manager = get_dataset_sharing_manager()
        self._query_history: List[Dict] = []
        logger.info("FederatedQueryEngine initialized")
    
    def execute_query(
        self,
        organization_code: str,
        dataset_ids: List[str],
        query_type: str,
        parameters: Dict,
        user_id: str = None
    ) -> Dict:
        """
        Execute a federated query across datasets.
        
        Args:
            organization_code: Requesting organization
            dataset_ids: Datasets to query
            query_type: Type of query (aggregate, describe, sample, etc.)
            parameters: Query parameters
            user_id: User executing the query
            
        Returns:
            Query results
        """
        query_id = str(uuid.uuid4())
        start_time = datetime.utcnow()
        
        logger.info(f"Executing federated query {query_id} for {organization_code}")
        
        # Validate access to all datasets
        accessible_datasets = []
        denied_datasets = []
        
        for dataset_id in dataset_ids:
            access = self.sharing_manager.check_access(dataset_id, organization_code)
            if access["has_access"]:
                accessible_datasets.append({
                    "dataset_id": dataset_id,
                    "access_type": access["access_type"],
                    "share_id": access.get("share_id")
                })
                
                # Record access if it's a share
                if access.get("share_id"):
                    self.sharing_manager.record_access(access["share_id"])
                
                # Increment query count
                self.catalog.increment_stats(dataset_id, "query")
            else:
                denied_datasets.append({
                    "dataset_id": dataset_id,
                    "reason": access.get("reason")
                })
        
        if not accessible_datasets:
            return {
                "success": False,
                "query_id": query_id,
                "error": "No accessible datasets",
                "denied_datasets": denied_datasets
            }
        
        # Execute query based on type
        try:
            if query_type == "describe":
                result = self._execute_describe(accessible_datasets, parameters)
            elif query_type == "aggregate":
                result = self._execute_aggregate(accessible_datasets, parameters)
            elif query_type == "sample":
                result = self._execute_sample(accessible_datasets, parameters)
            elif query_type == "columns":
                result = self._execute_columns(accessible_datasets, parameters)
            elif query_type == "count":
                result = self._execute_count(accessible_datasets, parameters)
            else:
                result = {
                    "success": False,
                    "error": f"Unknown query type: {query_type}"
                }
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            result = {
                "success": False,
                "error": str(e)
            }
        
        end_time = datetime.utcnow()
        duration_ms = int((end_time - start_time).total_seconds() * 1000)
        
        # Record query history
        query_record = {
            "query_id": query_id,
            "organization_code": organization_code,
            "user_id": user_id,
            "query_type": query_type,
            "dataset_count": len(accessible_datasets),
            "denied_count": len(denied_datasets),
            "success": result.get("success", False),
            "duration_ms": duration_ms,
            "executed_at": start_time.isoformat()
        }
        self._query_history.append(query_record)
        
        # Limit history size
        if len(self._query_history) > 1000:
            self._query_history = self._query_history[-1000:]
        
        return {
            "query_id": query_id,
            "success": result.get("success", True),
            "datasets_queried": len(accessible_datasets),
            "datasets_denied": denied_datasets if denied_datasets else None,
            "result": result.get("data") if result.get("success") else None,
            "error": result.get("error") if not result.get("success") else None,
            "duration_ms": duration_ms,
            "timestamp": end_time.isoformat()
        }
    
    def _execute_describe(self, datasets: List[Dict], parameters: Dict) -> Dict:
        """Execute describe query - returns dataset metadata"""
        results = []
        
        for ds in datasets:
            dataset = self.catalog.get_dataset(ds["dataset_id"])
            if dataset:
                results.append({
                    "dataset_id": dataset["id"],
                    "name": dataset["name"],
                    "organization": dataset["organization_code"],
                    "type": dataset["dataset_type"],
                    "row_count": dataset["statistics"].get("row_count"),
                    "column_count": dataset["statistics"].get("column_count"),
                    "schema": dataset.get("schema"),
                    "temporal_coverage": dataset.get("temporal_coverage"),
                    "geographic_coverage": dataset.get("geographic_coverage"),
                    "update_frequency": dataset.get("update_frequency")
                })
        
        return {"success": True, "data": results}
    
    def _execute_columns(self, datasets: List[Dict], parameters: Dict) -> Dict:
        """Execute columns query - returns column information"""
        results = []
        
        for ds in datasets:
            dataset = self.catalog.get_dataset(ds["dataset_id"])
            if dataset:
                schema = dataset.get("schema", {})
                columns = []
                
                for col_name, col_info in schema.items():
                    columns.append({
                        "name": col_name,
                        "type": col_info.get("type"),
                        "description": col_info.get("description"),
                        "nullable": col_info.get("nullable", True)
                    })
                
                results.append({
                    "dataset_id": dataset["id"],
                    "dataset_name": dataset["name"],
                    "columns": columns
                })
        
        return {"success": True, "data": results}
    
    def _execute_count(self, datasets: List[Dict], parameters: Dict) -> Dict:
        """Execute count query - returns record counts"""
        results = []
        total = 0
        
        for ds in datasets:
            dataset = self.catalog.get_dataset(ds["dataset_id"])
            if dataset:
                count = dataset["statistics"].get("row_count", 0) or 0
                total += count
                results.append({
                    "dataset_id": dataset["id"],
                    "dataset_name": dataset["name"],
                    "row_count": count
                })
        
        return {
            "success": True,
            "data": {
                "datasets": results,
                "total_rows": total
            }
        }
    
    def _execute_aggregate(self, datasets: List[Dict], parameters: Dict) -> Dict:
        """
        Execute aggregate query.
        
        This is a simulated aggregation - in production, this would
        execute actual queries on the data sources.
        """
        # Get aggregation parameters
        group_by = parameters.get("group_by")
        agg_column = parameters.get("column")
        agg_function = parameters.get("function", "sum")  # sum, mean, count, min, max
        
        if not agg_column:
            return {
                "success": False,
                "error": "Aggregation column is required"
            }
        
        # Simulated result (in production, would query actual data)
        results = []
        
        for ds in datasets:
            dataset = self.catalog.get_dataset(ds["dataset_id"])
            if dataset:
                # Check if column exists in schema
                schema = dataset.get("schema", {})
                if agg_column not in schema:
                    results.append({
                        "dataset_id": dataset["id"],
                        "error": f"Column '{agg_column}' not found"
                    })
                    continue
                
                # Simulated aggregation result
                results.append({
                    "dataset_id": dataset["id"],
                    "dataset_name": dataset["name"],
                    "aggregation": {
                        "column": agg_column,
                        "function": agg_function,
                        "result": None,  # Would contain actual result
                        "note": "Aggregation requires actual data connection"
                    }
                })
        
        return {"success": True, "data": results}
    
    def _execute_sample(self, datasets: List[Dict], parameters: Dict) -> Dict:
        """
        Execute sample query - returns sample records.
        
        Note: This is a privacy-preserving operation that only
        returns a small sample, not full data dumps.
        """
        sample_size = min(parameters.get("size", 5), 10)  # Max 10 records
        
        results = []
        
        for ds in datasets:
            dataset = self.catalog.get_dataset(ds["dataset_id"])
            if dataset:
                # In production, would fetch actual sample
                results.append({
                    "dataset_id": dataset["id"],
                    "dataset_name": dataset["name"],
                    "sample": None,  # Would contain sample data
                    "sample_size": sample_size,
                    "note": "Sampling requires actual data connection"
                })
        
        return {"success": True, "data": results}
    
    def get_accessible_datasets(self, organization_code: str) -> List[Dict]:
        """
        Get all datasets accessible to an organization.
        
        Args:
            organization_code: Organization code
            
        Returns:
            List of accessible datasets
        """
        accessible = []
        
        # Get all datasets from catalog
        all_datasets = self.catalog.search(limit=1000)
        
        for dataset in all_datasets:
            access = self.sharing_manager.check_access(
                dataset["id"],
                organization_code
            )
            
            if access["has_access"]:
                accessible.append({
                    "dataset_id": dataset["id"],
                    "name": dataset["name"],
                    "organization": dataset["organization_code"],
                    "type": dataset["dataset_type"],
                    "access_type": access["access_type"],
                    "expires_at": access.get("expires_at")
                })
        
        return accessible
    
    def get_query_history(
        self,
        organization_code: str = None,
        limit: int = 50
    ) -> List[Dict]:
        """Get query execution history"""
        history = self._query_history
        
        if organization_code:
            history = [
                q for q in history
                if q["organization_code"] == organization_code
            ]
        
        # Sort by time descending
        history = sorted(history, key=lambda x: x["executed_at"], reverse=True)
        
        return history[:limit]
    
    def get_statistics(self) -> Dict:
        """Get query engine statistics"""
        stats = {
            "total_queries": len(self._query_history),
            "successful_queries": sum(1 for q in self._query_history if q.get("success")),
            "failed_queries": sum(1 for q in self._query_history if not q.get("success")),
            "by_type": {},
            "by_organization": {},
            "avg_duration_ms": 0
        }
        
        if self._query_history:
            total_duration = sum(q.get("duration_ms", 0) for q in self._query_history)
            stats["avg_duration_ms"] = total_duration / len(self._query_history)
            
            for query in self._query_history:
                qtype = query.get("query_type", "unknown")
                org = query.get("organization_code", "unknown")
                
                stats["by_type"][qtype] = stats["by_type"].get(qtype, 0) + 1
                stats["by_organization"][org] = stats["by_organization"].get(org, 0) + 1
        
        return stats


# Singleton instance
_federated_query_engine: Optional[FederatedQueryEngine] = None


def get_federated_query_engine() -> FederatedQueryEngine:
    """Get the global FederatedQueryEngine instance"""
    global _federated_query_engine
    if _federated_query_engine is None:
        _federated_query_engine = FederatedQueryEngine()
    return _federated_query_engine
