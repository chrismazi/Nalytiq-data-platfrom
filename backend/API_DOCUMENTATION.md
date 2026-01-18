# Nalytiq Platform - API Documentation

##  Enhanced Universal Analytics API

The Nalytiq platform now features a **universal analytics engine** that works with ANY dataset structure. No more Rwanda-specific limitations!

---

##  **Core Features**

### **1. Universal Data Processing**
- Works with any CSV, Excel, or Stata file
- Automatic type detection and conversion
- Intelligent missing value handling
- Duplicate removal
- Outlier detection
- Data quality scoring

### **2. Comprehensive EDA**
- Descriptive statistics for all column types
- Correlation analysis (Pearson, Spearman, Kendall)
- Distribution analysis
- Relationship detection (ANOVA, Chi-square)
- Time series analysis
- Automated insights generation

### **3. Advanced Analytics**
- Grouped statistics with any aggregation
- Cross-tabulation / Pivot tables
- Top N analysis
- Comparison analysis
- Trend analysis
- Segment analysis

### **4. Machine Learning**
- Random Forest Classifier/Regressor
- Automatic feature encoding
- Cross-validation
- Feature importance
- Model evaluation metrics
- Prediction capabilities

---

##  **API Endpoints**

### **Data Upload & Processing**

#### **POST /api/upload-enhanced/**
Enhanced upload with automatic cleaning and profiling

**Request:**
- `file`: Upload file (multipart/form-data)
- `name`: Dataset name (optional)
- `description`: Description (optional)
- `auto_clean`: Enable automatic cleaning (default: true)

**Response:**
```json
{
  "dataset_id": 1,
  "file_info": {
    "filename": "data.csv",
    "size_mb": 2.5,
    "extension": ".csv"
  },
  "basic_info": {
    "rows": 10000,
    "columns": 25,
    "memory_mb": 15.2,
    "total_missing": 150,
    "missing_percentage": 0.6,
    "duplicates": 5
  },
  "columns": {
    "column_name": {
      "dtype": "float64",
      "non_null": 9950,
      "null": 50,
      "null_percentage": 0.5,
      "unique": 8500,
      "mean": 125.5,
      "std": 45.2,
      "min": 10.0,
      "max": 500.0
    }
  },
  "descriptive_stats": {...},
  "correlations": {...},
  "distributions": {...},
  "quality_score": {
    "completeness": 99.4,
    "consistency": 95.0,
    "uniqueness": 99.95,
    "validity": 98.0,
    "overall": 98.1,
    "grade": "A (Excellent)"
  },
  "insights": [
    "Excellent data completeness - minimal missing values",
    "Found 3 strong correlations - potential for feature engineering"
  ],
  "warnings": []
}
```

---

### **Advanced Analysis**

#### **POST /api/analyze/grouped-stats/**
Compute grouped statistics with any aggregation

**Request:**
```json
{
  "dataset_id": 1,
  "group_by": "category",
  "value_col": "sales",
  "aggregation": "mean"
}
```

**Aggregations:** mean, sum, count, min, max, median, std, var

**Response:**
```json
{
  "group_by": "category",
  "value_col": "sales",
  "aggregation": "mean",
  "data": [
    {"category": "Electronics", "value": 1250.50},
    {"category": "Clothing", "value": 850.25}
  ],
  "n_groups": 5,
  "total": 12500.0,
  "max": 1500.0,
  "min": 500.0,
  "mean": 1000.0
}
```

---

#### **POST /api/analyze/crosstab/**
Generate cross-tabulation / pivot tables

**Request:**
```json
{
  "dataset_id": 1,
  "row_col": "region",
  "col_col": "product_type",
  "value_col": "revenue",
  "aggfunc": "sum",
  "normalize": false
}
```

**Response:**
```json
{
  "row_variable": "region",
  "column_variable": "product_type",
  "value_variable": "revenue",
  "aggregation": "sum",
  "normalized": false,
  "data": [
    {
      "category": "North",
      "Electronics": 15000,
      "Clothing": 8000,
      "Food": 5000
    }
  ],
  "row_labels": ["North", "South", "East", "West"],
  "column_labels": ["Electronics", "Clothing", "Food"],
  "row_totals": {...},
  "column_totals": {...},
  "grand_total": 125000.0
}
```

---

#### **POST /api/analyze/top-n/**
Get top N records by value

**Request:**
```json
{
  "dataset_id": 1,
  "group_col": "customer",
  "value_col": "total_purchases",
  "n": 10,
  "ascending": false
}
```

---

#### **POST /api/analyze/comparison/**
Compare values across categories

**Request:**
```json
{
  "dataset_id": 1,
  "category_col": "department",
  "value_col": "satisfaction_score",
  "categories": ["Sales", "Marketing", "Engineering"]
}
```

**Response:**
```json
{
  "category_col": "department",
  "value_col": "satisfaction_score",
  "n_categories": 3,
  "data": [
    {
      "category": "Engineering",
      "count": 150,
      "mean": 8.5,
      "median": 8.7,
      "std": 1.2,
      "min": 5.0,
      "max": 10.0
    }
  ],
  "overall_mean": 7.8,
  "overall_std": 1.5
}
```

