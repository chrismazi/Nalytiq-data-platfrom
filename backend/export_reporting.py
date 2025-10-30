"""
Export & Reporting System with:
- PDF Report Generation
- Chart Export (PNG, SVG)
- Email Reports
- Scheduled Reports
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
import json
from datetime import datetime
import io
import base64
import logging

# PDF Generation
from reportlab.lib.pdfsize import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, 
    Spacer, PageBreak, Image as RLImage
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT

# Plotting
import matplotlib
matplotlib.use('Agg')  # Use non-GUI backend
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

# Image processing
from PIL import Image as PILImage

logger = logging.getLogger(__name__)

class ReportGenerator:
    """Generate comprehensive PDF reports"""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1e40af'),
            spaceAfter=30,
            alignment=TA_CENTER
        )
        self.heading_style = ParagraphStyle(
            'CustomHeading',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#1e40af'),
            spaceAfter=12
        )
    
    def generate_analysis_report(self, analysis_data: Dict, output_path: str) -> str:
        """Generate comprehensive analysis PDF report"""
        doc = SimpleDocTemplate(
            output_path,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18
        )
        
        story = []
        
        # Title Page
        story.append(Paragraph(
            analysis_data.get('title', 'Analysis Report'),
            self.title_style
        ))
        story.append(Spacer(1, 0.3*inch))
        
        # Metadata
        metadata_text = f"""
        <b>Generated:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br/>
        <b>Dataset:</b> {analysis_data.get('dataset_name', 'N/A')}<br/>
        <b>Analysis Type:</b> {analysis_data.get('analysis_type', 'N/A')}<br/>
        <b>Rows:</b> {analysis_data.get('n_rows', 'N/A'):,}<br/>
        <b>Columns:</b> {analysis_data.get('n_columns', 'N/A')}
        """
        story.append(Paragraph(metadata_text, self.styles['Normal']))
        story.append(Spacer(1, 0.5*inch))
        
        # Executive Summary
        if 'summary' in analysis_data:
            story.append(Paragraph("Executive Summary", self.heading_style))
            story.append(Paragraph(analysis_data['summary'], self.styles['Normal']))
            story.append(Spacer(1, 0.3*inch))
        
        # Key Metrics
        if 'metrics' in analysis_data:
            story.append(Paragraph("Key Metrics", self.heading_style))
            metrics_table = self._create_metrics_table(analysis_data['metrics'])
            story.append(metrics_table)
            story.append(Spacer(1, 0.3*inch))
        
        # Visualizations
        if 'charts' in analysis_data:
            story.append(PageBreak())
            story.append(Paragraph("Visualizations", self.heading_style))
            for chart_data in analysis_data['charts']:
                chart_img = self._create_chart_image(chart_data)
                if chart_img:
                    story.append(chart_img)
                    story.append(Spacer(1, 0.2*inch))
        
        # Data Tables
        if 'data_tables' in analysis_data:
            story.append(PageBreak())
            story.append(Paragraph("Detailed Data", self.heading_style))
            for table_data in analysis_data['data_tables']:
                data_table = self._create_data_table(table_data)
                story.append(data_table)
                story.append(Spacer(1, 0.3*inch))
        
        # Insights & Recommendations
        if 'insights' in analysis_data:
            story.append(PageBreak())
            story.append(Paragraph("Insights & Recommendations", self.heading_style))
            for i, insight in enumerate(analysis_data['insights'], 1):
                story.append(Paragraph(f"{i}. {insight}", self.styles['Normal']))
                story.append(Spacer(1, 0.1*inch))
        
        # Build PDF
        doc.build(story)
        logger.info(f"PDF report generated: {output_path}")
        return output_path
    
    def _create_metrics_table(self, metrics: Dict) -> Table:
        """Create a formatted metrics table"""
        data = [['Metric', 'Value']]
        for key, value in metrics.items():
            if isinstance(value, float):
                value = f"{value:.4f}"
            data.append([key.replace('_', ' ').title(), str(value)])
        
        table = Table(data, colWidths=[3*inch, 2*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3b82f6')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        return table
    
    def _create_data_table(self, table_data: Dict) -> Table:
        """Create a formatted data table"""
        df = pd.DataFrame(table_data.get('data', []))
        if df.empty:
            return Paragraph("No data available", self.styles['Normal'])
        
        # Limit rows for PDF
        df = df.head(50)
        
        # Prepare data
        data = [df.columns.tolist()] + df.values.tolist()
        
        table = Table(data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3b82f6')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        return table
    
    def _create_chart_image(self, chart_data: Dict) -> Optional[RLImage]:
        """Create chart image for PDF"""
        try:
            chart_type = chart_data.get('type', 'bar')
            data = chart_data.get('data', {})
            
            # Create matplotlib figure
            fig, ax = plt.subplots(figsize=(8, 5))
            
            if chart_type == 'bar':
                x = data.get('x', [])
                y = data.get('y', [])
                ax.bar(x, y, color='#3b82f6')
                ax.set_xlabel(data.get('xlabel', ''))
                ax.set_ylabel(data.get('ylabel', ''))
            elif chart_type == 'line':
                x = data.get('x', [])
                y = data.get('y', [])
                ax.plot(x, y, color='#3b82f6', linewidth=2)
                ax.set_xlabel(data.get('xlabel', ''))
                ax.set_ylabel(data.get('ylabel', ''))
            elif chart_type == 'scatter':
                x = data.get('x', [])
                y = data.get('y', [])
                ax.scatter(x, y, color='#3b82f6', alpha=0.6)
                ax.set_xlabel(data.get('xlabel', ''))
                ax.set_ylabel(data.get('ylabel', ''))
            
            ax.set_title(chart_data.get('title', ''), fontsize=14, fontweight='bold')
            ax.grid(True, alpha=0.3)
            plt.tight_layout()
            
            # Save to bytes
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
            img_buffer.seek(0)
            plt.close(fig)
            
            # Create ReportLab image
            img = RLImage(img_buffer, width=5*inch, height=3*inch)
            return img
            
        except Exception as e:
            logger.error(f"Error creating chart image: {e}")
            return None

class ChartExporter:
    """Export charts in various formats"""
    
    @staticmethod
    def export_plotly_chart(fig: go.Figure, output_path: str, format: str = 'png') -> str:
        """Export Plotly chart to file"""
        if format == 'html':
            fig.write_html(output_path)
        elif format == 'png':
            fig.write_image(output_path, width=1200, height=800)
        elif format == 'svg':
            fig.write_image(output_path, format='svg')
        elif format == 'pdf':
            fig.write_image(output_path, format='pdf')
        
        logger.info(f"Chart exported to {output_path}")
        return output_path
    
    @staticmethod
    def create_comparison_chart(data: List[Dict], chart_type: str = 'bar') -> go.Figure:
        """Create comparison chart"""
        if chart_type == 'bar':
            fig = go.Figure()
            for item in data:
                fig.add_trace(go.Bar(
                    name=item['name'],
                    x=item['x'],
                    y=item['y']
                ))
            fig.update_layout(
                title='Comparison Analysis',
                xaxis_title='Category',
                yaxis_title='Value',
                barmode='group'
            )
        elif chart_type == 'line':
            fig = go.Figure()
            for item in data:
                fig.add_trace(go.Scatter(
                    name=item['name'],
                    x=item['x'],
                    y=item['y'],
                    mode='lines+markers'
                ))
            fig.update_layout(
                title='Trend Comparison',
                xaxis_title='Time/Category',
                yaxis_title='Value'
            )
        
        return fig
    
    @staticmethod
    def create_dashboard_report(analyses: List[Dict]) -> go.Figure:
        """Create multi-panel dashboard"""
        n_analyses = len(analyses)
        rows = (n_analyses + 1) // 2
        cols = min(n_analyses, 2)
        
        fig = make_subplots(
            rows=rows, cols=cols,
            subplot_titles=[a.get('title', f'Analysis {i+1}') 
                          for i, a in enumerate(analyses)]
        )
        
        for i, analysis in enumerate(analyses):
            row = (i // 2) + 1
            col = (i % 2) + 1
            
            chart_type = analysis.get('chart_type', 'bar')
            data = analysis.get('data', {})
            
            if chart_type == 'bar':
                fig.add_trace(
                    go.Bar(x=data.get('x', []), y=data.get('y', [])),
                    row=row, col=col
                )
            elif chart_type == 'scatter':
                fig.add_trace(
                    go.Scatter(
                        x=data.get('x', []), 
                        y=data.get('y', []),
                        mode='markers'
                    ),
                    row=row, col=col
                )
        
        fig.update_layout(
            title_text="Analysis Dashboard",
            showlegend=False,
            height=300 * rows
        )
        
        return fig

class EmailReporter:
    """Send reports via email"""
    
    def __init__(self, api_key: str = None):
        """Initialize with SendGrid API key"""
        self.api_key = api_key or os.getenv('SENDGRID_API_KEY')
        
        if self.api_key:
            from sendgrid import SendGridAPIClient
            from sendgrid.helpers.mail import Mail, Attachment, FileContent, FileName, FileType, Disposition
            self.sg = SendGridAPIClient(self.api_key)
            self.Mail = Mail
            self.Attachment = Attachment
            self.FileContent = FileContent
            self.FileName = FileName
            self.FileType = FileType
            self.Disposition = Disposition
        else:
            logger.warning("SendGrid API key not configured")
    
    def send_report(self, to_email: str, subject: str, body: str, 
                   attachments: List[str] = None) -> bool:
        """Send email report with attachments"""
        if not self.api_key:
            logger.error("Cannot send email: SendGrid not configured")
            return False
        
        try:
            message = self.Mail(
                from_email='reports@nalytiq.com',
                to_emails=to_email,
                subject=subject,
                html_content=body
            )
            
            # Add attachments
            if attachments:
                for file_path in attachments:
                    with open(file_path, 'rb') as f:
                        data = f.read()
                    encoded = base64.b64encode(data).decode()
                    
                    attachment = self.Attachment()
                    attachment.file_content = self.FileContent(encoded)
                    attachment.file_name = self.FileName(os.path.basename(file_path))
                    attachment.disposition = self.Disposition('attachment')
                    
                    if file_path.endswith('.pdf'):
                        attachment.file_type = self.FileType('application/pdf')
                    elif file_path.endswith('.png'):
                        attachment.file_type = self.FileType('image/png')
                    
                    message.add_attachment(attachment)
            
            response = self.sg.send(message)
            logger.info(f"Email sent successfully: {response.status_code}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False

class ReportScheduler:
    """Schedule automated report generation"""
    
    def __init__(self):
        from apscheduler.schedulers.background import BackgroundScheduler
        from apscheduler.triggers.cron import CronTrigger
        
        self.scheduler = BackgroundScheduler()
        self.CronTrigger = CronTrigger
        self.jobs = {}
    
    def schedule_report(self, job_id: str, analysis_id: int, 
                       schedule_config: Dict, recipients: List[str]) -> bool:
        """Schedule periodic report generation"""
        try:
            schedule_type = schedule_config.get('type', 'daily')
            
            if schedule_type == 'daily':
                trigger = self.CronTrigger(hour=schedule_config.get('hour', 9))
            elif schedule_type == 'weekly':
                trigger = self.CronTrigger(
                    day_of_week=schedule_config.get('day_of_week', 'mon'),
                    hour=schedule_config.get('hour', 9)
                )
            elif schedule_type == 'monthly':
                trigger = self.CronTrigger(
                    day=schedule_config.get('day', 1),
                    hour=schedule_config.get('hour', 9)
                )
            else:
                logger.error(f"Unknown schedule type: {schedule_type}")
                return False
            
            job = self.scheduler.add_job(
                self._generate_and_send_report,
                trigger=trigger,
                args=[analysis_id, recipients],
                id=job_id
            )
            
            self.jobs[job_id] = job
            logger.info(f"Report scheduled: {job_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to schedule report: {e}")
            return False
    
    def start(self):
        """Start the scheduler"""
        self.scheduler.start()
        logger.info("Report scheduler started")
    
    def stop(self):
        """Stop the scheduler"""
        self.scheduler.shutdown()
        logger.info("Report scheduler stopped")
    
    def _generate_and_send_report(self, analysis_id: int, recipients: List[str]):
        """Internal method to generate and send report"""
        logger.info(f"Generating scheduled report for analysis {analysis_id}")
        # Implementation depends on database access
        pass

# Utility functions

def create_executive_summary(analysis_results: Dict) -> str:
    """Generate executive summary from analysis results"""
    summary_parts = []
    
    if 'dataset' in analysis_results:
        summary_parts.append(
            f"This analysis examines {analysis_results['dataset']['rows']:,} records "
            f"across {analysis_results['dataset']['columns']} variables."
        )
    
    if 'key_findings' in analysis_results:
        summary_parts.append("Key findings include:")
        for finding in analysis_results['key_findings'][:3]:
            summary_parts.append(f"• {finding}")
    
    if 'metrics' in analysis_results:
        metrics = analysis_results['metrics']
        if 'accuracy' in metrics:
            summary_parts.append(
                f"The model achieved {metrics['accuracy']*100:.1f}% accuracy."
            )
        elif 'r2_score' in metrics:
            summary_parts.append(
                f"The model explains {metrics['r2_score']*100:.1f}% of variance."
            )
    
    return " ".join(summary_parts)
