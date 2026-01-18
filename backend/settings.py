"""
Production Configuration Module

Environment-based settings with validation, secrets management,
and comprehensive configuration for all platform components.
"""

import os
import secrets
from typing import Optional, List, Any
from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings
from functools import lru_cache
import logging

logger = logging.getLogger(__name__)


class DatabaseSettings(BaseSettings):
    """Database connection settings"""
    
    # PostgreSQL settings (production)
    POSTGRES_HOST: str = Field(default="localhost", description="PostgreSQL host")
    POSTGRES_PORT: int = Field(default=5432, description="PostgreSQL port")
    POSTGRES_USER: str = Field(default="nalytiq", description="PostgreSQL user")
    POSTGRES_PASSWORD: str = Field(default="", description="PostgreSQL password")
    POSTGRES_DB: str = Field(default="nalytiq_db", description="PostgreSQL database name")
    
    # Connection pool settings
    DB_POOL_SIZE: int = Field(default=10, description="Database connection pool size")
    DB_MAX_OVERFLOW: int = Field(default=20, description="Max connections beyond pool size")
    DB_POOL_TIMEOUT: int = Field(default=30, description="Pool timeout in seconds")
    DB_POOL_RECYCLE: int = Field(default=1800, description="Recycle connections after seconds")
    
    # SQLite fallback (development)
    USE_SQLITE: bool = Field(default=True, description="Use SQLite instead of PostgreSQL")
    SQLITE_PATH: str = Field(default="./data/nalytiq.db", description="SQLite database path")
    
    @property
    def database_url(self) -> str:
        """Get database URL based on configuration"""
        if self.USE_SQLITE:
            return f"sqlite:///{self.SQLITE_PATH}"
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
    
    @property
    def sync_database_url(self) -> str:
        """Get synchronous database URL"""
        if self.USE_SQLITE:
            return f"sqlite:///{self.SQLITE_PATH}"
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
    
    class Config:
        env_prefix = ""
        extra = "ignore"


class RedisSettings(BaseSettings):
    """Redis connection settings"""
    
    REDIS_HOST: str = Field(default="localhost", description="Redis host")
    REDIS_PORT: int = Field(default=6379, description="Redis port")
    REDIS_PASSWORD: str = Field(default="", description="Redis password")
    REDIS_DB: int = Field(default=0, description="Redis database number")
    REDIS_SSL: bool = Field(default=False, description="Use SSL for Redis")
    
    # Cache settings
    CACHE_TTL: int = Field(default=3600, description="Default cache TTL in seconds")
    CACHE_PREFIX: str = Field(default="nalytiq:", description="Cache key prefix")
    
    @property
    def redis_url(self) -> str:
        """Get Redis URL"""
        protocol = "rediss" if self.REDIS_SSL else "redis"
        auth = f":{self.REDIS_PASSWORD}@" if self.REDIS_PASSWORD else ""
        return f"{protocol}://{auth}{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
    
    class Config:
        env_prefix = ""
        extra = "ignore"


class SecuritySettings(BaseSettings):
    """Security and authentication settings"""
    
    # JWT settings
    SECRET_KEY: str = Field(
        default_factory=lambda: secrets.token_urlsafe(32),
        description="JWT secret key"
    )
    ALGORITHM: str = Field(default="HS256", description="JWT algorithm")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, description="Access token expiry")
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7, description="Refresh token expiry")
    
    # Password hashing
    PASSWORD_HASH_ROUNDS: int = Field(default=12, description="Bcrypt rounds")
    
    # CORS settings
    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        description="Allowed CORS origins"
    )
    CORS_ALLOW_CREDENTIALS: bool = Field(default=True, description="Allow credentials")
    CORS_ALLOW_METHODS: List[str] = Field(default=["*"], description="Allowed methods")
    CORS_ALLOW_HEADERS: List[str] = Field(default=["*"], description="Allowed headers")
    
    # Rate limiting
    RATE_LIMIT_PER_MINUTE: int = Field(default=100, description="API rate limit per minute")
    RATE_LIMIT_BURST: int = Field(default=20, description="Rate limit burst allowance")
    
    # Session settings
    SESSION_COOKIE_NAME: str = Field(default="nalytiq_session", description="Session cookie name")
    SESSION_COOKIE_SECURE: bool = Field(default=True, description="Secure cookie flag")
    SESSION_COOKIE_HTTPONLY: bool = Field(default=True, description="HttpOnly cookie flag")
    SESSION_COOKIE_SAMESITE: str = Field(default="lax", description="SameSite cookie policy")
    
    @field_validator('SECRET_KEY')
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        if len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters")
        return v
    
    class Config:
        env_prefix = ""
        extra = "ignore"