---

### **Machine Learning**

#### **POST /api/ml/train/**
Train Random Forest model

**Request:**
```json
{
  "dataset_id": 1,
  "target": "churn",
  "features": ["age", "tenure", "usage", "satisfaction"],
  "test_size": 0.2,
  "n_estimators": 100,
  "max_depth": 10
}
```

**Response:**
```json
{
  "model_type": "classification",
  "target": "churn",
  "features": ["age", "tenure", "usage", "satisfaction"],
  "n_samples": 10000,
  "n_features": 4,
  "train_size": 8000,
  "test_size": 2000,
  "metrics": {
    "train_accuracy": 0.95,
    "test_accuracy": 0.88,
    "precision": 0.87,
    "recall": 0.86,
    "f1_score": 0.865,
    "cv_accuracy_mean": 0.87,
    "cv_accuracy_std": 0.02
  },
  "feature_importance": [
    {"feature": "usage", "importance": 0.45, "importance_pct": 45.0},
    {"feature": "satisfaction", "importance": 0.30, "importance_pct": 30.0}
  ],
  "insights": [
    "Good model performance (>80% accuracy)",
    "Single dominant feature: usage (45.0%)"
  ]
}
```

---

### **Data Management**

#### **GET /api/datasets/**
List all uploaded datasets

**Response:**
```json
{
  "datasets": [
    {
      "id": 1,
      "name": "Customer Data Q1 2024",
      "filename": "customers.csv",
      "num_rows": 10000,
      "num_columns": 25,
      "file_size": 2621440,
      "upload_date": "2024-01-15T10:30:00",
      "status": "active"
    }
  ],
  "count": 10
}
```

---

#### **GET /api/datasets/{dataset_id}/**
Get dataset information

---

#### **GET /api/datasets/{dataset_id}/download/?format=csv**
Download cleaned dataset

**Formats:** csv, excel, json

---

##  **Usage Examples**

### **Example 1: Sales Analysis**

```python
# 1. Upload sales data
response = requests.post(
    'http://localhost:8000/api/upload-enhanced/',
    files={'file': open('sales.csv', 'rb')},
    data={'name': 'Sales Q1 2024', 'auto_clean': True}
)
dataset_id = response.json()['dataset_id']

# 2. Analyze sales by region
response = requests.post(
    'http://localhost:8000/api/analyze/grouped-stats/',
    json={
        'dataset_id': dataset_id,
        'group_by': 'region',
        'value_col': 'revenue',
        'aggregation': 'sum'
    }
)

# 3. Compare products across regions
response = requests.post(
    'http://localhost:8000/api/analyze/crosstab/',
    json={
        'dataset_id': dataset_id,
        'row_col': 'region',
        'col_col': 'product',
        'value_col': 'units_sold',
        'aggfunc': 'sum'
    }
)
```

### **Example 2: Customer Churn Prediction**

```python
# 1. Upload customer data
response = requests.post(
    'http://localhost:8000/api/upload-enhanced/',
    files={'file': open('customers.csv', 'rb')}
)
dataset_id = response.json()['dataset_id']

# 2. Train churn prediction model
response = requests.post(
    'http://localhost:8000/api/ml/train/',
    json={
        'dataset_id': dataset_id,
        'target': 'churned',
        'features': ['age', 'tenure', 'monthly_charges', 'total_charges', 'satisfaction_score'],
        'n_estimators': 100
    }
)

print(f"Model Accuracy: {response.json()['metrics']['test_accuracy']}")
print(f"Top Features: {response.json()['feature_importance'][:3]}")
```

---

##  **Configuration**

### **Environment Variables**

```env
# Backend (.env)
SECRET_KEY=your-secret-key
MAX_FILE_SIZE_MB=500
ALLOWED_EXTENSIONS=csv,xlsx,xls,dta
LOG_LEVEL=INFO
```

---

##  **Best Practices**

1. **Always check data quality score** before analysis
2. **Review insights and warnings** from the upload response
3. **Use auto_clean=true** for automatic data preparation
4. **Cache dataset_id** for subsequent analyses
5. **Monitor feature importance** in ML models
6. **Use cross-validation scores** to assess model reliability

---

##  **Error Handling**

All endpoints return structured error responses:

```json
{
  "error": "Validation failed",
  "code": "VALIDATION_ERROR",
  "status_code": 422,
  "details": {
    "field": ["Error message"]
  }
}
```

**Common Error Codes:**
- `FILE_VALIDATION_ERROR` (400): Invalid file format or size
- `DATA_PROCESSING_ERROR` (400): Data analysis failure
- `ANALYSIS_ERROR` (400): Analysis computation error
- `ML_ERROR` (400): ML training failure
- `DATABASE_ERROR` (500): Database operation failure

---

##  **Interactive Documentation**

Visit http://localhost:8000/api/docs for interactive Swagger UI with:
- Try-it-out functionality
- Request/response examples
- Schema definitions
- Authentication testing

---

**Built with  for universal data analytics**
