"""
Custom Report Builder

Generate custom reports with:
- SQL-like query interface
- Multiple output formats (PDF, Excel, CSV)
- Scheduled report generation
- Template-based reports
- Visualization embedding
"""

import logging
import uuid
import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict
from enum import Enum
from io import BytesIO
import base64

logger = logging.getLogger(__name__)


class ReportFormat(str, Enum):
    PDF = "pdf"
    EXCEL = "xlsx"
    CSV = "csv"
    JSON = "json"
    HTML = "html"


class ReportStatus(str, Enum):
    DRAFT = "draft"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"
    SCHEDULED = "scheduled"


class ChartType(str, Enum):
    BAR = "bar"
    LINE = "line"
    PIE = "pie"
    SCATTER = "scatter"
    AREA = "area"
    HEATMAP = "heatmap"
    TABLE = "table"


@dataclass
class ReportSection:
    """Report section definition"""
    section_id: str
    title: str
    section_type: str  # text, chart, table, query
    content: Dict[str, Any]
    order: int
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ReportDefinition:
    """Report template definition"""
    report_id: str
    name: str
    description: str
    sections: List[ReportSection]
    parameters: Dict[str, Any]
    created_by: Optional[str]
    created_at: str
    updated_at: str
    tags: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['sections'] = [s.to_dict() for s in self.sections]
        return data


@dataclass
class GeneratedReport:
    """Generated report instance"""
    instance_id: str
    report_id: str
    report_name: str
    format: ReportFormat
    status: ReportStatus
    parameters_used: Dict[str, Any]
    generated_at: str
    generated_by: Optional[str]
    file_path: Optional[str]
    file_size_bytes: int
    error_message: Optional[str]
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['format'] = self.format.value
        data['status'] = self.status.value
        return data


