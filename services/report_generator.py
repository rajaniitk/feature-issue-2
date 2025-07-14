import pandas as pd
import numpy as np
from datetime import datetime
import os
import json
from jinja2 import Template
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import logging
from models import Dataset, Analysis, MLModel, Report, db
from services.data_processor import DataProcessor
from services.analysis_engine import AnalysisEngine
from services.insights_generator import InsightsGenerator
from flask import current_app
import io
import base64

class ReportGenerator:
    def __init__(self):
        self.data_processor = DataProcessor()
        self.analysis_engine = AnalysisEngine()
        self.insights_generator = InsightsGenerator()
        self.reports_dir = 'reports'
        self.ensure_reports_dir()
        
        # Set up matplotlib for dark theme
        plt.style.use('dark_background')
        sns.set_theme(style="darkgrid")
    
    def ensure_reports_dir(self):
        if not os.path.exists(self.reports_dir):
            os.makedirs(self.reports_dir)
    
    def generate_report(self, dataset_id, report_type='comprehensive', sections=None, format_type='html'):
        try:
            dataset = Dataset.query.get_or_404(dataset_id)
            
            # Generate report content based on type
            if report_type == 'comprehensive':
                content = self.generate_comprehensive_report(dataset_id)
            elif report_type == 'eda':
                content = self.generate_eda_report(dataset_id)
            elif report_type == 'statistical':
                content = self.generate_statistical_report(dataset_id)
            elif report_type == 'ml_models':
                content = self.generate_ml_models_report(dataset_id)
            elif report_type == 'feature_engineering':
                content = self.generate_feature_engineering_report(dataset_id)
            else:
                return {'success': False, 'error': f'Unknown report type: {report_type}'}
            
            # Generate file
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'{report_type}_report_{dataset_id}_{timestamp}.{format_type}'
            file_path = os.path.join(self.reports_dir, filename)
            
            if format_type == 'html':
                self.generate_html_report(content, file_path)
            elif format_type == 'pdf':
                self.generate_pdf_report(content, file_path)
            else:
                return {'success': False, 'error': f'Unsupported format: {format_type}'}
            
            # Save report record
            report = Report(
                dataset_id=dataset_id,
                report_type=report_type,
                title=content['title'],
                content=json.dumps(content),
                file_path=file_path,
                file_size=os.path.getsize(file_path),
                status='completed'
            )
            
            db.session.add(report)
            db.session.commit()
            
            return {
                'success': True,
                'report_id': report.id,
                'file_path': file_path,
                'file_size': report.file_size
            }
            
        except Exception as e:
            current_app.logger.error(f"Report generation error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def generate_comprehensive_report(self, dataset_id):
        try:
            dataset = Dataset.query.get_or_404(dataset_id)
            df = self.data_processor.load_dataset(dataset)
            
            # Get all analyses
            eda_results = self.analysis_engine.run_comprehensive_eda(dataset_id)
            insights_results = self.insights_generator.generate_comprehensive_insights(dataset_id)
            
            # Get ML models
            ml_models = MLModel.query.filter_by(dataset_id=dataset_id).all()
            
            content = {
                'title': f'Comprehensive Data Analysis Report - {dataset.original_filename}',
                'dataset_info': {
                    'filename': dataset.original_filename,
                    'upload_date': dataset.upload_timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                    'rows': dataset.rows,
                    'columns': dataset.columns,
                    'file_size': dataset.file_size,
                    'memory_usage': dataset.memory_usage
                },
                'executive_summary': self.generate_executive_summary(dataset_id),
                'data_overview': self.generate_data_overview(df),
                'data_quality': self.generate_data_quality_section(df),
                'statistical_analysis': eda_results.get('results', {}) if eda_results['success'] else {},
                'insights': insights_results.get('results', {}) if insights_results['success'] else {},
                'visualizations': self.generate_visualizations_section(df),
                'ml_models': self.generate_ml_models_section(ml_models),
                'recommendations': self.generate_recommendations_section(dataset_id),
                'appendix': self.generate_appendix_section(df)
            }
            
            return content
            
        except Exception as e:
            current_app.logger.error(f"Comprehensive report generation error: {str(e)}")
            return {'title': 'Error generating report', 'error': str(e)}
    
    def generate_eda_report(self, dataset_id):
        try:
            dataset = Dataset.query.get_or_404(dataset_id)
            df = self.data_processor.load_dataset(dataset)
            
            # Run EDA
            eda_results = self.analysis_engine.run_comprehensive_eda(dataset_id)
            
            content = {
                'title': f'Exploratory Data Analysis Report - {dataset.original_filename}',
                'dataset_info': {
                    'filename': dataset.original_filename,
                    'rows': dataset.rows,
                    'columns': dataset.columns,
                    'upload_date': dataset.upload_timestamp.strftime('%Y-%m-%d %H:%M:%S')
                },
                'data_overview': self.generate_data_overview(df),
                'basic_statistics': eda_results.get('results', {}).get('basic_stats', {}),
                'missing_values': eda_results.get('results', {}).get('missing_analysis', {}),
                'correlations': eda_results.get('results', {}).get('correlations', {}),
                'distributions': eda_results.get('results', {}).get('skew_kurt', {}),
                'outliers': eda_results.get('results', {}).get('outliers', {}),
                'duplicates': eda_results.get('results', {}).get('duplicates', {}),
                'data_types': eda_results.get('results', {}).get('dtypes_analysis', {}),
                'visualizations': self.generate_eda_visualizations(df)
            }
            
            return content
            
        except Exception as e:
            current_app.logger.error(f"EDA report generation error: {str(e)}")
            return {'title': 'Error generating EDA report', 'error': str(e)}
    
    def generate_statistical_report(self, dataset_id):
        try:
            dataset = Dataset.query.get_or_404(dataset_id)
            df = self.data_processor.load_dataset(dataset)
            
            # Get statistical analyses
            analyses = Analysis.query.filter_by(dataset_id=dataset_id).all()
            
            content = {
                'title': f'Statistical Analysis Report - {dataset.original_filename}',
                'dataset_info': {
                    'filename': dataset.original_filename,
                    'rows': dataset.rows,
                    'columns': dataset.columns
                },
                'descriptive_statistics': self.generate_descriptive_stats(df),
                'inferential_statistics': self.generate_inferential_stats(analyses),
                'hypothesis_tests': self.generate_hypothesis_tests(analyses),
                'correlation_analysis': self.generate_correlation_analysis(df),
                'distribution_analysis': self.generate_distribution_analysis(df),
                'statistical_visualizations': self.generate_statistical_visualizations(df)
            }
            
            return content
            
        except Exception as e:
            current_app.logger.error(f"Statistical report generation error: {str(e)}")
            return {'title': 'Error generating statistical report', 'error': str(e)}
    
    def generate_ml_models_report(self, dataset_id):
        try:
            dataset = Dataset.query.get_or_404(dataset_id)
            ml_models = MLModel.query.filter_by(dataset_id=dataset_id).all()
            
            content = {
                'title': f'Machine Learning Models Report - {dataset.original_filename}',
                'dataset_info': {
                    'filename': dataset.original_filename,
                    'rows': dataset.rows,
                    'columns': dataset.columns
                },
                'models_overview': self.generate_models_overview(ml_models),
                'model_performance': self.generate_model_performance(ml_models),
                'feature_importance': self.generate_feature_importance_analysis(ml_models),
                'model_comparison': self.generate_model_comparison(ml_models),
                'recommendations': self.generate_ml_recommendations(ml_models)
            }
            
            return content
            
        except Exception as e:
            current_app.logger.error(f"ML models report generation error: {str(e)}")
            return {'title': 'Error generating ML models report', 'error': str(e)}
    
    def generate_feature_engineering_report(self, dataset_id):
        try:
            dataset = Dataset.query.get_or_404(dataset_id)
            df = self.data_processor.load_dataset(dataset)
            
            # Get feature engineering analyses
            analyses = Analysis.query.filter_by(dataset_id=dataset_id).filter(
                Analysis.analysis_type.in_(['pca', 'rfe', 'feature_selection', 'dimensionality_reduction'])
            ).all()
            
            content = {
                'title': f'Feature Engineering Report - {dataset.original_filename}',
                'dataset_info': {
                    'filename': dataset.original_filename,
                    'rows': dataset.rows,
                    'columns': dataset.columns
                },
                'feature_overview': self.generate_feature_overview(df),
                'dimensionality_reduction': self.generate_dimensionality_reduction_section(analyses),
                'feature_selection': self.generate_feature_selection_section(analyses),
                'feature_importance': self.generate_feature_importance_section(analyses),
                'feature_transformations': self.generate_feature_transformations_section(analyses),
                'recommendations': self.generate_feature_recommendations(df)
            }
            
            return content
            
        except Exception as e:
            current_app.logger.error(f"Feature engineering report generation error: {str(e)}")
            return {'title': 'Error generating feature engineering report', 'error': str(e)}
    
    def generate_executive_summary(self, dataset_id):
        try:
            insights_results = self.insights_generator.generate_comprehensive_insights(dataset_id)
            
            if insights_results['success']:
                executive_summary = insights_results['results'].get('executive_summary', {})
                return {
                    'data_quality_score': executive_summary.get('data_quality_score', 0),
                    'key_findings': executive_summary.get('key_findings', []),
                    'priority_actions': executive_summary.get('priority_actions', []),
                    'dataset_overview': executive_summary.get('dataset_overview', {})
                }
            else:
                return {
                    'data_quality_score': 0,
                    'key_findings': [],
                    'priority_actions': [],
                    'dataset_overview': {}
                }
        except Exception as e:
            current_app.logger.error(f"Executive summary generation error: {str(e)}")
            return {}
    
    def generate_data_overview(self, df):
        try:
            overview = {
                'shape': df.shape,
                'columns': df.columns.tolist(),
                'dtypes': df.dtypes.astype(str).to_dict(),
                'missing_values': df.isnull().sum().to_dict(),
                'memory_usage': df.memory_usage(deep=True).sum() / (1024 * 1024),  # MB
                'duplicate_rows': df.duplicated().sum(),
                'numeric_columns': df.select_dtypes(include=[np.number]).columns.tolist(),
                'categorical_columns': df.select_dtypes(include=['object']).columns.tolist(),
                'datetime_columns': df.select_dtypes(include=['datetime64']).columns.tolist()
            }
            return overview
        except Exception as e:
            current_app.logger.error(f"Data overview generation error: {str(e)}")
            return {}
    
    def generate_data_quality_section(self, df):
        try:
            quality_metrics = {
                'completeness': (1 - df.isnull().sum().sum() / (len(df) * len(df.columns))) * 100,
                'uniqueness': (1 - df.duplicated().sum() / len(df)) * 100,
                'consistency': 100,  # Placeholder
                'accuracy': 100  # Placeholder
            }
            
            quality_issues = []
            
            # Missing values
            missing_cols = df.isnull().sum()
            high_missing = missing_cols[missing_cols > len(df) * 0.5]
            if not high_missing.empty:
                quality_issues.append({
                    'type': 'missing_values',
                    'severity': 'high',
                    'description': f'Columns with >50% missing values: {list(high_missing.index)}',
                    'affected_columns': list(high_missing.index)
                })
            
            # Duplicates
            if df.duplicated().sum() > 0:
                quality_issues.append({
                    'type': 'duplicates',
                    'severity': 'medium',
                    'description': f'{df.duplicated().sum()} duplicate rows found',
                    'count': df.duplicated().sum()
                })
            
            return {
                'quality_metrics': quality_metrics,
                'quality_issues': quality_issues,
                'overall_score': sum(quality_metrics.values()) / len(quality_metrics)
            }
        except Exception as e:
            current_app.logger.error(f"Data quality section generation error: {str(e)}")
            return {}
    
    def generate_visualizations_section(self, df):
        try:
            visualizations = []
            
            # Correlation heatmap
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            if len(numeric_cols) > 1:
                corr_matrix = df[numeric_cols].corr()
                fig = px.imshow(
                    corr_matrix,
                    title='Correlation Heatmap',
                    color_continuous_scale='RdBu',
                    aspect='auto'
                )
                visualizations.append({
                    'type': 'correlation_heatmap',
                    'title': 'Correlation Heatmap',
                    'plot_json': fig.to_json()
                })
            
            # Distribution plots for numeric columns
            for col in numeric_cols[:5]:  # Limit to first 5 columns
                fig = px.histogram(
                    df, x=col,
                    title=f'Distribution of {col}',
                    nbins=30
                )
                visualizations.append({
                    'type': 'histogram',
                    'title': f'Distribution of {col}',
                    'plot_json': fig.to_json()
                })
            
            # Box plots for outlier detection
            for col in numeric_cols[:5]:
                fig = px.box(
                    df, y=col,
                    title=f'Box Plot of {col}',
                    points='outliers'
                )
                visualizations.append({
                    'type': 'boxplot',
                    'title': f'Box Plot of {col}',
                    'plot_json': fig.to_json()
                })
            
            return visualizations
        except Exception as e:
            current_app.logger.error(f"Visualizations section generation error: {str(e)}")
            return []
    
    def generate_ml_models_section(self, ml_models):
        try:
            models_info = []
            
            for model in ml_models:
                model_info = {
                    'id': model.id,
                    'type': model.model_type,
                    'target': model.target_column,
                    'features': model.features,
                    'performance': model.performance_metrics,
                    'training_time': model.training_time,
                    'timestamp': model.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                    'status': model.status
                }
                models_info.append(model_info)
            
            return {
                'models': models_info,
                'total_models': len(ml_models),
                'model_types': list(set([m.model_type for m in ml_models]))
            }
        except Exception as e:
            current_app.logger.error(f"ML models section generation error: {str(e)}")
            return {}
    
    def generate_recommendations_section(self, dataset_id):
        try:
            insights_results = self.insights_generator.generate_comprehensive_insights(dataset_id)
            
            if insights_results['success']:
                recommendations = []
                
                # Extract recommendations from insights
                for category, insights in insights_results['results'].items():
                    if isinstance(insights, list):
                        for insight in insights:
                            if insight.get('recommendation'):
                                recommendations.append({
                                    'category': category,
                                    'type': insight.get('type', 'general'),
                                    'severity': insight.get('severity', 'medium'),
                                    'title': insight.get('title', 'Recommendation'),
                                    'message': insight.get('message', ''),
                                    'recommendation': insight.get('recommendation', ''),
                                    'action': insight.get('action', '')
                                })
                
                return {
                    'recommendations': recommendations,
                    'priority_recommendations': [r for r in recommendations if r['severity'] == 'high']
                }
            else:
                return {'recommendations': [], 'priority_recommendations': []}
        except Exception as e:
            current_app.logger.error(f"Recommendations section generation error: {str(e)}")
            return {}
    
    def generate_appendix_section(self, df):
        try:
            appendix = {
                'data_dictionary': {},
                'technical_details': {
                    'analysis_timestamp': datetime.now().isoformat(),
                    'analysis_version': '1.0',
                    'data_types': df.dtypes.astype(str).to_dict(),
                    'null_counts': df.isnull().sum().to_dict(),
                    'unique_counts': df.nunique().to_dict()
                },
                'column_profiles': {}
            }
            
            # Generate column profiles
            for col in df.columns:
                if pd.api.types.is_numeric_dtype(df[col]):
                    profile = {
                        'type': 'numeric',
                        'count': int(df[col].count()),
                        'mean': float(df[col].mean()) if not df[col].isna().all() else None,
                        'std': float(df[col].std()) if not df[col].isna().all() else None,
                        'min': float(df[col].min()) if not df[col].isna().all() else None,
                        'max': float(df[col].max()) if not df[col].isna().all() else None,
                        'quartiles': df[col].quantile([0.25, 0.5, 0.75]).to_dict()
                    }
                else:
                    profile = {
                        'type': 'categorical',
                        'count': int(df[col].count()),
                        'unique': int(df[col].nunique()),
                        'top_values': df[col].value_counts().head(10).to_dict()
                    }
                
                appendix['column_profiles'][col] = profile
            
            return appendix
        except Exception as e:
            current_app.logger.error(f"Appendix section generation error: {str(e)}")
            return {}
    
    def generate_html_report(self, content, file_path):
        try:
            html_template = """
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>{{ title }}</title>
                <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
                <style>
                    body {
                        background-color: #0a0a0a;
                        color: #ffffff;
                        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    }
                    .container {
                        background: rgba(255, 255, 255, 0.05);
                        border-radius: 15px;
                        padding: 30px;
                        margin: 20px auto;
                        backdrop-filter: blur(10px);
                        border: 1px solid rgba(255, 255, 255, 0.1);
                    }
                    .section {
                        margin-bottom: 40px;
                        padding: 20px;
                        background: rgba(255, 255, 255, 0.03);
                        border-radius: 10px;
                        border: 1px solid rgba(255, 255, 255, 0.1);
                    }
                    h1, h2, h3 {
                        color: #ffffff;
                        margin-bottom: 20px;
                    }
                    h1 {
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        -webkit-background-clip: text;
                        -webkit-text-fill-color: transparent;
                        background-clip: text;
                    }
                    .table-dark {
                        background: rgba(255, 255, 255, 0.05);
                        border: 1px solid rgba(255, 255, 255, 0.1);
                    }
                    .badge {
                        padding: 5px 10px;
                        border-radius: 20px;
                        font-size: 12px;
                    }
                    .badge-high { background: linear-gradient(135deg, #ff6b6b 0%, #ffa726 100%); }
                    .badge-medium { background: linear-gradient(135deg, #fa709a 0%, #fee140 100%); }
                    .badge-low { background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%); }
                    .badge-info { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
                    .metric-card {
                        background: rgba(255, 255, 255, 0.05);
                        border: 1px solid rgba(255, 255, 255, 0.1);
                        border-radius: 10px;
                        padding: 20px;
                        text-align: center;
                        margin-bottom: 20px;
                    }
                    .metric-value {
                        font-size: 2rem;
                        font-weight: bold;
                        color: #667eea;
                    }
                    .metric-label {
                        color: #b0b0b0;
                        font-size: 0.9rem;
                    }
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>{{ title }}</h1>
                    
                    {% if dataset_info %}
                    <div class="section">
                        <h2>Dataset Information</h2>
                        <div class="row">
                            <div class="col-md-3">
                                <div class="metric-card">
                                    <div class="metric-value">{{ dataset_info.rows|default(0) }}</div>
                                    <div class="metric-label">Rows</div>
                                </div>
                            </div>
                            <div class="col-md-3">
                                <div class="metric-card">
                                    <div class="metric-value">{{ dataset_info.columns|default(0) }}</div>
                                    <div class="metric-label">Columns</div>
                                </div>
                            </div>
                            <div class="col-md-3">
                                <div class="metric-card">
                                    <div class="metric-value">{{ "%.1f"|format(dataset_info.file_size|default(0) / 1024 / 1024) }} MB</div>
                                    <div class="metric-label">File Size</div>
                                </div>
                            </div>
                            <div class="col-md-3">
                                <div class="metric-card">
                                    <div class="metric-value">{{ "%.1f"|format(dataset_info.memory_usage|default(0) / 1024 / 1024) }} MB</div>
                                    <div class="metric-label">Memory Usage</div>
                                </div>
                            </div>
                        </div>
                        <p><strong>Filename:</strong> {{ dataset_info.filename|default('N/A') }}</p>
                        <p><strong>Upload Date:</strong> {{ dataset_info.upload_date|default('N/A') }}</p>
                    </div>
                    {% endif %}
                    
                    {% if executive_summary %}
                    <div class="section">
                        <h2>Executive Summary</h2>
                        <div class="row">
                            <div class="col-md-6">
                                <div class="metric-card">
                                    <div class="metric-value">{{ executive_summary.data_quality_score|default(0) }}</div>
                                    <div class="metric-label">Data Quality Score</div>
                                </div>
                            </div>
                        </div>
                        
                        {% if executive_summary.key_findings %}
                        <h3>Key Findings</h3>
                        <ul>
                            {% for finding in executive_summary.key_findings %}
                            <li>
                                <span class="badge badge-{{ finding.severity|default('info') }}">{{ finding.severity|default('info')|upper }}</span>
                                <strong>{{ finding.title|default('Finding') }}:</strong> {{ finding.message|default('') }}
                            </li>
                            {% endfor %}
                        </ul>
                        {% endif %}
                        
                        {% if executive_summary.priority_actions %}
                        <h3>Priority Actions</h3>
                        <ul>
                            {% for action in executive_summary.priority_actions %}
                            <li>
                                <span class="badge badge-{{ action.severity|default('high') }}">{{ action.severity|default('high')|upper }}</span>
                                <strong>{{ action.title|default('Action') }}:</strong> {{ action.recommendation|default('') }}
                            </li>
                            {% endfor %}
                        </ul>
                        {% endif %}
                    </div>
                    {% endif %}
                    
                    {% if data_overview %}
                    <div class="section">
                        <h2>Data Overview</h2>
                        <div class="row">
                            <div class="col-md-4">
                                <div class="metric-card">
                                    <div class="metric-value">{{ data_overview.numeric_columns|length|default(0) }}</div>
                                    <div class="metric-label">Numeric Columns</div>
                                </div>
                            </div>
                            <div class="col-md-4">
                                <div class="metric-card">
                                    <div class="metric-value">{{ data_overview.categorical_columns|length|default(0) }}</div>
                                    <div class="metric-label">Categorical Columns</div>
                                </div>
                            </div>
                            <div class="col-md-4">
                                <div class="metric-card">
                                    <div class="metric-value">{{ data_overview.duplicate_rows|default(0) }}</div>
                                    <div class="metric-label">Duplicate Rows</div>
                                </div>
                            </div>
                        </div>
                        
                        <h3>Column Information</h3>
                        <table class="table table-dark">
                            <thead>
                                <tr>
                                    <th>Column</th>
                                    <th>Data Type</th>
                                    <th>Missing Values</th>
                                    <th>Category</th>
                                </tr>
                            </thead>
                            <tbody>
                                {% for col in data_overview.columns %}
                                <tr>
                                    <td>{{ col }}</td>
                                    <td>{{ data_overview.dtypes[col]|default('unknown') }}</td>
                                    <td>{{ data_overview.missing_values[col]|default(0) }}</td>
                                    <td>
                                        {% if col in data_overview.numeric_columns %}
                                        <span class="badge badge-info">Numeric</span>
                                        {% elif col in data_overview.categorical_columns %}
                                        <span class="badge badge-medium">Categorical</span>
                                        {% else %}
                                        <span class="badge badge-low">Other</span>
                                        {% endif %}
                                    </td>
                                </tr>
                                {% endfor %}
                            </tbody>
                        </table>
                    </div>
                    {% endif %}
                    
                    {% if recommendations %}
                    <div class="section">
                        <h2>Recommendations</h2>
                        
                        {% if recommendations.priority_recommendations %}
                        <h3>Priority Recommendations</h3>
                        <ul>
                            {% for rec in recommendations.priority_recommendations %}
                            <li>
                                <span class="badge badge-{{ rec.severity|default('high') }}">{{ rec.severity|default('high')|upper }}</span>
                                <strong>{{ rec.title|default('Recommendation') }}:</strong> {{ rec.recommendation|default('') }}
                            </li>
                            {% endfor %}
                        </ul>
                        {% endif %}
                        
                        {% if recommendations.recommendations %}
                        <h3>All Recommendations</h3>
                        <table class="table table-dark">
                            <thead>
                                <tr>
                                    <th>Category</th>
                                    <th>Type</th>
                                    <th>Severity</th>
                                    <th>Title</th>
                                    <th>Recommendation</th>
                                </tr>
                            </thead>
                            <tbody>
                                {% for rec in recommendations.recommendations %}
                                <tr>
                                    <td>{{ rec.category|default('General') }}</td>
                                    <td>{{ rec.type|default('General') }}</td>
                                    <td><span class="badge badge-{{ rec.severity|default('medium') }}">{{ rec.severity|default('medium')|upper }}</span></td>
                                    <td>{{ rec.title|default('Recommendation') }}</td>
                                    <td>{{ rec.recommendation|default('') }}</td>
                                </tr>
                                {% endfor %}
                            </tbody>
                        </table>
                        {% endif %}
                    </div>
                    {% endif %}
                    
                    <div class="section">
                        <h2>Report Information</h2>
                        <p><strong>Generated:</strong> {{ datetime.now().strftime('%Y-%m-%d %H:%M:%S') }}</p>
                        <p><strong>Version:</strong> 1.0</p>
                    </div>
                </div>
                
                <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
            </body>
            </html>
            """
            
            from jinja2 import Template
            template = Template(html_template)
            html_content = template.render(**content, datetime=datetime)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
                
        except Exception as e:
            current_app.logger.error(f"HTML report generation error: {str(e)}")
            raise e
    
    def generate_pdf_report(self, content, file_path):
        try:
            doc = SimpleDocTemplate(file_path, pagesize=A4)
            styles = getSampleStyleSheet()
            story = []
            
            # Title
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Title'],
                fontSize=24,
                spaceAfter=30,
                alignment=TA_CENTER
            )
            story.append(Paragraph(content['title'], title_style))
            story.append(Spacer(1, 12))
            
            # Dataset Information
            if 'dataset_info' in content:
                story.append(Paragraph('Dataset Information', styles['Heading1']))
                
                data = [
                    ['Property', 'Value'],
                    ['Filename', content['dataset_info'].get('filename', 'N/A')],
                    ['Rows', str(content['dataset_info'].get('rows', 0))],
                    ['Columns', str(content['dataset_info'].get('columns', 0))],
                    ['File Size', f"{content['dataset_info'].get('file_size', 0) / 1024 / 1024:.1f} MB"],
                    ['Upload Date', content['dataset_info'].get('upload_date', 'N/A')]
                ]
                
                table = Table(data)
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 14),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                story.append(table)
                story.append(Spacer(1, 12))
            
            # Executive Summary
            if 'executive_summary' in content:
                story.append(Paragraph('Executive Summary', styles['Heading1']))
                
                if content['executive_summary'].get('data_quality_score'):
                    story.append(Paragraph(
                        f"Data Quality Score: {content['executive_summary']['data_quality_score']}/100",
                        styles['Normal']
                    ))
                
                if content['executive_summary'].get('key_findings'):
                    story.append(Paragraph('Key Findings:', styles['Heading2']))
                    for finding in content['executive_summary']['key_findings']:
                        story.append(Paragraph(
                            f"• {finding.get('title', 'Finding')}: {finding.get('message', '')}",
                            styles['Normal']
                        ))
                
                story.append(Spacer(1, 12))
            
            # Build PDF
            doc.build(story)
            
        except Exception as e:
            current_app.logger.error(f"PDF report generation error: {str(e)}")
            raise e
    
    def delete_report(self, report_id):
        try:
            report = Report.query.get_or_404(report_id)
            
            # Delete file
            if os.path.exists(report.file_path):
                os.remove(report.file_path)
            
            # Delete database record
            db.session.delete(report)
            db.session.commit()
            
            return {'success': True, 'message': 'Report deleted successfully'}
            
        except Exception as e:
            current_app.logger.error(f"Delete report error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def export_report(self, report_id, format_type):
        try:
            report = Report.query.get_or_404(report_id)
            
            if format_type == report.file_path.split('.')[-1]:
                return {'success': True, 'file_path': report.file_path}
            
            # Convert to different format
            content = json.loads(report.content)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'{report.report_type}_report_{report.dataset_id}_{timestamp}.{format_type}'
            file_path = os.path.join(self.reports_dir, filename)
            
            if format_type == 'html':
                self.generate_html_report(content, file_path)
            elif format_type == 'pdf':
                self.generate_pdf_report(content, file_path)
            else:
                return {'success': False, 'error': f'Unsupported format: {format_type}'}
            
            return {'success': True, 'file_path': file_path}
            
        except Exception as e:
            current_app.logger.error(f"Export report error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def generate_custom_report(self, dataset_id, template, parameters):
        try:
            # Custom report generation would be implemented here
            # For now, return a basic custom report
            
            dataset = Dataset.query.get_or_404(dataset_id)
            
            content = {
                'title': f'Custom Report - {dataset.original_filename}',
                'dataset_info': {
                    'filename': dataset.original_filename,
                    'rows': dataset.rows,
                    'columns': dataset.columns
                },
                'custom_content': template,
                'parameters': parameters
            }
            
            return {'success': True, 'content': content}
            
        except Exception as e:
            current_app.logger.error(f"Custom report generation error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    # Additional helper methods for specific report sections
    def generate_descriptive_stats(self, df):
        try:
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            if len(numeric_cols) > 0:
                return df[numeric_cols].describe().to_dict()
            return {}
        except Exception as e:
            current_app.logger.error(f"Descriptive stats generation error: {str(e)}")
            return {}
    
    def generate_inferential_stats(self, analyses):
        try:
            inferential_stats = []
            for analysis in analyses:
                if analysis.analysis_type in ['ttest', 'anova', 'chi_square']:
                    inferential_stats.append({
                        'type': analysis.analysis_type,
                        'results': analysis.results,
                        'timestamp': analysis.timestamp.isoformat()
                    })
            return inferential_stats
        except Exception as e:
            current_app.logger.error(f"Inferential stats generation error: {str(e)}")
            return []
    
    def generate_hypothesis_tests(self, analyses):
        try:
            hypothesis_tests = []
            for analysis in analyses:
                if 'test' in analysis.analysis_type.lower():
                    hypothesis_tests.append({
                        'test_name': analysis.analysis_type,
                        'results': analysis.results,
                        'timestamp': analysis.timestamp.isoformat()
                    })
            return hypothesis_tests
        except Exception as e:
            current_app.logger.error(f"Hypothesis tests generation error: {str(e)}")
            return []
    
    def generate_correlation_analysis(self, df):
        try:
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            if len(numeric_cols) > 1:
                return {
                    'pearson': df[numeric_cols].corr(method='pearson').to_dict(),
                    'spearman': df[numeric_cols].corr(method='spearman').to_dict()
                }
            return {}
        except Exception as e:
            current_app.logger.error(f"Correlation analysis generation error: {str(e)}")
            return {}
    
    def generate_distribution_analysis(self, df):
        try:
            distribution_analysis = {}
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            
            for col in numeric_cols:
                col_data = df[col].dropna()
                if len(col_data) > 0:
                    distribution_analysis[col] = {
                        'skewness': float(col_data.skew()),
                        'kurtosis': float(col_data.kurtosis()),
                        'normality_test': 'normal' if abs(col_data.skew()) < 0.5 else 'not_normal'
                    }
            
            return distribution_analysis
        except Exception as e:
            current_app.logger.error(f"Distribution analysis generation error: {str(e)}")
            return {}
    
    def generate_statistical_visualizations(self, df):
        try:
            visualizations = []
            
            # Q-Q plots for normality
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            for col in numeric_cols[:3]:  # Limit to first 3
                visualizations.append({
                    'type': 'qq_plot',
                    'title': f'Q-Q Plot of {col}',
                    'description': 'Assess normality of distribution'
                })
            
            return visualizations
        except Exception as e:
            current_app.logger.error(f"Statistical visualizations generation error: {str(e)}")
            return []
    
    def generate_models_overview(self, ml_models):
        try:
            overview = {
                'total_models': len(ml_models),
                'model_types': list(set([m.model_type for m in ml_models])),
                'targets': list(set([m.target_column for m in ml_models])),
                'avg_training_time': sum([m.training_time for m in ml_models]) / len(ml_models) if ml_models else 0
            }
            return overview
        except Exception as e:
            current_app.logger.error(f"Models overview generation error: {str(e)}")
            return {}
    
    def generate_model_performance(self, ml_models):
        try:
            performance = []
            for model in ml_models:
                perf = {
                    'model_id': model.id,
                    'model_type': model.model_type,
                    'target': model.target_column,
                    'metrics': model.performance_metrics,
                    'training_time': model.training_time
                }
                performance.append(perf)
            return performance
        except Exception as e:
            current_app.logger.error(f"Model performance generation error: {str(e)}")
            return []
    
    def generate_feature_importance_analysis(self, ml_models):
        try:
            feature_importance = {}
            for model in ml_models:
                if model.feature_importance:
                    feature_importance[f'{model.model_type}_{model.id}'] = model.feature_importance
            return feature_importance
        except Exception as e:
            current_app.logger.error(f"Feature importance analysis generation error: {str(e)}")
            return {}
    
    def generate_model_comparison(self, ml_models):
        try:
            comparison = []
            for model in ml_models:
                metrics = model.performance_metrics or {}
                comparison.append({
                    'model_type': model.model_type,
                    'target': model.target_column,
                    'accuracy': metrics.get('accuracy', metrics.get('r2_score', 0)),
                    'training_time': model.training_time
                })
            return comparison
        except Exception as e:
            current_app.logger.error(f"Model comparison generation error: {str(e)}")
            return []
    
    def generate_ml_recommendations(self, ml_models):
        try:
            recommendations = []
            
            if not ml_models:
                recommendations.append({
                    'type': 'no_models',
                    'message': 'No machine learning models found',
                    'recommendation': 'Train some models to get performance insights'
                })
                return recommendations
            
            # Find best performing model
            best_model = None
            best_score = -1
            
            for model in ml_models:
                metrics = model.performance_metrics or {}
                score = metrics.get('accuracy', metrics.get('r2_score', 0))
                if score > best_score:
                    best_score = score
                    best_model = model
            
            if best_model:
                recommendations.append({
                    'type': 'best_model',
                    'message': f'Best performing model: {best_model.model_type}',
                    'recommendation': f'Consider using {best_model.model_type} for production'
                })
            
            return recommendations
        except Exception as e:
            current_app.logger.error(f"ML recommendations generation error: {str(e)}")
            return []
    
    def generate_eda_visualizations(self, df):
        try:
            visualizations = []
            
            # Distribution plots
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            for col in numeric_cols[:5]:
                visualizations.append({
                    'type': 'histogram',
                    'title': f'Distribution of {col}',
                    'description': 'Shows the frequency distribution of values'
                })
            
            # Correlation heatmap
            if len(numeric_cols) > 1:
                visualizations.append({
                    'type': 'heatmap',
                    'title': 'Correlation Matrix',
                    'description': 'Shows relationships between numeric variables'
                })
            
            return visualizations
        except Exception as e:
            current_app.logger.error(f"EDA visualizations generation error: {str(e)}")
            return []
    
    def generate_feature_overview(self, df):
        try:
            overview = {
                'total_features': len(df.columns),
                'numeric_features': len(df.select_dtypes(include=[np.number]).columns),
                'categorical_features': len(df.select_dtypes(include=['object']).columns),
                'datetime_features': len(df.select_dtypes(include=['datetime64']).columns),
                'feature_list': df.columns.tolist()
            }
            return overview
        except Exception as e:
            current_app.logger.error(f"Feature overview generation error: {str(e)}")
            return {}
    
    def generate_dimensionality_reduction_section(self, analyses):
        try:
            dim_reduction = []
            for analysis in analyses:
                if analysis.analysis_type in ['pca', 'dimensionality_reduction']:
                    dim_reduction.append({
                        'type': analysis.analysis_type,
                        'results': analysis.results,
                        'timestamp': analysis.timestamp.isoformat()
                    })
            return dim_reduction
        except Exception as e:
            current_app.logger.error(f"Dimensionality reduction section generation error: {str(e)}")
            return []
    
    def generate_feature_selection_section(self, analyses):
        try:
            feature_selection = []
            for analysis in analyses:
                if analysis.analysis_type in ['feature_selection', 'rfe']:
                    feature_selection.append({
                        'type': analysis.analysis_type,
                        'results': analysis.results,
                        'timestamp': analysis.timestamp.isoformat()
                    })
            return feature_selection
        except Exception as e:
            current_app.logger.error(f"Feature selection section generation error: {str(e)}")
            return []
    
    def generate_feature_importance_section(self, analyses):
        try:
            feature_importance = []
            for analysis in analyses:
                if 'importance' in analysis.analysis_type.lower():
                    feature_importance.append({
                        'type': analysis.analysis_type,
                        'results': analysis.results,
                        'timestamp': analysis.timestamp.isoformat()
                    })
            return feature_importance
        except Exception as e:
            current_app.logger.error(f"Feature importance section generation error: {str(e)}")
            return []
    
    def generate_feature_transformations_section(self, analyses):
        try:
            transformations = []
            for analysis in analyses:
                if analysis.analysis_type in ['scaling', 'encoding', 'binning']:
                    transformations.append({
                        'type': analysis.analysis_type,
                        'results': analysis.results,
                        'timestamp': analysis.timestamp.isoformat()
                    })
            return transformations
        except Exception as e:
            current_app.logger.error(f"Feature transformations section generation error: {str(e)}")
            return []
    
    def generate_feature_recommendations(self, df):
        try:
            recommendations = []
            
            # High cardinality features
            for col in df.select_dtypes(include=['object']).columns:
                if df[col].nunique() > len(df) * 0.8:
                    recommendations.append({
                        'type': 'high_cardinality',
                        'feature': col,
                        'message': f'Feature {col} has high cardinality',
                        'recommendation': 'Consider dimensionality reduction or removal'
                    })
            
            # Low variance features
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            for col in numeric_cols:
                if df[col].var() < 0.01:
                    recommendations.append({
                        'type': 'low_variance',
                        'feature': col,
                        'message': f'Feature {col} has low variance',
                        'recommendation': 'Consider removing this feature'
                    })
            
            return recommendations
        except Exception as e:
            current_app.logger.error(f"Feature recommendations generation error: {str(e)}")
            return []
