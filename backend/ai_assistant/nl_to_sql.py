"""Natural Language to SQL Converter.

Converts user questions in natural language to SQL queries for the
federated data platform. Uses LLM with schema context and examples.

This module follows Google style guidelines and best practices for
production ML systems.

Example usage:
    converter = get_nl_to_sql_converter()
    result = await converter.convert(
        "What is the average population by district?",
        tables=["census_2024"]
    )
    print(result.sql)
"""

from __future__ import annotations

import json
import logging
import os
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from .rag_engine import LLMClient, OpenAIClient, LocalClient, LLMProvider

logger = logging.getLogger(__name__)


class SQLDialect(str, Enum):
    """Supported SQL dialects."""
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    SQLITE = "sqlite"
    BIGQUERY = "bigquery"


@dataclass
class TableSchema:
    """Schema definition for a database table.
    
    Attributes:
        table_name: Name of the table.
        columns: List of column definitions.
        description: Human-readable description.
        sample_values: Example values for better LLM understanding.
    """
    table_name: str
    columns: List[Dict[str, Any]]
    description: str = ""
    sample_values: Optional[Dict[str, List[Any]]] = None
    
    def to_schema_string(self) -> str:
        """Convert to SQL-like schema representation."""
        col_defs = []
        for col in self.columns:
            col_def = f"  {col['name']} {col['type']}"
            if col.get("description"):
                col_def += f"  -- {col['description']}"
            col_defs.append(col_def)
        
        schema_str = f"CREATE TABLE {self.table_name} (\n"
        schema_str += ",\n".join(col_defs)
        schema_str += "\n);"
        
        if self.description:
            schema_str = f"-- {self.description}\n{schema_str}"
        
        return schema_str


@dataclass
class NLToSQLResult:
    """Result of natural language to SQL conversion.
    
    Attributes:
        sql: Generated SQL query.
        natural_language: Original question.
        confidence: Confidence score (0-1).
        explanation: Explanation of the query.
        tables_used: Tables referenced in query.
        is_safe: Whether query is read-only.
        warnings: Any warnings about the query.
    """
    sql: str
    natural_language: str
    confidence: float
    explanation: str
    tables_used: List[str]
    is_safe: bool = True
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "sql": self.sql,
            "natural_language": self.natural_language,
            "confidence": self.confidence,
            "explanation": self.explanation,
            "tables_used": self.tables_used,
            "is_safe": self.is_safe,
            "warnings": self.warnings,
            "metadata": self.metadata,
        }


