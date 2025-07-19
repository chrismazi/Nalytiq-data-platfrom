import pandas as pd
from typing import List, Dict, Any
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, mean_squared_error

def run_model(df: pd.DataFrame, target: str, features: List[str]) -> Dict[str, Any]:
    X = df[features].select_dtypes(include=['number']).fillna(0)
    y = df[target]
    if y.dtype.kind in 'biu':
        model = RandomForestClassifier(n_estimators=20, random_state=42)
    else:
        model = RandomForestRegressor(n_estimators=20, random_state=42)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    if y.dtype.kind in 'biu':
        score = accuracy_score(y_test, y_pred)
    else:
        score = mean_squared_error(y_test, y_pred) ** 0.5
    importances = dict(zip(X.columns, model.feature_importances_))
    return {'score': score, 'importances': importances, 'predictions': y_pred[:20].tolist()} 