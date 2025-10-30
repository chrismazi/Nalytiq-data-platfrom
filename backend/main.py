from fastapi import FastAPI, File, UploadFile, Form, Body, HTTPException, status
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
import pandas as pd
import tempfile
import os
from auth import router as auth_router
from data_analysis import DataAnalyzer
import re
from eda import automated_eda
from crosstab import compute_crosstab
from modeling import run_model
from chatbot import ask_chatbot
from typing import List, Optional

# Import new utilities
from config import settings
from logger import get_logger
from exceptions import (
    validation_exception_handler,
    http_exception_handler,
    general_exception_handler,
    DataProcessingError,
    FileValidationError,
    create_error_response
)
from validators import FileValidator, DataValidator

# Initialize logger
logger = get_logger(__name__)

# Initialize databases
from database_enhanced import init_enhanced_database
from database import init_database

# Initialize FastAPI app
app = FastAPI(
    title="Nalytiq Data Platform API",
    description="AI-powered data analytics platform for NISR Rwanda",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Initialize databases on startup
@app.on_event("startup")
async def startup_event():
    """Initialize databases on application startup"""
    logger.info("Initializing databases...")
    init_database()  # Original database
    init_enhanced_database()  # Enhanced database with users table
    logger.info("Databases initialized successfully")

# Exception handlers
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router, prefix="/auth", tags=["Authentication"])

# Include enhanced endpoints
from enhanced_endpoints import router as enhanced_router
app.include_router(enhanced_router, prefix="/api", tags=["Enhanced Analytics"])

# Include analysis history endpoints
from analysis_history_endpoints import router as history_router
app.include_router(history_router, tags=["Analysis History"])

# Include advanced ML endpoints
from ml_endpoints import router as ml_router
app.include_router(ml_router, tags=["Advanced ML"])

# Include visualization endpoints
from visualization_endpoints import router as viz_router
app.include_router(viz_router, tags=["Visualizations"])

# Include export and transformation endpoints
from export_transform_endpoints import router as export_transform_router
app.include_router(export_transform_router, tags=["Export & Transformation"])

@app.get("/", tags=["Health"])
async def root():
    """API health check endpoint"""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "service": "Nalytiq Data Platform API"
    }

@app.get("/health", tags=["Health"])
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "database": "connected",
        "timestamp": pd.Timestamp.now().isoformat()
    }