class CelerySettings(BaseSettings):
    """Celery task queue settings"""
    
    CELERY_BROKER_URL: str = Field(
        default="redis://localhost:6379/1",
        description="Celery broker URL"
    )
    CELERY_RESULT_BACKEND: str = Field(
        default="redis://localhost:6379/2",
        description="Celery result backend"
    )
    CELERY_TASK_SERIALIZER: str = Field(default="json", description="Task serializer")
    CELERY_RESULT_SERIALIZER: str = Field(default="json", description="Result serializer")
    CELERY_ACCEPT_CONTENT: List[str] = Field(default=["json"], description="Accepted content types")
    CELERY_TIMEZONE: str = Field(default="Africa/Kigali", description="Celery timezone")
    CELERY_TASK_TRACK_STARTED: bool = Field(default=True, description="Track task start")
    CELERY_TASK_TIME_LIMIT: int = Field(default=3600, description="Task time limit in seconds")
    
    class Config:
        env_prefix = ""
        extra = "ignore"


class StorageSettings(BaseSettings):
    """File storage settings"""
    
    # Local storage
    UPLOAD_DIR: str = Field(default="./uploads", description="Upload directory")
    MAX_UPLOAD_SIZE_MB: int = Field(default=100, description="Max upload size in MB")
    ALLOWED_EXTENSIONS: List[str] = Field(
        default=["csv", "xlsx", "xls", "json", "parquet"],
        description="Allowed file extensions"
    )
    
    # S3-compatible storage (production)
    USE_S3: bool = Field(default=False, description="Use S3 for storage")
    S3_ENDPOINT: str = Field(default="", description="S3 endpoint URL")
    S3_ACCESS_KEY: str = Field(default="", description="S3 access key")
    S3_SECRET_KEY: str = Field(default="", description="S3 secret key")
    S3_BUCKET: str = Field(default="nalytiq-data", description="S3 bucket name")
    S3_REGION: str = Field(default="eu-west-1", description="S3 region")
    
    class Config:
        env_prefix = ""
        extra = "ignore"


class MLSettings(BaseSettings):
    """Machine learning settings"""
    
    MODEL_DIR: str = Field(default="./models", description="ML model directory")
    MAX_TRAINING_TIME: int = Field(default=3600, description="Max training time in seconds")
    DEFAULT_CV_FOLDS: int = Field(default=5, description="Default cross-validation folds")
    MAX_FEATURE_IMPORTANCE: int = Field(default=20, description="Max features for importance")
    
    # TensorFlow settings
    TF_CPP_MIN_LOG_LEVEL: str = Field(default="2", description="TensorFlow log level")
    TF_FORCE_GPU_ALLOW_GROWTH: bool = Field(default=True, description="GPU memory growth")
    
    class Config:
        env_prefix = ""
        extra = "ignore"


