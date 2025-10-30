"""
Enhanced Database Schema with support for:
- Analysis History & Persistence
- Collaboration Features
- User Management
- Background Jobs
- Data Transformations
"""
import sqlite3
import json
from datetime import datetime
from typing import Optional, List, Dict, Any
from contextlib import contextmanager
import os
import hashlib

DATABASE_FILE = "datasets_enhanced.db"

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

def init_enhanced_database():
    """Initialize all database tables with enhanced schema"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Users table (for collaboration)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                full_name TEXT,
                role TEXT DEFAULT 'user',
                avatar_url TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                is_active BOOLEAN DEFAULT 1,
                preferences TEXT
            )
        """)
        
        # Teams table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS teams (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                created_by INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (created_by) REFERENCES users(id)
            )
        """)
        
        # Team members
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS team_members (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                team_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                role TEXT DEFAULT 'member',
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (team_id) REFERENCES teams(id),
                FOREIGN KEY (user_id) REFERENCES users(id),
                UNIQUE(team_id, user_id)
            )
        """)
        
        # Enhanced datasets table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS datasets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                team_id INTEGER,
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
                metadata TEXT,
                is_public BOOLEAN DEFAULT 0,
                tags TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (team_id) REFERENCES teams(id)
            )
        """)
        
        # Dataset sharing
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS dataset_shares (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                dataset_id INTEGER NOT NULL,
                shared_with_user_id INTEGER,
                shared_with_team_id INTEGER,
                permission TEXT DEFAULT 'view',
                shared_by INTEGER NOT NULL,
                shared_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP,
                FOREIGN KEY (dataset_id) REFERENCES datasets(id),
                FOREIGN KEY (shared_with_user_id) REFERENCES users(id),
                FOREIGN KEY (shared_with_team_id) REFERENCES teams(id),
                FOREIGN KEY (shared_by) REFERENCES users(id)
            )
        """)
        
        # Enhanced analysis results with saved configurations
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS analysis_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                dataset_id INTEGER NOT NULL,
                user_id INTEGER,
                analysis_type TEXT NOT NULL,
                title TEXT,
                description TEXT,
                parameters TEXT,
                results TEXT,
                visualization_data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_saved BOOLEAN DEFAULT 0,
                is_favorite BOOLEAN DEFAULT 0,
                tags TEXT,
                execution_time_ms INTEGER,
                FOREIGN KEY (dataset_id) REFERENCES datasets(id),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        
        # Saved analysis configurations (templates)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS saved_analysis_configs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                analysis_type TEXT NOT NULL,
                parameters TEXT NOT NULL,
                is_public BOOLEAN DEFAULT 0,
                usage_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        
        # Analysis comparisons
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS analysis_comparisons (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                analysis_ids TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        
        # Comments on analyses
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS comments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                analysis_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                parent_comment_id INTEGER,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_edited BOOLEAN DEFAULT 0,
                FOREIGN KEY (analysis_id) REFERENCES analysis_results(id),
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (parent_comment_id) REFERENCES comments(id)
            )
        """)
        
        # Data quality reports
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS quality_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                dataset_id INTEGER NOT NULL,
                missing_values INTEGER,
                duplicate_rows INTEGER,
                outliers_detected INTEGER,
                quality_score REAL,
                quality_grade TEXT,
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
                user_id INTEGER,
                name TEXT,
                model_type TEXT NOT NULL,
                algorithm TEXT NOT NULL,
                target_variable TEXT,
                features TEXT,
                parameters TEXT,
                metrics TEXT,
                model_path TEXT,
                feature_importance TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_deployed BOOLEAN DEFAULT 0,
                version INTEGER DEFAULT 1,
                FOREIGN KEY (dataset_id) REFERENCES datasets(id),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        
        # Data transformations history
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS data_transformations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                dataset_id INTEGER NOT NULL,
                user_id INTEGER,
                transformation_type TEXT NOT NULL,
                parameters TEXT NOT NULL,
                affected_columns TEXT,
                rows_affected INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (dataset_id) REFERENCES datasets(id),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        
        # Background jobs for async processing
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS background_jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                job_type TEXT NOT NULL,
                dataset_id INTEGER,
                parameters TEXT,
                status TEXT DEFAULT 'pending',
                progress INTEGER DEFAULT 0,
                result TEXT,
                error_message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                started_at TIMESTAMP,
                completed_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (dataset_id) REFERENCES datasets(id)
            )
        """)
        
        # Export history
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS export_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                resource_type TEXT NOT NULL,
                resource_id INTEGER NOT NULL,
                export_format TEXT NOT NULL,
                file_path TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        
        # Scheduled reports
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS scheduled_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                analysis_id INTEGER NOT NULL,
                schedule_type TEXT NOT NULL,
                schedule_config TEXT,
                recipients TEXT,
                is_active BOOLEAN DEFAULT 1,
                last_run TIMESTAMP,
                next_run TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (analysis_id) REFERENCES analysis_results(id)
            )
        """)
        
        # Notifications
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                type TEXT NOT NULL,
                title TEXT NOT NULL,
                message TEXT,
                link TEXT,
                is_read BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        
        # Activity log
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS activity_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                action TEXT NOT NULL,
                resource_type TEXT,
                resource_id INTEGER,
                details TEXT,
                ip_address TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        
        # Cache table for performance
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cache (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                expires_at TIMESTAMP NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create indexes for performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_datasets_user ON datasets(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_datasets_team ON datasets(team_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_analysis_dataset ON analysis_results(dataset_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_analysis_user ON analysis_results(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_analysis_created ON analysis_results(created_at DESC)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_comments_analysis ON comments(analysis_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_jobs_status ON background_jobs(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_jobs_user ON background_jobs(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_activity_user ON activity_log(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_cache_expires ON cache(expires_at)")
        
        conn.commit()
        print("✅ Enhanced database schema initialized successfully")

# Repository classes for enhanced tables

class UserRepository:
    """Repository for user management"""
    
    @staticmethod
    def create_user(username: str, email: str, password: str, full_name: str = None, role: str = 'user') -> int:
        """Create a new user"""
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO users (username, email, password_hash, full_name, role)
                VALUES (?, ?, ?, ?, ?)
            """, (username, email, password_hash, full_name, role))
            return cursor.lastrowid
    
    @staticmethod
    def get_user(user_id: int) -> Optional[Dict]:
        """Get user by ID"""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    @staticmethod
    def get_user_by_email(email: str) -> Optional[Dict]:
        """Get user by email"""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
            row = cursor.fetchone()
            return dict(row) if row else None

