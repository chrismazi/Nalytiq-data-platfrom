"""
Federation Module

Cross-organization data sharing and federated analytics:
- Dataset sharing
- Federated queries
- Data catalog
- Access request management
"""

from .data_catalog import DataCatalog, get_data_catalog
from .dataset_sharing import DatasetSharingManager, get_dataset_sharing_manager
from .federated_query import FederatedQueryEngine, get_federated_query_engine

__all__ = [
    'DataCatalog',
    'get_data_catalog',
    'DatasetSharingManager',
    'get_dataset_sharing_manager',
    'FederatedQueryEngine',
    'get_federated_query_engine'
]
