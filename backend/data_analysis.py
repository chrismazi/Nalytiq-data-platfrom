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
        try:
            grouped = self.df.groupby(group_by)[value].agg(agg).reset_index()
            return {"group": group_by, "value": value, "agg": agg, "data": grouped.to_dict(orient="records")}
        except Exception as e:
            return {"error": str(e)}

    def get_top_districts_by_consumption(self, top_n: int = 5) -> Dict[str, Any]:
        if self.df is None:
            return {"error": "No dataset loaded"}
        try:
            top = self.df.groupby("district")["Consumption"].mean().nlargest(top_n).reset_index()
            return {"data": top.to_dict(orient="records")}
        except Exception as e:
            return {"error": str(e)}

    def get_poverty_by_education(self) -> Dict[str, Any]:
        if self.df is None:
            return {"error": "No dataset loaded"}
        try:
            if "education_level" not in self.df.columns:
                return {"error": "education_level column missing"}
            crosstab = pd.crosstab(self.df["education_level"], self.df["poverty"]).reset_index()
            melted = crosstab.melt(id_vars=["education_level"], var_name="poverty_level", value_name="count")
            return {"data": melted.to_dict(orient="records")}
        except Exception as e:
            return {"error": str(e)}

    def get_urban_rural_consumption(self) -> Dict[str, Any]:
        if self.df is None:
            return {"error": "No dataset loaded"}
        try:
            grouped = self.df.groupby("ur2_2012")["Consumption"].mean().reset_index()
            return {"data": grouped.to_dict(orient="records")}
        except Exception as e:
            return {"error": str(e)}

    def get_poverty_by_gender(self) -> Dict[str, Any]:
        if self.df is None:
            return {"error": "No dataset loaded"}
        try:
            grouped = self.df.groupby("s1q1")["poverty"].mean().reset_index()
            return {"data": grouped.to_dict(orient="records")}
        except Exception as e:
            return {"error": str(e)}

    def get_poverty_by_province(self) -> Dict[str, Any]:
        if self.df is None:
            return {"error": "No dataset loaded"}
        try:
            grouped = self.df.groupby("province")["poverty"].mean().reset_index()
            return {"data": grouped.to_dict(orient="records")}
        except Exception as e:
            return {"error": str(e)}

    def get_avg_consumption_by_province(self) -> Dict[str, Any]:
        if self.df is None:
            return {"error": "No dataset loaded"}
        try:
            grouped = self.df.groupby("province")["Consumption"].mean().reset_index()
            return {"data": grouped.to_dict(orient="records")}
        except Exception as e:
            return {"error": str(e)}

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