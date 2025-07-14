import pandas as pd
import numpy as np
import json
import logging
from datetime import datetime
from models import Dataset, Analysis, db
from services.data_processor import DataProcessor
from flask import current_app
from scipy import stats
from sklearn.preprocessing import StandardScaler, LabelEncoder
import seaborn as sns
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import io
import base64

class AnalysisEngine:
    def __init__(self):
        self.data_processor = DataProcessor()
        plt.style.use('dark_background')
        sns.set_theme(style="darkgrid")
    
    def run_comprehensive_eda(self, dataset_id):
        try:
            dataset = Dataset.query.get_or_404(dataset_id)
            df = self.data_processor.load_dataset(dataset)
            
            # Basic statistics
            basic_stats = self.get_basic_statistics(df)
            
            # Correlation analysis
            correlations = self.get_correlations(df)
            
            # Missing values analysis
            missing_analysis = self.analyze_missing_values(df)
            
            # Data types analysis
            dtypes_analysis = self.analyze_data_types(df)
            
            # Outlier detection
            outliers = self.detect_all_outliers(df)
            
            # Skewness and kurtosis
            skew_kurt = self.analyze_skewness_kurtosis(df)
            
            # Duplicates analysis
            duplicates = self.analyze_duplicates(df)
            
            # Cardinality analysis
            cardinality = self.analyze_cardinality(df)
            
            # Variance analysis
            variance = self.analyze_variance(df)
            
            results = {
                'basic_stats': basic_stats,
                'correlations': correlations,
                'missing_analysis': missing_analysis,
                'dtypes_analysis': dtypes_analysis,
                'outliers': outliers,
                'skew_kurt': skew_kurt,
                'duplicates': duplicates,
                'cardinality': cardinality,
                'variance': variance,
                'summary': self.generate_eda_summary(df)
            }
            
            # Save analysis
            analysis = Analysis(
                dataset_id=dataset_id,
                analysis_type='comprehensive_eda',
                results=results,
                status='completed'
            )
            db.session.add(analysis)
            db.session.commit()
            
            return {'success': True, 'results': results}
            
        except Exception as e:
            current_app.logger.error(f"Comprehensive EDA error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def get_basic_statistics(self, df):
        stats = {}
        
        # Numerical columns
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 0:
            stats['numeric'] = df[numeric_cols].describe().to_dict()
        
        # Categorical columns
        categorical_cols = df.select_dtypes(include=['object']).columns
        if len(categorical_cols) > 0:
            stats['categorical'] = {}
            for col in categorical_cols:
                stats['categorical'][col] = {
                    'count': int(df[col].count()),
                    'unique': int(df[col].nunique()),
                    'top': df[col].mode().iloc[0] if not df[col].mode().empty else None,
                    'freq': int(df[col].value_counts().iloc[0]) if not df[col].value_counts().empty else 0
                }
        
        return stats
    
    def get_correlations(self, df):
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) < 2:
            return {}
        
        correlations = {
            'pearson': df[numeric_cols].corr(method='pearson').to_dict(),
            'spearman': df[numeric_cols].corr(method='spearman').to_dict(),
            'kendall': df[numeric_cols].corr(method='kendall').to_dict()
        }
        
        return correlations
    
    def analyze_missing_values(self, df):
        missing_data = df.isnull().sum()
        missing_percent = (missing_data / len(df)) * 100
        
        return {
            'missing_counts': missing_data.to_dict(),
            'missing_percentages': missing_percent.to_dict(),
            'total_missing': int(missing_data.sum()),
            'columns_with_missing': missing_data[missing_data > 0].index.tolist()
        }
    
    def analyze_data_types(self, df):
        dtypes = df.dtypes.to_dict()
        
        type_counts = {
            'numeric': len(df.select_dtypes(include=[np.number]).columns),
            'categorical': len(df.select_dtypes(include=['object']).columns),
            'datetime': len(df.select_dtypes(include=['datetime64']).columns),
            'boolean': len(df.select_dtypes(include=['bool']).columns)
        }
        
        return {
            'column_types': {k: str(v) for k, v in dtypes.items()},
            'type_counts': type_counts
        }
    
    def detect_all_outliers(self, df):
        outliers = {}
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        
        for col in numeric_cols:
            outliers[col] = self.detect_outliers_column(df, col)
        
        return outliers
    
    def detect_outliers_column(self, df, column):
        col_data = df[column].dropna()
        
        # IQR method
        Q1 = col_data.quantile(0.25)
        Q3 = col_data.quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        
        iqr_outliers = col_data[(col_data < lower_bound) | (col_data > upper_bound)]
        
        # Z-score method
        z_scores = np.abs(stats.zscore(col_data))
        z_outliers = col_data[z_scores > 3]
        
        return {
            'iqr_outliers': len(iqr_outliers),
            'z_outliers': len(z_outliers),
            'iqr_bounds': {'lower': lower_bound, 'upper': upper_bound},
            'outlier_indices': iqr_outliers.index.tolist()
        }
    
    def analyze_skewness_kurtosis(self, df):
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        skew_kurt = {}
        
        for col in numeric_cols:
            col_data = df[col].dropna()
            if len(col_data) > 0:
                skew_kurt[col] = {
                    'skewness': float(stats.skew(col_data)),
                    'kurtosis': float(stats.kurtosis(col_data))
                }
        
        return skew_kurt
    
    def analyze_duplicates(self, df):
        duplicate_rows = df.duplicated().sum()
        duplicate_percent = (duplicate_rows / len(df)) * 100
        
        return {
            'duplicate_rows': int(duplicate_rows),
            'duplicate_percent': float(duplicate_percent),
            'unique_rows': int(len(df) - duplicate_rows)
        }
    
    def analyze_cardinality(self, df):
        cardinality = {}
        
        for col in df.columns:
            unique_count = df[col].nunique()
            total_count = len(df)
            cardinality[col] = {
                'unique_count': unique_count,
                'cardinality_ratio': unique_count / total_count if total_count > 0 else 0,
                'is_high_cardinality': unique_count > total_count * 0.8,
                'is_low_cardinality': unique_count < 10
            }
        
        return cardinality
    
    def analyze_variance(self, df):
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        variance_analysis = {}
        
        for col in numeric_cols:
            col_data = df[col].dropna()
            if len(col_data) > 0:
                variance_analysis[col] = {
                    'variance': float(col_data.var()),
                    'std_dev': float(col_data.std()),
                    'coefficient_of_variation': float(col_data.std() / col_data.mean()) if col_data.mean() != 0 else 0
                }
        
        return variance_analysis
    
    def generate_eda_summary(self, df):
        return {
            'total_rows': len(df),
            'total_columns': len(df.columns),
            'memory_usage': float(df.memory_usage(deep=True).sum()),
            'missing_values_total': int(df.isnull().sum().sum()),
            'duplicate_rows': int(df.duplicated().sum()),
            'numeric_columns': len(df.select_dtypes(include=[np.number]).columns),
            'categorical_columns': len(df.select_dtypes(include=['object']).columns),
            'datetime_columns': len(df.select_dtypes(include=['datetime64']).columns)
        }
    
    def correlation_analysis(self, dataset_id, method='pearson'):
        try:
            dataset = Dataset.query.get_or_404(dataset_id)
            df = self.data_processor.load_dataset(dataset)
            
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            if len(numeric_cols) < 2:
                return {'success': False, 'error': 'Not enough numeric columns for correlation analysis'}
            
            correlation_matrix = df[numeric_cols].corr(method=method)
            
            results = {
                'correlation_matrix': correlation_matrix.to_dict(),
                'method': method,
                'strong_correlations': self.find_strong_correlations(correlation_matrix),
                'weak_correlations': self.find_weak_correlations(correlation_matrix)
            }
            
            return {'success': True, 'results': results}
            
        except Exception as e:
            current_app.logger.error(f"Correlation analysis error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def find_strong_correlations(self, corr_matrix, threshold=0.7):
        strong_corr = []
        for i in range(len(corr_matrix.columns)):
            for j in range(i+1, len(corr_matrix.columns)):
                if abs(corr_matrix.iloc[i, j]) > threshold:
                    strong_corr.append({
                        'var1': corr_matrix.columns[i],
                        'var2': corr_matrix.columns[j],
                        'correlation': float(corr_matrix.iloc[i, j])
                    })
        return strong_corr
    
    def find_weak_correlations(self, corr_matrix, threshold=0.1):
        weak_corr = []
        for i in range(len(corr_matrix.columns)):
            for j in range(i+1, len(corr_matrix.columns)):
                if abs(corr_matrix.iloc[i, j]) < threshold:
                    weak_corr.append({
                        'var1': corr_matrix.columns[i],
                        'var2': corr_matrix.columns[j],
                        'correlation': float(corr_matrix.iloc[i, j])
                    })
        return weak_corr
    
    def distribution_analysis(self, dataset_id, column):
        try:
            dataset = Dataset.query.get_or_404(dataset_id)
            df = self.data_processor.load_dataset(dataset)
            
            if column not in df.columns:
                return {'success': False, 'error': f'Column {column} not found'}
            
            col_data = df[column].dropna()
            
            if pd.api.types.is_numeric_dtype(col_data):
                results = self.analyze_numeric_distribution(col_data)
            else:
                results = self.analyze_categorical_distribution(col_data)
            
            results['column'] = column
            results['data_type'] = str(df[column].dtype)
            
            return {'success': True, 'results': results}
            
        except Exception as e:
            current_app.logger.error(f"Distribution analysis error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def analyze_numeric_distribution(self, data):
        return {
            'mean': float(data.mean()),
            'median': float(data.median()),
            'mode': float(data.mode().iloc[0]) if not data.mode().empty else None,
            'std': float(data.std()),
            'variance': float(data.var()),
            'skewness': float(stats.skew(data)),
            'kurtosis': float(stats.kurtosis(data)),
            'min': float(data.min()),
            'max': float(data.max()),
            'range': float(data.max() - data.min()),
            'iqr': float(data.quantile(0.75) - data.quantile(0.25)),
            'normality_test': self.test_normality(data)
        }
    
    def analyze_categorical_distribution(self, data):
        value_counts = data.value_counts()
        return {
            'unique_values': int(data.nunique()),
            'most_frequent': value_counts.index[0] if not value_counts.empty else None,
            'least_frequent': value_counts.index[-1] if not value_counts.empty else None,
            'value_counts': value_counts.to_dict(),
            'frequency_distribution': (value_counts / len(data)).to_dict()
        }
    
    def test_normality(self, data):
        if len(data) < 8:
            return {'test': 'insufficient_data', 'statistic': None, 'p_value': None}
        
        try:
            stat, p_value = stats.shapiro(data)
            return {
                'test': 'shapiro_wilk',
                'statistic': float(stat),
                'p_value': float(p_value),
                'is_normal': p_value > 0.05
            }
        except:
            return {'test': 'failed', 'statistic': None, 'p_value': None}
    
    def detect_outliers(self, dataset_id, column, method='iqr'):
        try:
            dataset = Dataset.query.get_or_404(dataset_id)
            df = self.data_processor.load_dataset(dataset)
            
            if column not in df.columns:
                return {'success': False, 'error': f'Column {column} not found'}
            
            results = self.detect_outliers_column(df, column)
            results['method'] = method
            
            return {'success': True, 'results': results}
            
        except Exception as e:
            current_app.logger.error(f"Outlier detection error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def missing_value_analysis(self, dataset_id):
        try:
            dataset = Dataset.query.get_or_404(dataset_id)
            df = self.data_processor.load_dataset(dataset)
            
            results = self.analyze_missing_values(df)
            
            # Missing value patterns
            missing_pattern = df.isnull().sum().sort_values(ascending=False)
            results['missing_pattern'] = missing_pattern.to_dict()
            
            # Missing value correlation
            if df.isnull().sum().sum() > 0:
                missing_corr = df.isnull().corr()
                results['missing_correlation'] = missing_corr.to_dict()
            
            return {'success': True, 'results': results}
            
        except Exception as e:
            current_app.logger.error(f"Missing value analysis error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def summary_statistics(self, dataset_id):
        try:
            dataset = Dataset.query.get_or_404(dataset_id)
            df = self.data_processor.load_dataset(dataset)
            
            results = self.get_basic_statistics(df)
            results['summary'] = self.generate_eda_summary(df)
            
            return {'success': True, 'results': results}
            
        except Exception as e:
            current_app.logger.error(f"Summary statistics error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def skewness_analysis(self, dataset_id):
        try:
            dataset = Dataset.query.get_or_404(dataset_id)
            df = self.data_processor.load_dataset(dataset)
            
            results = self.analyze_skewness_kurtosis(df)
            
            return {'success': True, 'results': results}
            
        except Exception as e:
            current_app.logger.error(f"Skewness analysis error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def variance_analysis(self, dataset_id):
        try:
            dataset = Dataset.query.get_or_404(dataset_id)
            df = self.data_processor.load_dataset(dataset)
            
            results = self.analyze_variance(df)
            
            return {'success': True, 'results': results}
            
        except Exception as e:
            current_app.logger.error(f"Variance analysis error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def duplicate_analysis(self, dataset_id):
        try:
            dataset = Dataset.query.get_or_404(dataset_id)
            df = self.data_processor.load_dataset(dataset)
            
            results = self.analyze_duplicates(df)
            
            return {'success': True, 'results': results}
            
        except Exception as e:
            current_app.logger.error(f"Duplicate analysis error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def cardinality_analysis(self, dataset_id):
        try:
            dataset = Dataset.query.get_or_404(dataset_id)
            df = self.data_processor.load_dataset(dataset)
            
            results = self.analyze_cardinality(df)
            
            return {'success': True, 'results': results}
            
        except Exception as e:
            current_app.logger.error(f"Cardinality analysis error: {str(e)}")
            return {'success': False, 'error': str(e)}
