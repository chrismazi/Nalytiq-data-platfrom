"""
Universal Data Processor - Works with any dataset
Provides comprehensive data cleaning, profiling, and analysis
"""
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import logging
from scipy import stats

logger = logging.getLogger(__name__)

class UniversalDataProcessor:
    """
    Universal data processor that works with any dataset structure
    """
    
    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()
        self.original_df = df.copy()
        self.metadata = {}
        self.cleaning_log = []
        
    def auto_detect_types(self) -> Dict[str, str]:
        """
        Intelligently detect and convert column types
        """
        type_changes = {}
        
        for col in self.df.columns:
            original_type = str(self.df[col].dtype)
            
            # Skip if already numeric
            if pd.api.types.is_numeric_dtype(self.df[col]):
                continue
            
            # Try to convert to datetime
            if self.df[col].dtype == 'object':
                try:
                    # Sample a few non-null values
                    sample = self.df[col].dropna().head(100)
                    if len(sample) > 0:
                        # Try parsing as datetime
                        pd.to_datetime(sample, errors='raise')
                        self.df[col] = pd.to_datetime(self.df[col], errors='coerce')
                        type_changes[col] = f"{original_type} → datetime"
                        logger.info(f"Converted {col} to datetime")
                        continue
                except:
                    pass
                
                # Try to convert to numeric
                try:
                    # Remove common non-numeric characters
                    cleaned = self.df[col].str.replace(',', '').str.replace('$', '').str.replace('%', '')
                    numeric_converted = pd.to_numeric(cleaned, errors='coerce')
                    
                    # Only convert if at least 80% of values are numeric
                    non_null_pct = numeric_converted.notna().sum() / len(numeric_converted)
                    if non_null_pct > 0.8:
                        self.df[col] = numeric_converted
                        type_changes[col] = f"{original_type} → numeric"
                        logger.info(f"Converted {col} to numeric")
                        continue
                except:
                    pass
                
                # Check if it should be categorical
                unique_ratio = self.df[col].nunique() / len(self.df[col])
                if unique_ratio < 0.05 and self.df[col].nunique() < 100:
                    self.df[col] = self.df[col].astype('category')
                    type_changes[col] = f"{original_type} → category"
                    logger.info(f"Converted {col} to category")
        
        self.cleaning_log.append({
            'action': 'auto_detect_types',
            'changes': type_changes
        })
        
        return type_changes
    
    def standardize_column_names(self) -> Dict[str, str]:
        """
        Standardize column names: lowercase, no spaces, no special chars
        """
        name_mapping = {}
        new_columns = []
        
        for col in self.df.columns:
            # Convert to string and lowercase
            new_name = str(col).lower().strip()
            
            # Replace spaces and special characters with underscores
            new_name = ''.join(c if c.isalnum() else '_' for c in new_name)
            
            # Remove consecutive underscores
            while '__' in new_name:
                new_name = new_name.replace('__', '_')
            
            # Remove leading/trailing underscores
            new_name = new_name.strip('_')
            
            # Ensure uniqueness
            if new_name in new_columns:
                counter = 1
                while f"{new_name}_{counter}" in new_columns:
                    counter += 1
                new_name = f"{new_name}_{counter}"
            
            new_columns.append(new_name)
            if new_name != col:
                name_mapping[col] = new_name
        
        self.df.columns = new_columns
        
        self.cleaning_log.append({
            'action': 'standardize_column_names',
            'changes': name_mapping
        })
        
        return name_mapping
    
    def handle_missing_values(
        self, 
        strategy: str = 'auto',
        numeric_strategy: str = 'median',
        categorical_strategy: str = 'mode'
    ) -> Dict[str, Any]:
        """
        Handle missing values with various strategies
        """
        missing_report = {}
        
        for col in self.df.columns:
            missing_count = self.df[col].isnull().sum()
            if missing_count == 0:
                continue
            
            missing_pct = missing_count / len(self.df)
            
            # Drop columns with >50% missing unless specified otherwise
            if missing_pct > 0.5 and strategy == 'auto':
                self.df = self.df.drop(columns=[col])
                missing_report[col] = f"Dropped (>{missing_pct:.1%} missing)"
                logger.info(f"Dropped column {col} due to high missingness")
                continue
            
            # Handle numeric columns
            if pd.api.types.is_numeric_dtype(self.df[col]):
                if numeric_strategy == 'mean':
                    fill_value = self.df[col].mean()
                elif numeric_strategy == 'median':
                    fill_value = self.df[col].median()
                elif numeric_strategy == 'zero':
                    fill_value = 0
                else:
                    fill_value = self.df[col].median()
                
                self.df[col] = self.df[col].fillna(fill_value)
                missing_report[col] = f"Filled with {numeric_strategy}: {fill_value:.2f}"
            
            # Handle categorical columns
            elif self.df[col].dtype == 'object' or self.df[col].dtype == 'category':
                if categorical_strategy == 'mode':
                    mode_value = self.df[col].mode()
                    if len(mode_value) > 0:
                        fill_value = mode_value[0]
                        self.df[col] = self.df[col].fillna(fill_value)
                        missing_report[col] = f"Filled with mode: {fill_value}"
                else:
                    self.df[col] = self.df[col].fillna('Unknown')
                    missing_report[col] = "Filled with 'Unknown'"
            
            # Handle datetime columns
            elif pd.api.types.is_datetime64_any_dtype(self.df[col]):
                # Forward fill for time series
                self.df[col] = self.df[col].fillna(method='ffill')
                missing_report[col] = "Forward filled"
        
        self.cleaning_log.append({
            'action': 'handle_missing_values',
            'report': missing_report
        })
        
        return missing_report
    
    def remove_duplicates(self, subset: Optional[List[str]] = None) -> int:
        """
        Remove duplicate rows
        """
        initial_count = len(self.df)
        self.df = self.df.drop_duplicates(subset=subset, keep='first')
        removed_count = initial_count - len(self.df)
        
        self.cleaning_log.append({
            'action': 'remove_duplicates',
            'removed': removed_count
        })
        
        logger.info(f"Removed {removed_count} duplicate rows")
        return removed_count
    
    def detect_outliers(
        self, 
        method: str = 'iqr', 
        threshold: float = 3.0
    ) -> Dict[str, List[int]]:
        """
        Detect outliers in numeric columns
        Methods: 'iqr', 'zscore', 'isolation_forest'
        """
        outliers = {}
        
        numeric_cols = self.df.select_dtypes(include=[np.number]).columns
        
        for col in numeric_cols:
            col_outliers = []
            
            if method == 'iqr':
                Q1 = self.df[col].quantile(0.25)
                Q3 = self.df[col].quantile(0.75)
                IQR = Q3 - Q1
                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR
                col_outliers = self.df[
                    (self.df[col] < lower_bound) | (self.df[col] > upper_bound)
                ].index.tolist()
            
            elif method == 'zscore':
                z_scores = np.abs(stats.zscore(self.df[col].dropna()))
                col_outliers = self.df[col].dropna()[z_scores > threshold].index.tolist()
            
            if col_outliers:
                outliers[col] = col_outliers
        
        return outliers
    
    def generate_profile(self) -> Dict[str, Any]:
        """
        Generate comprehensive data profile
        """
        profile = {
            'basic_info': {
                'rows': len(self.df),
                'columns': len(self.df.columns),
                'memory_mb': self.df.memory_usage(deep=True).sum() / 1024 / 1024,
                'total_missing': int(self.df.isnull().sum().sum()),
                'missing_percentage': float(self.df.isnull().sum().sum() / (len(self.df) * len(self.df.columns)) * 100),
                'duplicates': int(self.df.duplicated().sum())
            },
            'columns': {},
            'correlations': {},
            'warnings': [],
            'insights': []
        }
        
        # Column-level statistics
        for col in self.df.columns:
            col_profile = {
                'dtype': str(self.df[col].dtype),
                'non_null': int(self.df[col].count()),
                'null': int(self.df[col].isnull().sum()),
                'null_percentage': float(self.df[col].isnull().sum() / len(self.df) * 100),
                'unique': int(self.df[col].nunique()),
                'unique_percentage': float(self.df[col].nunique() / len(self.df) * 100)
            }
            
            if pd.api.types.is_numeric_dtype(self.df[col]):
                col_profile.update({
                    'mean': float(self.df[col].mean()) if not pd.isna(self.df[col].mean()) else None,
                    'std': float(self.df[col].std()) if not pd.isna(self.df[col].std()) else None,
                    'min': float(self.df[col].min()) if not pd.isna(self.df[col].min()) else None,
                    'max': float(self.df[col].max()) if not pd.isna(self.df[col].max()) else None,
                    'median': float(self.df[col].median()) if not pd.isna(self.df[col].median()) else None,
                    'q25': float(self.df[col].quantile(0.25)) if not pd.isna(self.df[col].quantile(0.25)) else None,
                    'q75': float(self.df[col].quantile(0.75)) if not pd.isna(self.df[col].quantile(0.75)) else None,
                })
                
                # Detect skewness
                skew = self.df[col].skew()
                if abs(skew) > 1:
                    profile['warnings'].append(f"{col}: High skewness ({skew:.2f})")
            
            elif self.df[col].dtype == 'object' or self.df[col].dtype == 'category':
                top_values = self.df[col].value_counts().head(10).to_dict()
                col_profile['top_values'] = {str(k): int(v) for k, v in top_values.items()}
            
            profile['columns'][col] = col_profile
        
        # Correlation analysis for numeric columns
        numeric_df = self.df.select_dtypes(include=[np.number])
        if len(numeric_df.columns) >= 2:
            corr_matrix = numeric_df.corr()
            
            # Find strong correlations
            for i, col1 in enumerate(corr_matrix.columns):
                for col2 in corr_matrix.columns[i+1:]:
                    corr_value = corr_matrix.loc[col1, col2]
                    if not pd.isna(corr_value) and abs(corr_value) > 0.7:
                        profile['insights'].append(
                            f"Strong correlation between {col1} and {col2}: {corr_value:.3f}"
                        )
                        profile['correlations'][f"{col1}_vs_{col2}"] = float(corr_value)
        
        # Data quality warnings
        if profile['basic_info']['missing_percentage'] > 10:
            profile['warnings'].append(
                f"High overall missingness: {profile['basic_info']['missing_percentage']:.1f}%"
            )
        
        if profile['basic_info']['duplicates'] > len(self.df) * 0.05:
            profile['warnings'].append(
                f"High duplicate rate: {profile['basic_info']['duplicates']} rows"
            )
        
        # Constant columns
        constant_cols = [col for col in self.df.columns if self.df[col].nunique() <= 1]
        if constant_cols:
            profile['warnings'].append(f"Constant columns detected: {', '.join(constant_cols)}")
        
        return profile
    
    def get_sample_data(self, n: int = 10) -> List[Dict]:
        """
        Get sample rows as list of dictionaries
        """
        sample = self.df.head(n)
        return sample.replace({np.nan: None}).to_dict('records')
    
    def get_cleaning_summary(self) -> Dict[str, Any]:
        """
        Get summary of all cleaning operations performed
        """
        return {
            'operations': self.cleaning_log,
            'rows_before': len(self.original_df),
            'rows_after': len(self.df),
            'columns_before': len(self.original_df.columns),
            'columns_after': len(self.df.columns),
            'rows_removed': len(self.original_df) - len(self.df),
            'columns_removed': len(self.original_df.columns) - len(self.df.columns)
        }
    
    def export_cleaned_data(self, format: str = 'csv') -> bytes:
        """
        Export cleaned data in specified format
        """
        if format == 'csv':
            return self.df.to_csv(index=False).encode('utf-8')
        elif format == 'excel':
            import io
            output = io.BytesIO()
            self.df.to_excel(output, index=False, engine='openpyxl')
            return output.getvalue()
        elif format == 'json':
            return self.df.to_json(orient='records').encode('utf-8')
        else:
            raise ValueError(f"Unsupported format: {format}")
