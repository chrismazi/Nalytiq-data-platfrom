"""
Advanced Analysis Functions
Universal functions that work with any dataset structure
"""
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)

class AdvancedAnalyzer:
    """
    Universal advanced analytics that work with any dataset
    """
    
    def __init__(self, df: pd.DataFrame):
        self.df = df
    
    def grouped_statistics(
        self,
        group_by: str,
        value_col: str,
        aggregation: str = 'mean'
    ) -> Dict[str, Any]:
        """
        Compute grouped statistics
        """
        if group_by not in self.df.columns:
            raise ValueError(f"Column '{group_by}' not found")
        
        if value_col not in self.df.columns:
            raise ValueError(f"Column '{value_col}' not found")
        
        if not pd.api.types.is_numeric_dtype(self.df[value_col]):
            raise ValueError(f"Column '{value_col}' must be numeric")
        
        # Valid aggregations
        valid_aggs = ['mean', 'sum', 'count', 'min', 'max', 'median', 'std', 'var']
        if aggregation not in valid_aggs:
            raise ValueError(f"Invalid aggregation. Must be one of: {', '.join(valid_aggs)}")
        
        # Perform aggregation
        if aggregation == 'median':
            grouped = self.df.groupby(group_by)[value_col].median()
        else:
            grouped = self.df.groupby(group_by)[value_col].agg(aggregation)
        
        # Convert to list of dicts for frontend
        data = [
            {
                'category': str(cat),
                'value': float(val) if not pd.isna(val) else 0
            }
            for cat, val in grouped.items()
        ]
        
        # Sort by value descending
        data.sort(key=lambda x: x['value'], reverse=True)
        
        return {
            'group_by': group_by,
            'value_col': value_col,
            'aggregation': aggregation,
            'data': data,
            'n_groups': len(data),
            'total': float(grouped.sum()) if aggregation in ['sum', 'count'] else None,
            'max': float(grouped.max()),
            'min': float(grouped.min()),
            'mean': float(grouped.mean())
        }
    
    def crosstab_analysis(
        self,
        row_col: str,
        col_col: str,
        value_col: Optional[str] = None,
        aggfunc: str = 'count',
        normalize: bool = False
    ) -> Dict[str, Any]:
        """
        Create crosstabulation / pivot table
        """
        if row_col not in self.df.columns:
            raise ValueError(f"Column '{row_col}' not found")
        
        if col_col not in self.df.columns:
            raise ValueError(f"Column '{col_col}' not found")
        
        if value_col and value_col not in self.df.columns:
            raise ValueError(f"Column '{value_col}' not found")
        
        # Create crosstab
        if value_col:
            # Pivot with aggregation
            if aggfunc == 'count':
                ct = pd.pivot_table(
                    self.df, 
                    index=row_col, 
                    columns=col_col, 
                    values=value_col,
                    aggfunc='count',
                    fill_value=0
                )
            elif aggfunc in ['mean', 'sum', 'min', 'max', 'median']:
                ct = pd.pivot_table(
                    self.df,
                    index=row_col,
                    columns=col_col,
                    values=value_col,
                    aggfunc=aggfunc,
                    fill_value=0
                )
            else:
                raise ValueError(f"Invalid aggfunc: {aggfunc}")
        else:
            # Simple frequency table
            ct = pd.crosstab(self.df[row_col], self.df[col_col])
        
        # Normalize if requested
        if normalize:
            ct = ct.div(ct.sum(axis=1), axis=0) * 100
        
        # Convert to format suitable for frontend
        data = []
        for row_idx in ct.index:
            row_data = {'category': str(row_idx)}
            for col_idx in ct.columns:
                row_data[str(col_idx)] = float(ct.loc[row_idx, col_idx])
            data.append(row_data)
        
        return {
            'row_variable': row_col,
            'column_variable': col_col,
            'value_variable': value_col,
            'aggregation': aggfunc,
            'normalized': normalize,
            'data': data,
            'row_labels': [str(x) for x in ct.index.tolist()],
            'column_labels': [str(x) for x in ct.columns.tolist()],
            'row_totals': ct.sum(axis=1).to_dict(),
            'column_totals': ct.sum(axis=0).to_dict(),
            'grand_total': float(ct.sum().sum())
        }
    
    def top_n_analysis(
        self,
        group_col: str,
        value_col: str,
        n: int = 10,
        ascending: bool = False
    ) -> Dict[str, Any]:
        """
        Get top N records by a value
        """
        if group_col not in self.df.columns:
            raise ValueError(f"Column '{group_col}' not found")
        
        if value_col not in self.df.columns:
            raise ValueError(f"Column '{value_col}' not found")
        
        if not pd.api.types.is_numeric_dtype(self.df[value_col]):
            raise ValueError(f"Column '{value_col}' must be numeric")
        
        # Group and aggregate
        grouped = self.df.groupby(group_col)[value_col].mean().sort_values(ascending=ascending)
        top_n = grouped.head(n)
        
        data = [
            {
                'name': str(cat),
                'value': float(val)
            }
            for cat, val in top_n.items()
        ]
        
        return {
            'group_col': group_col,
            'value_col': value_col,
            'n': n,
            'order': 'ascending' if ascending else 'descending',
            'data': data
        }
    
    def comparison_analysis(
        self,
        category_col: str,
        value_col: str,
        categories: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Compare values across categories
        """
        if category_col not in self.df.columns:
            raise ValueError(f"Column '{category_col}' not found")
        
        if value_col not in self.df.columns:
            raise ValueError(f"Column '{value_col}' not found")
        
        if not pd.api.types.is_numeric_dtype(self.df[value_col]):
            raise ValueError(f"Column '{value_col}' must be numeric")
        
        # Filter to specific categories if provided
        if categories:
            df_filtered = self.df[self.df[category_col].isin(categories)]
        else:
            df_filtered = self.df
        
        # Compute statistics for each category
        comparison = df_filtered.groupby(category_col)[value_col].agg([
            'count', 'mean', 'median', 'std', 'min', 'max'
        ]).reset_index()
        
        data = []
        for _, row in comparison.iterrows():
            data.append({
                'category': str(row[category_col]),
                'count': int(row['count']),
                'mean': float(row['mean']),
                'median': float(row['median']),
                'std': float(row['std']) if not pd.isna(row['std']) else 0,
                'min': float(row['min']),
                'max': float(row['max'])
            })
        
        # Sort by mean descending
        data.sort(key=lambda x: x['mean'], reverse=True)
        
        return {
            'category_col': category_col,
            'value_col': value_col,
            'n_categories': len(data),
            'data': data,
            'overall_mean': float(df_filtered[value_col].mean()),
            'overall_std': float(df_filtered[value_col].std())
        }
    
    def trend_analysis(
        self,
        date_col: str,
        value_col: str,
        freq: str = 'M'
    ) -> Dict[str, Any]:
        """
        Analyze trends over time
        """
        if date_col not in self.df.columns:
            raise ValueError(f"Column '{date_col}' not found")
        
        if value_col not in self.df.columns:
            raise ValueError(f"Column '{value_col}' not found")
        
        # Convert to datetime if not already
        if not pd.api.types.is_datetime64_any_dtype(self.df[date_col]):
            try:
                df_copy = self.df.copy()
                df_copy[date_col] = pd.to_datetime(df_copy[date_col])
            except:
                raise ValueError(f"Cannot convert '{date_col}' to datetime")
        else:
            df_copy = self.df.copy()
        
        # Sort by date
        df_copy = df_copy.sort_values(by=date_col)
        
        # Resample by frequency
        df_copy = df_copy.set_index(date_col)
        resampled = df_copy[value_col].resample(freq).mean()
        
        data = [
            {
                'date': date.strftime('%Y-%m-%d'),
                'value': float(val) if not pd.isna(val) else 0
            }
            for date, val in resampled.items()
        ]
        
        # Calculate trend
        if len(resampled) > 1:
            x = np.arange(len(resampled))
            y = resampled.values
            mask = ~np.isnan(y)
            if mask.sum() > 1:
                from scipy import stats as scipy_stats
                slope, intercept, r_value, p_value, std_err = scipy_stats.linregress(x[mask], y[mask])
                trend = 'increasing' if slope > 0 else 'decreasing'
                significant = p_value < 0.05
            else:
                slope, r_value, p_value, trend, significant = 0, 0, 1, 'flat', False
        else:
            slope, r_value, p_value, trend, significant = 0, 0, 1, 'flat', False
        
        return {
            'date_col': date_col,
            'value_col': value_col,
            'frequency': freq,
            'data': data,
            'n_periods': len(data),
            'trend': {
                'direction': trend,
                'slope': float(slope),
                'r_squared': float(r_value ** 2),
                'p_value': float(p_value),
                'significant': significant
            }
        }
    
    def segment_analysis(
        self,
        segment_col: str,
        metrics: List[str]
    ) -> Dict[str, Any]:
        """
        Analyze multiple metrics by segment
        """
        if segment_col not in self.df.columns:
            raise ValueError(f"Column '{segment_col}' not found")
        
        for metric in metrics:
            if metric not in self.df.columns:
                raise ValueError(f"Metric column '{metric}' not found")
            if not pd.api.types.is_numeric_dtype(self.df[metric]):
                raise ValueError(f"Metric '{metric}' must be numeric")
        
        # Compute metrics for each segment
        segments = []
        for segment_value in self.df[segment_col].unique():
            if pd.isna(segment_value):
                continue
            
            segment_df = self.df[self.df[segment_col] == segment_value]
            segment_data = {
                'segment': str(segment_value),
                'count': len(segment_df)
            }
            
            for metric in metrics:
                segment_data[f'{metric}_mean'] = float(segment_df[metric].mean())
                segment_data[f'{metric}_median'] = float(segment_df[metric].median())
                segment_data[f'{metric}_std'] = float(segment_df[metric].std()) if not pd.isna(segment_df[metric].std()) else 0
            
            segments.append(segment_data)
        
        return {
            'segment_col': segment_col,
            'metrics': metrics,
            'n_segments': len(segments),
            'segments': segments
        }
    
    def correlation_heatmap_data(self, columns: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Generate data for correlation heatmap
        """
        # Get numeric columns
        numeric_cols = self.df.select_dtypes(include=[np.number]).columns.tolist()
        
        if columns:
            numeric_cols = [col for col in columns if col in numeric_cols]
        
        if len(numeric_cols) < 2:
            raise ValueError("Need at least 2 numeric columns")
        
        # Calculate correlation
        corr_matrix = self.df[numeric_cols].corr()
        
        # Convert to format for heatmap
        data = []
        for i, col1 in enumerate(corr_matrix.columns):
            for j, col2 in enumerate(corr_matrix.columns):
                data.append({
                    'x': str(col1),
                    'y': str(col2),
                    'value': float(corr_matrix.iloc[i, j])
                })
        
        return {
            'columns': numeric_cols,
            'data': data,
            'size': len(numeric_cols)
        }