@app.post("/upload/", tags=["Data Processing"])
async def upload_file(file: UploadFile = File(...)):
    """
    Upload and analyze a dataset
    
    Supports CSV, Excel (.xlsx, .xls), and Stata (.dta) files
    """
    logger.info(f"Upload request received for file: {file.filename}")
    tmp_path = None
    
    try:
        # Validate file
        await FileValidator.validate_upload(file)
        file_info = FileValidator.get_file_info(file)
        logger.info(f"File validation passed: {file_info}")
        
        # Save uploaded file to temp location
        with tempfile.NamedTemporaryFile(
            delete=False, 
            suffix=os.path.splitext(file.filename or "data.csv")[-1]
        ) as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name
            logger.debug(f"File saved to: {tmp_path}")
        
        # Analyze file
        analyzer = DataAnalyzer()
        result = analyzer.read_file(tmp_path)
        
        if "error" in result:
            logger.error(f"Analysis error: {result['error']}")
            raise DataProcessingError(result["error"])
        
        # Add descriptive stats
        desc_stats = analyzer.get_descriptive_stats()
        if "error" not in desc_stats:
            result.update(desc_stats)
        
        # Format response
        summary = {
            "columns": result["columns"],
            "shape": result["shape"],
            "dtypes": result["dtypes"],
            "head": result["sample_data"],
            "describe": result.get("descriptive_stats", {}),
            "insights": result.get("insights", {}),
            "file_info": file_info,
        }
        
        logger.info(f"Upload successful: {len(summary['columns'])} columns, {summary['shape'][0]} rows")
        return JSONResponse(content=summary)
        
    except FileValidationError as e:
        logger.warning(f"File validation failed: {str(e)}")
        return create_error_response(str(e), "FILE_VALIDATION_ERROR", status.HTTP_400_BAD_REQUEST)
    
    except DataProcessingError as e:
        logger.error(f"Data processing failed: {str(e)}")
        return create_error_response(str(e), "DATA_PROCESSING_ERROR", status.HTTP_400_BAD_REQUEST)
    
    except Exception as e:
        logger.exception(f"Unexpected error processing file: {str(e)}")
        return create_error_response(
            "Failed to process file. Please check the file format and try again.",
            "PROCESSING_ERROR",
            status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
    finally:
        # Clean up temp file
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
                logger.debug(f"Temp file removed: {tmp_path}")
            except Exception as e:
                logger.warning(f"Failed to remove temp file: {str(e)}")

@app.post("/profile/")
async def profile_file(file: UploadFile = File(...)):
    print(f"Profiling file: {file.filename}")
    # Save uploaded file to a temp location
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[-1]) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name
    try:
        # Use the DataAnalyzer to read and analyze the file
        analyzer = DataAnalyzer()
        result = analyzer.read_file(tmp_path)
        
        if "error" in result:
            return JSONResponse(status_code=400, content={"error": result["error"]})
        
        # Add descriptive stats and correlation matrix
        desc_stats = analyzer.get_descriptive_stats()
        if "error" not in desc_stats:
            result.update(desc_stats)
        
        corr_matrix = analyzer.get_correlation_matrix()
        if "error" not in corr_matrix:
            result.update(corr_matrix)
        
        # Add insights
        insights = result.get("insights", {})
        # Create a comprehensive HTML report (add insights section)
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Data Profile Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .section {{ margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }}
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
                .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 10px; }}
                .stat-card {{ background: #f9f9f9; padding: 10px; border-radius: 5px; }}
                .error {{ color: red; }}
            </style>
        </head>
        <body>
            <h1>Data Profile Report</h1>
            <div class="section">
                <h2>Automated Insights & Warnings</h2>
                <ul>"""
        for w in insights.get("warnings", []):
            html_content += f'<li style="color:red">⚠️ {w}</li>'
        for i in insights.get("insights", []):
            html_content += f'<li style="color:green">💡 {i}</li>'
        html_content += """</ul>
            </div>
            <div class="section">
                <h2>Dataset Overview</h2>
                <div class="stats">
                    <div class="stat-card">
                        <strong>Rows:</strong> {result['shape'][0]:,}
                    </div>
                    <div class="stat-card">
                        <strong>Columns:</strong> {result['shape'][1]:,}
                    </div>
                    <div class="stat-card">
                        <strong>Memory Usage:</strong> {result['memory_usage_mb']} MB
                    </div>
                    <div class="stat-card">
                        <strong>Missing Values:</strong> {result['missing_values']:,}
                    </div>
                    <div class="stat-card">
                        <strong>Duplicate Rows:</strong> {result['duplicate_rows']:,}
                    </div>
                </div>
            </div>
            
            <div class="section">
                <h2>Column Information</h2>
                <table>
                    <tr>
                        <th>Column</th>
                        <th>Type</th>
                        <th>Non-Null Count</th>
                        <th>Missing Values</th>
                        <th>Unique Values</th>
                    </tr>
        """
        
        for col, stats in result['column_stats'].items():
            html_content += f"""
                    <tr>
                        <td>{col}</td>
                        <td>{stats['dtype']}</td>
                        <td>{stats['non_null_count']:,}</td>
                        <td>{stats['missing_count']:,}</td>
                        <td>{stats['unique_count']:,}</td>
                    </tr>
            """
        
        html_content += """
                </table>
            </div>
            
            <div class="section">
                <h2>Sample Data (First 10 rows)</h2>
                <table>
        """
        
        # Add header row
        html_content += "<tr>"
        for col in result['columns']:
            html_content += f"<th>{col}</th>"
        html_content += "</tr>"
        
        # Add data rows
        for row in result['sample_data']:
            html_content += "<tr>"
            for col in result['columns']:
                value = row.get(col, "")
                if value is None:
                    value = ""
                html_content += f"<td>{value}</td>"
            html_content += "</tr>"
        
        html_content += """
                </table>
            </div>
        """
        
        # Add correlation matrix if available
        if 'correlation_matrix' in result:
            html_content += """
            <div class="section">
                <h2>Correlation Matrix (Numeric Columns)</h2>
                <table>
            """
            
            # Add header row
            html_content += "<tr><th></th>"
            for col in result['correlation_matrix'].keys():
                html_content += f"<th>{col}</th>"
            html_content += "</tr>"
            
            # Add data rows
            for col1 in result['correlation_matrix'].keys():
                html_content += f"<tr><th>{col1}</th>"
                for col2 in result['correlation_matrix'].keys():
                    value = result['correlation_matrix'][col1][col2]
                    if value is None:
                        value = ""
                    else:
                        value = f"{value:.3f}"
                    html_content += f"<td>{value}</td>"
                html_content += "</tr>"
            
            html_content += """
                </table>
            </div>
            """
        
        html_content += """
        </body>
        </html>
        """
        
        print(f"Profile created, HTML length: {len(html_content)}")
        return HTMLResponse(content=html_content)
        
    except Exception as e:
        print(f"Error creating profile: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})
    finally:
        os.remove(tmp_path) 

@app.post("/clean/")
async def clean_file(file: UploadFile = File(...)):
    print(f"Cleaning file: {file.filename}")
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[-1]) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name
    try:
        analyzer = DataAnalyzer()
        result = analyzer.read_file(tmp_path)
        if "error" in result:
            return JSONResponse(status_code=400, content={"error": result["error"]})
        df = analyzer.df
        # --- Cleaning steps ---
        # 1. Standardize column names
        df.columns = [re.sub(r'[^a-zA-Z0-9_]', '_', c).lower() for c in df.columns]
        # 2. Remove duplicate rows
        df = df.drop_duplicates()
        # 3. Fill missing values (simple strategy: fill with 'Unknown' for object, 0 for numeric)
        for col in df.columns:
            if pd.api.types.is_categorical_dtype(df[col]):
                if "Unknown" not in df[col].cat.categories:
                    df[col] = df[col].cat.add_categories(["Unknown"])
                df[col] = df[col].fillna("Unknown")
            elif df[col].dtype == object:
                df[col] = df[col].fillna("Unknown")
            else:
                df[col] = df[col].fillna(0)
        # 4. Update analyzer with cleaned df
        analyzer.df = df
        # Suggest frequency table columns (categorical columns with < 30 unique values)
        freq_candidates = [col for col in df.columns if (df[col].dtype == object or df[col].nunique() < 30)]
        # Build cleaned_result in the expected structure
        cleaned_result = {
            "columns": list(df.columns),
            "head": df.head(10).to_dict(orient="records"),
            "dtypes": df.dtypes.astype(str).to_dict(),
            "shape": list(df.shape),
            "frequency_candidates": freq_candidates,
        }
        print(f"Cleaned data: {len(df)} rows, {len(df.columns)} columns")
        return JSONResponse(content=cleaned_result)
    except Exception as e:
        print(f"Error cleaning file: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})
    finally:
        os.remove(tmp_path) 

@app.post("/eda/")
async def eda_file(file: UploadFile = File(...)):
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[-1]) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name
    try:
        analyzer = DataAnalyzer()
        analyzer.read_file(tmp_path)
        df = analyzer.df
        if df is None:
            return JSONResponse(status_code=400, content={"error": "Could not load file"})
        result = automated_eda(df)
        return JSONResponse(content=result)
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
    finally:
        os.remove(tmp_path)

@app.post("/crosstab/")
async def crosstab_file(file: UploadFile = File(...), columns: str = Form(...)):
    # columns is a JSON string list
    import json
    columns_list = json.loads(columns)
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[-1]) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name
    try:
        analyzer = DataAnalyzer()
        analyzer.read_file(tmp_path)
        df = analyzer.df
        if df is None:
            return JSONResponse(status_code=400, content={"error": "Could not load file"})
        result = compute_crosstab(df, columns_list)
        return JSONResponse(content=result)
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
    finally:
        os.remove(tmp_path)

@app.post("/model/")
async def model_file(file: UploadFile = File(...), target: str = Form(...), features: str = Form(...)):
    import json
    features_list = json.loads(features)
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[-1]) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name
    try:
        analyzer = DataAnalyzer()
        analyzer.read_file(tmp_path)
        df = analyzer.df
        if df is None:
            return JSONResponse(status_code=400, content={"error": "Could not load file"})
        result = run_model(df, target, features_list)
        return JSONResponse(content=result)
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
    finally:
        os.remove(tmp_path)

@app.post("/chatbot/")
async def chatbot_ask(question: str = Form(...), context: Optional[str] = Form(None)):
    import json
    ctx = json.loads(context) if context else {}
    result = ask_chatbot(question, ctx)
    return JSONResponse(content=result)

@app.post("/eda/json/")
async def eda_json(data: dict = Body(...)):
    try:
        df = pd.DataFrame(data["head"], columns=data["columns"])
        # Optionally, set dtypes from data["dtypes"]
        result = automated_eda(df)
        return JSONResponse(content=result)
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)}) 

@app.post("/grouped-stats/")
async def grouped_stats(file: UploadFile = File(...), group_by: str = Form(...), value: str = Form(...), agg: str = Form('mean')):
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[-1]) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name
    try:
        analyzer = DataAnalyzer()
        analyzer.read_file(tmp_path)
        result = analyzer.get_grouped_stats(group_by, value, agg)
        return JSONResponse(content=result)
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
    finally:
        os.remove(tmp_path)

@app.post("/top-districts/")
async def top_districts(file: UploadFile = File(...), top_n: int = Form(5)):
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[-1]) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name
    try:
        analyzer = DataAnalyzer()
        analyzer.read_file(tmp_path)
        result = analyzer.get_top_districts_by_consumption(top_n)
        return JSONResponse(content=result)
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
    finally:
        os.remove(tmp_path)

@app.post("/poverty-by-education/")
async def poverty_by_education(file: UploadFile = File(...)):
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[-1]) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name
    try:
        analyzer = DataAnalyzer()
        analyzer.read_file(tmp_path)
        result = analyzer.get_poverty_by_education()
        return JSONResponse(content=result)
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
    finally:
        os.remove(tmp_path)

@app.post("/urban-rural-consumption/")
async def urban_rural_consumption(file: UploadFile = File(...)):
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[-1]) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name
    try:
        analyzer = DataAnalyzer()
        analyzer.read_file(tmp_path)
        result = analyzer.get_urban_rural_consumption()
        return JSONResponse(content=result)
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
    finally:
        os.remove(tmp_path)

@app.post("/poverty-by-gender/")
async def poverty_by_gender(file: UploadFile = File(...)):
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[-1]) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name
    try:
        analyzer = DataAnalyzer()
        analyzer.read_file(tmp_path)
        result = analyzer.get_poverty_by_gender()
        return JSONResponse(content=result)
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
    finally:
        os.remove(tmp_path)

@app.post("/poverty-by-province/")
async def poverty_by_province(file: UploadFile = File(...)):
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[-1]) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name
    try:
        analyzer = DataAnalyzer()
        analyzer.read_file(tmp_path)
        result = analyzer.get_poverty_by_province()
        return JSONResponse(content=result)
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
    finally:
        os.remove(tmp_path)

@app.post("/avg-consumption-by-province/")
async def avg_consumption_by_province(file: UploadFile = File(...)):
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[-1]) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name
    try:
        analyzer = DataAnalyzer()
        analyzer.read_file(tmp_path)
        result = analyzer.get_avg_consumption_by_province()
        return JSONResponse(content=result)
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
    finally:
        os.remove(tmp_path) 