class MonitoringSettings(BaseSettings):
    """Logging and monitoring settings"""
    
    # Logging
    LOG_LEVEL: str = Field(default="INFO", description="Log level")
    LOG_FORMAT: str = Field(default="json", description="Log format: json or text")
    LOG_FILE: str = Field(default="./logs/app.log", description="Log file path")
    LOG_MAX_BYTES: int = Field(default=10485760, description="Max log file size (10MB)")
    LOG_BACKUP_COUNT: int = Field(default=5, description="Number of log backups")
    
    # Sentry
    SENTRY_DSN: str = Field(default="", description="Sentry DSN for error tracking")
    SENTRY_ENVIRONMENT: str = Field(default="development", description="Sentry environment")
    SENTRY_TRACES_SAMPLE_RATE: float = Field(default=0.1, description="Sentry trace sample rate")
    
    # Metrics
    ENABLE_METRICS: bool = Field(default=True, description="Enable Prometheus metrics")
    METRICS_PORT: int = Field(default=9090, description="Metrics server port")
    
    class Config:
        env_prefix = ""
        extra = "ignore"


class XRoadSettings(BaseSettings):
    """X-Road infrastructure settings"""
    
    XROAD_INSTANCE: str = Field(default="RW", description="X-Road instance identifier")
    XROAD_MEMBER_CLASS: str = Field(default="GOV", description="Default member class")
    XROAD_SECURITY_SERVER_URL: str = Field(default="", description="Security server URL")
    
    # PKI settings
    PKI_KEY_SIZE: int = Field(default=2048, description="RSA key size")
    PKI_CERT_VALIDITY_DAYS: int = Field(default=365, description="Certificate validity")
    PKI_CA_SUBJECT: str = Field(
        default="CN=R-NDIP Root CA,O=NISR,C=RW",
        description="CA certificate subject"
    )
    
    class Config:
        env_prefix = ""
        extra = "ignore"


class Settings(BaseSettings):
    """Main application settings combining all modules"""
    
    # Application
    APP_NAME: str = Field(default="Nalytiq Data Platform", description="Application name")
    APP_VERSION: str = Field(default="1.0.0", description="Application version")
    APP_DESCRIPTION: str = Field(
        default="National Data Intelligence Platform for Rwanda",
        description="Application description"
    )
    
    # Environment
    ENVIRONMENT: str = Field(default="development", description="Environment: development, staging, production")
    DEBUG: bool = Field(default=False, description="Debug mode")
    TESTING: bool = Field(default=False, description="Testing mode")
    
    # Server
    HOST: str = Field(default="0.0.0.0", description="Server host")
    PORT: int = Field(default=8000, description="Server port")
    WORKERS: int = Field(default=4, description="Number of workers")
    RELOAD: bool = Field(default=False, description="Auto-reload on changes")
    
    # Feature flags
    ENABLE_DOCS: bool = Field(default=True, description="Enable API documentation")
    ENABLE_WEBSOCKETS: bool = Field(default=True, description="Enable WebSocket support")
    ENABLE_BACKGROUND_TASKS: bool = Field(default=True, description="Enable background tasks")
    ENABLE_ML_TRAINING: bool = Field(default=True, description="Enable ML training")
    ENABLE_XROAD: bool = Field(default=True, description="Enable X-Road integration")
    
    # Sub-settings
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    redis: RedisSettings = Field(default_factory=RedisSettings)
    security: SecuritySettings = Field(default_factory=SecuritySettings)
    celery: CelerySettings = Field(default_factory=CelerySettings)
    storage: StorageSettings = Field(default_factory=StorageSettings)
    ml: MLSettings = Field(default_factory=MLSettings)
    monitoring: MonitoringSettings = Field(default_factory=MonitoringSettings)
    xroad: XRoadSettings = Field(default_factory=XRoadSettings)
    
    @model_validator(mode='after')
    def set_environment_defaults(self) -> 'Settings':
        """Set defaults based on environment"""
        if self.ENVIRONMENT == "production":
            self.DEBUG = False
            self.RELOAD = False
            self.security.SESSION_COOKIE_SECURE = True
            self.database.USE_SQLITE = False
        elif self.ENVIRONMENT == "development":
            self.DEBUG = True
            self.RELOAD = True
            self.security.SESSION_COOKIE_SECURE = False
        return self
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


# Convenience function
settings = get_settings()