class AnalysisHistoryRepository:
    """Repository for analysis history and persistence"""
    
    @staticmethod
    def save_analysis(dataset_id: int, user_id: int, analysis_type: str, 
                     title: str, parameters: Dict, results: Dict,
                     visualization_data: Dict = None, is_saved: bool = False,
                     execution_time_ms: int = None) -> int:
        """Save analysis result"""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO analysis_results 
                (dataset_id, user_id, analysis_type, title, parameters, results, 
                 visualization_data, is_saved, execution_time_ms)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                dataset_id, user_id, analysis_type, title,
                json.dumps(parameters), json.dumps(results),
                json.dumps(visualization_data) if visualization_data else None,
                is_saved, execution_time_ms
            ))
            return cursor.lastrowid
    
    @staticmethod
    def get_analysis_history(dataset_id: int = None, user_id: int = None, 
                            limit: int = 50) -> List[Dict]:
        """Get analysis history"""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            query = "SELECT * FROM analysis_results WHERE 1=1"
            params = []
            
            if dataset_id:
                query += " AND dataset_id = ?"
                params.append(dataset_id)
            
            if user_id:
                query += " AND user_id = ?"
                params.append(user_id)
            
            query += " ORDER BY created_at DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    @staticmethod
    def get_analysis(analysis_id: int) -> Optional[Dict]:
        """Get specific analysis"""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM analysis_results WHERE id = ?", (analysis_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    @staticmethod
    def toggle_favorite(analysis_id: int, user_id: int) -> bool:
        """Toggle favorite status"""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE analysis_results 
                SET is_favorite = NOT is_favorite 
                WHERE id = ? AND user_id = ?
            """, (analysis_id, user_id))
            return cursor.rowcount > 0
    
    @staticmethod
    def delete_analysis(analysis_id: int, user_id: int) -> bool:
        """Delete analysis"""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM analysis_results 
                WHERE id = ? AND user_id = ?
            """, (analysis_id, user_id))
            return cursor.rowcount > 0

