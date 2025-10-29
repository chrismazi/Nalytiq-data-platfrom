"""
Database models and connection management
"""
import sqlite3
import json
from datetime import datetime
from typing import Optional, List, Dict, Any
from contextlib import contextmanager
import os

DATABASE_FILE = "datasets.db"

@contextmanager
def get_db_connection():
    """Context manager for database connections"""
    conn = sqlite3.connect(DATABASE_FILE)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def init_database():
    """Initialize database tables"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Datasets table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS datasets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                name TEXT NOT NULL,
                description TEXT,
                filename TEXT NOT NULL,
                file_path TEXT NOT NULL,
                file_size INTEGER,
                file_type TEXT,
                num_rows INTEGER,
                num_columns INTEGER,
                columns TEXT,
                dtypes TEXT,
                upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'active',
                metadata TEXT
            )
        """)
        
        # Analysis results table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS analysis_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                dataset_id INTEGER NOT NULL,
                analysis_type TEXT NOT NULL,
                parameters TEXT,
                results TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (dataset_id) REFERENCES datasets(id)
            )
        """)
        
        # Data quality reports table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS quality_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                dataset_id INTEGER NOT NULL,
                missing_values INTEGER,
                duplicate_rows INTEGER,
                outliers_detected INTEGER,
                warnings TEXT,
                insights TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (dataset_id) REFERENCES datasets(id)
            )
        """)
        
        # ML models table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ml_models (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                dataset_id INTEGER NOT NULL,
                model_type TEXT NOT NULL,
                target_variable TEXT,
                features TEXT,
                parameters TEXT,
                metrics TEXT,
                model_path TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (dataset_id) REFERENCES datasets(id)
            )
        """)
        
        conn.commit()

class DatasetRepository:
    """Repository for dataset operations"""
    
    @staticmethod
    def create_dataset(
        name: str,
        filename: str,
        file_path: str,
        file_size: int,
        file_type: str,
        num_rows: int,
        num_columns: int,
        columns: List[str],
        dtypes: Dict[str, str],
        user_id: Optional[int] = None,
        description: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> int:
        """Create a new dataset record"""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO datasets (
                    user_id, name, description, filename, file_path,
                    file_size, file_type, num_rows, num_columns,
                    columns, dtypes, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                user_id, name, description, filename, file_path,
                file_size, file_type, num_rows, num_columns,
                json.dumps(columns), json.dumps(dtypes),
                json.dumps(metadata) if metadata else None
            ))
            return cursor.lastrowid
    
    @staticmethod
    def get_dataset(dataset_id: int) -> Optional[Dict]:
        """Get dataset by ID"""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM datasets WHERE id = ? AND status = 'active'
            """, (dataset_id,))
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
    
    @staticmethod
    def get_all_datasets(user_id: Optional[int] = None, limit: int = 100) -> List[Dict]:
        """Get all datasets for a user"""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            if user_id:
                cursor.execute("""
                    SELECT * FROM datasets 
                    WHERE user_id = ? AND status = 'active'
                    ORDER BY upload_date DESC
                    LIMIT ?
                """, (user_id, limit))
            else:
                cursor.execute("""
                    SELECT * FROM datasets 
                    WHERE status = 'active'
                    ORDER BY upload_date DESC
                    LIMIT ?
                """, (limit,))
            return [dict(row) for row in cursor.fetchall()]
    
    @staticmethod
    def update_last_accessed(dataset_id: int):
        """Update last accessed timestamp"""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE datasets 
                SET last_accessed = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (dataset_id,))
    
    @staticmethod
    def delete_dataset(dataset_id: int):
        """Soft delete a dataset"""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE datasets 
                SET status = 'deleted'
                WHERE id = ?
            """, (dataset_id,))

class AnalysisRepository:
    """Repository for analysis results"""
    
    @staticmethod
    def save_analysis(
        dataset_id: int,
        analysis_type: str,
        results: Dict,
        parameters: Optional[Dict] = None
    ) -> int:
        """Save analysis results"""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO analysis_results (
                    dataset_id, analysis_type, parameters, results
                ) VALUES (?, ?, ?, ?)
            """, (
                dataset_id, analysis_type,
                json.dumps(parameters) if parameters else None,
                json.dumps(results)
            ))
            return cursor.lastrowid
    
    @staticmethod
    def get_analysis(dataset_id: int, analysis_type: Optional[str] = None) -> List[Dict]:
        """Get analysis results for a dataset"""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            if analysis_type:
                cursor.execute("""
                    SELECT * FROM analysis_results 
                    WHERE dataset_id = ? AND analysis_type = ?
                    ORDER BY created_at DESC
                """, (dataset_id, analysis_type))
            else:
                cursor.execute("""
                    SELECT * FROM analysis_results 
                    WHERE dataset_id = ?
                    ORDER BY created_at DESC
                """, (dataset_id,))
            return [dict(row) for row in cursor.fetchall()]

class QualityReportRepository:
    """Repository for data quality reports"""
    
    @staticmethod
    def save_report(
        dataset_id: int,
        missing_values: int,
        duplicate_rows: int,
        outliers_detected: int,
        warnings: List[str],
        insights: List[str]
    ) -> int:
        """Save quality report"""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO quality_reports (
                    dataset_id, missing_values, duplicate_rows,
                    outliers_detected, warnings, insights
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                dataset_id, missing_values, duplicate_rows,
                outliers_detected,
                json.dumps(warnings),
                json.dumps(insights)
            ))
            return cursor.lastrowid
    
    @staticmethod
    def get_latest_report(dataset_id: int) -> Optional[Dict]:
        """Get latest quality report for a dataset"""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM quality_reports 
                WHERE dataset_id = ?
                ORDER BY created_at DESC
                LIMIT 1
            """, (dataset_id,))
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None

# Initialize database on import
init_database()
