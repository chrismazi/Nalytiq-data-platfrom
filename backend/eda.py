import pandas as pd
import numpy as np
from typing import Dict, Any

def automated_eda(df: pd.DataFrame) -> Dict[str, Any]:
    summary = {}
    summary['shape'] = list(df.shape)
    summary['columns'] = list(df.columns)
    summary['dtypes'] = {col: str(dtype) for col, dtype in df.dtypes.items()}
    summary['missing'] = df.isnull().sum().to_dict()
    summary['describe'] = df.describe(include='all').replace({np.nan: None}).to_dict()
    # Suggest visualizations based on column types
    suggestions = []
    for col in df.columns:
        if pd.api.types.is_numeric_dtype(df[col]):
            suggestions.append({'column': col, 'type': 'histogram'})
        elif pd.api.types.is_categorical_dtype(df[col]) or df[col].nunique() < 20:
            suggestions.append({'column': col, 'type': 'bar'})
    summary['visualization_suggestions'] = suggestions
    return summary 