class SQLValidator:
    """Validates generated SQL for safety and correctness."""
    
    # Keywords that indicate potentially dangerous operations
    DANGEROUS_KEYWORDS = {
        "DROP", "DELETE", "TRUNCATE", "UPDATE", "INSERT",
        "ALTER", "CREATE", "GRANT", "REVOKE", "EXEC", "EXECUTE",
        "--", ";--", "/*", "*/", "xp_", "sp_"
    }
    
    @classmethod
    def validate(cls, sql: str) -> Tuple[bool, List[str]]:
        """Validate SQL query for safety.
        
        Args:
            sql: SQL query to validate.
            
        Returns:
            Tuple of (is_safe, list_of_warnings).
        """
        warnings = []
        sql_upper = sql.upper()
        
        # Check for dangerous keywords
        for keyword in cls.DANGEROUS_KEYWORDS:
            if keyword in sql_upper:
                if keyword in ["DROP", "DELETE", "TRUNCATE", "UPDATE", "INSERT"]:
                    warnings.append(f"Query contains data modification keyword: {keyword}")
                else:
                    warnings.append(f"Query contains potentially dangerous pattern: {keyword}")
        
        # Check for multiple statements (SQL injection risk)
        statements = [s.strip() for s in sql.split(";") if s.strip()]
        if len(statements) > 1:
            warnings.append("Query contains multiple statements")
        
        # Check for basic SQL structure
        if not any(kw in sql_upper for kw in ["SELECT", "WITH"]):
            warnings.append("Query does not appear to be a SELECT statement")
        
        is_safe = not any(
            kw in sql_upper for kw in ["DROP", "DELETE", "TRUNCATE", "UPDATE", "INSERT"]
        )
        
        return is_safe, warnings
    
    @classmethod
    def extract_tables(cls, sql: str) -> List[str]:
        """Extract table names from SQL query."""
        tables = []
        
        # Pattern for FROM and JOIN clauses
        patterns = [
            r'\bFROM\s+([a-zA-Z_][a-zA-Z0-9_]*)',
            r'\bJOIN\s+([a-zA-Z_][a-zA-Z0-9_]*)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, sql, re.IGNORECASE)
            tables.extend(matches)
        
        return list(set(tables))


class SchemaRegistry:
    """Registry of available table schemas.
    
    Maintains metadata about available tables for SQL generation.
    """
    
    def __init__(self):
        self._schemas: Dict[str, TableSchema] = {}
        self._load_default_schemas()
    
    def _load_default_schemas(self) -> None:
        """Load default schemas for the data platform."""
        default_schemas = [
            TableSchema(
                table_name="datasets",
                description="Catalog of all datasets in the platform",
                columns=[
                    {"name": "id", "type": "VARCHAR(50)", "description": "Unique dataset ID"},
                    {"name": "name", "type": "VARCHAR(255)", "description": "Dataset name"},
                    {"name": "description", "type": "TEXT", "description": "Dataset description"},
                    {"name": "provider_org", "type": "VARCHAR(100)", "description": "Provider organization"},
                    {"name": "category", "type": "VARCHAR(50)", "description": "Data category"},
                    {"name": "format", "type": "VARCHAR(20)", "description": "Data format"},
                    {"name": "row_count", "type": "BIGINT", "description": "Number of records"},
                    {"name": "created_at", "type": "TIMESTAMP", "description": "Creation date"},
                    {"name": "updated_at", "type": "TIMESTAMP", "description": "Last update date"},
                    {"name": "access_level", "type": "VARCHAR(20)", "description": "Access restriction level"},
                ],
            ),
            TableSchema(
                table_name="organizations",
                description="Government ministries and agencies",
                columns=[
                    {"name": "org_code", "type": "VARCHAR(50)", "description": "Organization code"},
                    {"name": "name", "type": "VARCHAR(255)", "description": "Organization name"},
                    {"name": "type", "type": "VARCHAR(50)", "description": "Organization type"},
                    {"name": "sector", "type": "VARCHAR(100)", "description": "Government sector"},
                    {"name": "xroad_member_code", "type": "VARCHAR(50)", "description": "X-Road member ID"},
                ],
            ),
            TableSchema(
                table_name="data_requests",
                description="Data access requests from organizations",
                columns=[
                    {"name": "request_id", "type": "VARCHAR(50)", "description": "Request ID"},
                    {"name": "dataset_id", "type": "VARCHAR(50)", "description": "Requested dataset"},
                    {"name": "requester_org", "type": "VARCHAR(100)", "description": "Requesting organization"},
                    {"name": "status", "type": "VARCHAR(20)", "description": "Request status"},
                    {"name": "purpose", "type": "TEXT", "description": "Purpose of request"},
                    {"name": "created_at", "type": "TIMESTAMP", "description": "Request date"},
                    {"name": "approved_at", "type": "TIMESTAMP", "description": "Approval date"},
                ],
            ),
            TableSchema(
                table_name="audit_log",
                description="System audit trail for data access",
                columns=[
                    {"name": "log_id", "type": "BIGINT", "description": "Log entry ID"},
                    {"name": "user_id", "type": "VARCHAR(50)", "description": "User who performed action"},
                    {"name": "action", "type": "VARCHAR(50)", "description": "Action type"},
                    {"name": "resource_type", "type": "VARCHAR(50)", "description": "Type of resource accessed"},
                    {"name": "resource_id", "type": "VARCHAR(50)", "description": "ID of resource accessed"},
                    {"name": "timestamp", "type": "TIMESTAMP", "description": "When action occurred"},
                    {"name": "ip_address", "type": "VARCHAR(50)", "description": "Client IP address"},
                ],
            ),
        ]
        
        for schema in default_schemas:
            self.register(schema)
    
    def register(self, schema: TableSchema) -> None:
        """Register a table schema."""
        self._schemas[schema.table_name] = schema
        logger.debug(f"Registered schema: {schema.table_name}")
    
    def get(self, table_name: str) -> Optional[TableSchema]:
        """Get schema by table name."""
        return self._schemas.get(table_name)
    
    def get_all(self) -> List[TableSchema]:
        """Get all registered schemas."""
        return list(self._schemas.values())
    
    def get_schema_context(
        self,
        tables: Optional[List[str]] = None
    ) -> str:
        """Generate schema context for LLM prompt.
        
        Args:
            tables: Specific tables to include. If None, includes all.
            
        Returns:
            String representation of schemas.
        """
        if tables:
            schemas = [self._schemas[t] for t in tables if t in self._schemas]
        else:
            schemas = list(self._schemas.values())
        
        if not schemas:
            return "No schemas available."
        
        return "\n\n".join(schema.to_schema_string() for schema in schemas)


class NLToSQLConverter:
    """Converts natural language questions to SQL queries.
    
    Uses LLM with schema context and few-shot examples for accurate
    SQL generation. Includes validation and safety checks.
    
    Example:
        converter = NLToSQLConverter()
        result = await converter.convert(
            "Show me all datasets from NISR",
            tables=["datasets"]
        )
    """
    
    SYSTEM_PROMPT = """You are an expert SQL query generator for the Nalytiq Data Platform.
Your task is to convert natural language questions into valid SQL queries.

Guidelines:
1. Generate only SELECT queries - never modify data
2. Use proper SQL syntax for PostgreSQL
3. Include appropriate JOINs when multiple tables are needed
4. Use aliases for clarity in complex queries
5. Add LIMIT clause for potentially large results
6. Handle NULL values appropriately
7. Use aggregate functions (COUNT, SUM, AVG) when asked for statistics

Output format:
Return ONLY the SQL query, nothing else. Do not include explanations or markdown formatting.
"""
    
    FEW_SHOT_EXAMPLES = [
        {
            "question": "How many datasets are there?",
            "sql": "SELECT COUNT(*) AS total_datasets FROM datasets;"
        },
        {
            "question": "What are the most recent datasets?",
            "sql": "SELECT name, description, created_at FROM datasets ORDER BY created_at DESC LIMIT 10;"
        },
        {
            "question": "Show datasets by category",
            "sql": "SELECT category, COUNT(*) AS count FROM datasets GROUP BY category ORDER BY count DESC;"
        },
        {
            "question": "What organizations have made the most data requests?",
            "sql": """SELECT o.name, COUNT(dr.request_id) AS request_count 
FROM organizations o 
JOIN data_requests dr ON o.org_code = dr.requester_org 
GROUP BY o.name 
ORDER BY request_count DESC 
LIMIT 10;"""
        },
    ]
    
    def __init__(
        self,
        llm_client: Optional[LLMClient] = None,
        schema_registry: Optional[SchemaRegistry] = None,
        dialect: SQLDialect = SQLDialect.POSTGRESQL
    ):
        """Initialize the converter.
        
        Args:
            llm_client: LLM client for generation.
            schema_registry: Registry of available schemas.
            dialect: SQL dialect to generate.
        """
        self._llm_client = llm_client or self._create_default_client()
        self._schema_registry = schema_registry or SchemaRegistry()
        self._dialect = dialect
        self._validator = SQLValidator()
    
    def _create_default_client(self) -> LLMClient:
        """Create default LLM client."""
        if os.environ.get("OPENAI_API_KEY"):
            return OpenAIClient(model="gpt-4o-mini")
        logger.warning("No LLM API key found, using local client")
        return LocalClient()
    
    def _build_prompt(
        self,
        question: str,
        tables: Optional[List[str]] = None,
        additional_context: str = ""
    ) -> str:
        """Build the conversion prompt."""
        # Get schema context
        schema_context = self._schema_registry.get_schema_context(tables)
        
        # Build few-shot examples
        examples_text = "\n\n".join([
            f"Question: {ex['question']}\nSQL: {ex['sql']}"
            for ex in self.FEW_SHOT_EXAMPLES
        ])
        
        prompt = f"""Database Schema:
{schema_context}

Example conversions:
{examples_text}

{additional_context}

Now convert this question to SQL:
Question: {question}
SQL:"""
        
        return prompt
    
    async def convert(
        self,
        question: str,
        tables: Optional[List[str]] = None,
        additional_context: str = "",
        validate: bool = True
    ) -> NLToSQLResult:
        """Convert natural language question to SQL.
        
        Args:
            question: Natural language question.
            tables: Specific tables to consider.
            additional_context: Extra context for the model.
            validate: Whether to validate the generated SQL.
            
        Returns:
            NLToSQLResult with query and metadata.
        """
        # Build prompt
        prompt = self._build_prompt(question, tables, additional_context)
        
        # Generate SQL
        try:
            sql = await self._llm_client.generate(
                prompt=prompt,
                system_prompt=self.SYSTEM_PROMPT,
                max_tokens=500,
                temperature=0.0  # Deterministic for SQL
            )
        except Exception as e:
            logger.error(f"SQL generation failed: {e}")
            return NLToSQLResult(
                sql="",
                natural_language=question,
                confidence=0.0,
                explanation=f"Generation failed: {str(e)}",
                tables_used=[],
                is_safe=False,
                warnings=["SQL generation failed"]
            )
        
        # Clean up SQL
        sql = self._clean_sql(sql)
        
        # Validate
        if validate:
            is_safe, warnings = self._validator.validate(sql)
        else:
            is_safe, warnings = True, []
        
        # Extract tables used
        tables_used = self._validator.extract_tables(sql)
        
        # Generate explanation
        explanation = self._generate_explanation(question, sql, tables_used)
        
        # Calculate confidence (heuristic based on validation)
        confidence = 0.9 if is_safe and not warnings else 0.5
        if not sql:
            confidence = 0.0
        
        return NLToSQLResult(
            sql=sql,
            natural_language=question,
            confidence=confidence,
            explanation=explanation,
            tables_used=tables_used,
            is_safe=is_safe,
            warnings=warnings,
            metadata={
                "dialect": self._dialect.value,
                "generated_at": datetime.utcnow().isoformat(),
            }
        )
    
    def _clean_sql(self, sql: str) -> str:
        """Clean up generated SQL."""
        # Remove markdown code blocks
        sql = re.sub(r'```sql\s*', '', sql)
        sql = re.sub(r'```\s*', '', sql)
        
        # Remove leading/trailing whitespace
        sql = sql.strip()
        
        # Ensure single statement ends with semicolon
        if sql and not sql.endswith(';'):
            sql += ';'
        
        return sql
    
    def _generate_explanation(
        self,
        question: str,
        sql: str,
        tables: List[str]
    ) -> str:
        """Generate a simple explanation of the query."""
        if not sql:
            return "Could not generate a valid SQL query."
        
        parts = []
        
        # Check for aggregations
        sql_upper = sql.upper()
        if "COUNT" in sql_upper:
            parts.append("counts records")
        if "SUM" in sql_upper:
            parts.append("calculates totals")
        if "AVG" in sql_upper:
            parts.append("calculates averages")
        if "GROUP BY" in sql_upper:
            parts.append("groups results")
        if "ORDER BY" in sql_upper:
            parts.append("sorts results")
        if "JOIN" in sql_upper:
            parts.append("joins multiple tables")
        if "WHERE" in sql_upper:
            parts.append("filters data")
        
        if tables:
            parts.append(f"from {', '.join(tables)}")
        
        if parts:
            return "This query " + ", ".join(parts) + "."
        return "This query retrieves data from the database."
    
    def register_table(self, schema: TableSchema) -> None:
        """Register a new table schema."""
        self._schema_registry.register(schema)
    
    def get_available_tables(self) -> List[str]:
        """Get list of available table names."""
        return [s.table_name for s in self._schema_registry.get_all()]


# Module-level singleton
_converter: Optional[NLToSQLConverter] = None


def get_nl_to_sql_converter() -> NLToSQLConverter:
    """Get the global NL-to-SQL converter instance."""
    global _converter
    if _converter is None:
        _converter = NLToSQLConverter()
    return _converter
