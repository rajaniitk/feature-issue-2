import pandas as pd
import numpy as np
import os
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.figure_factory as ff
import seaborn as sns
import matplotlib.pyplot as plt
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
import logging
from datetime import datetime
from models import Dataset, Analysis, db
from services.data_processor import DataProcessor
from flask import current_app
import json
import io
import base64

class VisualizationEngine:
    def __init__(self):
        self.data_processor = DataProcessor()
        
    def generate_chart_data(self, file_path, chart_type, x_column, y_column=None, color_column=None):
        """Generic method to generate chart data based on chart type"""
        try:
            # Parse dataset
            filename = os.path.basename(file_path)
            df = self.data_processor.parse_file(file_path, filename)
            if df is None:
                return {'success': False, 'error': 'Failed to load dataset'}
            
            # Validate columns exist
            if x_column not in df.columns:
                return {'success': False, 'error': f'Column {x_column} not found'}
            
            if y_column and y_column not in df.columns:
                return {'success': False, 'error': f'Column {y_column} not found'}
            
            if color_column and color_column not in df.columns:
                return {'success': False, 'error': f'Column {color_column} not found'}
            
            # Generate chart based on type
            if chart_type == 'histogram':
                if not pd.api.types.is_numeric_dtype(df[x_column]):
                    return {'success': False, 'error': f'Column {x_column} must be numeric for histogram'}
                
                fig = px.histogram(
                    df, x=x_column,
                    title=f'Histogram of {x_column}',
                    template='plotly_dark'
                )
                
            elif chart_type == 'scatter':
                if not y_column:
                    return {'success': False, 'error': 'Y column required for scatter plot'}
                
                fig = px.scatter(
                    df, x=x_column, y=y_column, color=color_column,
                    title=f'Scatter: {x_column} vs {y_column}',
                    template='plotly_dark'
                )
                
            elif chart_type == 'line':
                if not y_column:
                    return {'success': False, 'error': 'Y column required for line plot'}
                
                fig = px.line(
                    df, x=x_column, y=y_column, color=color_column,
                    title=f'Line: {y_column} over {x_column}',
                    template='plotly_dark'
                )
                
            elif chart_type == 'bar':
                if y_column:
                    # Grouped bar chart
                    fig = px.bar(
                        df, x=x_column, y=y_column, color=color_column,
                        title=f'Bar Chart: {y_column} by {x_column}',
                        template='plotly_dark'
                    )
                else:
                    # Count bar chart
                    counts = df[x_column].value_counts().reset_index()
                    counts.columns = [x_column, 'count']
                    fig = px.bar(
                        counts, x=x_column, y='count',
                        title=f'Bar Chart: Count of {x_column}',
                        template='plotly_dark'
                    )
                    
            elif chart_type == 'pie':
                counts = df[x_column].value_counts()
                # Limit to top 10
                if len(counts) > 10:
                    top_counts = counts.head(10)
                    other_count = counts.tail(len(counts) - 10).sum()
                    if other_count > 0:
                        top_counts['Others'] = other_count
                    counts = top_counts
                
                fig = px.pie(
                    values=counts.values, names=counts.index,
                    title=f'Pie Chart: {x_column}',
                    template='plotly_dark'
                )
                
            elif chart_type == 'box':
                if y_column:
                    fig = px.box(
                        df, x=x_column, y=y_column, color=color_column,
                        title=f'Box Plot: {y_column} by {x_column}',
                        template='plotly_dark'
                    )
                else:
                    fig = px.box(
                        df, y=x_column,
                        title=f'Box Plot: {x_column}',
                        template='plotly_dark'
                    )
                    
            else:
                return {'success': False, 'error': f'Unsupported chart type: {chart_type}'}
            
            # Apply dark theme
            fig.update_layout(self.dark_template['layout'])
            
            return {
                'success': True,
                'plot_json': fig.to_json(),
                'plot_html': fig.to_html(include_plotlyjs=True),
                'chart_type': chart_type,
                'columns_used': {
                    'x': x_column,
                    'y': y_column,
                    'color': color_column
                }
            }
            
        except Exception as e:
            current_app.logger.error(f"Generate chart data error: {str(e)}")
            return {'success': False, 'error': str(e)}
        
        # Dark theme template for plotly
        self.dark_template = {
            'layout': {
                'paper_bgcolor': '#0a0a0a',
                'plot_bgcolor': '#1a1a1a',
                'font': {'color': '#ffffff'},
                'colorway': ['#667eea', '#764ba2', '#f093fb', '#f5576c', '#4facfe', 
                            '#00f2fe', '#43e97b', '#38f9d7', '#fa709a', '#fee140'],
                'xaxis': {
                    'gridcolor': '#2a2a2a',
                    'linecolor': '#2a2a2a',
                    'tickcolor': '#2a2a2a'
                },
                'yaxis': {
                    'gridcolor': '#2a2a2a',
                    'linecolor': '#2a2a2a',
                    'tickcolor': '#2a2a2a'
                }
            }
        }
        
        # Available plot types organized by category
        self.plot_catalog = {
            'univariate': {
                'numerical': ['histogram', 'boxplot', 'violin', 'density', 'qq_plot', 'strip'],
                'categorical': ['bar_chart', 'pie_chart', 'donut_chart', 'countplot']
            },
            'bivariate': {
                'numerical_numerical': ['scatter', 'line', 'jointplot', 'hexbin', 'regression'],
                'numerical_categorical': ['boxplot_grouped', 'violin_grouped', 'strip_grouped', 'swarm'],
                'categorical_categorical': ['heatmap_crosstab', 'mosaic', 'stacked_bar']
            },
            'multivariate': {
                'general': ['pairplot', 'parallel_coordinates', 'radar_chart', 'correlation_heatmap'],
                'dimensional': ['scatter_3d', 'surface_3d', 'pca_biplot', 'tsne_plot']
            },
            'time_series': {
                'temporal': ['line_time', 'area_chart', 'candlestick', 'seasonal_decompose']
            },
            'statistical': {
                'distributions': ['probability_plot', 'residual_plot', 'leverage_plot'],
                'comparisons': ['forest_plot', 'funnel_chart']
            },
            'hierarchical': {
                'tree_based': ['treemap', 'sunburst', 'icicle', 'dendrogram']
            },
            'geographic': {
                'spatial': ['choropleth', 'scatter_geo', 'density_mapbox']
            },
            'specialized': {
                'network': ['sankey', 'chord_diagram'],
                'financial': ['ohlc', 'volume_profile'],
                'scientific': ['contour', 'streamline', 'quiver']
            }
        }
    
    def histogram(self, dataset_id, column, bins=30):
        try:
            dataset = Dataset.query.get_or_404(dataset_id)
            df = self.data_processor.load_dataset(dataset)
            
            if column not in df.columns:
                return {'success': False, 'error': f'Column {column} not found'}
            
            data = df[column].dropna()
            
            if not pd.api.types.is_numeric_dtype(data):
                return {'success': False, 'error': f'Column {column} is not numeric'}
            
            # Create histogram
            fig = px.histogram(
                x=data, 
                nbins=bins,
                title=f'Distribution of {column}',
                labels={'x': column, 'y': 'Frequency'},
                template='plotly_dark'
            )
            
            # Update layout for dark theme
            fig.update_layout(self.dark_template['layout'])
            
            # Add statistics annotation
            stats_text = f"Mean: {data.mean():.2f}<br>Std: {data.std():.2f}<br>Skewness: {data.skew():.2f}"
            fig.add_annotation(
                x=0.02, y=0.98,
                xref='paper', yref='paper',
                text=stats_text,
                showarrow=False,
                bgcolor='rgba(255,255,255,0.1)',
                bordercolor='rgba(255,255,255,0.2)'
            )
            
            result = {
                'plot_type': 'histogram',
                'plot_json': fig.to_json(),
                'plot_html': fig.to_html(include_plotlyjs=True),
                'statistics': {
                    'mean': float(data.mean()),
                    'median': float(data.median()),
                    'std': float(data.std()),
                    'skewness': float(data.skew()),
                    'kurtosis': float(data.kurtosis()),
                    'count': len(data)
                }
            }
            
            # Save visualization
            self.save_visualization(dataset_id, 'histogram', column, result)
            
            return {'success': True, 'result': result}
            
        except Exception as e:
            current_app.logger.error(f"Histogram error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def boxplot(self, dataset_id, column, group_by=None):
        try:
            dataset = Dataset.query.get_or_404(dataset_id)
            df = self.data_processor.load_dataset(dataset)
            
            if column not in df.columns:
                return {'success': False, 'error': f'Column {column} not found'}
            
            if group_by and group_by not in df.columns:
                return {'success': False, 'error': f'Group column {group_by} not found'}
            
            # Create boxplot
            if group_by:
                fig = px.box(
                    df, 
                    x=group_by, 
                    y=column,
                    title=f'Box Plot of {column} by {group_by}',
                    template='plotly_dark'
                )
            else:
                fig = px.box(
                    y=df[column].dropna(),
                    title=f'Box Plot of {column}',
                    template='plotly_dark'
                )
            
            # Update layout for dark theme
            fig.update_layout(self.dark_template['layout'])
            
            # Add outlier statistics
            if not group_by:
                data = df[column].dropna()
                Q1 = data.quantile(0.25)
                Q3 = data.quantile(0.75)
                IQR = Q3 - Q1
                outliers = data[(data < Q1 - 1.5 * IQR) | (data > Q3 + 1.5 * IQR)]
                
                stats_text = f"Outliers: {len(outliers)}<br>IQR: {IQR:.2f}<br>Median: {data.median():.2f}"
                fig.add_annotation(
                    x=0.02, y=0.98,
                    xref='paper', yref='paper',
                    text=stats_text,
                    showarrow=False,
                    bgcolor='rgba(255,255,255,0.1)',
                    bordercolor='rgba(255,255,255,0.2)'
                )
            
            result = {
                'plot_type': 'boxplot',
                'plot_json': fig.to_json(),
                'plot_html': fig.to_html(include_plotlyjs=True),
                'group_by': group_by
            }
            
            # Save visualization
            self.save_visualization(dataset_id, 'boxplot', column, result)
            
            return {'success': True, 'result': result}
            
        except Exception as e:
            current_app.logger.error(f"Boxplot error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def scatter(self, dataset_id, x_column, y_column, color_column=None, size_column=None):
        try:
            dataset = Dataset.query.get_or_404(dataset_id)
            df = self.data_processor.load_dataset(dataset)
            
            required_cols = [x_column, y_column]
            if not all(col in df.columns for col in required_cols):
                return {'success': False, 'error': 'Required columns not found'}
            
            # Create scatter plot
            fig = px.scatter(
                df,
                x=x_column,
                y=y_column,
                color=color_column,
                size=size_column,
                title=f'Scatter Plot: {x_column} vs {y_column}',
                template='plotly_dark',
                trendline='ols' if not color_column else None
            )
            
            # Update layout for dark theme
            fig.update_layout(self.dark_template['layout'])
            
            # Calculate correlation
            clean_data = df[[x_column, y_column]].dropna()
            if len(clean_data) > 1:
                correlation = clean_data[x_column].corr(clean_data[y_column])
                
                stats_text = f"Correlation: {correlation:.3f}<br>Sample size: {len(clean_data)}"
                fig.add_annotation(
                    x=0.02, y=0.98,
                    xref='paper', yref='paper',
                    text=stats_text,
                    showarrow=False,
                    bgcolor='rgba(255,255,255,0.1)',
                    bordercolor='rgba(255,255,255,0.2)'
                )
            
            result = {
                'plot_type': 'scatter',
                'plot_json': fig.to_json(),
                'plot_html': fig.to_html(include_plotlyjs=True),
                'x_column': x_column,
                'y_column': y_column,
                'color_column': color_column,
                'size_column': size_column
            }
            
            # Save visualization
            self.save_visualization(dataset_id, 'scatter', f'{x_column}_vs_{y_column}', result)
            
            return {'success': True, 'result': result}
            
        except Exception as e:
            current_app.logger.error(f"Scatter plot error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def line_plot(self, dataset_id, x_column, y_column, group_by=None):
        try:
            dataset = Dataset.query.get_or_404(dataset_id)
            df = self.data_processor.load_dataset(dataset)
            
            if x_column not in df.columns or y_column not in df.columns:
                return {'success': False, 'error': 'Required columns not found'}
            
            # Sort by x column
            df_sorted = df.sort_values(x_column)
            
            # Create line plot
            if group_by and group_by in df.columns:
                fig = px.line(
                    df_sorted,
                    x=x_column,
                    y=y_column,
                    color=group_by,
                    title=f'Line Plot: {y_column} over {x_column}',
                    template='plotly_dark'
                )
            else:
                fig = px.line(
                    df_sorted,
                    x=x_column,
                    y=y_column,
                    title=f'Line Plot: {y_column} over {x_column}',
                    template='plotly_dark'
                )
            
            # Update layout for dark theme
            fig.update_layout(self.dark_template['layout'])
            
            result = {
                'plot_type': 'line',
                'plot_json': fig.to_json(),
                'plot_html': fig.to_html(include_plotlyjs=True),
                'x_column': x_column,
                'y_column': y_column,
                'group_by': group_by
            }
            
            # Save visualization
            self.save_visualization(dataset_id, 'line', f'{y_column}_over_{x_column}', result)
            
            return {'success': True, 'result': result}
            
        except Exception as e:
            current_app.logger.error(f"Line plot error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def bar_chart(self, dataset_id, column, value_column=None):
        try:
            dataset = Dataset.query.get_or_404(dataset_id)
            df = self.data_processor.load_dataset(dataset)
            
            if column not in df.columns:
                return {'success': False, 'error': f'Column {column} not found'}
            
            if value_column:
                if value_column not in df.columns:
                    return {'success': False, 'error': f'Value column {value_column} not found'}
                
                # Grouped bar chart
                grouped_data = df.groupby(column)[value_column].mean().reset_index()
                fig = px.bar(
                    grouped_data,
                    x=column,
                    y=value_column,
                    title=f'Bar Chart: Average {value_column} by {column}',
                    template='plotly_dark'
                )
            else:
                # Count bar chart
                counts = df[column].value_counts().reset_index()
                counts.columns = [column, 'count']
                fig = px.bar(
                    counts,
                    x=column,
                    y='count',
                    title=f'Bar Chart: Count of {column}',
                    template='plotly_dark'
                )
            
            # Update layout for dark theme
            fig.update_layout(self.dark_template['layout'])
            
            result = {
                'plot_type': 'bar',
                'plot_json': fig.to_json(),
                'plot_html': fig.to_html(include_plotlyjs=True),
                'column': column,
                'value_column': value_column
            }
            
            # Save visualization
            self.save_visualization(dataset_id, 'bar', column, result)
            
            return {'success': True, 'result': result}
            
        except Exception as e:
            current_app.logger.error(f"Bar chart error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def pie_chart(self, dataset_id, column):
        try:
            dataset = Dataset.query.get_or_404(dataset_id)
            df = self.data_processor.load_dataset(dataset)
            
            if column not in df.columns:
                return {'success': False, 'error': f'Column {column} not found'}
            
            # Get value counts
            counts = df[column].value_counts()
            
            # Limit to top 10 categories
            if len(counts) > 10:
                top_counts = counts.head(10)
                other_count = counts.tail(len(counts) - 10).sum()
                if other_count > 0:
                    top_counts['Others'] = other_count
                counts = top_counts
            
            # Create pie chart
            fig = px.pie(
                values=counts.values,
                names=counts.index,
                title=f'Pie Chart: Distribution of {column}',
                template='plotly_dark'
            )
            
            # Update layout for dark theme
            fig.update_layout(self.dark_template['layout'])
            
            result = {
                'plot_type': 'pie',
                'plot_json': fig.to_json(),
                'plot_html': fig.to_html(include_plotlyjs=True),
                'column': column,
                'categories': len(counts)
            }
            
            # Save visualization
            self.save_visualization(dataset_id, 'pie', column, result)
            
            return {'success': True, 'result': result}
            
        except Exception as e:
            current_app.logger.error(f"Pie chart error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def heatmap(self, dataset_id, method='correlation', columns=None):
        try:
            dataset = Dataset.query.get_or_404(dataset_id)
            df = self.data_processor.load_dataset(dataset)
            
            if columns:
                if not all(col in df.columns for col in columns):
                    return {'success': False, 'error': 'Some columns not found'}
                df_subset = df[columns]
            else:
                df_subset = df.select_dtypes(include=[np.number])
            
            if df_subset.empty:
                return {'success': False, 'error': 'No numeric columns found'}
            
            if method == 'correlation':
                matrix = df_subset.corr()
                title = 'Correlation Heatmap'
                colorscale = 'RdBu'
                zmin, zmax = -1, 1
            elif method == 'covariance':
                matrix = df_subset.cov()
                title = 'Covariance Heatmap'
                colorscale = 'Viridis'
                zmin, zmax = None, None
            else:
                return {'success': False, 'error': f'Unknown method: {method}'}
            
            # Create heatmap
            fig = px.imshow(
                matrix,
                title=title,
                color_continuous_scale=colorscale,
                aspect='auto',
                template='plotly_dark',
                zmin=zmin,
                zmax=zmax
            )
            
            # Update layout for dark theme
            fig.update_layout(self.dark_template['layout'])
            
            # Add text annotations
            fig.update_traces(
                text=np.around(matrix.values, decimals=2),
                texttemplate='%{text}',
                textfont={'size': 10}
            )
            
            result = {
                'plot_type': 'heatmap',
                'plot_json': fig.to_json(),
                'plot_html': fig.to_html(include_plotlyjs=True),
                'method': method,
                'matrix': matrix.to_dict()
            }
            
            # Save visualization
            self.save_visualization(dataset_id, 'heatmap', method, result)
            
            return {'success': True, 'result': result}
            
        except Exception as e:
            current_app.logger.error(f"Heatmap error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def violin_plot(self, dataset_id, column, group_by=None):
        try:
            dataset = Dataset.query.get_or_404(dataset_id)
            df = self.data_processor.load_dataset(dataset)
            
            if column not in df.columns:
                return {'success': False, 'error': f'Column {column} not found'}
            
            # Create violin plot
            if group_by and group_by in df.columns:
                fig = px.violin(
                    df,
                    x=group_by,
                    y=column,
                    box=True,
                    title=f'Violin Plot of {column} by {group_by}',
                    template='plotly_dark'
                )
            else:
                fig = px.violin(
                    y=df[column].dropna(),
                    box=True,
                    title=f'Violin Plot of {column}',
                    template='plotly_dark'
                )
            
            # Update layout for dark theme
            fig.update_layout(self.dark_template['layout'])
            
            result = {
                'plot_type': 'violin',
                'plot_json': fig.to_json(),
                'plot_html': fig.to_html(include_plotlyjs=True),
                'column': column,
                'group_by': group_by
            }
            
            # Save visualization
            self.save_visualization(dataset_id, 'violin', column, result)
            
            return {'success': True, 'result': result}
            
        except Exception as e:
            current_app.logger.error(f"Violin plot error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def density_plot(self, dataset_id, column):
        try:
            dataset = Dataset.query.get_or_404(dataset_id)
            df = self.data_processor.load_dataset(dataset)
            
            if column not in df.columns:
                return {'success': False, 'error': f'Column {column} not found'}
            
            data = df[column].dropna()
            
            if not pd.api.types.is_numeric_dtype(data):
                return {'success': False, 'error': f'Column {column} is not numeric'}
            
            # Create density plot using distplot
            fig = ff.create_distplot(
                [data.values],
                [column],
                bin_size=0.2,
                show_hist=False,
                show_rug=False
            )
            
            fig.update_layout(
                title=f'Density Plot of {column}',
                **self.dark_template['layout']
            )
            
            result = {
                'plot_type': 'density',
                'plot_json': fig.to_json(),
                'plot_html': fig.to_html(include_plotlyjs=True),
                'column': column
            }
            
            # Save visualization
            self.save_visualization(dataset_id, 'density', column, result)
            
            return {'success': True, 'result': result}
            
        except Exception as e:
            current_app.logger.error(f"Density plot error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def qq_plot(self, dataset_id, column, distribution='norm'):
        try:
            dataset = Dataset.query.get_or_404(dataset_id)
            df = self.data_processor.load_dataset(dataset)
            
            if column not in df.columns:
                return {'success': False, 'error': f'Column {column} not found'}
            
            data = df[column].dropna()
            
            if not pd.api.types.is_numeric_dtype(data):
                return {'success': False, 'error': f'Column {column} is not numeric'}
            
            # Create Q-Q plot
            fig = go.Figure()
            
            # Calculate theoretical quantiles
            from scipy import stats as scipy_stats
            if distribution == 'norm':
                theoretical_quantiles = scipy_stats.norm.ppf(np.linspace(0.01, 0.99, len(data)))
                dist_name = 'Normal'
            else:
                theoretical_quantiles = scipy_stats.norm.ppf(np.linspace(0.01, 0.99, len(data)))
                dist_name = 'Normal'
            
            sample_quantiles = np.sort(data)
            
            # Add scatter plot
            fig.add_trace(go.Scatter(
                x=theoretical_quantiles,
                y=sample_quantiles,
                mode='markers',
                name='Data points',
                marker=dict(color='#667eea')
            ))
            
            # Add reference line
            min_val = min(min(theoretical_quantiles), min(sample_quantiles))
            max_val = max(max(theoretical_quantiles), max(sample_quantiles))
            
            fig.add_trace(go.Scatter(
                x=[min_val, max_val],
                y=[min_val, max_val],
                mode='lines',
                name='Reference line',
                line=dict(color='#f5576c', dash='dash')
            ))
            
            fig.update_layout(
                title=f'Q-Q Plot: {column} vs {dist_name} Distribution',
                xaxis_title=f'Theoretical Quantiles ({dist_name})',
                yaxis_title=f'Sample Quantiles ({column})',
                **self.dark_template['layout']
            )
            
            result = {
                'plot_type': 'qq_plot',
                'plot_json': fig.to_json(),
                'plot_html': fig.to_html(include_plotlyjs=True),
                'column': column,
                'distribution': distribution
            }
            
            # Save visualization
            self.save_visualization(dataset_id, 'qq_plot', column, result)
            
            return {'success': True, 'result': result}
            
        except Exception as e:
            current_app.logger.error(f"Q-Q plot error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def pairplot(self, dataset_id, columns=None, hue=None):
        try:
            dataset = Dataset.query.get_or_404(dataset_id)
            df = self.data_processor.load_dataset(dataset)
            
            if columns:
                if not all(col in df.columns for col in columns):
                    return {'success': False, 'error': 'Some columns not found'}
                df_subset = df[columns]
            else:
                df_subset = df.select_dtypes(include=[np.number])
            
            if df_subset.empty:
                return {'success': False, 'error': 'No numeric columns found'}
            
            # Limit to 6 columns for performance
            if len(df_subset.columns) > 6:
                df_subset = df_subset.iloc[:, :6]
            
            # Create pairplot using plotly
            dims = df_subset.columns.tolist()
            
            fig = go.Figure(data=go.Splom(
                dimensions=[dict(label=col, values=df_subset[col]) for col in dims],
                text=df[hue] if hue and hue in df.columns else None,
                marker=dict(
                    color=df[hue] if hue and hue in df.columns else '#667eea',
                    colorscale='Viridis',
                    size=5,
                    line=dict(width=0.5, color='rgba(230,230,230,0.5)')
                )
            ))
            
            fig.update_layout(
                title='Pairplot Matrix',
                dragmode='select',
                width=800,
                height=800,
                hovermode='closest',
                **self.dark_template['layout']
            )
            
            result = {
                'plot_type': 'pairplot',
                'plot_json': fig.to_json(),
                'plot_html': fig.to_html(include_plotlyjs=True),
                'columns': dims,
                'hue': hue
            }
            
            # Save visualization
            self.save_visualization(dataset_id, 'pairplot', 'matrix', result)
            
            return {'success': True, 'result': result}
            
        except Exception as e:
            current_app.logger.error(f"Pairplot error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def jointplot(self, dataset_id, x_column, y_column, kind='scatter'):
        try:
            dataset = Dataset.query.get_or_404(dataset_id)
            df = self.data_processor.load_dataset(dataset)
            
            if x_column not in df.columns or y_column not in df.columns:
                return {'success': False, 'error': 'Required columns not found'}
            
            clean_data = df[[x_column, y_column]].dropna()
            
            # Create subplots
            fig = make_subplots(
                rows=2, cols=2,
                column_widths=[0.7, 0.3],
                row_heights=[0.3, 0.7],
                specs=[[{'secondary_y': False}, {'secondary_y': False}],
                       [{'secondary_y': False}, {'secondary_y': False}]],
                horizontal_spacing=0.02,
                vertical_spacing=0.02
            )
            
            # Main scatter plot
            if kind == 'scatter':
                fig.add_trace(
                    go.Scatter(
                        x=clean_data[x_column],
                        y=clean_data[y_column],
                        mode='markers',
                        marker=dict(color='#667eea', opacity=0.6),
                        name='Data'
                    ),
                    row=2, col=1
                )
            
            # X distribution (top)
            fig.add_trace(
                go.Histogram(
                    x=clean_data[x_column],
                    nbinsx=30,
                    marker_color='#764ba2',
                    showlegend=False
                ),
                row=1, col=1
            )
            
            # Y distribution (right)
            fig.add_trace(
                go.Histogram(
                    y=clean_data[y_column],
                    nbinsy=30,
                    marker_color='#f093fb',
                    showlegend=False
                ),
                row=2, col=2
            )
            
            fig.update_layout(
                title=f'Joint Plot: {x_column} vs {y_column}',
                **self.dark_template['layout']
            )
            
            result = {
                'plot_type': 'jointplot',
                'plot_json': fig.to_json(),
                'plot_html': fig.to_html(include_plotlyjs=True),
                'x_column': x_column,
                'y_column': y_column,
                'kind': kind
            }
            
            # Save visualization
            self.save_visualization(dataset_id, 'jointplot', f'{x_column}_vs_{y_column}', result)
            
            return {'success': True, 'result': result}
            
        except Exception as e:
            current_app.logger.error(f"Joint plot error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def swarm_plot(self, dataset_id, x_column, y_column):
        try:
            dataset = Dataset.query.get_or_404(dataset_id)
            df = self.data_processor.load_dataset(dataset)
            
            if x_column not in df.columns or y_column not in df.columns:
                return {'success': False, 'error': 'Required columns not found'}
            
            # Create swarm plot (approximated with jittered strip plot)
            fig = px.strip(
                df,
                x=x_column,
                y=y_column,
                title=f'Swarm Plot: {y_column} by {x_column}',
                template='plotly_dark'
            )
            
            # Update layout for dark theme
            fig.update_layout(self.dark_template['layout'])
            
            result = {
                'plot_type': 'swarm',
                'plot_json': fig.to_json(),
                'plot_html': fig.to_html(include_plotlyjs=True),
                'x_column': x_column,
                'y_column': y_column
            }
            
            # Save visualization
            self.save_visualization(dataset_id, 'swarm', f'{y_column}_by_{x_column}', result)
            
            return {'success': True, 'result': result}
            
        except Exception as e:
            current_app.logger.error(f"Swarm plot error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def strip_plot(self, dataset_id, x_column, y_column):
        try:
            dataset = Dataset.query.get_or_404(dataset_id)
            df = self.data_processor.load_dataset(dataset)
            
            if x_column not in df.columns or y_column not in df.columns:
                return {'success': False, 'error': 'Required columns not found'}
            
            # Create strip plot
            fig = px.strip(
                df,
                x=x_column,
                y=y_column,
                title=f'Strip Plot: {y_column} by {x_column}',
                template='plotly_dark'
            )
            
            # Update layout for dark theme
            fig.update_layout(self.dark_template['layout'])
            
            result = {
                'plot_type': 'strip',
                'plot_json': fig.to_json(),
                'plot_html': fig.to_html(include_plotlyjs=True),
                'x_column': x_column,
                'y_column': y_column
            }
            
            # Save visualization
            self.save_visualization(dataset_id, 'strip', f'{y_column}_by_{x_column}', result)
            
            return {'success': True, 'result': result}
            
        except Exception as e:
            current_app.logger.error(f"Strip plot error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def scatter_3d(self, dataset_id, x_column, y_column, z_column, color_column=None):
        try:
            dataset = Dataset.query.get_or_404(dataset_id)
            df = self.data_processor.load_dataset(dataset)
            
            required_cols = [x_column, y_column, z_column]
            if not all(col in df.columns for col in required_cols):
                return {'success': False, 'error': 'Required columns not found'}
            
            # Create 3D scatter plot
            fig = px.scatter_3d(
                df,
                x=x_column,
                y=y_column,
                z=z_column,
                color=color_column,
                title=f'3D Scatter Plot: {x_column}, {y_column}, {z_column}',
                template='plotly_dark'
            )
            
            # Update layout for dark theme
            fig.update_layout(self.dark_template['layout'])
            
            result = {
                'plot_type': 'scatter_3d',
                'plot_json': fig.to_json(),
                'plot_html': fig.to_html(include_plotlyjs=True),
                'x_column': x_column,
                'y_column': y_column,
                'z_column': z_column,
                'color_column': color_column
            }
            
            # Save visualization
            self.save_visualization(dataset_id, 'scatter_3d', f'{x_column}_{y_column}_{z_column}', result)
            
            return {'success': True, 'result': result}
            
        except Exception as e:
            current_app.logger.error(f"3D scatter plot error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def sunburst(self, dataset_id, path_columns, value_column=None):
        try:
            dataset = Dataset.query.get_or_404(dataset_id)
            df = self.data_processor.load_dataset(dataset)
            
            if not all(col in df.columns for col in path_columns):
                return {'success': False, 'error': 'Some path columns not found'}
            
            # Prepare data for sunburst
            if value_column and value_column in df.columns:
                # Use value column for sizing
                fig = px.sunburst(
                    df,
                    path=path_columns,
                    values=value_column,
                    title=f'Sunburst Chart: {" → ".join(path_columns)}',
                    template='plotly_dark'
                )
            else:
                # Use count for sizing
                fig = px.sunburst(
                    df,
                    path=path_columns,
                    title=f'Sunburst Chart: {" → ".join(path_columns)}',
                    template='plotly_dark'
                )
            
            # Update layout for dark theme
            fig.update_layout(self.dark_template['layout'])
            
            result = {
                'plot_type': 'sunburst',
                'plot_json': fig.to_json(),
                'plot_html': fig.to_html(include_plotlyjs=True),
                'path_columns': path_columns,
                'value_column': value_column
            }
            
            # Save visualization
            self.save_visualization(dataset_id, 'sunburst', '_'.join(path_columns), result)
            
            return {'success': True, 'result': result}
            
        except Exception as e:
            current_app.logger.error(f"Sunburst chart error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def treemap(self, dataset_id, path_columns, value_column=None):
        try:
            dataset = Dataset.query.get_or_404(dataset_id)
            df = self.data_processor.load_dataset(dataset)
            
            if not all(col in df.columns for col in path_columns):
                return {'success': False, 'error': 'Some path columns not found'}
            
            # Prepare data for treemap
            if value_column and value_column in df.columns:
                # Use value column for sizing
                fig = px.treemap(
                    df,
                    path=path_columns,
                    values=value_column,
                    title=f'Treemap: {" → ".join(path_columns)}',
                    template='plotly_dark'
                )
            else:
                # Use count for sizing
                fig = px.treemap(
                    df,
                    path=path_columns,
                    title=f'Treemap: {" → ".join(path_columns)}',
                    template='plotly_dark'
                )
            
            # Update layout for dark theme
            fig.update_layout(self.dark_template['layout'])
            
            result = {
                'plot_type': 'treemap',
                'plot_json': fig.to_json(),
                'plot_html': fig.to_html(include_plotlyjs=True),
                'path_columns': path_columns,
                'value_column': value_column
            }
            
            # Save visualization
            self.save_visualization(dataset_id, 'treemap', '_'.join(path_columns), result)
            
            return {'success': True, 'result': result}
            
        except Exception as e:
            current_app.logger.error(f"Treemap error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def get_available_plots(self, dataset_id):
        try:
            dataset = Dataset.query.get_or_404(dataset_id)
            df = self.data_processor.load_dataset(dataset)
            
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            categorical_cols = df.select_dtypes(include=['object']).columns.tolist()
            datetime_cols = df.select_dtypes(include=['datetime64']).columns.tolist()
            
            available_plots = {}
            
            # Univariate plots
            available_plots['univariate'] = {
                'numerical': [
                    {'name': 'histogram', 'description': 'Distribution of values', 'requires': 'numeric_column'},
                    {'name': 'boxplot', 'description': 'Summary statistics and outliers', 'requires': 'numeric_column'},
                    {'name': 'violin', 'description': 'Distribution shape and density', 'requires': 'numeric_column'},
                    {'name': 'density', 'description': 'Probability density', 'requires': 'numeric_column'},
                    {'name': 'qq_plot', 'description': 'Normality assessment', 'requires': 'numeric_column'}
                ] if numeric_cols else [],
                'categorical': [
                    {'name': 'bar_chart', 'description': 'Category frequencies', 'requires': 'categorical_column'},
                    {'name': 'pie_chart', 'description': 'Proportion of categories', 'requires': 'categorical_column'}
                ] if categorical_cols else []
            }
            
            # Bivariate plots
            available_plots['bivariate'] = {
                'numerical_numerical': [
                    {'name': 'scatter', 'description': 'Relationship between variables', 'requires': '2_numeric_columns'},
                    {'name': 'line', 'description': 'Trend over sequence', 'requires': '2_numeric_columns'},
                    {'name': 'jointplot', 'description': 'Joint distribution', 'requires': '2_numeric_columns'}
                ] if len(numeric_cols) >= 2 else [],
                'numerical_categorical': [
                    {'name': 'boxplot_grouped', 'description': 'Compare distributions by group', 'requires': 'numeric_and_categorical'},
                    {'name': 'violin_grouped', 'description': 'Distribution shape by group', 'requires': 'numeric_and_categorical'},
                    {'name': 'strip', 'description': 'Individual points by group', 'requires': 'numeric_and_categorical'}
                ] if numeric_cols and categorical_cols else [],
                'categorical_categorical': [
                    {'name': 'heatmap_crosstab', 'description': 'Cross-tabulation heatmap', 'requires': '2_categorical_columns'}
                ] if len(categorical_cols) >= 2 else []
            }
            
            # Multivariate plots
            available_plots['multivariate'] = {
                'general': [
                    {'name': 'pairplot', 'description': 'Pairwise relationships', 'requires': 'multiple_numeric_columns'},
                    {'name': 'heatmap', 'description': 'Correlation matrix', 'requires': 'multiple_numeric_columns'},
                    {'name': 'scatter_3d', 'description': '3D relationships', 'requires': '3_numeric_columns'}
                ] if len(numeric_cols) >= 2 else [],
                'hierarchical': [
                    {'name': 'sunburst', 'description': 'Hierarchical data structure', 'requires': 'multiple_categorical_columns'},
                    {'name': 'treemap', 'description': 'Hierarchical proportions', 'requires': 'multiple_categorical_columns'}
                ] if len(categorical_cols) >= 2 else []
            }
            
            # Time series plots
            if datetime_cols:
                available_plots['time_series'] = [
                    {'name': 'line_time', 'description': 'Time series plot', 'requires': 'datetime_and_numeric'},
                    {'name': 'area_chart', 'description': 'Area under curve over time', 'requires': 'datetime_and_numeric'}
                ]
            
            # Calculate total available plots
            total_plots = 0
            for category in available_plots.values():
                if isinstance(category, dict):
                    for subcategory in category.values():
                        total_plots += len(subcategory)
                else:
                    total_plots += len(category)
            
            return {
                'success': True,
                'available_plots': available_plots,
                'total_plots': total_plots,
                'dataset_info': {
                    'numeric_columns': len(numeric_cols),
                    'categorical_columns': len(categorical_cols),
                    'datetime_columns': len(datetime_cols),
                    'total_columns': len(df.columns)
                }
            }
            
        except Exception as e:
            current_app.logger.error(f"Get available plots error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def get_plot_recommendations(self, dataset_id, columns=None):
        try:
            dataset = Dataset.query.get_or_404(dataset_id)
            df = self.data_processor.load_dataset(dataset)
            
            if columns:
                df_subset = df[columns]
            else:
                df_subset = df
            
            recommendations = []
            
            numeric_cols = df_subset.select_dtypes(include=[np.number]).columns.tolist()
            categorical_cols = df_subset.select_dtypes(include=['object']).columns.tolist()
            
            # Univariate recommendations
            for col in numeric_cols[:3]:  # Limit to first 3
                recommendations.append({
                    'plot_type': 'histogram',
                    'priority': 'high',
                    'reason': 'Understand distribution shape',
                    'columns': [col],
                    'description': f'Visualize distribution of {col}'
                })
            
            for col in categorical_cols[:2]:  # Limit to first 2
                unique_count = df[col].nunique()
                if unique_count <= 10:
                    recommendations.append({
                        'plot_type': 'pie_chart',
                        'priority': 'medium',
                        'reason': 'Show category proportions',
                        'columns': [col],
                        'description': f'Show distribution of {col}'
                    })
                else:
                    recommendations.append({
                        'plot_type': 'bar_chart',
                        'priority': 'medium',
                        'reason': 'Too many categories for pie chart',
                        'columns': [col],
                        'description': f'Show top categories in {col}'
                    })
            
            # Bivariate recommendations
            if len(numeric_cols) >= 2:
                # Find highest correlation pair
                corr_matrix = df[numeric_cols].corr()
                max_corr = 0
                best_pair = None
                
                for i in range(len(numeric_cols)):
                    for j in range(i+1, len(numeric_cols)):
                        corr_val = abs(corr_matrix.iloc[i, j])
                        if corr_val > max_corr:
                            max_corr = corr_val
                            best_pair = (numeric_cols[i], numeric_cols[j])
                
                if best_pair and max_corr > 0.3:
                    recommendations.append({
                        'plot_type': 'scatter',
                        'priority': 'high',
                        'reason': f'Strong correlation ({max_corr:.2f})',
                        'columns': list(best_pair),
                        'description': f'Explore relationship between {best_pair[0]} and {best_pair[1]}'
                    })
            
            # Group comparison recommendations
            for cat_col in categorical_cols[:2]:
                for num_col in numeric_cols[:2]:
                    unique_groups = df[cat_col].nunique()
                    if 2 <= unique_groups <= 6:
                        recommendations.append({
                            'plot_type': 'boxplot',
                            'priority': 'medium',
                            'reason': f'Compare {num_col} across {unique_groups} groups',
                            'columns': [num_col, cat_col],
                            'description': f'Compare {num_col} distribution by {cat_col}'
                        })
            
            # Multivariate recommendations
            if len(numeric_cols) >= 3:
                recommendations.append({
                    'plot_type': 'heatmap',
                    'priority': 'high',
                    'reason': 'Identify correlation patterns',
                    'columns': numeric_cols[:6],  # Limit for readability
                    'description': 'Correlation matrix of numeric variables'
                })
            
            if len(numeric_cols) >= 4:
                recommendations.append({
                    'plot_type': 'pairplot',
                    'priority': 'medium',
                    'reason': 'Comprehensive pairwise analysis',
                    'columns': numeric_cols[:5],  # Limit for performance
                    'description': 'Pairwise relationships matrix'
                })
            
            # Sort by priority
            priority_order = {'high': 3, 'medium': 2, 'low': 1}
            recommendations.sort(key=lambda x: priority_order.get(x['priority'], 0), reverse=True)
            
            return {
                'success': True,
                'recommendations': recommendations[:8],  # Limit to top 8
                'summary': {
                    'total_recommendations': len(recommendations),
                    'high_priority': len([r for r in recommendations if r['priority'] == 'high']),
                    'medium_priority': len([r for r in recommendations if r['priority'] == 'medium']),
                    'low_priority': len([r for r in recommendations if r['priority'] == 'low'])
                }
            }
            
        except Exception as e:
            current_app.logger.error(f"Plot recommendations error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def save_visualization(self, dataset_id, plot_type, identifier, result):
        try:
            # Save visualization result to database
            analysis = Analysis(
                dataset_id=dataset_id,
                analysis_type=f'visualization_{plot_type}',
                parameters={'identifier': identifier, 'plot_type': plot_type},
                results=result,
                status='completed'
            )
            db.session.add(analysis)
            db.session.commit()
            
        except Exception as e:
            current_app.logger.error(f"Save visualization error: {str(e)}")
