import pandas as pd
from typing import List, Dict, Any

def compute_crosstab(df: pd.DataFrame, columns: List[str]) -> Dict[str, Any]:
    if len(columns) == 1:
        freq = df[columns[0]].value_counts(dropna=False).reset_index()
        freq.columns = [columns[0], 'count']
        return {'type': 'frequency', 'data': freq.to_dict(orient='records')}
    elif len(columns) == 2:
        ct = pd.crosstab(df[columns[0]], df[columns[1]], dropna=False)
        return {'type': 'crosstab', 'data': ct.reset_index().to_dict(orient='records'), 'columns': list(ct.columns)}
    else:
        return {'error': 'Select 1 or 2 columns for crosstab'} 