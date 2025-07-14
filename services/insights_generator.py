import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.feature_selection import SelectKBest, f_classif, f_regression, mutual_info_classif, mutual_info_regression
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, r2_score
import logging
from datetime import datetime
from models import Dataset, Analysis, db
from services.data_processor import DataProcessor
from flask import current_app
from scipy import stats
import json

class InsightsGenerator:
    def __init__(self):
        self.data_processor = DataProcessor()
        self.random_state = 42
    
    def generate_comprehensive_insights(self, dataset_id):
        try:
            dataset = Dataset.query.get_or_404(dataset_id)
            df = self.data_processor.load_dataset(dataset)
            
            insights = {
                'data_quality': self.data_quality_insights(dataset_id)['results'],
                'correlation': self.correlation_insights(dataset_id)['results'],
                'distribution': self.distribution_insights(dataset_id)['results'],
                'outliers': self.outlier_insights(dataset_id)['results'],
                'preprocessing': self.preprocessing_recommendations(dataset_id)['results'],
                'feature_engineering': self.feature_engineering_recommendations(dataset_id)['results'],
                'ml_recommendations': self.ml_recommendations(dataset_id)['results'],
                'performance': self.performance_insights(dataset_id)['results'],
                'trends': self.trend_insights(dataset_id)['results']
            }
            
            # Generate executive summary
            insights['executive_summary'] = self.generate_executive_summary(df, insights)
            
            # Save comprehensive insights
            analysis = Analysis(
                dataset_id=dataset_id,
                analysis_type='comprehensive_insights',
                results=insights,
                status='completed'
            )
            db.session.add(analysis)
            db.session.commit()
            
            return {'success': True, 'results': insights}
            
        except Exception as e:
            current_app.logger.error(f"Comprehensive insights error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def data_quality_insights(self, dataset_id):
        try:
            dataset = Dataset.query.get_or_404(dataset_id)
            df = self.data_processor.load_dataset(dataset)
            
            insights = []
            
            # Missing values analysis
            missing_percent = (df.isnull().sum() / len(df)) * 100
            high_missing_cols = missing_percent[missing_percent > 50].index.tolist()
            moderate_missing_cols = missing_percent[(missing_percent > 10) & (missing_percent <= 50)].index.tolist()
            
            if high_missing_cols:
                insights.append({
                    'type': 'data_quality',
                    'severity': 'high',
                    'title': 'High Missing Values',
                    'message': f'Columns with >50% missing values: {", ".join(high_missing_cols)}',
                    'recommendation': 'Consider dropping these columns or investigate data collection issues',
                    'columns': high_missing_cols
                })
            
            if moderate_missing_cols:
                insights.append({
                    'type': 'data_quality',
                    'severity': 'medium',
                    'title': 'Moderate Missing Values',
                    'message': f'Columns with 10-50% missing values: {", ".join(moderate_missing_cols)}',
                    'recommendation': 'Consider imputation strategies or further investigation',
                    'columns': moderate_missing_cols
                })
            
            # Duplicate analysis
            duplicate_count = df.duplicated().sum()
            if duplicate_count > 0:
                duplicate_percent = (duplicate_count / len(df)) * 100
                insights.append({
                    'type': 'data_quality',
                    'severity': 'medium' if duplicate_percent > 10 else 'low',
                    'title': 'Duplicate Records',
                    'message': f'{duplicate_count} duplicate records found ({duplicate_percent:.1f}%)',
                    'recommendation': 'Review and remove duplicate records if appropriate',
                    'count': duplicate_count
                })
            
            # Data type inconsistencies
            for col in df.columns:
                if df[col].dtype == 'object':
                    # Check for numeric strings
                    numeric_strings = df[col].str.isnumeric().sum() if df[col].dtype == 'object' else 0
                    if numeric_strings > len(df) * 0.8:
                        insights.append({
                            'type': 'data_quality',
                            'severity': 'low',
                            'title': 'Data Type Inconsistency',
                            'message': f'Column {col} contains mostly numeric strings',
                            'recommendation': 'Consider converting to numeric type',
                            'column': col
                        })
            
            # Data completeness score
            completeness_score = (1 - df.isnull().sum().sum() / (len(df) * len(df.columns))) * 100
            insights.append({
                'type': 'data_quality',
                'severity': 'info',
                'title': 'Data Completeness Score',
                'message': f'Overall data completeness: {completeness_score:.1f}%',
                'recommendation': 'Higher completeness indicates better data quality',
                'score': completeness_score
            })
            
            return {'success': True, 'results': insights}
            
        except Exception as e:
            current_app.logger.error(f"Data quality insights error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def correlation_insights(self, dataset_id):
        try:
            dataset = Dataset.query.get_or_404(dataset_id)
            df = self.data_processor.load_dataset(dataset)
            
            insights = []
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            
            if len(numeric_cols) < 2:
                return {'success': True, 'results': []}
            
            # Calculate correlation matrix
            corr_matrix = df[numeric_cols].corr()
            
            # Find strong positive correlations
            strong_pos_corr = []
            for i in range(len(corr_matrix.columns)):
                for j in range(i+1, len(corr_matrix.columns)):
                    corr_val = corr_matrix.iloc[i, j]
                    if corr_val > 0.8:
                        strong_pos_corr.append((corr_matrix.columns[i], corr_matrix.columns[j], corr_val))
            
            if strong_pos_corr:
                insights.append({
                    'type': 'correlation',
                    'severity': 'high',
                    'title': 'Strong Positive Correlations',
                    'message': f'Found {len(strong_pos_corr)} strong positive correlations (>0.8)',
                    'recommendation': 'Consider removing redundant features to avoid multicollinearity',
                    'correlations': [{'var1': x[0], 'var2': x[1], 'correlation': x[2]} for x in strong_pos_corr]
                })
            
            # Find strong negative correlations
            strong_neg_corr = []
            for i in range(len(corr_matrix.columns)):
                for j in range(i+1, len(corr_matrix.columns)):
                    corr_val = corr_matrix.iloc[i, j]
                    if corr_val < -0.8:
                        strong_neg_corr.append((corr_matrix.columns[i], corr_matrix.columns[j], corr_val))
            
            if strong_neg_corr:
                insights.append({
                    'type': 'correlation',
                    'severity': 'medium',
                    'title': 'Strong Negative Correlations',
                    'message': f'Found {len(strong_neg_corr)} strong negative correlations (<-0.8)',
                    'recommendation': 'These relationships might be valuable for modeling',
                    'correlations': [{'var1': x[0], 'var2': x[1], 'correlation': x[2]} for x in strong_neg_corr]
                })
            
            # Find weak correlations
            weak_corr = []
            for i in range(len(corr_matrix.columns)):
                for j in range(i+1, len(corr_matrix.columns)):
                    corr_val = abs(corr_matrix.iloc[i, j])
                    if corr_val < 0.1:
                        weak_corr.append((corr_matrix.columns[i], corr_matrix.columns[j], corr_matrix.iloc[i, j]))
            
            if weak_corr:
                insights.append({
                    'type': 'correlation',
                    'severity': 'low',
                    'title': 'Weak Correlations',
                    'message': f'Found {len(weak_corr)} weak correlations (<0.1)',
                    'recommendation': 'These features may be independent and valuable for modeling',
                    'correlations': [{'var1': x[0], 'var2': x[1], 'correlation': x[2]} for x in weak_corr[:10]]
                })
            
            return {'success': True, 'results': insights}
            
        except Exception as e:
            current_app.logger.error(f"Correlation insights error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def distribution_insights(self, dataset_id):
        try:
            dataset = Dataset.query.get_or_404(dataset_id)
            df = self.data_processor.load_dataset(dataset)
            
            insights = []
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            
            for col in numeric_cols:
                col_data = df[col].dropna()
                if len(col_data) > 10:
                    skewness = stats.skew(col_data)
                    kurtosis = stats.kurtosis(col_data)
                    
                    # Skewness insights
                    if abs(skewness) > 2:
                        insights.append({
                            'type': 'distribution',
                            'severity': 'high',
                            'title': f'Highly Skewed Distribution - {col}',
                            'message': f'Skewness: {skewness:.3f}',
                            'recommendation': 'Consider log transformation or other normalization techniques',
                            'column': col,
                            'skewness': skewness
                        })
                    elif abs(skewness) > 1:
                        insights.append({
                            'type': 'distribution',
                            'severity': 'medium',
                            'title': f'Moderately Skewed Distribution - {col}',
                            'message': f'Skewness: {skewness:.3f}',
                            'recommendation': 'May benefit from transformation',
                            'column': col,
                            'skewness': skewness
                        })
                    
                    # Kurtosis insights
                    if abs(kurtosis) > 3:
                        insights.append({
                            'type': 'distribution',
                            'severity': 'medium',
                            'title': f'Extreme Kurtosis - {col}',
                            'message': f'Kurtosis: {kurtosis:.3f}',
                            'recommendation': 'Distribution has heavy tails, consider outlier treatment',
                            'column': col,
                            'kurtosis': kurtosis
                        })
                    
                    # Normality test
                    if len(col_data) >= 8:
                        try:
                            _, p_value = stats.shapiro(col_data)
                            if p_value > 0.05:
                                insights.append({
                                    'type': 'distribution',
                                    'severity': 'info',
                                    'title': f'Normal Distribution - {col}',
                                    'message': f'Shapiro-Wilk p-value: {p_value:.3f}',
                                    'recommendation': 'Data appears to be normally distributed',
                                    'column': col,
                                    'p_value': p_value
                                })
                        except:
                            pass
            
            return {'success': True, 'results': insights}
            
        except Exception as e:
            current_app.logger.error(f"Distribution insights error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def outlier_insights(self, dataset_id):
        try:
            dataset = Dataset.query.get_or_404(dataset_id)
            df = self.data_processor.load_dataset(dataset)
            
            insights = []
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            
            for col in numeric_cols:
                col_data = df[col].dropna()
                if len(col_data) > 10:
                    # IQR method
                    Q1 = col_data.quantile(0.25)
                    Q3 = col_data.quantile(0.75)
                    IQR = Q3 - Q1
                    lower_bound = Q1 - 1.5 * IQR
                    upper_bound = Q3 + 1.5 * IQR
                    
                    outliers = col_data[(col_data < lower_bound) | (col_data > upper_bound)]
                    outlier_percent = (len(outliers) / len(col_data)) * 100
                    
                    if outlier_percent > 10:
                        insights.append({
                            'type': 'outliers',
                            'severity': 'high',
                            'title': f'High Outlier Count - {col}',
                            'message': f'{len(outliers)} outliers ({outlier_percent:.1f}%)',
                            'recommendation': 'Consider outlier treatment or investigation',
                            'column': col,
                            'outlier_count': len(outliers),
                            'outlier_percent': outlier_percent
                        })
                    elif outlier_percent > 5:
                        insights.append({
                            'type': 'outliers',
                            'severity': 'medium',
                            'title': f'Moderate Outlier Count - {col}',
                            'message': f'{len(outliers)} outliers ({outlier_percent:.1f}%)',
                            'recommendation': 'Monitor outliers for impact on analysis',
                            'column': col,
                            'outlier_count': len(outliers),
                            'outlier_percent': outlier_percent
                        })
            
            return {'success': True, 'results': insights}
            
        except Exception as e:
            current_app.logger.error(f"Outlier insights error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def feature_importance_insights(self, dataset_id, target_column):
        try:
            dataset = Dataset.query.get_or_404(dataset_id)
            df = self.data_processor.load_dataset(dataset)
            
            if target_column not in df.columns:
                return {'success': False, 'error': f'Target column {target_column} not found'}
            
            insights = []
            
            # Prepare features
            feature_cols = [col for col in df.columns if col != target_column]
            numeric_features = df[feature_cols].select_dtypes(include=[np.number]).columns.tolist()
            
            if len(numeric_features) == 0:
                return {'success': True, 'results': []}
            
            X = df[numeric_features].fillna(df[numeric_features].mean())
            y = df[target_column].fillna(df[target_column].mode()[0] if not df[target_column].mode().empty else 0)
            
            # Feature importance using Random Forest
            if pd.api.types.is_numeric_dtype(y):
                model = RandomForestRegressor(n_estimators=100, random_state=self.random_state)
                score_func = f_regression
            else:
                model = RandomForestRegressor(n_estimators=100, random_state=self.random_state)
                score_func = f_classif
            
            model.fit(X, y)
            importances = model.feature_importances_
            
            # Sort features by importance
            feature_importance = list(zip(numeric_features, importances))
            feature_importance.sort(key=lambda x: x[1], reverse=True)
            
            # Top important features
            top_features = feature_importance[:5]
            insights.append({
                'type': 'feature_importance',
                'severity': 'info',
                'title': 'Top Important Features',
                'message': f'Most important features for {target_column}',
                'recommendation': 'Focus on these features for modeling',
                'features': [{'feature': f[0], 'importance': f[1]} for f in top_features]
            })
            
            # Low importance features
            low_importance = [f for f in feature_importance if f[1] < 0.01]
            if low_importance:
                insights.append({
                    'type': 'feature_importance',
                    'severity': 'low',
                    'title': 'Low Importance Features',
                    'message': f'{len(low_importance)} features with very low importance',
                    'recommendation': 'Consider removing these features to reduce complexity',
                    'features': [{'feature': f[0], 'importance': f[1]} for f in low_importance]
                })
            
            return {'success': True, 'results': insights}
            
        except Exception as e:
            current_app.logger.error(f"Feature importance insights error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def ml_recommendations(self, dataset_id):
        try:
            dataset = Dataset.query.get_or_404(dataset_id)
            df = self.data_processor.load_dataset(dataset)
            
            insights = []
            
            # Dataset size recommendations
            n_rows, n_cols = df.shape
            
            if n_rows < 100:
                insights.append({
                    'type': 'ml_recommendation',
                    'severity': 'high',
                    'title': 'Small Dataset',
                    'message': f'Dataset has only {n_rows} rows',
                    'recommendation': 'Consider simple models, cross-validation, or data augmentation',
                    'size': n_rows
                })
            elif n_rows < 1000:
                insights.append({
                    'type': 'ml_recommendation',
                    'severity': 'medium',
                    'title': 'Medium Dataset',
                    'message': f'Dataset has {n_rows} rows',
                    'recommendation': 'Good for most traditional ML algorithms',
                    'size': n_rows
                })
            else:
                insights.append({
                    'type': 'ml_recommendation',
                    'severity': 'info',
                    'title': 'Large Dataset',
                    'message': f'Dataset has {n_rows} rows',
                    'recommendation': 'Consider ensemble methods or deep learning',
                    'size': n_rows
                })
            
            # Feature count recommendations
            if n_cols > n_rows:
                insights.append({
                    'type': 'ml_recommendation',
                    'severity': 'high',
                    'title': 'High Dimensionality',
                    'message': f'More features ({n_cols}) than samples ({n_rows})',
                    'recommendation': 'Apply dimensionality reduction or feature selection',
                    'features': n_cols,
                    'samples': n_rows
                })
            
            # Data type recommendations
            numeric_cols = len(df.select_dtypes(include=[np.number]).columns)
            categorical_cols = len(df.select_dtypes(include=['object']).columns)
            
            if categorical_cols > numeric_cols:
                insights.append({
                    'type': 'ml_recommendation',
                    'severity': 'medium',
                    'title': 'Categorical Heavy Dataset',
                    'message': f'More categorical ({categorical_cols}) than numeric ({numeric_cols}) features',
                    'recommendation': 'Consider tree-based models or proper encoding strategies',
                    'categorical_count': categorical_cols,
                    'numeric_count': numeric_cols
                })
            
            # Missing values recommendations
            missing_percent = (df.isnull().sum().sum() / (len(df) * len(df.columns))) * 100
            if missing_percent > 20:
                insights.append({
                    'type': 'ml_recommendation',
                    'severity': 'high',
                    'title': 'High Missing Values',
                    'message': f'{missing_percent:.1f}% of data is missing',
                    'recommendation': 'Implement robust imputation strategy before modeling',
                    'missing_percent': missing_percent
                })
            
            return {'success': True, 'results': insights}
            
        except Exception as e:
            current_app.logger.error(f"ML recommendations error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def preprocessing_recommendations(self, dataset_id):
        try:
            dataset = Dataset.query.get_or_404(dataset_id)
            df = self.data_processor.load_dataset(dataset)
            
            insights = []
            
            # Scaling recommendations
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            if numeric_cols:
                scales = []
                for col in numeric_cols:
                    col_data = df[col].dropna()
                    if len(col_data) > 0:
                        scales.append(col_data.max() - col_data.min())
                
                if scales and max(scales) / min(scales) > 100:
                    insights.append({
                        'type': 'preprocessing',
                        'severity': 'high',
                        'title': 'Scale Differences',
                        'message': 'Features have very different scales',
                        'recommendation': 'Apply standardization or normalization',
                        'scale_ratio': max(scales) / min(scales) if min(scales) > 0 else 0
                    })
            
            # Encoding recommendations
            categorical_cols = df.select_dtypes(include=['object']).columns.tolist()
            for col in categorical_cols:
                unique_count = df[col].nunique()
                if unique_count > 50:
                    insights.append({
                        'type': 'preprocessing',
                        'severity': 'medium',
                        'title': f'High Cardinality - {col}',
                        'message': f'{unique_count} unique values',
                        'recommendation': 'Consider target encoding or dimensionality reduction',
                        'column': col,
                        'unique_count': unique_count
                    })
                elif unique_count == 2:
                    insights.append({
                        'type': 'preprocessing',
                        'severity': 'info',
                        'title': f'Binary Variable - {col}',
                        'message': 'Binary categorical variable',
                        'recommendation': 'Simple label encoding is sufficient',
                        'column': col
                    })
            
            return {'success': True, 'results': insights}
            
        except Exception as e:
            current_app.logger.error(f"Preprocessing recommendations error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def feature_engineering_recommendations(self, dataset_id):
        try:
            dataset = Dataset.query.get_or_404(dataset_id)
            df = self.data_processor.load_dataset(dataset)
            
            insights = []
            
            # Date/time features
            date_cols = df.select_dtypes(include=['datetime64']).columns.tolist()
            for col in date_cols:
                insights.append({
                    'type': 'feature_engineering',
                    'severity': 'info',
                    'title': f'DateTime Feature - {col}',
                    'message': 'DateTime column detected',
                    'recommendation': 'Extract year, month, day, weekday, hour features',
                    'column': col
                })
            
            # Text features
            text_cols = []
            for col in df.select_dtypes(include=['object']).columns:
                if df[col].astype(str).str.len().mean() > 50:
                    text_cols.append(col)
            
            for col in text_cols:
                insights.append({
                    'type': 'feature_engineering',
                    'severity': 'medium',
                    'title': f'Text Feature - {col}',
                    'message': 'Long text column detected',
                    'recommendation': 'Consider text feature extraction (TF-IDF, sentiment analysis)',
                    'column': col
                })
            
            # Interaction features
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            if len(numeric_cols) >= 2:
                insights.append({
                    'type': 'feature_engineering',
                    'severity': 'low',
                    'title': 'Interaction Features',
                    'message': f'{len(numeric_cols)} numeric features available',
                    'recommendation': 'Consider creating interaction features between numeric variables',
                    'numeric_count': len(numeric_cols)
                })
            
            return {'success': True, 'results': insights}
            
        except Exception as e:
            current_app.logger.error(f"Feature engineering recommendations error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def column_specific_insights(self, dataset_id, column):
        try:
            dataset = Dataset.query.get_or_404(dataset_id)
            df = self.data_processor.load_dataset(dataset)
            
            if column not in df.columns:
                return {'success': False, 'error': f'Column {column} not found'}
            
            insights = []
            col_data = df[column]
            
            # Missing values
            missing_count = col_data.isnull().sum()
            if missing_count > 0:
                missing_percent = (missing_count / len(col_data)) * 100
                insights.append({
                    'type': 'column_specific',
                    'severity': 'high' if missing_percent > 20 else 'medium',
                    'title': f'Missing Values - {column}',
                    'message': f'{missing_count} missing values ({missing_percent:.1f}%)',
                    'recommendation': 'Consider imputation or investigation',
                    'column': column,
                    'missing_count': missing_count,
                    'missing_percent': missing_percent
                })
            
            # Data type specific insights
            if pd.api.types.is_numeric_dtype(col_data):
                # Numeric column insights
                numeric_data = col_data.dropna()
                if len(numeric_data) > 0:
                    # Zero values
                    zero_count = (numeric_data == 0).sum()
                    if zero_count > len(numeric_data) * 0.1:
                        insights.append({
                            'type': 'column_specific',
                            'severity': 'medium',
                            'title': f'Many Zero Values - {column}',
                            'message': f'{zero_count} zero values',
                            'recommendation': 'Consider if zeros are meaningful or missing',
                            'column': column,
                            'zero_count': zero_count
                        })
                    
                    # Negative values
                    negative_count = (numeric_data < 0).sum()
                    if negative_count > 0:
                        insights.append({
                            'type': 'column_specific',
                            'severity': 'info',
                            'title': f'Negative Values - {column}',
                            'message': f'{negative_count} negative values',
                            'recommendation': 'Verify if negative values are expected',
                            'column': column,
                            'negative_count': negative_count
                        })
            
            else:
                # Categorical column insights
                unique_count = col_data.nunique()
                mode_freq = col_data.value_counts().iloc[0] if not col_data.value_counts().empty else 0
                mode_percent = (mode_freq / len(col_data)) * 100
                
                if mode_percent > 90:
                    insights.append({
                        'type': 'column_specific',
                        'severity': 'high',
                        'title': f'Low Variance - {column}',
                        'message': f'Most frequent value appears {mode_percent:.1f}% of the time',
                        'recommendation': 'Consider removing this low-variance feature',
                        'column': column,
                        'mode_percent': mode_percent
                    })
                
                if unique_count == len(col_data):
                    insights.append({
                        'type': 'column_specific',
                        'severity': 'high',
                        'title': f'All Unique Values - {column}',
                        'message': 'Every value is unique',
                        'recommendation': 'This might be an ID column, consider removing',
                        'column': column
                    })
            
            return {'success': True, 'results': insights}
            
        except Exception as e:
            current_app.logger.error(f"Column specific insights error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def performance_insights(self, dataset_id):
        try:
            dataset = Dataset.query.get_or_404(dataset_id)
            df = self.data_processor.load_dataset(dataset)
            
            insights = []
            
            # Memory usage
            memory_usage = df.memory_usage(deep=True).sum()
            memory_mb = memory_usage / (1024 * 1024)
            
            if memory_mb > 100:
                insights.append({
                    'type': 'performance',
                    'severity': 'high',
                    'title': 'High Memory Usage',
                    'message': f'Dataset uses {memory_mb:.1f} MB of memory',
                    'recommendation': 'Consider data type optimization or sampling',
                    'memory_mb': memory_mb
                })
            
            # Processing recommendations
            n_rows, n_cols = df.shape
            if n_rows * n_cols > 1000000:
                insights.append({
                    'type': 'performance',
                    'severity': 'medium',
                    'title': 'Large Dataset',
                    'message': f'Dataset has {n_rows * n_cols} total elements',
                    'recommendation': 'Consider parallel processing or chunking for large operations',
                    'total_elements': n_rows * n_cols
                })
            
            return {'success': True, 'results': insights}
            
        except Exception as e:
            current_app.logger.error(f"Performance insights error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def trend_insights(self, dataset_id):
        try:
            dataset = Dataset.query.get_or_404(dataset_id)
            df = self.data_processor.load_dataset(dataset)
            
            insights = []
            
            # Look for date/time columns
            date_cols = df.select_dtypes(include=['datetime64']).columns.tolist()
            
            # Check for string columns that might be dates
            for col in df.select_dtypes(include=['object']).columns:
                sample_vals = df[col].dropna().head(100)
                if sample_vals.astype(str).str.match(r'\d{4}-\d{2}-\d{2}').sum() > 50:
                    date_cols.append(col)
            
            if date_cols:
                insights.append({
                    'type': 'trend',
                    'severity': 'info',
                    'title': 'Time Series Analysis Possible',
                    'message': f'Date/time columns detected: {", ".join(date_cols)}',
                    'recommendation': 'Consider time series analysis and trend detection',
                    'date_columns': date_cols
                })
            
            # Look for sequential patterns in numeric columns
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            for col in numeric_cols:
                col_data = df[col].dropna()
                if len(col_data) > 10:
                    # Check for monotonic trends
                    if col_data.is_monotonic_increasing:
                        insights.append({
                            'type': 'trend',
                            'severity': 'medium',
                            'title': f'Monotonic Increasing - {col}',
                            'message': 'Values are consistently increasing',
                            'recommendation': 'Consider if this represents a time trend',
                            'column': col
                        })
                    elif col_data.is_monotonic_decreasing:
                        insights.append({
                            'type': 'trend',
                            'severity': 'medium',
                            'title': f'Monotonic Decreasing - {col}',
                            'message': 'Values are consistently decreasing',
                            'recommendation': 'Consider if this represents a time trend',
                            'column': col
                        })
            
            return {'success': True, 'results': insights}
            
        except Exception as e:
            current_app.logger.error(f"Trend insights error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def generate_executive_summary(self, df, insights):
        summary = {
            'dataset_overview': {
                'rows': len(df),
                'columns': len(df.columns),
                'memory_usage_mb': df.memory_usage(deep=True).sum() / (1024 * 1024),
                'missing_values_percent': (df.isnull().sum().sum() / (len(df) * len(df.columns))) * 100,
                'duplicate_rows': df.duplicated().sum()
            },
            'key_findings': [],
            'priority_actions': [],
            'data_quality_score': 0
        }
        
        # Extract key findings from insights
        all_insights = []
        for category, category_insights in insights.items():
            if isinstance(category_insights, list):
                all_insights.extend(category_insights)
        
        # Priority actions (high severity items)
        high_severity = [insight for insight in all_insights if insight.get('severity') == 'high']
        summary['priority_actions'] = high_severity[:5]  # Top 5 priority actions
        
        # Key findings (mix of different types)
        key_findings = []
        for insight_type in ['correlation', 'distribution', 'outliers', 'data_quality']:
            type_insights = [insight for insight in all_insights if insight.get('type') == insight_type]
            if type_insights:
                key_findings.append(type_insights[0])
        
        summary['key_findings'] = key_findings
        
        # Calculate data quality score
        base_score = 100
        
        # Deduct for missing values
        missing_penalty = min(summary['dataset_overview']['missing_values_percent'], 50)
        base_score -= missing_penalty
        
        # Deduct for duplicates
        duplicate_penalty = min((summary['dataset_overview']['duplicate_rows'] / len(df)) * 100, 20)
        base_score -= duplicate_penalty
        
        # Deduct for high severity issues
        severity_penalty = len(high_severity) * 5
        base_score -= severity_penalty
        
        summary['data_quality_score'] = max(base_score, 0)
        
        return summary
