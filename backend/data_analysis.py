import pandas as pd
import numpy as np
import os
from typing import Dict, Any

class DataAnalyzer:
    """A simple data analyzer for CSV, Excel, and Stata files"""
    def __init__(self):
        self.df = None
        self.file_path = None
        self.file_type = None

    def _map_education_levels(self, df: pd.DataFrame) -> pd.DataFrame:
        education_mapping = {
            'Pre-primary': 'Nursery',
            'Primary 1': 'Primary',
            'Primary 2': 'Primary',
            'Primary 3': 'Primary',
            'Primary 4': 'Primary',
            'Primary 5': 'Primary',
            'Primary 6,7,8': 'Primary',
            'Not complete P1': 'Primary Dropout',
            'Secondary 1': 'Secondary',
            'Secondary 2': 'Secondary',
            'Secondary 3': 'Secondary',
            'Secondary 4': 'Secondary',
            'Secondary 5': 'Secondary',
            'Post primary 1': 'Post-Secondary',
            'Post primary 2': 'Post-Secondary',
            'Post primary 3': 'Post-Secondary',
            'Post primary 4': 'Post-Secondary',
            'Post primary 5': 'Post-Secondary',
            'Post primary 6,7,8': 'Post-Secondary',
            'University 1': 'Bachelors',
            'University 2': 'Bachelors',
            'University 3': 'Bachelors',
            'University 4': 'Masters',
            'University 5': 'Masters',
            'University 6': 'PhD',
            'University 7': 'PhD',
            'Missing': 'Unknown',
            'nan': 'Unknown',
            'Unknown': 'Unknown'
        }
        if 's4aq2' in df.columns:
            df['education_level'] = df['s4aq2'].map(education_mapping).fillna('Unknown')
        return df

    def read_file(self, file_path: str) -> Dict[str, Any]:
        self.file_path = file_path
        self.file_type = os.path.splitext(file_path)[-1].lower()
        try:
            if self.file_type == '.csv':
                self.df = self._read_csv(file_path)
            elif self.file_type in ['.xls', '.xlsx']:
                self.df = self._read_excel(file_path)
            elif self.file_type == '.dta':
                self.df = self._read_stata(file_path)
            else:
                raise ValueError(f"Unsupported file type: {self.file_type}")
            # Standardize column names: lowercase and strip spaces
            self.df.columns = [str(c).strip().lower() for c in self.df.columns]
            # Apply education mapping and categorical cleaning
            self.df = self._map_education_levels(self.df)
            for col in self.df.columns:
                if str(self.df[col].dtype).startswith('category'):
                    if 'Unknown' not in self.df[col].cat.categories:
                        self.df[col] = self.df[col].cat.add_categories(['Unknown'])
                    self.df[col] = self.df[col].fillna('Unknown')
                elif self.df[col].dtype == object:
                    self.df[col] = self.df[col].fillna('Unknown')
            return self._get_basic_info()
        except Exception as e:
            return {"error": str(e)}

    def _read_csv(self, file_path: str) -> pd.DataFrame:
        encodings = ['utf-8', 'latin1', 'cp1252', 'iso-8859-1']
        for encoding in encodings:
            try:
                df = pd.read_csv(file_path, encoding=encoding)
                print(f"Successfully read CSV with {encoding} encoding")
                return df
            except UnicodeDecodeError:
                continue
            except Exception as e:
                print(f"Error reading CSV with {encoding}: {e}")
                continue
        raise ValueError("Could not read CSV file with any supported encoding")

    def _read_excel(self, file_path: str) -> pd.DataFrame:
        try:
            df = pd.read_excel(file_path)
            print("Successfully read Excel file")
            return df
        except Exception as e:
            raise ValueError(f"Error reading Excel file: {e}")

    def _read_stata(self, file_path: str) -> pd.DataFrame:
        try:
            df = pd.read_stata(file_path)
            print("Successfully read Stata file")
            return df
        except Exception as e:
            raise ValueError(f"Error reading Stata file: {e}")

    def _get_basic_info(self) -> Dict[str, Any]:
        if self.df is None:
            return {"error": "No dataset loaded"}
        df_clean = self.df.copy()
        df_clean = df_clean.replace([np.inf, -np.inf], np.nan)
        info = {
            "file_type": self.file_type,
            "shape": list(self.df.shape),
            "columns": list(self.df.columns),
            "dtypes": {col: str(dtype) for col, dtype in self.df.dtypes.items()},
            "memory_usage_mb": round(self.df.memory_usage(deep=True).sum() / 1024 / 1024, 2),
            "missing_values": int(self.df.isnull().sum().sum()),
            "duplicate_rows": int(self.df.duplicated().sum()),
        }
        sample_data = []
        for idx, row in self.df.head(10).iterrows():
            row_dict = {}
            for col in self.df.columns:
                value = row[col]
                if pd.isna(value) or value is None:
                    row_dict[col] = None
                elif isinstance(value, (np.integer, np.floating)):
                    row_dict[col] = float(value) if np.isnan(value) else value.item()
                else:
                    row_dict[col] = str(value)
            sample_data.append(row_dict)
        info["sample_data"] = sample_data
        column_stats = {}
        for col in self.df.columns:
            col_stats = {
                "dtype": str(self.df[col].dtype),
                "non_null_count": int(self.df[col].count()),
                "missing_count": int(self.df[col].isnull().sum()),
                "unique_count": int(self.df[col].nunique()),
            }
            if pd.api.types.is_numeric_dtype(self.df[col]):
                col_stats.update({
                    "min": float(self.df[col].min()) if not pd.isna(self.df[col].min()) else None,
                    "max": float(self.df[col].max()) if not pd.isna(self.df[col].max()) else None,
                    "mean": float(self.df[col].mean()) if not pd.isna(self.df[col].mean()) else None,
                    "std": float(self.df[col].std()) if not pd.isna(self.df[col].std()) else None,
                })
            column_stats[col] = col_stats
        info["column_stats"] = column_stats
        return info

    def get_descriptive_stats(self) -> Dict[str, Any]:
        """Get descriptive statistics"""
        if self.df is None:
            return {"error": "No dataset loaded"}
        
        try:
            # Get describe() output and handle NaN values
            desc = self.df.describe(include='all')
            
            # Convert to dictionary with proper NaN handling
            desc_dict = {}
            for col in desc.columns:
                col_dict = {}
                for idx in desc.index:
                    value = desc.loc[idx, col]
                    if pd.isna(value):
                        col_dict[str(idx)] = None
                    elif isinstance(value, (np.integer, np.floating)):
                        col_dict[str(idx)] = float(value)
                    else:
                        col_dict[str(idx)] = str(value)
                desc_dict[col] = col_dict
            
            return {"descriptive_stats": desc_dict}
            
        except Exception as e:
            return {"error": f"Error calculating descriptive stats: {e}"}

    def get_correlation_matrix(self) -> Dict[str, Any]:
        """Get correlation matrix for numeric columns"""
        if self.df is None:
            return {"error": "No dataset loaded"}
        
        try:
            # Select only numeric columns
            numeric_cols = self.df.select_dtypes(include=[np.number]).columns
            
            if len(numeric_cols) < 2:
                return {"error": "Need at least 2 numeric columns for correlation"}
            
            corr_matrix = self.df[numeric_cols].corr()
            
            # Convert to dictionary with proper NaN handling
            corr_dict = {}
            for col1 in corr_matrix.columns:
                col_dict = {}
                for col2 in corr_matrix.columns:
                    value = corr_matrix.loc[col1, col2]
                    if pd.isna(value):
                        col_dict[col2] = None
                    else:
                        col_dict[col2] = float(value)
                corr_dict[col1] = col_dict
            
            return {"correlation_matrix": corr_dict}
            
        except Exception as e:
            return {"error": f"Error calculating correlation matrix: {e}"}

    def get_grouped_stats(self, group_by: str, value: str, agg: str = 'mean') -> Dict[str, Any]:
        if self.df is None:
            return {"error": "No dataset loaded"}
        if group_by not in self.df.columns or value not in self.df.columns:
            return {"error": f"Column {group_by} or {value} not found in dataset"}
        if self.df[group_by].dropna().empty or self.df[value].dropna().empty:
            return {"error": f"No data in column {group_by} or {value}"}
        try:
            # Convert group_by to string to avoid pandas category issues
            self.df[group_by] = self.df[group_by].astype(str)
            grouped = self.df.groupby(group_by, observed=False)[value].agg(agg).reset_index()
            return {"group": group_by, "value": value, "agg": agg, "data": grouped.to_dict(orient="records")}
        except Exception as e:
            return {"error": f"Groupby failed: {e}"}

    def get_top_districts_by_consumption(self, top_n: int = 5) -> Dict[str, Any]:
        if self.df is None:
            return {"error": "No dataset loaded"}
        if "district" not in self.df.columns or "consumption" not in self.df.columns:
            return {"error": "Column district or consumption not found in dataset"}
        if self.df["district"].dropna().empty or self.df["consumption"].dropna().empty:
            return {"error": "No data in column district or consumption"}
        try:
            self.df["district"] = self.df["district"].astype(str)
            top = self.df.groupby("district", observed=False)["consumption"].mean().nlargest(top_n).reset_index()
            return {"data": top.to_dict(orient="records")}
        except Exception as e:
            return {"error": f"Groupby failed: {e}"}

    def get_poverty_by_education(self) -> Dict[str, Any]:
        if self.df is None:
            return {"error": "No dataset loaded"}
        if "education_level" not in self.df.columns or "poverty" not in self.df.columns:
            return {"error": "Column education_level or poverty not found in dataset"}
        if self.df["education_level"].dropna().empty or self.df["poverty"].dropna().empty:
            return {"error": "No data in column education_level or poverty"}
        try:
            self.df["education_level"] = self.df["education_level"].astype(str)
            crosstab = pd.crosstab(self.df["education_level"], self.df["poverty"]).reset_index()
            melted = crosstab.melt(id_vars=["education_level"], var_name="poverty_level", value_name="count")
            return {"data": melted.to_dict(orient="records")}
        except Exception as e:
            return {"error": f"Crosstab failed: {e}"}

    def get_urban_rural_consumption(self) -> Dict[str, Any]:
        if self.df is None:
            return {"error": "No dataset loaded"}
        if "ur2_2012" not in self.df.columns or "consumption" not in self.df.columns:
            return {"error": "Column ur2_2012 or consumption not found in dataset"}
        if self.df["ur2_2012"].dropna().empty or self.df["consumption"].dropna().empty:
            return {"error": "No data in column ur2_2012 or consumption"}
        try:
            self.df["ur2_2012"] = self.df["ur2_2012"].astype(str)
            grouped = self.df.groupby("ur2_2012", observed=False)["consumption"].mean().reset_index()
            return {"data": grouped.to_dict(orient="records")}
        except Exception as e:
            return {"error": f"Groupby failed: {e}"}

    def get_poverty_by_gender(self) -> Dict[str, Any]:
        if self.df is None:
            return {"error": "No dataset loaded"}
        if "s1q1" not in self.df.columns or "poverty" not in self.df.columns:
            return {"error": "Column s1q1 or poverty not found in dataset"}
        if self.df["s1q1"].dropna().empty or self.df["poverty"].dropna().empty:
            return {"error": "No data in column s1q1 or poverty"}
        try:
            self.df["s1q1"] = self.df["s1q1"].astype(str)
            grouped = self.df.groupby("s1q1", observed=False)["poverty"].mean().reset_index()
            return {"data": grouped.to_dict(orient="records")}
        except Exception as e:
            return {"error": f"Groupby failed: {e}"}

    def get_poverty_by_province(self) -> Dict[str, Any]:
        if self.df is None:
            return {"error": "No dataset loaded"}
        if "province" not in self.df.columns or "poverty" not in self.df.columns:
            return {"error": "Column province or poverty not found in dataset"}
        if self.df["province"].dropna().empty or self.df["poverty"].dropna().empty:
            return {"error": "No data in column province or poverty"}
        try:
            self.df["province"] = self.df["province"].astype(str)
            grouped = self.df.groupby("province", observed=False)["poverty"].mean().reset_index()
            return {"data": grouped.to_dict(orient="records")}
        except Exception as e:
            return {"error": f"Groupby failed: {e}"}

    def get_avg_consumption_by_province(self) -> Dict[str, Any]:
        if self.df is None:
            return {"error": "No dataset loaded"}
        if "province" not in self.df.columns or "consumption" not in self.df.columns:
            return {"error": "Column province or consumption not found in dataset"}
        if self.df["province"].dropna().empty or self.df["consumption"].dropna().empty:
            return {"error": "No data in column province or consumption"}
        try:
            self.df["province"] = self.df["province"].astype(str)
            grouped = self.df.groupby("province", observed=False)["consumption"].mean().reset_index()
            return {"data": grouped.to_dict(orient="records")}
        except Exception as e:
            return {"error": f"Groupby failed: {e}"}

if __name__ == "__main__":
    test_file = "test_data.csv"
    if os.path.exists(test_file):
        print("Analyzing test file...")
        analyzer = DataAnalyzer()
        result = analyzer.read_file(test_file)
        print("Analysis result:")
        print(f"Shape: {result.get('shape', 'N/A')}")
        print(f"Columns: {result.get('columns', 'N/A')}")
        print(f"Missing values: {result.get('missing_values', 'N/A')}")
        print(f"Sample data rows: {len(result.get('sample_data', []))}")
    else:
        print(f"Test file {test_file} not found. Create a CSV file to test.") 