class SavedConfigRepository:
    """Repository for saved analysis configurations"""
    
    @staticmethod
    def save_config(user_id: int, name: str, analysis_type: str, 
                   parameters: Dict, description: str = None) -> int:
        """Save analysis configuration"""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO saved_analysis_configs 
                (user_id, name, description, analysis_type, parameters)
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, name, description, analysis_type, json.dumps(parameters)))
            return cursor.lastrowid
    
    @staticmethod
    def get_configs(user_id: int, analysis_type: str = None) -> List[Dict]:
        """Get saved configurations"""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            if analysis_type:
                cursor.execute("""
                    SELECT * FROM saved_analysis_configs 
                    WHERE user_id = ? AND analysis_type = ?
                    ORDER BY updated_at DESC
                """, (user_id, analysis_type))
            else:
                cursor.execute("""
                    SELECT * FROM saved_analysis_configs 
                    WHERE user_id = ?
                    ORDER BY updated_at DESC
                """, (user_id,))
            
            return [dict(row) for row in cursor.fetchall()]

class CommentRepository:
    """Repository for comments"""
    
    @staticmethod
    def add_comment(analysis_id: int, user_id: int, content: str, 
                   parent_comment_id: int = None) -> int:
        """Add a comment"""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO comments (analysis_id, user_id, content, parent_comment_id)
                VALUES (?, ?, ?, ?)
            """, (analysis_id, user_id, content, parent_comment_id))
            return cursor.lastrowid
    
    @staticmethod
    def get_comments(analysis_id: int) -> List[Dict]:
        """Get comments for an analysis"""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT c.*, u.username, u.full_name, u.avatar_url
                FROM comments c
                JOIN users u ON c.user_id = u.id
                WHERE c.analysis_id = ?
                ORDER BY c.created_at ASC
            """, (analysis_id,))
            return [dict(row) for row in cursor.fetchall()]

class BackgroundJobRepository:
    """Repository for background jobs"""
    
    @staticmethod
    def create_job(user_id: int, job_type: str, dataset_id: int = None, 
                  parameters: Dict = None) -> int:
        """Create a background job"""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO background_jobs 
                (user_id, job_type, dataset_id, parameters, status)
                VALUES (?, ?, ?, ?, 'pending')
            """, (user_id, job_type, dataset_id, json.dumps(parameters) if parameters else None))
            return cursor.lastrowid
    
    @staticmethod
    def update_job_status(job_id: int, status: str, progress: int = None, 
                         result: Dict = None, error: str = None):
        """Update job status"""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            updates = ["status = ?"]
            params = [status]
            
            if progress is not None:
                updates.append("progress = ?")
                params.append(progress)
            
            if status == 'running' and progress is None:
                updates.append("started_at = CURRENT_TIMESTAMP")
            
            if status in ['completed', 'failed']:
                updates.append("completed_at = CURRENT_TIMESTAMP")
            
            if result:
                updates.append("result = ?")
                params.append(json.dumps(result))
            
            if error:
                updates.append("error_message = ?")
                params.append(error)
            
            params.append(job_id)
            
            cursor.execute(f"""
                UPDATE background_jobs 
                SET {', '.join(updates)}
                WHERE id = ?
            """, params)
    
    @staticmethod
    def get_job(job_id: int) -> Optional[Dict]:
        """Get job by ID"""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM background_jobs WHERE id = ?", (job_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

# Initialize database on module import
if __name__ == "__main__":
    init_enhanced_database()