class QueryEngine:
    """Execute data queries for reports"""
    
    def __init__(self):
        self.cache: Dict[str, Any] = {}
    
    def execute(
        self,
        query: Dict[str, Any],
        parameters: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Execute a query definition.
        
        Query format:
        {
            "source": "dataset_id or table_name",
            "select": ["column1", "column2"],
            "where": [{"column": "col", "operator": "=", "value": "x"}],
            "group_by": ["column"],
            "order_by": [{"column": "col", "direction": "asc"}],
            "limit": 100
        }
        """
        # This is a mock implementation - in production, connect to actual data
        source = query.get('source', '')
        columns = query.get('select', ['*'])
        filters = query.get('where', [])
        group_by = query.get('group_by', [])
        limit = query.get('limit', 1000)
        
        # Generate mock data based on query
        import random
        
        num_rows = min(limit, random.randint(10, 100))
        
        # Create column data
        result_columns = columns if columns != ['*'] else ['id', 'name', 'value', 'date']
        
        rows = []
        for i in range(num_rows):
            row = {}
            for col in result_columns:
                if 'id' in col.lower():
                    row[col] = i + 1
                elif 'name' in col.lower():
                    row[col] = f"Item {i + 1}"
                elif 'value' in col.lower() or 'amount' in col.lower():
                    row[col] = round(random.uniform(100, 10000), 2)
                elif 'date' in col.lower():
                    row[col] = (datetime.now() - timedelta(days=random.randint(0, 365))).isoformat()
                elif 'count' in col.lower():
                    row[col] = random.randint(1, 1000)
                else:
                    row[col] = f"{col}_{i}"
            rows.append(row)
        
        return {
            'columns': result_columns,
            'rows': rows,
            'row_count': len(rows),
            'query_time_ms': random.randint(10, 500)
        }
    
    def aggregate(
        self,
        data: List[Dict],
        group_by: str,
        aggregations: List[Dict[str, str]]
    ) -> List[Dict]:
        """
        Aggregate data.
        
        aggregations format: [{"column": "value", "function": "sum"}]
        """
        from collections import defaultdict
        
        groups = defaultdict(list)
        for row in data:
            key = row.get(group_by, 'unknown')
            groups[key].append(row)
        
        results = []
        for key, rows in groups.items():
            result = {group_by: key}
            for agg in aggregations:
                col = agg['column']
                func = agg['function']
                values = [r.get(col, 0) for r in rows if r.get(col) is not None]
                
                if func == 'sum':
                    result[f"{col}_{func}"] = sum(values)
                elif func == 'avg':
                    result[f"{col}_{func}"] = sum(values) / len(values) if values else 0
                elif func == 'count':
                    result[f"{col}_{func}"] = len(values)
                elif func == 'min':
                    result[f"{col}_{func}"] = min(values) if values else 0
                elif func == 'max':
                    result[f"{col}_{func}"] = max(values) if values else 0
            
            results.append(result)
        
        return results


class ChartGenerator:
    """Generate charts for reports"""
    
    @staticmethod
    def generate_chart(
        chart_type: ChartType,
        data: List[Dict],
        x_column: str,
        y_column: str,
        title: str = "",
        **options
    ) -> str:
        """
        Generate a chart and return as base64 encoded image.
        """
        try:
            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt
            
            x_values = [row.get(x_column, '') for row in data]
            y_values = [row.get(y_column, 0) for row in data]
            
            fig, ax = plt.subplots(figsize=(10, 6))
            
            if chart_type == ChartType.BAR:
                ax.bar(x_values, y_values, color='steelblue')
            elif chart_type == ChartType.LINE:
                ax.plot(x_values, y_values, marker='o', color='steelblue')
            elif chart_type == ChartType.PIE:
                ax.pie(y_values, labels=x_values, autopct='%1.1f%%')
            elif chart_type == ChartType.SCATTER:
                ax.scatter(x_values, y_values, color='steelblue')
            elif chart_type == ChartType.AREA:
                ax.fill_between(range(len(x_values)), y_values, alpha=0.5)
                ax.set_xticks(range(len(x_values)))
                ax.set_xticklabels(x_values)
            
            ax.set_title(title)
            if chart_type != ChartType.PIE:
                ax.set_xlabel(x_column)
                ax.set_ylabel(y_column)
                plt.xticks(rotation=45, ha='right')
            
            plt.tight_layout()
            
            # Convert to base64
            buffer = BytesIO()
            plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.read()).decode('utf-8')
            plt.close(fig)
            
            return f"data:image/png;base64,{image_base64}"
            
        except Exception as e:
            logger.error(f"Failed to generate chart: {e}")
            return ""


class ReportGenerator:
    """Generate reports in various formats"""
    
    def __init__(self, output_dir: str = "./reports"):
        self.output_dir = output_dir
        self.query_engine = QueryEngine()
        self.chart_generator = ChartGenerator()
        os.makedirs(output_dir, exist_ok=True)
    
    def generate(
        self,
        report: ReportDefinition,
        output_format: ReportFormat,
        parameters: Dict[str, Any] = None,
        user_id: Optional[str] = None
    ) -> GeneratedReport:
        """Generate a report in the specified format"""
        instance_id = str(uuid.uuid4())
        
        generated = GeneratedReport(
            instance_id=instance_id,
            report_id=report.report_id,
            report_name=report.name,
            format=output_format,
            status=ReportStatus.GENERATING,
            parameters_used=parameters or {},
            generated_at=datetime.utcnow().isoformat(),
            generated_by=user_id,
            file_path=None,
            file_size_bytes=0,
            error_message=None
        )
        
        try:
            # Process sections
            processed_sections = []
            for section in report.sections:
                processed = self._process_section(section, parameters or {})
                processed_sections.append(processed)
            
            # Generate output file
            if output_format == ReportFormat.PDF:
                file_path = self._generate_pdf(report, processed_sections, instance_id)
            elif output_format == ReportFormat.EXCEL:
                file_path = self._generate_excel(report, processed_sections, instance_id)
            elif output_format == ReportFormat.CSV:
                file_path = self._generate_csv(report, processed_sections, instance_id)
            elif output_format == ReportFormat.HTML:
                file_path = self._generate_html(report, processed_sections, instance_id)
            else:
                file_path = self._generate_json(report, processed_sections, instance_id)
            
            generated.file_path = file_path
            generated.file_size_bytes = os.path.getsize(file_path) if os.path.exists(file_path) else 0
            generated.status = ReportStatus.COMPLETED
            
        except Exception as e:
            logger.error(f"Failed to generate report: {e}")
            generated.status = ReportStatus.FAILED
            generated.error_message = str(e)
        
        return generated
    
    def _process_section(
        self,
        section: ReportSection,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process a report section"""
        result = {
            'section_id': section.section_id,
            'title': section.title,
            'type': section.section_type,
            'order': section.order
        }
        
        if section.section_type == 'text':
            # Replace parameter placeholders in text
            text = section.content.get('text', '')
            for key, value in parameters.items():
                text = text.replace(f'{{{key}}}', str(value))
            result['content'] = text
            
        elif section.section_type == 'query':
            # Execute query and return data
            query = section.content.get('query', {})
            data = self.query_engine.execute(query, parameters)
            result['data'] = data
            
        elif section.section_type == 'chart':
            # Execute query and generate chart
            query = section.content.get('query', {})
            data = self.query_engine.execute(query, parameters)
            
            chart_image = ChartGenerator.generate_chart(
                chart_type=ChartType(section.content.get('chart_type', 'bar')),
                data=data['rows'],
                x_column=section.content.get('x_column', ''),
                y_column=section.content.get('y_column', ''),
                title=section.title
            )
            result['chart_image'] = chart_image
            result['data'] = data
            
        elif section.section_type == 'table':
            # Execute query for table
            query = section.content.get('query', {})
            data = self.query_engine.execute(query, parameters)
            result['data'] = data
        
        return result
    
    def _generate_pdf(
        self,
        report: ReportDefinition,
        sections: List[Dict],
        instance_id: str
    ) -> str:
        """Generate PDF report"""
        try:
            from reportlab.lib.pagesizes import letter, A4
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib import colors
            from reportlab.lib.units import inch
            
            file_path = os.path.join(self.output_dir, f"{instance_id}.pdf")
            doc = SimpleDocTemplate(file_path, pagesize=A4)
            story = []
            styles = getSampleStyleSheet()
            
            # Title
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                spaceAfter=30
            )
            story.append(Paragraph(report.name, title_style))
            story.append(Paragraph(report.description, styles['Normal']))
            story.append(Spacer(1, 20))
            
            # Metadata
            story.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
            story.append(Spacer(1, 30))
            
            # Sections
            for section in sorted(sections, key=lambda x: x['order']):
                story.append(Paragraph(section['title'], styles['Heading2']))
                story.append(Spacer(1, 10))
                
                if section['type'] == 'text':
                    story.append(Paragraph(section.get('content', ''), styles['Normal']))
                    
                elif section['type'] in ['query', 'table']:
                    data = section.get('data', {})
                    if data.get('rows'):
                        # Create table
                        columns = data.get('columns', [])
                        rows = data.get('rows', [])
                        
                        table_data = [columns] + [[str(row.get(c, '')) for c in columns] for row in rows[:50]]
                        
                        t = Table(table_data)
                        t.setStyle(TableStyle([
                            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                            ('FONTSIZE', (0, 0), (-1, 0), 10),
                            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                            ('GRID', (0, 0), (-1, -1), 1, colors.black)
                        ]))
                        story.append(t)
                        
                elif section['type'] == 'chart':
                    chart_image = section.get('chart_image', '')
                    if chart_image and chart_image.startswith('data:image'):
                        # Decode base64 image
                        import base64
                        image_data = base64.b64decode(chart_image.split(',')[1])
                        img_buffer = BytesIO(image_data)
                        img = Image(img_buffer, width=5*inch, height=3*inch)
                        story.append(img)
                
                story.append(Spacer(1, 20))
            
            doc.build(story)
            return file_path
            
        except Exception as e:
            logger.error(f"PDF generation failed: {e}")
            raise
    
    def _generate_excel(
        self,
        report: ReportDefinition,
        sections: List[Dict],
        instance_id: str
    ) -> str:
        """Generate Excel report"""
        try:
            import pandas as pd
            
            file_path = os.path.join(self.output_dir, f"{instance_id}.xlsx")
            
            with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                # Summary sheet
                summary_df = pd.DataFrame([{
                    'Report': report.name,
                    'Description': report.description,
                    'Generated': datetime.now().isoformat()
                }])
                summary_df.to_excel(writer, sheet_name='Summary', index=False)
                
                # Data sheets
                for section in sorted(sections, key=lambda x: x['order']):
                    if section['type'] in ['query', 'table', 'chart']:
                        data = section.get('data', {})
                        if data.get('rows'):
                            df = pd.DataFrame(data['rows'])
                            sheet_name = section['title'][:31]  # Excel sheet name limit
                            df.to_excel(writer, sheet_name=sheet_name, index=False)
            
            return file_path
            
        except Exception as e:
            logger.error(f"Excel generation failed: {e}")
            raise
    
    def _generate_csv(
        self,
        report: ReportDefinition,
        sections: List[Dict],
        instance_id: str
    ) -> str:
        """Generate CSV report (first data section only)"""
        import csv
        
        file_path = os.path.join(self.output_dir, f"{instance_id}.csv")
        
        # Find first data section
        for section in sorted(sections, key=lambda x: x['order']):
            if section['type'] in ['query', 'table']:
                data = section.get('data', {})
                if data.get('rows'):
                    columns = data.get('columns', [])
                    rows = data.get('rows', [])
                    
                    with open(file_path, 'w', newline='') as f:
                        writer = csv.DictWriter(f, fieldnames=columns)
                        writer.writeheader()
                        writer.writerows(rows)
                    
                    return file_path
        
        # No data found, create empty file
        with open(file_path, 'w') as f:
            f.write('')
        
        return file_path
    
    def _generate_html(
        self,
        report: ReportDefinition,
        sections: List[Dict],
        instance_id: str
    ) -> str:
        """Generate HTML report"""
        file_path = os.path.join(self.output_dir, f"{instance_id}.html")
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>{report.name}</title>
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 1200px; margin: 0 auto; padding: 20px; }}
        h1 {{ color: #333; border-bottom: 2px solid #4a90d9; padding-bottom: 10px; }}
        h2 {{ color: #555; margin-top: 30px; }}
        table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #4a90d9; color: white; }}
        tr:nth-child(even) {{ background-color: #f9f9f9; }}
        .meta {{ color: #777; font-size: 0.9em; }}
        .chart {{ max-width: 100%; margin: 20px 0; }}
    </style>
</head>
<body>
    <h1>{report.name}</h1>
    <p>{report.description}</p>
    <p class="meta">Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
"""
        
        for section in sorted(sections, key=lambda x: x['order']):
            html += f"<h2>{section['title']}</h2>"
            
            if section['type'] == 'text':
                html += f"<p>{section.get('content', '')}</p>"
                
            elif section['type'] == 'chart':
                chart_image = section.get('chart_image', '')
                if chart_image:
                    html += f'<img src="{chart_image}" class="chart" alt="{section["title"]}">'
                    
            elif section['type'] in ['query', 'table']:
                data = section.get('data', {})
                if data.get('rows'):
                    columns = data.get('columns', [])
                    rows = data.get('rows', [])
                    
                    html += "<table><thead><tr>"
                    for col in columns:
                        html += f"<th>{col}</th>"
                    html += "</tr></thead><tbody>"
                    
                    for row in rows[:100]:
                        html += "<tr>"
                        for col in columns:
                            html += f"<td>{row.get(col, '')}</td>"
                        html += "</tr>"
                    
                    html += "</tbody></table>"
        
        html += """
</body>
</html>
"""
        
        with open(file_path, 'w') as f:
            f.write(html)
        
        return file_path
    
    def _generate_json(
        self,
        report: ReportDefinition,
        sections: List[Dict],
        instance_id: str
    ) -> str:
        """Generate JSON report"""
        file_path = os.path.join(self.output_dir, f"{instance_id}.json")
        
        output = {
            'report': report.to_dict(),
            'generated_at': datetime.utcnow().isoformat(),
            'sections': sections
        }
        
        with open(file_path, 'w') as f:
            json.dump(output, f, indent=2, default=str)
        
        return file_path


class ReportBuilder:
    """High-level report builder API"""
    
    def __init__(self, reports_dir: str = "./data"):
        self.reports_dir = reports_dir
        self.reports_file = os.path.join(reports_dir, "report_definitions.json")
        self.reports: Dict[str, ReportDefinition] = {}
        self.generated_reports: Dict[str, GeneratedReport] = {}
        self.generator = ReportGenerator()
        self._load()
    
    def _load(self) -> None:
        """Load report definitions"""
        try:
            if os.path.exists(self.reports_file):
                with open(self.reports_file, 'r') as f:
                    data = json.load(f)
                    for report_data in data.get('reports', []):
                        sections = [ReportSection(**s) for s in report_data.get('sections', [])]
                        report_data['sections'] = sections
                        self.reports[report_data['report_id']] = ReportDefinition(**report_data)
        except Exception as e:
            logger.warning(f"Failed to load reports: {e}")
    
    def _save(self) -> None:
        """Save report definitions"""
        try:
            os.makedirs(self.reports_dir, exist_ok=True)
            with open(self.reports_file, 'w') as f:
                json.dump({
                    'reports': [r.to_dict() for r in self.reports.values()]
                }, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save reports: {e}")
    
    def create_report(
        self,
        name: str,
        description: str = "",
        sections: List[Dict] = None,
        parameters: Dict[str, Any] = None,
        created_by: Optional[str] = None,
        tags: List[str] = None
    ) -> ReportDefinition:
        """Create a new report definition"""
        report_id = str(uuid.uuid4())
        
        # Convert section dicts to objects
        section_objects = []
        for i, s in enumerate(sections or []):
            section_objects.append(ReportSection(
                section_id=s.get('section_id', str(uuid.uuid4())),
                title=s.get('title', f'Section {i+1}'),
                section_type=s.get('type', 'text'),
                content=s.get('content', {}),
                order=s.get('order', i)
            ))
        
        report = ReportDefinition(
            report_id=report_id,
            name=name,
            description=description,
            sections=section_objects,
            parameters=parameters or {},
            created_by=created_by,
            created_at=datetime.utcnow().isoformat(),
            updated_at=datetime.utcnow().isoformat(),
            tags=tags or []
        )
        
        self.reports[report_id] = report
        self._save()
        
        return report
    
    def generate_report(
        self,
        report_id: str,
        format: ReportFormat = ReportFormat.PDF,
        parameters: Dict[str, Any] = None,
        user_id: Optional[str] = None
    ) -> GeneratedReport:
        """Generate a report"""
        if report_id not in self.reports:
            raise ValueError(f"Report {report_id} not found")
        
        report = self.reports[report_id]
        generated = self.generator.generate(report, format, parameters, user_id)
        
        self.generated_reports[generated.instance_id] = generated
        return generated
    
    def list_reports(self) -> List[Dict[str, Any]]:
        """List all report definitions"""
        return [r.to_dict() for r in self.reports.values()]
    
    def get_generated_reports(self, report_id: str = None) -> List[Dict[str, Any]]:
        """Get generated report instances"""
        reports = self.generated_reports.values()
        if report_id:
            reports = [r for r in reports if r.report_id == report_id]
        return [r.to_dict() for r in reports]


# Global instance
report_builder = ReportBuilder()

def get_report_builder() -> ReportBuilder:
    return report_builder
