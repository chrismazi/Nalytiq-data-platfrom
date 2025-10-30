"""
Advanced Visualization Engine with Plotly
Generates interactive charts and graphs with export capabilities
"""
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
import json
import logging

logger = logging.getLogger(__name__)

class PlotlyVisualizer:
    """Generate interactive Plotly visualizations"""
    
    def __init__(self, df: pd.DataFrame):
        self.df = df
        self.default_config = {
            'displayModeBar': True,
            'displaylogo': False,
            'modeBarButtonsToRemove': ['pan2d', 'lasso2d', 'select2d']
        }
    
    # ============= Basic Charts =============
    
    def create_bar_chart(
        self, 
        x_col: str, 
        y_col: str, 
        title: Optional[str] = None,
        orientation: str = 'v',
        color_col: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Create interactive bar chart"""
        try:
            fig = px.bar(
                self.df,
                x=x_col,
                y=y_col,
                title=title or f"{y_col} by {x_col}",
                orientation=orientation,
                color=color_col,
                **kwargs
            )
            
            fig.update_layout(
                template='plotly_white',
                hovermode='closest',
                showlegend=True if color_col else False
            )
            
            return {
                'type': 'bar',
                'data': json.loads(fig.to_json())
            }
        except Exception as e:
            logger.error(f"Bar chart creation failed: {e}")
            raise
    
    def create_line_chart(
        self,
        x_col: str,
        y_cols: List[str],
        title: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Create interactive line chart"""
        try:
            fig = go.Figure()
            
            for y_col in y_cols:
                fig.add_trace(go.Scatter(
                    x=self.df[x_col],
                    y=self.df[y_col],
                    mode='lines+markers',
                    name=y_col,
                    **kwargs
                ))
            
            fig.update_layout(
                title=title or f"Trend Analysis",
                xaxis_title=x_col,
                yaxis_title="Value",
                template='plotly_white',
                hovermode='x unified'
            )
            
            return {
                'type': 'line',
                'data': json.loads(fig.to_json())
            }
        except Exception as e:
            logger.error(f"Line chart creation failed: {e}")
            raise
    
    def create_scatter_plot(
        self,
        x_col: str,
        y_col: str,
        title: Optional[str] = None,
        color_col: Optional[str] = None,
        size_col: Optional[str] = None,
        trendline: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Create interactive scatter plot"""
        try:
            fig = px.scatter(
                self.df,
                x=x_col,
                y=y_col,
                title=title or f"{y_col} vs {x_col}",
                color=color_col,
                size=size_col,
                trendline=trendline,
                **kwargs
            )
            
            fig.update_layout(
                template='plotly_white',
                hovermode='closest'
            )
            
            return {
                'type': 'scatter',
                'data': json.loads(fig.to_json())
            }
        except Exception as e:
            logger.error(f"Scatter plot creation failed: {e}")
            raise
    
    def create_histogram(
        self,
        col: str,
        title: Optional[str] = None,
        bins: int = 30,
        **kwargs
    ) -> Dict[str, Any]:
        """Create histogram"""
        try:
            fig = px.histogram(
                self.df,
                x=col,
                title=title or f"Distribution of {col}",
                nbins=bins,
                **kwargs
            )
            
            fig.update_layout(
                template='plotly_white',
                showlegend=False
            )
            
            return {
                'type': 'histogram',
                'data': json.loads(fig.to_json())
            }
        except Exception as e:
            logger.error(f"Histogram creation failed: {e}")
            raise
    
    def create_box_plot(
        self,
        y_col: str,
        x_col: Optional[str] = None,
        title: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Create box plot"""
        try:
            fig = px.box(
                self.df,
                y=y_col,
                x=x_col,
                title=title or f"Distribution of {y_col}",
                **kwargs
            )
            
            fig.update_layout(
                template='plotly_white'
            )
            
            return {
                'type': 'box',
                'data': json.loads(fig.to_json())
            }
        except Exception as e:
            logger.error(f"Box plot creation failed: {e}")
            raise
    
    def create_pie_chart(
        self,
        values_col: str,
        names_col: str,
        title: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Create pie chart"""
        try:
            fig = px.pie(
                self.df,
                values=values_col,
                names=names_col,
                title=title or f"{values_col} Distribution",
                **kwargs
            )
            
            fig.update_layout(
                template='plotly_white'
            )
            
            return {
                'type': 'pie',
                'data': json.loads(fig.to_json())
            }
        except Exception as e:
            logger.error(f"Pie chart creation failed: {e}")
            raise
    
    # ============= Advanced Charts =============
    
    def create_heatmap(
        self,
        columns: Optional[List[str]] = None,
        title: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Create correlation heatmap"""
        try:
            # Use specified columns or all numeric columns
            if columns:
                data = self.df[columns].select_dtypes(include=[np.number])
            else:
                data = self.df.select_dtypes(include=[np.number])
            
            # Calculate correlation matrix
            corr = data.corr()
            
            fig = go.Figure(data=go.Heatmap(
                z=corr.values,
                x=corr.columns,
                y=corr.columns,
                colorscale='RdBu',
                zmid=0,
                text=corr.values.round(2),
                texttemplate='%{text}',
                textfont={"size": 10},
                **kwargs
            ))
            
            fig.update_layout(
                title=title or "Correlation Heatmap",
                template='plotly_white',
                width=700,
                height=700
            )
            
            return {
                'type': 'heatmap',
                'data': json.loads(fig.to_json()),
                'correlation_matrix': corr.to_dict()
            }
        except Exception as e:
            logger.error(f"Heatmap creation failed: {e}")
            raise
    
    def create_grouped_bar(
        self,
        x_col: str,
        y_cols: List[str],
        title: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Create grouped bar chart"""
        try:
            fig = go.Figure()
            
            for y_col in y_cols:
                fig.add_trace(go.Bar(
                    name=y_col,
                    x=self.df[x_col],
                    y=self.df[y_col],
                    **kwargs
                ))
            
            fig.update_layout(
                title=title or f"Grouped Comparison",
                xaxis_title=x_col,
                yaxis_title="Value",
                barmode='group',
                template='plotly_white',
                hovermode='x unified'
            )
            
            return {
                'type': 'grouped_bar',
                'data': json.loads(fig.to_json())
            }
        except Exception as e:
            logger.error(f"Grouped bar chart creation failed: {e}")
            raise
    
    def create_stacked_bar(
        self,
        x_col: str,
        y_cols: List[str],
        title: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Create stacked bar chart"""
        try:
            fig = go.Figure()
            
            for y_col in y_cols:
                fig.add_trace(go.Bar(
                    name=y_col,
                    x=self.df[x_col],
                    y=self.df[y_col],
                    **kwargs
                ))
            
            fig.update_layout(
                title=title or f"Stacked Comparison",
                xaxis_title=x_col,
                yaxis_title="Value",
                barmode='stack',
                template='plotly_white',
                hovermode='x unified'
            )
            
            return {
                'type': 'stacked_bar',
                'data': json.loads(fig.to_json())
            }
        except Exception as e:
            logger.error(f"Stacked bar chart creation failed: {e}")
            raise
    
    def create_area_chart(
        self,
        x_col: str,
        y_cols: List[str],
        title: Optional[str] = None,
        stacked: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """Create area chart"""
        try:
            fig = go.Figure()
            
            for y_col in y_cols:
                fig.add_trace(go.Scatter(
                    x=self.df[x_col],
                    y=self.df[y_col],
                    mode='lines',
                    name=y_col,
                    fill='tonexty' if stacked else 'tozeroy',
                    **kwargs
                ))
            
            fig.update_layout(
                title=title or f"Area Chart",
                xaxis_title=x_col,
                yaxis_title="Value",
                template='plotly_white',
                hovermode='x unified'
            )
            
            return {
                'type': 'area',
                'data': json.loads(fig.to_json())
            }
        except Exception as e:
            logger.error(f"Area chart creation failed: {e}")
            raise
    
    def create_funnel_chart(
        self,
        stages_col: str,
        values_col: str,
        title: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Create funnel chart"""
        try:
            fig = go.Figure(go.Funnel(
                y=self.df[stages_col],
                x=self.df[values_col],
                textinfo="value+percent initial",
                **kwargs
            ))
            
            fig.update_layout(
                title=title or "Funnel Analysis",
                template='plotly_white'
            )
            
            return {
                'type': 'funnel',
                'data': json.loads(fig.to_json())
            }
        except Exception as e:
            logger.error(f"Funnel chart creation failed: {e}")
            raise
    
    # ============= Statistical Charts =============
    
    def create_violin_plot(
        self,
        y_col: str,
        x_col: Optional[str] = None,
        title: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Create violin plot"""
        try:
            fig = px.violin(
                self.df,
                y=y_col,
                x=x_col,
                title=title or f"Distribution of {y_col}",
                box=True,
                **kwargs
            )
            
            fig.update_layout(
                template='plotly_white'
            )
            
            return {
                'type': 'violin',
                'data': json.loads(fig.to_json())
            }
        except Exception as e:
            logger.error(f"Violin plot creation failed: {e}")
            raise
    
    def create_3d_scatter(
        self,
        x_col: str,
        y_col: str,
        z_col: str,
        title: Optional[str] = None,
        color_col: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Create 3D scatter plot"""
        try:
            fig = px.scatter_3d(
                self.df,
                x=x_col,
                y=y_col,
                z=z_col,
                title=title or "3D Scatter Plot",
                color=color_col,
                **kwargs
            )
            
            fig.update_layout(
                template='plotly_white'
            )
            
            return {
                'type': '3d_scatter',
                'data': json.loads(fig.to_json())
            }
        except Exception as e:
            logger.error(f"3D scatter plot creation failed: {e}")
            raise
    
    # ============= Dashboard Creation =============
    
    def create_dashboard(
        self,
        charts: List[Dict[str, Any]],
        layout: str = 'grid',
        title: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create multi-chart dashboard"""
        try:
            n_charts = len(charts)
            
            if layout == 'grid':
                rows = int(np.ceil(np.sqrt(n_charts)))
                cols = int(np.ceil(n_charts / rows))
            elif layout == 'vertical':
                rows, cols = n_charts, 1
            elif layout == 'horizontal':
                rows, cols = 1, n_charts
            else:
                rows, cols = 2, int(np.ceil(n_charts / 2))
            
            # Create subplots
            subplot_titles = [chart.get('title', f'Chart {i+1}') 
                            for i, chart in enumerate(charts)]
            
            fig = make_subplots(
                rows=rows,
                cols=cols,
                subplot_titles=subplot_titles
            )
            
            # Add charts to subplots
            for i, chart_config in enumerate(charts):
                row = (i // cols) + 1
                col = (i % cols) + 1
                
                # This is simplified - in practice you'd reconstruct each chart
                # For now, return the configuration
            
            fig.update_layout(
                title_text=title or "Analytics Dashboard",
                showlegend=True,
                template='plotly_white',
                height=300 * rows
            )
            
            return {
                'type': 'dashboard',
                'layout': layout,
                'charts': charts,
                'data': json.loads(fig.to_json())
            }
        except Exception as e:
            logger.error(f"Dashboard creation failed: {e}")
            raise
    
    # ============= Export Functions =============
    
    @staticmethod
    def export_to_image(
        fig_json: str,
        format: str = 'png',
        width: int = 1200,
        height: int = 800
    ) -> bytes:
        """Export Plotly figure to image (requires kaleido)"""
        try:
            fig = go.Figure(json.loads(fig_json))
            
            img_bytes = fig.to_image(
                format=format,
                width=width,
                height=height,
                engine='kaleido'
            )
            
            return img_bytes
        except Exception as e:
            logger.error(f"Image export failed: {e}")
            raise
    
    @staticmethod
    def get_chart_types() -> List[Dict[str, Any]]:
        """Get available chart types and their parameters"""
        return [
            {
                'id': 'bar',
                'name': 'Bar Chart',
                'description': 'Compare values across categories',
                'params': ['x_col', 'y_col', 'orientation', 'color_col']
            },
            {
                'id': 'line',
                'name': 'Line Chart',
                'description': 'Show trends over time',
                'params': ['x_col', 'y_cols']
            },
            {
                'id': 'scatter',
                'name': 'Scatter Plot',
                'description': 'Show relationships between variables',
                'params': ['x_col', 'y_col', 'color_col', 'size_col', 'trendline']
            },
            {
                'id': 'histogram',
                'name': 'Histogram',
                'description': 'Show distribution of values',
                'params': ['col', 'bins']
            },
            {
                'id': 'box',
                'name': 'Box Plot',
                'description': 'Show statistical distribution',
                'params': ['y_col', 'x_col']
            },
            {
                'id': 'pie',
                'name': 'Pie Chart',
                'description': 'Show proportions',
                'params': ['values_col', 'names_col']
            },
            {
                'id': 'heatmap',
                'name': 'Heatmap',
                'description': 'Show correlations',
                'params': ['columns']
            },
            {
                'id': 'grouped_bar',
                'name': 'Grouped Bar',
                'description': 'Compare multiple series',
                'params': ['x_col', 'y_cols']
            },
            {
                'id': 'stacked_bar',
                'name': 'Stacked Bar',
                'description': 'Show composition',
                'params': ['x_col', 'y_cols']
            },
            {
                'id': 'area',
                'name': 'Area Chart',
                'description': 'Show cumulative trends',
                'params': ['x_col', 'y_cols', 'stacked']
            },
            {
                'id': 'violin',
                'name': 'Violin Plot',
                'description': 'Show distribution density',
                'params': ['y_col', 'x_col']
            },
            {
                'id': '3d_scatter',
                'name': '3D Scatter',
                'description': 'Show 3D relationships',
                'params': ['x_col', 'y_col', 'z_col', 'color_col']
            },
            {
                'id': 'funnel',
                'name': 'Funnel Chart',
                'description': 'Show conversion rates',
                'params': ['stages_col', 'values_col']
            }
        ]
