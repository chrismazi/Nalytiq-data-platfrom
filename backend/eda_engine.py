"""
Comprehensive Exploratory Data Analysis Engine
Provides advanced statistical analysis and visualization recommendations
"""
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from scipy import stats
from sklearn.preprocessing import StandardScaler
import logging

logger = logging.getLogger(__name__)

class EDAEngine:
    """
    Advanced EDA engine for comprehensive data analysis
    """
    
    def __init__(self, df: pd.DataFrame):
        self.df = df
        self.numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        self.categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
        self.datetime_cols = df.select_dtypes(include=['datetime64']).columns.tolist()
    
    def descriptive_statistics(self) -> Dict[str, Any]:
        """
        Comprehensive descriptive statistics
        """
        stats_dict = {
            'numeric': {},
            'categorical': {},
            'datetime': {}
        }
        
        # Numeric columns
        if self.numeric_cols:
            for col in self.numeric_cols:
                stats_dict['numeric'][col] = {
                    'count': int(self.df[col].count()),
                    'mean': float(self.df[col].mean()) if not pd.isna(self.df[col].mean()) else None,
                    'median': float(self.df[col].median()) if not pd.isna(self.df[col].median()) else None,
                    'mode': float(self.df[col].mode()[0]) if len(self.df[col].mode()) > 0 else None,
                    'std': float(self.df[col].std()) if not pd.isna(self.df[col].std()) else None,
                    'variance': float(self.df[col].var()) if not pd.isna(self.df[col].var()) else None,
                    'min': float(self.df[col].min()) if not pd.isna(self.df[col].min()) else None,
                    'max': float(self.df[col].max()) if not pd.isna(self.df[col].max()) else None,
                    'range': float(self.df[col].max() - self.df[col].min()) if not pd.isna(self.df[col].max()) else None,
                    'q25': float(self.df[col].quantile(0.25)),
                    'q50': float(self.df[col].quantile(0.50)),
                    'q75': float(self.df[col].quantile(0.75)),
                    'iqr': float(self.df[col].quantile(0.75) - self.df[col].quantile(0.25)),
                    'skewness': float(self.df[col].skew()),
                    'kurtosis': float(self.df[col].kurtosis()),
                    'cv': float(self.df[col].std() / self.df[col].mean()) if self.df[col].mean() != 0 else None
                }
        
        # Categorical columns
        if self.categorical_cols:
            for col in self.categorical_cols:
                value_counts = self.df[col].value_counts()
                stats_dict['categorical'][col] = {
                    'count': int(self.df[col].count()),
                    'unique': int(self.df[col].nunique()),
                    'top': str(value_counts.index[0]) if len(value_counts) > 0 else None,
                    'freq': int(value_counts.iloc[0]) if len(value_counts) > 0 else None,
                    'top_10': value_counts.head(10).to_dict()
                }
        
        # Datetime columns
        if self.datetime_cols:
            for col in self.datetime_cols:
                stats_dict['datetime'][col] = {
                    'min': str(self.df[col].min()),
                    'max': str(self.df[col].max()),
                    'range_days': (self.df[col].max() - self.df[col].min()).days if pd.notna(self.df[col].min()) else None
                }
        
        return stats_dict
    
    def correlation_analysis(self, method: str = 'pearson') -> Dict[str, Any]:
        """
        Correlation analysis with multiple methods
        """
        if len(self.numeric_cols) < 2:
            return {'error': 'Need at least 2 numeric columns for correlation'}
        
        numeric_df = self.df[self.numeric_cols]
        
        # Calculate correlation matrix
        if method == 'pearson':
            corr_matrix = numeric_df.corr(method='pearson')
        elif method == 'spearman':
            corr_matrix = numeric_df.corr(method='spearman')
        elif method == 'kendall':
            corr_matrix = numeric_df.corr(method='kendall')
        else:
            corr_matrix = numeric_df.corr(method='pearson')
        
        # Convert to dictionary
        corr_dict = {}
        for col1 in corr_matrix.columns:
            corr_dict[col1] = {}
            for col2 in corr_matrix.columns:
                value = corr_matrix.loc[col1, col2]
                corr_dict[col1][col2] = float(value) if not pd.isna(value) else None
        
        # Find strong correlations
        strong_correlations = []
        for i, col1 in enumerate(corr_matrix.columns):
            for col2 in corr_matrix.columns[i+1:]:
                corr_value = corr_matrix.loc[col1, col2]
                if not pd.isna(corr_value) and abs(corr_value) > 0.7:
                    strong_correlations.append({
                        'var1': col1,
                        'var2': col2,
                        'correlation': float(corr_value),
                        'strength': 'very_strong' if abs(corr_value) > 0.9 else 'strong'
                    })
        
        return {
            'matrix': corr_dict,
            'method': method,
            'strong_correlations': strong_correlations
        }
    
    def distribution_analysis(self) -> Dict[str, Any]:
        """
        Analyze distributions of numeric variables
        """
        distributions = {}
        
        for col in self.numeric_cols:
            col_data = self.df[col].dropna()
            
            if len(col_data) < 3:
                continue
            
            # Test for normality
            _, p_value = stats.shapiro(col_data.sample(min(len(col_data), 5000)))
            is_normal = p_value > 0.05
            
            # Detect distribution type
            skew = col_data.skew()
            kurt = col_data.kurtosis()
            
            dist_type = 'normal'
            if abs(skew) > 1:
                dist_type = 'right_skewed' if skew > 0 else 'left_skewed'
            elif abs(kurt) > 3:
                dist_type = 'heavy_tailed' if kurt > 3 else 'light_tailed'
            
            distributions[col] = {
                'is_normal': is_normal,
                'normality_p_value': float(p_value),
                'distribution_type': dist_type,
                'skewness': float(skew),
                'kurtosis': float(kurt),
                'recommended_viz': 'histogram' if is_normal else 'boxplot'
            }
        
        return distributions
    
    def detect_relationships(self) -> List[Dict[str, Any]]:
        """
        Detect potential relationships between variables
        """
        relationships = []
        
        # Numeric vs Numeric (already covered by correlation)
        # Categorical vs Numeric (ANOVA)
        for cat_col in self.categorical_cols:
            for num_col in self.numeric_cols:
                groups = [group.dropna() for name, group in self.df.groupby(cat_col)[num_col] if len(group.dropna()) > 0]
                
                if len(groups) >= 2 and all(len(g) > 0 for g in groups):
                    try:
                        f_stat, p_value = stats.f_oneway(*groups)
                        
                        if p_value < 0.05:
                            relationships.append({
                                'type': 'categorical_numeric',
                                'categorical': cat_col,
                                'numeric': num_col,
                                'f_statistic': float(f_stat),
                                'p_value': float(p_value),
                                'significant': True,
                                'interpretation': f"{cat_col} has significant effect on {num_col}"
                            })
                    except:
                        pass
        
        # Categorical vs Categorical (Chi-square)
        for i, cat_col1 in enumerate(self.categorical_cols):
            for cat_col2 in self.categorical_cols[i+1:]:
                try:
                    contingency_table = pd.crosstab(self.df[cat_col1], self.df[cat_col2])
                    chi2, p_value, dof, expected = stats.chi2_contingency(contingency_table)
                    
                    if p_value < 0.05:
                        relationships.append({
                            'type': 'categorical_categorical',
                            'var1': cat_col1,
                            'var2': cat_col2,
                            'chi_square': float(chi2),
                            'p_value': float(p_value),
                            'degrees_of_freedom': int(dof),
                            'significant': True,
                            'interpretation': f"Significant association between {cat_col1} and {cat_col2}"
                        })
                except:
                    pass
        
        return relationships
    
    def time_series_analysis(self) -> Dict[str, Any]:
        """
        Basic time series analysis if datetime columns exist
        """
        if not self.datetime_cols:
            return {'error': 'No datetime columns found'}
        
        analysis = {}
        
        for date_col in self.datetime_cols:
            # Sort by date
            df_sorted = self.df.sort_values(by=date_col)
            
            # Calculate time gaps
            time_diffs = df_sorted[date_col].diff()
            
            analysis[date_col] = {
                'start_date': str(df_sorted[date_col].min()),
                'end_date': str(df_sorted[date_col].max()),
                'total_days': (df_sorted[date_col].max() - df_sorted[date_col].min()).days,
                'avg_gap_days': float(time_diffs.dt.days.mean()) if pd.notna(time_diffs.dt.days.mean()) else None,
                'has_gaps': bool(time_diffs.isna().any()),
                'recommended_analysis': ['trend', 'seasonality', 'autocorrelation']
            }
            
            # Analyze trends for numeric columns
            trends = {}
            for num_col in self.numeric_cols:
                if df_sorted[num_col].notna().sum() > 10:
                    # Simple linear trend
                    x = np.arange(len(df_sorted))
                    y = df_sorted[num_col].values
                    mask = ~np.isnan(y)
                    if mask.sum() > 1:
                        slope, intercept, r_value, p_value, std_err = stats.linregress(x[mask], y[mask])
                        trends[num_col] = {
                            'slope': float(slope),
                            'r_squared': float(r_value ** 2),
                            'p_value': float(p_value),
                            'trend': 'increasing' if slope > 0 else 'decreasing',
                            'significant': p_value < 0.05
                        }
            
            analysis[date_col]['trends'] = trends
        
        return analysis
    
    def outlier_analysis(self, method: str = 'iqr') -> Dict[str, Any]:
        """
        Comprehensive outlier analysis
        """
        outliers = {}
        
        for col in self.numeric_cols:
            col_data = self.df[col].dropna()
            
            if method == 'iqr':
                Q1 = col_data.quantile(0.25)
                Q3 = col_data.quantile(0.75)
                IQR = Q3 - Q1
                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR
                
                outlier_mask = (self.df[col] < lower_bound) | (self.df[col] > upper_bound)
                outlier_count = outlier_mask.sum()
                
            elif method == 'zscore':
                z_scores = np.abs(stats.zscore(col_data))
                outlier_mask = z_scores > 3
                outlier_count = outlier_mask.sum()
                lower_bound = col_data.mean() - 3 * col_data.std()
                upper_bound = col_data.mean() + 3 * col_data.std()
            
            else:
                continue
            
            if outlier_count > 0:
                outliers[col] = {
                    'count': int(outlier_count),
                    'percentage': float(outlier_count / len(self.df) * 100),
                    'lower_bound': float(lower_bound),
                    'upper_bound': float(upper_bound),
                    'method': method,
                    'recommendation': 'investigate' if outlier_count / len(self.df) > 0.01 else 'acceptable'
                }
        
        return outliers
    
    def data_quality_score(self) -> Dict[str, Any]:
        """
        Calculate overall data quality score
        """
        scores = {
            'completeness': 0,
            'consistency': 0,
            'uniqueness': 0,
            'validity': 0,
            'overall': 0
        }
        
        # Completeness: % of non-missing values
        total_cells = len(self.df) * len(self.df.columns)
        non_missing = total_cells - self.df.isnull().sum().sum()
        scores['completeness'] = (non_missing / total_cells) * 100
        
        # Consistency: % of columns with consistent data types
        consistent_cols = 0
        for col in self.df.columns:
            if pd.api.types.is_numeric_dtype(self.df[col]) or \
               pd.api.types.is_datetime64_any_dtype(self.df[col]) or \
               self.df[col].dtype == 'category':
                consistent_cols += 1
        scores['consistency'] = (consistent_cols / len(self.df.columns)) * 100
        
        # Uniqueness: inverse of duplicate percentage
        duplicate_pct = (self.df.duplicated().sum() / len(self.df)) * 100
        scores['uniqueness'] = 100 - duplicate_pct
        
        # Validity: % of columns without extreme outliers
        valid_cols = len(self.df.columns)
        outlier_analysis = self.outlier_analysis()
        for col, info in outlier_analysis.items():
            if info['percentage'] > 5:  # More than 5% outliers
                valid_cols -= 1
        scores['validity'] = (valid_cols / len(self.df.columns)) * 100
        
        # Overall score (weighted average)
        scores['overall'] = (
            scores['completeness'] * 0.3 +
            scores['consistency'] * 0.25 +
            scores['uniqueness'] * 0.25 +
            scores['validity'] * 0.2
        )
        
        # Add grade
        if scores['overall'] >= 90:
            scores['grade'] = 'A (Excellent)'
        elif scores['overall'] >= 80:
            scores['grade'] = 'B (Good)'
        elif scores['overall'] >= 70:
            scores['grade'] = 'C (Fair)'
        elif scores['overall'] >= 60:
            scores['grade'] = 'D (Poor)'
        else:
            scores['grade'] = 'F (Very Poor)'
        
        return scores
    
    def generate_insights(self) -> List[str]:
        """
        Generate automated insights from the data
        """
        insights = []
        
        # Dataset size insight
        if len(self.df) > 100000:
            insights.append(f"Large dataset with {len(self.df):,} rows - consider sampling for faster analysis")
        
        # Missing data insights
        missing_pct = (self.df.isnull().sum().sum() / (len(self.df) * len(self.df.columns))) * 100
        if missing_pct > 20:
            insights.append(f"High missingness detected ({missing_pct:.1f}%) - data imputation recommended")
        elif missing_pct < 1:
            insights.append("Excellent data completeness - minimal missing values")
        
        # Correlation insights
        if len(self.numeric_cols) >= 2:
            corr_analysis = self.correlation_analysis()
            if corr_analysis.get('strong_correlations'):
                insights.append(f"Found {len(corr_analysis['strong_correlations'])} strong correlations - potential for feature engineering")
        
        # Distribution insights
        dist_analysis = self.distribution_analysis()
        skewed_cols = [col for col, info in dist_analysis.items() if abs(info['skewness']) > 1]
        if skewed_cols:
            insights.append(f"{len(skewed_cols)} variables show skewness - consider log transformation")
        
        # Categorical insights
        high_cardinality = [col for col in self.categorical_cols if self.df[col].nunique() > 50]
        if high_cardinality:
            insights.append(f"High cardinality detected in {len(high_cardinality)} categorical variables")
        
        return insights
