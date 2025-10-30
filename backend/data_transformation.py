"""
Data Transformation Engine
Visual data manipulation and transformation
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Union
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class DataTransformer:
    """Transform and manipulate datasets"""
    
    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()
        self.original_df = df.copy()
        self.transformation_history = []
    
    # ============= Filtering Operations =============
    
    def filter_rows(self, column: str, operator: str, value: Any) -> 'DataTransformer':
        """Filter rows based on condition"""
        try:
            if operator == 'equals':
                self.df = self.df[self.df[column] == value]
            elif operator == 'not_equals':
                self.df = self.df[self.df[column] != value]
            elif operator == 'greater_than':
                self.df = self.df[self.df[column] > value]
            elif operator == 'less_than':
                self.df = self.df[self.df[column] < value]
            elif operator == 'greater_equal':
                self.df = self.df[self.df[column] >= value]
            elif operator == 'less_equal':
                self.df = self.df[self.df[column] <= value]
            elif operator == 'contains':
                self.df = self.df[self.df[column].astype(str).str.contains(str(value), na=False)]
            elif operator == 'not_contains':
                self.df = self.df[~self.df[column].astype(str).str.contains(str(value), na=False)]
            elif operator == 'in':
                self.df = self.df[self.df[column].isin(value)]
            elif operator == 'not_in':
                self.df = self.df[~self.df[column].isin(value)]
            else:
                raise ValueError(f"Unknown operator: {operator}")
            
            self.transformation_history.append({
                'operation': 'filter_rows',
                'params': {'column': column, 'operator': operator, 'value': value},
                'rows_before': len(self.original_df),
                'rows_after': len(self.df)
            })
            
            return self
            
        except Exception as e:
            logger.error(f"Filter rows failed: {e}")
            raise
    
    def filter_nulls(self, column: str, keep_nulls: bool = False) -> 'DataTransformer':
        """Filter null values"""
        try:
            if keep_nulls:
                self.df = self.df[self.df[column].isnull()]
            else:
                self.df = self.df[self.df[column].notnull()]
            
            self.transformation_history.append({
                'operation': 'filter_nulls',
                'params': {'column': column, 'keep_nulls': keep_nulls},
                'rows_after': len(self.df)
            })
            
            return self
            
        except Exception as e:
            logger.error(f"Filter nulls failed: {e}")
            raise
    
    # ============= Column Operations =============
    
    def select_columns(self, columns: List[str]) -> 'DataTransformer':
        """Select specific columns"""
        try:
            self.df = self.df[columns]
            
            self.transformation_history.append({
                'operation': 'select_columns',
                'params': {'columns': columns},
                'columns_after': len(self.df.columns)
            })
            
            return self
            
        except Exception as e:
            logger.error(f"Select columns failed: {e}")
            raise
    
    def drop_columns(self, columns: List[str]) -> 'DataTransformer':
        """Drop columns"""
        try:
            self.df = self.df.drop(columns=columns)
            
            self.transformation_history.append({
                'operation': 'drop_columns',
                'params': {'columns': columns},
                'columns_after': len(self.df.columns)
            })
            
            return self
            
        except Exception as e:
            logger.error(f"Drop columns failed: {e}")
            raise
    
    def rename_column(self, old_name: str, new_name: str) -> 'DataTransformer':
        """Rename a column"""
        try:
            self.df = self.df.rename(columns={old_name: new_name})
            
            self.transformation_history.append({
                'operation': 'rename_column',
                'params': {'old_name': old_name, 'new_name': new_name}
            })
            
            return self
            
        except Exception as e:
            logger.error(f"Rename column failed: {e}")
            raise
    
    def add_calculated_column(self, name: str, expression: str) -> 'DataTransformer':
        """Add calculated column using expression"""
        try:
            # Safe eval with only df columns available
            self.df[name] = self.df.eval(expression)
            
            self.transformation_history.append({
                'operation': 'add_calculated_column',
                'params': {'name': name, 'expression': expression}
            })
            
            return self
            
        except Exception as e:
            logger.error(f"Add calculated column failed: {e}")
            raise
    
    # ============= Data Type Operations =============
    
    def convert_type(self, column: str, target_type: str) -> 'DataTransformer':
        """Convert column data type"""
        try:
            if target_type == 'int':
                self.df[column] = pd.to_numeric(self.df[column], errors='coerce').astype('Int64')
            elif target_type == 'float':
                self.df[column] = pd.to_numeric(self.df[column], errors='coerce')
            elif target_type == 'string':
                self.df[column] = self.df[column].astype(str)
            elif target_type == 'datetime':
                self.df[column] = pd.to_datetime(self.df[column], errors='coerce')
            elif target_type == 'bool':
                self.df[column] = self.df[column].astype(bool)
            else:
                raise ValueError(f"Unknown type: {target_type}")
            
            self.transformation_history.append({
                'operation': 'convert_type',
                'params': {'column': column, 'target_type': target_type}
            })
            
            return self
            
        except Exception as e:
            logger.error(f"Convert type failed: {e}")
            raise
    
    # ============= Missing Value Operations =============
    
    def fill_missing(self, column: str, method: str = 'mean', value: Any = None) -> 'DataTransformer':
        """Fill missing values"""
        try:
            if method == 'mean':
                self.df[column] = self.df[column].fillna(self.df[column].mean())
            elif method == 'median':
                self.df[column] = self.df[column].fillna(self.df[column].median())
            elif method == 'mode':
                self.df[column] = self.df[column].fillna(self.df[column].mode()[0])
            elif method == 'forward':
                self.df[column] = self.df[column].fillna(method='ffill')
            elif method == 'backward':
                self.df[column] = self.df[column].fillna(method='bfill')
            elif method == 'value':
                self.df[column] = self.df[column].fillna(value)
            else:
                raise ValueError(f"Unknown method: {method}")
            
            self.transformation_history.append({
                'operation': 'fill_missing',
                'params': {'column': column, 'method': method, 'value': value}
            })
            
            return self
            
        except Exception as e:
            logger.error(f"Fill missing failed: {e}")
            raise
    
    def drop_missing(self, columns: Optional[List[str]] = None, how: str = 'any') -> 'DataTransformer':
        """Drop rows with missing values"""
        try:
            rows_before = len(self.df)
            self.df = self.df.dropna(subset=columns, how=how)
            
            self.transformation_history.append({
                'operation': 'drop_missing',
                'params': {'columns': columns, 'how': how},
                'rows_dropped': rows_before - len(self.df)
            })
            
            return self
            
        except Exception as e:
            logger.error(f"Drop missing failed: {e}")
            raise
    
    # ============= Aggregation Operations =============
    
    def group_by(self, group_columns: List[str], agg_dict: Dict[str, str]) -> 'DataTransformer':
        """Group by and aggregate"""
        try:
            self.df = self.df.groupby(group_columns).agg(agg_dict).reset_index()
            
            self.transformation_history.append({
                'operation': 'group_by',
                'params': {'group_columns': group_columns, 'agg_dict': agg_dict}
            })
            
            return self
            
        except Exception as e:
            logger.error(f"Group by failed: {e}")
            raise
    
    def pivot_table(self, index: str, columns: str, values: str, aggfunc: str = 'mean') -> 'DataTransformer':
        """Create pivot table"""
        try:
            self.df = pd.pivot_table(
                self.df,
                index=index,
                columns=columns,
                values=values,
                aggfunc=aggfunc
            ).reset_index()
            
            self.transformation_history.append({
                'operation': 'pivot_table',
                'params': {'index': index, 'columns': columns, 'values': values, 'aggfunc': aggfunc}
            })
            
            return self
            
        except Exception as e:
            logger.error(f"Pivot table failed: {e}")
            raise
    
    # ============= String Operations =============
    
    def string_operation(self, column: str, operation: str, **kwargs) -> 'DataTransformer':
        """Perform string operations"""
        try:
            if operation == 'uppercase':
                self.df[column] = self.df[column].str.upper()
            elif operation == 'lowercase':
                self.df[column] = self.df[column].str.lower()
            elif operation == 'trim':
                self.df[column] = self.df[column].str.strip()
            elif operation == 'replace':
                self.df[column] = self.df[column].str.replace(kwargs['old'], kwargs['new'])
            elif operation == 'split':
                self.df[[f"{column}_part{i}" for i in range(kwargs.get('n', 2))]] = \
                    self.df[column].str.split(kwargs.get('delimiter', ' '), expand=True, n=kwargs.get('n', 1))
            elif operation == 'extract':
                self.df[column] = self.df[column].str.extract(kwargs['pattern'])
            else:
                raise ValueError(f"Unknown operation: {operation}")
            
            self.transformation_history.append({
                'operation': 'string_operation',
                'params': {'column': column, 'operation': operation, **kwargs}
            })
            
            return self
            
        except Exception as e:
            logger.error(f"String operation failed: {e}")
            raise
    
    # ============= Sorting and Deduplication =============
    
    def sort_values(self, columns: List[str], ascending: bool = True) -> 'DataTransformer':
        """Sort by columns"""
        try:
            self.df = self.df.sort_values(by=columns, ascending=ascending).reset_index(drop=True)
            
            self.transformation_history.append({
                'operation': 'sort_values',
                'params': {'columns': columns, 'ascending': ascending}
            })
            
            return self
            
        except Exception as e:
            logger.error(f"Sort values failed: {e}")
            raise
    
    def drop_duplicates(self, columns: Optional[List[str]] = None, keep: str = 'first') -> 'DataTransformer':
        """Remove duplicate rows"""
        try:
            rows_before = len(self.df)
            self.df = self.df.drop_duplicates(subset=columns, keep=keep).reset_index(drop=True)
            
            self.transformation_history.append({
                'operation': 'drop_duplicates',
                'params': {'columns': columns, 'keep': keep},
                'rows_dropped': rows_before - len(self.df)
            })
            
            return self
            
        except Exception as e:
            logger.error(f"Drop duplicates failed: {e}")
            raise
    
    # ============= Sampling Operations =============
    
    def sample_rows(self, n: Optional[int] = None, frac: Optional[float] = None, random_state: int = 42) -> 'DataTransformer':
        """Sample random rows"""
        try:
            if n:
                self.df = self.df.sample(n=n, random_state=random_state)
            elif frac:
                self.df = self.df.sample(frac=frac, random_state=random_state)
            else:
                raise ValueError("Either n or frac must be specified")
            
            self.transformation_history.append({
                'operation': 'sample_rows',
                'params': {'n': n, 'frac': frac, 'random_state': random_state}
            })
            
            return self
            
        except Exception as e:
            logger.error(f"Sample rows failed: {e}")
            raise
    
    # ============= Result Methods =============
    
    def get_result(self) -> pd.DataFrame:
        """Get transformed dataframe"""
        return self.df.copy()
    
    def get_history(self) -> List[Dict[str, Any]]:
        """Get transformation history"""
        return self.transformation_history
    
    def reset(self) -> 'DataTransformer':
        """Reset to original dataframe"""
        self.df = self.original_df.copy()
        self.transformation_history = []
        return self
    
    def preview(self, n: int = 10) -> Dict[str, Any]:
        """Preview transformation result"""
        return {
            'shape': self.df.shape,
            'columns': self.df.columns.tolist(),
            'dtypes': self.df.dtypes.astype(str).to_dict(),
            'preview': self.df.head(n).to_dict('records'),
            'transformations_applied': len(self.transformation_history)
        }


def get_transformation_templates() -> List[Dict[str, Any]]:
    """Get predefined transformation templates"""
    return [
        {
            'id': 'clean_data',
            'name': 'Clean Data',
            'description': 'Remove duplicates and handle missing values',
            'steps': [
                {'operation': 'drop_duplicates'},
                {'operation': 'drop_missing', 'params': {'how': 'any'}}
            ]
        },
        {
            'id': 'normalize_text',
            'name': 'Normalize Text',
            'description': 'Convert text to lowercase and trim whitespace',
            'steps': [
                {'operation': 'string_operation', 'params': {'operation': 'trim'}},
                {'operation': 'string_operation', 'params': {'operation': 'lowercase'}}
            ]
        },
        {
            'id': 'aggregate_by_group',
            'name': 'Group and Aggregate',
            'description': 'Group data and calculate aggregations',
            'steps': [
                {'operation': 'group_by'}
            ]
        }
    ]
