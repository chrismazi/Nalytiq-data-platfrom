from fastapi import FastAPI, File, UploadFile, Form, Body
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
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

app = FastAPI()

# Allow CORS for local frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/auth")

@app.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    print(f"Received file: {file.filename}")
    # Save uploaded file to a temp location
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[-1]) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name
        print(f"File saved to: {tmp_path}")
    try:
        # Use the DataAnalyzer to read and analyze the file
        analyzer = DataAnalyzer()
        result = analyzer.read_file(tmp_path)
        
        if "error" in result:
            return JSONResponse(status_code=400, content={"error": result["error"]})
        
        # Add descriptive stats
        desc_stats = analyzer.get_descriptive_stats()
        if "error" not in desc_stats:
            result.update(desc_stats)
        
        # Format the response to match the expected frontend format
        summary = {
            "columns": result["columns"],
            "shape": result["shape"],
            "dtypes": result["dtypes"],
            "head": result["sample_data"],
            "describe": result.get("descriptive_stats", {}),
        }
        
        print(f"Summary created: {len(summary['columns'])} columns")
        return JSONResponse(content=summary)
        
    except Exception as e:
        print(f"Error processing file: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})
    finally:
        os.remove(tmp_path)

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
        
        # Create a comprehensive HTML report
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