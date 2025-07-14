import pandas as pd
import numpy as np
from scipy import stats
from sklearn.preprocessing import LabelEncoder
from sklearn.feature_selection import mutual_info_classif, mutual_info_regression
from typing import Dict, List, Any, Optional, Tuple
import logging
import warnings
import json
import matplotlib.pyplot as plt
import seaborn as sns
import io
import base64
from collections import Counter
from scipy.stats import kruskal

warnings.filterwarnings('ignore')
# Set matplotlib to use non-interactive backend
import matplotlib
matplotlib.use('Agg')

class ColumnAnalysis:
    """Comprehensive column-wise analysis service"""

    def __init__(self, file_path: str = None):
        self.file_path = file_path
        self.df = None
        if file_path:
            self._load_dataframe(file_path)
        self.logger = logging.getLogger(__name__)

    def _load_dataframe(self, file_path: str = None):
        """Load DataFrame from file path"""
        path = file_path or self.file_path
        if not path:
            raise ValueError("No file path provided")
        try:
            self.df = pd.read_csv(path)
            self.numeric_columns = self.df.select_dtypes(include=[np.number]).columns.tolist()
            self.categorical_columns = self.df.select_dtypes(include=['object', 'category']).columns.tolist()
            self.datetime_columns = self.df.select_dtypes(include=['datetime64']).columns.tolist()
        except FileNotFoundError:
            raise FileNotFoundError(f"File not found at {path}")
        except Exception as e:
            raise RuntimeError(f"Error loading DataFrame: {e}")

    def _convert_numpy_types(self, obj):
        """Convert numpy types to native Python types for JSON serialization"""
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            if np.isnan(obj) or np.isinf(obj):
                return None
            return float(obj)
        elif isinstance(obj, np.bool_):
            return bool(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, dict):
            return {key: self._convert_numpy_types(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_numpy_types(item) for item in obj]
        elif pd.isna(obj):
            return None
        return obj

    def analyze_columns(self, columns: List[str], analysis_type: str = 'comprehensive') -> Dict[str, Any]:
        """Analyze specific columns"""
        try:
            if self.df is None:
                raise ValueError("DataFrame not loaded. Please load the DataFrame first.")
            results = {}
            for column in columns:
                if column not in self.df.columns:
                    results[column] = {'error': f'Column {column} not found'}
                    continue
                if analysis_type == 'comprehensive':
                    results[column] = self.comprehensive_column_summary(column)
                elif analysis_type == 'univariate':
                    results[column] = self.univariate_analysis(column)
                elif analysis_type == 'quality':
                    results[column] = self.data_quality_analysis(column)
                elif analysis_type == 'statistical':
                    results[column] = self.statistical_analysis(column)
                else:
                    results[column] = {'error': f'Unknown analysis type: {analysis_type}'}
            return {
                'analysis_type': analysis_type,
                'columns_analyzed': columns,
                'results': {col: self._convert_numpy_types(res) for col, res in results.items()}
            }
        except Exception as e:
            self.logger.error(f"Error analyzing columns: {str(e)}")
            raise

    def univariate_analysis(self, column: str) -> Dict[str, Any]:
        """Perform comprehensive univariate analysis"""
        try:
            if column not in self.df.columns:
                raise ValueError(f"Column {column} not found")
            data = self.df[column]
            analysis = {
                'column_name': column,
                'data_type': str(data.dtype),
                'basic_info': self._get_basic_info(data),
                'missing_analysis': self._analyze_missing_values(data),
                'uniqueness_analysis': self._analyze_uniqueness(data),
                'distribution_analysis': {},
                'outlier_analysis': {},
                'normality_tests': {},
                'insights': [],
                'recommendations': []
            }
            # Type-specific analysis
            if pd.api.types.is_numeric_dtype(data):
                analysis['distribution_analysis'] = self._analyze_numeric_distribution(data)
                analysis['outlier_analysis'] = self._analyze_outliers(data)
                analysis['normality_tests'] = self._test_normality(data)
                analysis['insights'].extend(self._generate_numeric_insights(data, column))
            elif pd.api.types.is_categorical_dtype(data) or data.dtype == 'object':
                analysis['distribution_analysis'] = self._analyze_categorical_distribution(data)
                analysis['insights'].extend(self._generate_categorical_insights(data, column))
            elif pd.api.types.is_datetime64_any_dtype(data):
                analysis['temporal_analysis'] = self._analyze_temporal_patterns(data)
                analysis['insights'].extend(self._generate_temporal_insights(data, column))
            # Generate recommendations
            analysis['recommendations'] = self._generate_column_recommendations(data, column, analysis)
            return self._convert_numpy_types(analysis)
        except Exception as e:
            self.logger.error(f"Error in univariate analysis for column {column}: {str(e)}")
            raise

    def bivariate_analysis(self, column1: str, column2: str) -> Dict[str, Any]:
        """Perform bivariate analysis between two columns"""
        try:
            if self.df is None:
                raise ValueError("DataFrame not loaded. Please load the DataFrame first.")
            if column1 not in self.df.columns or column2 not in self.df.columns:
                raise ValueError("One or both columns not found")
            data1 = self.df[column1]
            data2 = self.df[column2]
            analysis = {
                'column1': column1,
                'column2': column2,
                'data_types': [str(data1.dtype), str(data2.dtype)],
                'relationship_type': self._determine_relationship_type(data1, data2),
                'correlation_analysis': {},
                'association_analysis': {},
                'statistical_tests': {},
                'insights': [],
                'recommendations': []
            }
            # Remove missing values for analysis
            combined_data = pd.DataFrame({column1: data1, column2: data2}).dropna()
            if len(combined_data) == 0:
                analysis['error'] = 'No valid pairs after removing missing values'
                return self._convert_numpy_types(analysis)
            clean_data1 = combined_data[column1]
            clean_data2 = combined_data[column2]
            # Determine analysis based on data types
            if pd.api.types.is_numeric_dtype(data1) and pd.api.types.is_numeric_dtype(data2):
                # Numeric vs Numeric
                analysis['correlation_analysis'] = self._analyze_numeric_correlation(clean_data1, clean_data2)
                analysis['statistical_tests'] = self._run_numeric_tests(clean_data1, clean_data2)
                analysis['insights'].extend(self._generate_numeric_bivariate_insights(clean_data1, clean_data2, column1, column2))
            elif (pd.api.types.is_numeric_dtype(data1) and not pd.api.types.is_numeric_dtype(data2)) or \
                 (not pd.api.types.is_numeric_dtype(data1) and pd.api.types.is_numeric_dtype(data2)):
                # Numeric vs Categorical
                analysis['association_analysis'] = self._analyze_numeric_categorical(clean_data1, clean_data2, column1, column2)
                analysis['statistical_tests'] = self._run_numeric_categorical_tests(clean_data1, clean_data2, column1, column2)
                analysis['insights'].extend(self._generate_numeric_categorical_insights(clean_data1, clean_data2, column1, column2))
            else:
                # Categorical vs Categorical
                analysis['association_analysis'] = self._analyze_categorical_association(clean_data1, clean_data2)
                analysis['statistical_tests'] = self._run_categorical_tests(clean_data1, clean_data2)
                analysis['insights'].extend(self._generate_categorical_bivariate_insights(clean_data1, clean_data2, column1, column2))
            analysis['recommendations'] = self._generate_bivariate_recommendations(analysis)
            return self._convert_numpy_types(analysis)
        except Exception as e:
            self.logger.error(f"Error in bivariate analysis for columns {column1}, {column2}: {str(e)}")
            raise

    def multivariate_analysis(self, columns: List[str], target_column: str = None) -> Dict[str, Any]:
        """Perform multivariate analysis"""
        try:
            if self.df is None:
                raise ValueError("DataFrame not loaded. Please load the DataFrame first.")
            if not all(col in self.df.columns for col in columns):
                missing = [col for col in columns if col not in self.df.columns]
                raise ValueError(f"Columns not found: {missing}")
            analysis = {
                'columns': columns,
                'target_column': target_column,
                'correlation_matrix': {},
                'feature_importance': {},
                'interactions': {},
                'dimensionality_analysis': {},
                'insights': [],
                'recommendations': []
            }
            # Filter to numeric columns for correlation analysis
            numeric_cols = [col for col in columns if col in self.numeric_columns]
            if len(numeric_cols) > 1:
                corr_matrix = self.df[numeric_cols].corr()
                analysis['correlation_matrix'] = {
                    'matrix': corr_matrix.to_dict(),
                    'high_correlations': self._find_high_correlations(corr_matrix),
                    'multicollinearity': self._detect_multicollinearity(corr_matrix)
                }
            # Feature importance analysis if target provided
            if target_column and target_column in self.df.columns:
                analysis['feature_importance'] = self._calculate_feature_importance(columns, target_column)
            # Interaction analysis
            if len(numeric_cols) >= 2:
                analysis['interactions'] = self._analyze_feature_interactions(numeric_cols, target_column)
            # Dimensionality analysis
            analysis['dimensionality_analysis'] = self._analyze_dimensionality(columns)
            # Generate insights and recommendations
            analysis['insights'] = self._generate_multivariate_insights(analysis)
            analysis['recommendations'] = self._generate_multivariate_recommendations(analysis)
            return self._convert_numpy_types(analysis)
        except Exception as e:
            self.logger.error(f"Error in multivariate analysis: {str(e)}")
            raise

    def outlier_analysis(self, column: str, method: str = 'iqr') -> Dict[str, Any]:
        """Comprehensive outlier analysis"""
        try:
            if column not in self.df.columns:
                raise ValueError(f"Column {column} not found")
            
            data = self.df[column].dropna()
            
            # Check if column is numeric
            if not pd.api.types.is_numeric_dtype(data):
                return {
                    'column': column,
                    'method': method,
                    'error': 'Outlier analysis only applicable to numeric columns',
                    'outlier_detection': {},
                    'outlier_impact': {},
                    'recommendations': ['Outlier analysis is not applicable to non-numeric data types.']
                }
            
            # Check if we have enough data
            if len(data) < 2:
                return {
                    'column': column,
                    'method': method,
                    'error': 'Insufficient data for outlier analysis (need at least 2 non-null values)',
                    'outlier_detection': {},
                    'outlier_impact': {},
                    'recommendations': ['Need more data points for meaningful outlier analysis.']
                }
            
            analysis = {
                'column': column,
                'method': method,
                'outlier_detection': {},
                'outlier_impact': {},
                'recommendations': []
            }
            
            # Multiple outlier detection methods
            methods_to_test = ['iqr', 'zscore', 'modified_zscore']
            for outlier_method in methods_to_test:
                try:
                    outliers = self._detect_outliers_method(data, outlier_method)
                    analysis['outlier_detection'][outlier_method] = outliers
                except Exception as e:
                    analysis['outlier_detection'][outlier_method] = {'error': str(e)}
            
            # Analyze outlier impact only if we have valid outlier detection results
            try:
                analysis['outlier_impact'] = self._analyze_outlier_impact(data, analysis['outlier_detection'])
            except Exception as e:
                analysis['outlier_impact'] = {'error': f'Impact analysis failed: {str(e)}'}
            
            # Generate recommendations
            try:
                analysis['recommendations'] = self._generate_outlier_recommendations(analysis)
            except Exception as e:
                analysis['recommendations'] = [f'Could not generate recommendations: {str(e)}']
            
            return self._convert_numpy_types(analysis)
        except Exception as e:
            self.logger.error(f"Error in outlier analysis for column {column}: {str(e)}")
            return {
                'column': column,
                'method': method,
                'error': f'Outlier analysis failed: {str(e)}',
                'outlier_detection': {},
                'outlier_impact': {},
                'recommendations': []
            }

    def missing_value_analysis(self, column: str) -> Dict[str, Any]:
        """Comprehensive missing value analysis"""
        try:
            if column not in self.df.columns:
                raise ValueError(f"Column {column} not found")
            data = self.df[column]
            analysis = {
                'column': column,
                'missing_info': self._analyze_missing_values(data),
                'missing_patterns': self._analyze_missing_patterns(column),
                'imputation_suggestions': self._suggest_imputation_methods(data),
                'impact_analysis': self._analyze_missing_impact(column),
                'recommendations': []
            }
            analysis['recommendations'] = self._generate_missing_value_recommendations(analysis)
            return self._convert_numpy_types(analysis)
        except Exception as e:
            self.logger.error(f"Error in missing value analysis for column {column}: {str(e)}")
            raise

    def distribution_analysis(self, column: str) -> Dict[str, Any]:
        """Comprehensive distribution analysis"""
        try:
            if column not in self.df.columns:
                raise ValueError(f"Column {column} not found")
            data = self.df[column].dropna()
            analysis = {
                'column': column,
                'distribution_type': self._identify_distribution_type(data),
                'distribution_parameters': {},
                'goodness_of_fit': {},
                'transformation_analysis': {},
                'recommendations': []
            }
            if pd.api.types.is_numeric_dtype(data):
                analysis['distribution_parameters'] = self._analyze_numeric_distribution(data)
                analysis['goodness_of_fit'] = self._test_distribution_fit(data)
                analysis['transformation_analysis'] = self._analyze_transformations(data)
            else:
                analysis['distribution_parameters'] = self._analyze_categorical_distribution(data)
            analysis['recommendations'] = self._generate_distribution_recommendations(analysis)
            return self._convert_numpy_types(analysis)
        except Exception as e:
            self.logger.error(f"Error in distribution analysis for column {column}: {str(e)}")
            raise

    def categorical_analysis(self, column: str) -> Dict[str, Any]:
        """Comprehensive categorical analysis"""
        try:
            if column not in self.df.columns:
                raise ValueError(f"Column {column} not found")
            data = self.df[column]
            analysis = {
                'column': column,
                'category_info': self._analyze_categorical_distribution(data),
                'encoding_analysis': self._analyze_encoding_needs(data),
                'cardinality_analysis': self._analyze_cardinality(data),
                'recommendations': []
            }
            analysis['recommendations'] = self._generate_categorical_recommendations(analysis)
            return self._convert_numpy_types(analysis)
        except Exception as e:
            self.logger.error(f"Error in categorical analysis for column {column}: {str(e)}")
            raise

    def temporal_analysis(self, column: str) -> Dict[str, Any]:
        """Comprehensive temporal analysis"""
        try:
            if column not in self.df.columns:
                raise ValueError(f"Column {column} not found")
            data = self.df[column]
            # Convert to datetime if not already
            if not pd.api.types.is_datetime64_any_dtype(data):
                try:
                    data = pd.to_datetime(data, errors='coerce')
                except Exception as e:
                    return {'error': f'Cannot convert column to datetime: {e}'}
            analysis = {
                'column': column,
                'temporal_patterns': self._analyze_temporal_patterns(data),
                'seasonality': self._analyze_seasonality(data),
                'trends': self._analyze_trends(data),
                'recommendations': []
            }
            analysis['recommendations'] = self._generate_temporal_recommendations(analysis)
            return self._convert_numpy_types(analysis)
        except Exception as e:
            self.logger.error(f"Error in temporal analysis for column {column}: {str(e)}")
            raise

    def get_column_summary(self, file_path: str, column: str) -> Dict[str, Any]:
        """Get comprehensive column summary for API endpoint"""
        try:
            self._load_dataframe(file_path)
            summary = self.comprehensive_column_summary(column)
            return self._convert_numpy_types(summary)
        except Exception as e:
            self.logger.error(f"Error getting column summary: {str(e)}")
            raise

    def detect_outliers(self, file_path: str, column: str, method: str = 'iqr') -> Dict[str, Any]:
        """Detect outliers for API endpoint"""
        try:
            # Load dataframe with better error handling
            try:
                self._load_dataframe(file_path)
            except FileNotFoundError:
                return {
                    'success': False,
                    'error': f'Dataset file not found at path: {file_path}',
                    'outlier_detection': {},
                    'outlier_impact': {},
                    'recommendations': []
                }
            except Exception as e:
                return {
                    'success': False,
                    'error': f'Failed to load dataset: {str(e)}',
                    'outlier_detection': {},
                    'outlier_impact': {},
                    'recommendations': []
                }
            
            # Check if dataframe was loaded successfully
            if self.df is None or self.df.empty:
                return {
                    'success': False,
                    'error': 'Dataset is empty or could not be loaded',
                    'outlier_detection': {},
                    'outlier_impact': {},
                    'recommendations': []
                }
            
            # Check if column exists
            if column not in self.df.columns:
                available_columns = list(self.df.columns)
                return {
                    'success': False,
                    'error': f'Column "{column}" not found. Available columns: {available_columns}',
                    'outlier_detection': {},
                    'outlier_impact': {},
                    'recommendations': []
                }
            
            # Perform outlier analysis
            outliers = self.outlier_analysis(column, method)
            
            # Add success flag if analysis completed
            if 'error' not in outliers:
                outliers['success'] = True
            else:
                outliers['success'] = False
            
            return self._convert_numpy_types(outliers)
        except Exception as e:
            self.logger.error(f"Error detecting outliers: {str(e)}")
            return {
                'success': False,
                'error': f'An unexpected error occurred during outlier detection: {str(e)}',
                'outlier_detection': {},
                'outlier_impact': {},
                'recommendations': []
            }

    def analyze_distribution(self, file_path: str, column: str) -> Dict[str, Any]:
        """Analyze distribution for API endpoint"""
        try:
            self._load_dataframe(file_path)
            distribution = self.distribution_analysis(column)
            return self._convert_numpy_types(distribution)
        except Exception as e:
            self.logger.error(f"Error analyzing distribution: {str(e)}")
            raise

    def analyze_missing_values(self, file_path: str, column: str) -> Dict[str, Any]:
        """Analyze missing values for API endpoint"""
        try:
            self._load_dataframe(file_path)
            missing = self.missing_value_analysis(column)
            return self._convert_numpy_types(missing)
        except Exception as e:
            self.logger.error(f"Error analyzing missing values: {str(e)}")
            raise

    def analyze_unique_values(self, file_path: str, column: str) -> Dict[str, Any]:
        """Analyze unique values for API endpoint"""
        try:
            self._load_dataframe(file_path)
            if column not in self.df.columns:
                raise ValueError(f"Column {column} not found")
            data = self.df[column]
            unique_analysis = {
                'column': column,
                'unique_count': int(data.nunique()),
                'total_count': int(len(data)),
                'unique_percentage': float((data.nunique() / len(data)) * 100) if len(data) > 0 else 0.0,
                'value_counts': data.value_counts().head(20).to_dict(),
                'most_frequent': data.mode().iloc[0] if not data.mode().empty else None,
                'least_frequent_values': data.value_counts().tail(10).to_dict()
            }
            return self._convert_numpy_types(unique_analysis)
        except Exception as e:
            self.logger.error(f"Error analyzing unique values: {str(e)}")
            raise

    def assess_data_quality(self, file_path: str, column: str) -> Dict[str, Any]:
        """Assess data quality for API endpoint"""
        try:
            self._load_dataframe(file_path)
            quality = self.data_quality_analysis(column)
            return self._convert_numpy_types(quality)
        except Exception as e:
            self.logger.error(f"Error assessing data quality: {str(e)}")
            raise

    def detect_patterns(self, file_path: str, column: str) -> Dict[str, Any]:
        """Detect patterns for API endpoint"""
        try:
            self._load_dataframe(file_path)
            if column not in self.df.columns:
                raise ValueError(f"Column {column} not found")
            data = self.df[column]
            patterns = {
                'column': column,
                'data_type': str(data.dtype),
                'string_patterns': {},
                'numerical_patterns': {},
                'temporal_patterns': {}
            }
            if data.dtype == 'object':
                # String pattern analysis
                patterns['string_patterns'] = {
                    'average_length': float(data.astype(str).str.len().mean()) if not data.empty else 0,
                    'contains_numbers': bool(data.astype(str).str.contains(r'\d', na=False).any()),
                    'contains_special_chars': bool(data.astype(str).str.contains(r'[^a-zA-Z0-9\s]', na=False).any()),
                    'all_uppercase': int(data.astype(str).str.isupper().sum()),
                    'all_lowercase': int(data.astype(str).str.islower().sum())
                }
            if pd.api.types.is_numeric_dtype(data):
                patterns['numerical_patterns'] = self._analyze_numeric_distribution(data)
            if pd.api.types.is_datetime64_any_dtype(data):
                patterns['temporal_patterns'] = self._analyze_temporal_patterns(data)
            return self._convert_numpy_types(patterns)
        except Exception as e:
            self.logger.error(f"Error detecting patterns: {str(e)}")
            raise

    def perform_temporal_analysis(self, file_path: str, column: str) -> Dict[str, Any]:
        """Perform temporal analysis for API endpoint"""
        try:
            self._load_dataframe(file_path)
            temporal = self.temporal_analysis(column)
            return self._convert_numpy_types(temporal)
        except Exception as e:
            self.logger.error(f"Error performing temporal analysis: {str(e)}")
            raise

    def perform_categorical_analysis(self, file_path: str, column: str) -> Dict[str, Any]:
        """Perform categorical analysis for API endpoint"""
        try:
            self._load_dataframe(file_path)
            categorical = self.categorical_analysis(column)
            return self._convert_numpy_types(categorical)
        except Exception as e:
            self.logger.error(f"Error performing categorical analysis: {str(e)}")
            raise

    def perform_numerical_analysis(self, file_path: str, column: str) -> Dict[str, Any]:
        """Perform numerical analysis for API endpoint"""
        try:
            self._load_dataframe(file_path)
            if column not in self.df.columns:
                raise ValueError(f"Column {column} not found")
            data = self.df[column]
            if not pd.api.types.is_numeric_dtype(data):
                raise ValueError(f"Column {column} is not numeric")
            numerical = {
                'column': column,
                'basic_stats': self._get_descriptive_statistics(data),
                'distribution': self._analyze_numeric_distribution(data),
                'outliers': self._analyze_outliers(data),
                'normality': self._test_normality(data)
            }
            return self._convert_numpy_types(numerical)
        except Exception as e:
            self.logger.error(f"Error performing numerical analysis: {str(e)}")
            raise

    def get_recommendations(self, file_path: str, column: str) -> Dict[str, Any]:
        """Get recommendations for API endpoint"""
        try:
            self._load_dataframe(file_path)
            if column not in self.df.columns:
                raise ValueError(f"Column {column} not found")
            data = self.df[column]
            # Re-running a simplified univariate analysis to get recommendations
            analysis_for_recs = self.univariate_analysis(column)
            recommendations = {
                'column': column,
                'recommendations': analysis_for_recs.get('recommendations', [])
            }
            return self._convert_numpy_types(recommendations)
        except Exception as e:
            self.logger.error(f"Error getting recommendations: {str(e)}")
            raise

    def comprehensive_column_summary(self, column: str) -> Dict[str, Any]:
        """Generate comprehensive column summary"""
        try:
            if column not in self.df.columns:
                raise ValueError(f"Column {column} not found")
            data = self.df[column]
            summary = {
                'column_name': column,
                'data_type': str(data.dtype),
                'basic_statistics': self._get_basic_info(data),
                'quality_metrics': self._get_quality_metrics(data),
                'distribution_summary': {},
                'outlier_summary': {},
                'normality_assessment': {},
                'cardinality_assessment': {},
                'temporal_summary': {},
                'insights': [],
                'recommendations': [],
                'analysis_completeness': {}
            }
            # Type-specific analysis
            if pd.api.types.is_numeric_dtype(data):
                summary['distribution_summary'] = self._analyze_numeric_distribution(data)
                summary['outlier_summary'] = self._get_outlier_summary(data)
                summary['normality_assessment'] = self._assess_normality(data)
                summary['insights'].extend(self._generate_numeric_insights(data, column))
            elif data.dtype == 'object' or pd.api.types.is_categorical_dtype(data):
                summary['distribution_summary'] = self._analyze_categorical_distribution(data)
                summary['cardinality_assessment'] = self._assess_cardinality(data)
                summary['insights'].extend(self._generate_categorical_insights(data, column))
            elif pd.api.types.is_datetime64_any_dtype(data):
                summary['temporal_summary'] = self._get_temporal_summary(data)
                summary['insights'].extend(self._generate_temporal_insights(data, column))
            # Overall recommendations
            summary['recommendations'] = self._generate_comprehensive_recommendations(data, column, summary)
            # Analysis completeness score
            summary['analysis_completeness'] = self._calculate_analysis_completeness(summary)
            return summary
        except Exception as e:
            self.logger.error(f"Error generating comprehensive summary for column {column}: {str(e)}")
            raise

    def data_quality_analysis(self, column: str) -> Dict[str, Any]:
        """Comprehensive data quality analysis"""
        try:
            if column not in self.df.columns:
                raise ValueError(f"Column {column} not found")
            data = self.df[column]
            quality_analysis = {
                'column': column,
                'completeness': self._assess_completeness(data),
                'consistency': self._assess_consistency(data),
                'validity': self._assess_validity(data),
                'accuracy': self._assess_accuracy(data), # This will likely be a placeholder
                'uniqueness': self._assess_uniqueness(data),
                'overall_score': 0,
                'issues': [],
                'recommendations': []
            }
            # Calculate overall quality score
            scores = [
                quality_analysis['completeness']['score'],
                quality_analysis['consistency']['score'],
                quality_analysis['validity']['score'],
                quality_analysis['accuracy']['score'],
                quality_analysis['uniqueness']['score']
            ]
            # Handle potential non-numeric scores if applicable
            numeric_scores = [s for s in scores if isinstance(s, (int, float))]
            quality_analysis['overall_score'] = np.mean(numeric_scores) if numeric_scores else 0.0

            # Collect issues
            for dimension, assessment in quality_analysis.items():
                if isinstance(assessment, dict) and 'issues' in assessment:
                    quality_analysis['issues'].extend(assessment['issues'])
            # Remove duplicates from issues list
            quality_analysis['issues'] = list(set(quality_analysis['issues']))

            # Generate recommendations
            quality_analysis['recommendations'] = self._generate_quality_recommendations(quality_analysis)
            return self._convert_numpy_types(quality_analysis)
        except Exception as e:
            self.logger.error(f"Error in data quality analysis for column {column}: {str(e)}")
            raise

    def statistical_analysis(self, column: str) -> Dict[str, Any]:
        """Comprehensive statistical analysis"""
        try:
            if column not in self.df.columns:
                raise ValueError(f"Column {column} not found")
            data = self.df[column].dropna()
            analysis = {
                'column': column,
                'descriptive_statistics': {},
                'inferential_statistics': {},
                'hypothesis_tests': {},
                'confidence_intervals': {},
                'effect_sizes': {},
                'recommendations': []
            }
            if pd.api.types.is_numeric_dtype(data):
                analysis['descriptive_statistics'] = self._get_descriptive_statistics(data)
                analysis['inferential_statistics'] = self._get_inferential_statistics(data)
                analysis['hypothesis_tests'] = self._run_hypothesis_tests(data)
                analysis['confidence_intervals'] = self._calculate_confidence_intervals(data)
                analysis['effect_sizes'] = self._calculate_effect_sizes(data)
            else:
                analysis['descriptive_statistics'] = self._get_categorical_statistics(data)
                analysis['hypothesis_tests'] = self._run_categorical_tests(data) # This might need to be specific for categorical
            analysis['recommendations'] = self._generate_statistical_recommendations(analysis)
            return self._convert_numpy_types(analysis)
        except Exception as e:
            self.logger.error(f"Error in statistical analysis for column {column}: {str(e)}")
            raise

    # Helper methods for analysis components
    def _get_basic_info(self, data: pd.Series) -> Dict[str, Any]:
        """Get basic information about the column"""
        total_count = len(data)
        non_null_count = data.count()
        null_count = total_count - non_null_count
        return {
            'count': int(total_count),
            'non_null_count': int(non_null_count),
            'null_count': int(null_count),
            'null_percentage': float((null_count / total_count) * 100) if total_count > 0 else 0.0,
            'unique_count': int(data.nunique()),
            'unique_percentage': float((data.nunique() / total_count) * 100) if total_count > 0 else 0.0,
            'memory_usage': int(data.memory_usage(deep=True)),
            'data_type': str(data.dtype)
        }

    def _analyze_missing_values(self, data: pd.Series) -> Dict[str, Any]:
        """Analyze missing values"""
        missing_count = data.isnull().sum()
        total_count = len(data)
        missing_percentage = (missing_count / total_count) * 100 if total_count > 0 else 0.0

        severity = 'low'
        if missing_percentage > 20:
            severity = 'high'
        elif missing_percentage > 5:
            severity = 'medium'

        return {
            'missing_count': int(missing_count),
            'missing_percentage': float(missing_percentage),
            'has_missing': missing_count > 0,
            'severity': severity
        }

    def _analyze_uniqueness(self, data: pd.Series) -> Dict[str, Any]:
        """Analyze uniqueness of values"""
        unique_count = data.nunique()
        total_count = len(data)
        unique_percentage = (unique_count / total_count) * 100 if total_count > 0 else 0.0
        duplicate_count = total_count - unique_count

        cardinality = 'low'
        if total_count > 0:
            if unique_percentage > 80:
                cardinality = 'high'
            elif unique_percentage > 50:
                cardinality = 'medium'

        return {
            'unique_count': int(unique_count),
            'unique_percentage': float(unique_percentage),
            'has_duplicates': unique_count < total_count,
            'duplicate_count': int(duplicate_count),
            'cardinality': cardinality
        }

    def _analyze_numeric_distribution(self, data: pd.Series) -> Dict[str, Any]:
        """Analyze numeric distribution"""
        clean_data = data.dropna()
        n_obs = len(clean_data)

        # Handle empty data case
        if n_obs == 0:
            return {
                'mean': None, 'median': None, 'mode': None, 'std': None, 'variance': None,
                'min': None, 'max': None, 'range': None, 'iqr': None, 'skewness': None,
                'kurtosis': None, 'cv': None, 'q1': None, 'q3': None, 'count': 0
            }

        # Calculate quartiles
        q1 = float(clean_data.quantile(0.25))
        q3 = float(clean_data.quantile(0.75))
        iqr = q3 - q1
        mean_val = clean_data.mean()
        std_val = clean_data.std()
        cv = std_val / mean_val if mean_val != 0 else float('inf')

        mode_val = None
        if not clean_data.mode().empty:
            mode_val = float(clean_data.mode().iloc[0])

        return {
            'mean': float(mean_val),
            'median': float(clean_data.median()),
            'mode': mode_val,
            'std': float(std_val),
            'variance': float(clean_data.var()),
            'min': float(clean_data.min()),
            'max': float(clean_data.max()),
            'range': float(clean_data.max() - clean_data.min()),
            'iqr': float(iqr),
            'q1': q1,
            'q3': q3,
            'skewness': float(stats.skew(clean_data)),
            'kurtosis': float(stats.kurtosis(clean_data)),
            'cv': float(cv),
            'count': int(n_obs)
        }

    def _analyze_categorical_distribution(self, data: pd.Series) -> Dict[str, Any]:
        """Analyze categorical distribution"""
        value_counts = data.value_counts()
        total_count = len(data)

        if total_count == 0:
            return {
                'unique_values': 0, 'most_frequent': None, 'most_frequent_count': 0,
                'least_frequent': None, 'least_frequent_count': 0, 'value_counts': {},
                'entropy': 0.0, 'concentration': 0.0, 'count': 0
            }

        most_frequent_val = value_counts.index[0] if not value_counts.empty else None
        most_frequent_count = value_counts.iloc[0] if not value_counts.empty else 0
        least_frequent_val = value_counts.index[-1] if not value_counts.empty else None
        least_frequent_count = value_counts.iloc[-1] if not value_counts.empty else 0

        # Calculate entropy and concentration
        if total_count > 0 and len(value_counts) > 0:
            probabilities = value_counts.values / total_count
            entropy = stats.entropy(probabilities)
            concentration = value_counts.iloc[0] / total_count if total_count > 0 else 0.0
        else:
            entropy = 0.0
            concentration = 0.0

        return {
            'unique_values': int(data.nunique()),
            'most_frequent': str(most_frequent_val) if most_frequent_val is not None else None,
            'most_frequent_count': int(most_frequent_count),
            'least_frequent': str(least_frequent_val) if least_frequent_val is not None else None,
            'least_frequent_count': int(least_frequent_count),
            'value_counts': {str(k): int(v) for k, v in value_counts.head(20).to_dict().items()},
            'entropy': float(entropy),
            'concentration': float(concentration),
            'count': int(total_count)
        }

    def _analyze_outliers(self, data: pd.Series) -> Dict[str, Any]:
        """Analyze outliers using multiple methods"""
        clean_data = data.dropna()
        n_obs = len(clean_data)
        if n_obs == 0:
            return {
                'iqr_method': {'count': 0, 'percentage': 0.0, 'lower_bound': None, 'upper_bound': None},
                'zscore_method': {'count': 0, 'percentage': 0.0},
                'modified_zscore_method': {'count': 0, 'percentage': 0.0}
            }

        # IQR method
        Q1 = clean_data.quantile(0.25)
        Q3 = clean_data.quantile(0.75)
        IQR = Q3 - Q1
        iqr_lower_bound = Q1 - 1.5 * IQR
        iqr_upper_bound = Q3 + 1.5 * IQR
        iqr_outliers = clean_data[(clean_data < iqr_lower_bound) | (clean_data > iqr_upper_bound)]

        # Z-score method
        z_scores = np.abs(stats.zscore(clean_data))
        zscore_outliers = clean_data[z_scores > 3]

        # Modified Z-score method
        median = clean_data.median()
        try:
            mad = stats.median_abs_deviation(clean_data)
            # Handle cases where MAD is zero or very close to zero
            if mad == 0:
                modified_z_scores = np.zeros_like(clean_data)
            else:
                modified_z_scores = 0.6745 * (clean_data - median) / mad
            modified_zscore_outliers = clean_data[np.abs(modified_z_scores) > 3.5]
        except Exception: # Catch potential division by zero or other MAD issues
            modified_zscore_outliers = pd.Series(dtype=clean_data.dtype) # Empty series

        return {
            'iqr_method': {
                'count': len(iqr_outliers),
                'percentage': (len(iqr_outliers) / n_obs) * 100,
                'lower_bound': float(iqr_lower_bound),
                'upper_bound': float(iqr_upper_bound)
            },
            'zscore_method': {
                'count': len(zscore_outliers),
                'percentage': (len(zscore_outliers) / n_obs) * 100
            },
            'modified_zscore_method': {
                'count': len(modified_zscore_outliers),
                'percentage': (len(modified_zscore_outliers) / n_obs) * 100
            }
        }

    def _test_normality(self, data: pd.Series) -> Dict[str, Any]:
        """Test for normality"""
        clean_data = data.dropna()
        n_obs = len(clean_data)
        results = {}

        if n_obs < 3:
            return {'error': 'Insufficient data (less than 3 observations) for normality tests'}

        # Shapiro-Wilk test
        if n_obs <= 5000:
            try:
                stat, p_value = stats.shapiro(clean_data)
                results['shapiro_wilk'] = {
                    'statistic': float(stat),
                    'p_value': float(p_value),
                    'is_normal': p_value > 0.05
                }
            except Exception as e:
                results['shapiro_wilk'] = {'error': f'Test failed: {str(e)}'}
        else:
            results['shapiro_wilk'] = {'note': 'Sample size too large for Shapiro-Wilk test'}

        # Kolmogorov-Smirnov test (for normality, comparing to standard normal distribution)
        try:
            # Ensure data is not constant for K-S test
            if clean_data.nunique() > 1:
                stat, p_value = stats.kstest(clean_data, 'norm', args=(clean_data.mean(), clean_data.std()))
                results['kolmogorov_smirnov'] = {
                    'statistic': float(stat),
                    'p_value': float(p_value),
                    'is_normal': p_value > 0.05
                }
            else:
                 results['kolmogorov_smirnov'] = {'note': 'Data is constant, K-S test not applicable'}
        except Exception as e:
            results['kolmogorov_smirnov'] = {'error': f'Test failed: {str(e)}'}

        # Anderson-Darling test
        try:
            result = stats.anderson(clean_data, dist='norm')
            # Interpretation based on critical values
            is_normal_ad = False
            for i in range(len(result.critical_values)):
                if result.significance_levels[i] < 5.0: # Significance level of 5%
                    if result.statistic < result.critical_values[i]:
                        is_normal_ad = True
                        break
            results['anderson_darling'] = {
                'statistic': float(result.statistic),
                'critical_values': result.critical_values.tolist(),
                'significance_levels': result.significance_levels.tolist(),
                'is_normal_at_5_percent': is_normal_ad
            }
        except Exception as e:
            results['anderson_darling'] = {'error': f'Test failed: {str(e)}'}

        return results

    def _generate_numeric_insights(self, data: pd.Series, column: str) -> List[str]:
        """Generate insights for numeric columns"""
        insights = []
        clean_data = data.dropna()
        if len(clean_data) == 0:
            return ["No valid numeric data to generate insights."]

        mean_val = clean_data.mean()
        median_val = clean_data.median()
        std_val = clean_data.std()
        skewness = stats.skew(clean_data)
        kurtosis = stats.kurtosis(clean_data)

        # Central tendency insights
        if std_val > 0 and abs(mean_val - median_val) / std_val > 0.5:
            insights.append(f"Mean ({mean_val:.2f}) and median ({median_val:.2f}) differ significantly, suggesting a skewed distribution.")
        elif std_val > 0 and abs(mean_val - median_val) / std_val < 0.1:
            insights.append(f"Mean ({mean_val:.2f}) and median ({median_val:.2f}) are very close, indicating a symmetric distribution.")

        # Skewness insights
        if abs(skewness) > 1:
            direction = "right" if skewness > 0 else "left"
            insights.append(f"Distribution is highly {direction}-skewed (skewness: {skewness:.2f}). Consider transformations.")
        elif abs(skewness) > 0.5:
            direction = "right" if skewness > 0 else "left"
            insights.append(f"Distribution shows moderate {direction}-skewness (skewness: {skewness:.2f}).")

        # Kurtosis insights
        if abs(kurtosis) > 1:
            if kurtosis > 0:
                insights.append(f"Distribution has heavier tails than normal (leptokurtic, kurtosis: {kurtosis:.2f}), indicating more extreme values.")
            else:
                insights.append(f"Distribution has lighter tails than normal (platykurtic, kurtosis: {kurtosis:.2f}), indicating fewer extreme values.")
        elif abs(kurtosis) < 0.5:
             insights.append(f"Distribution has tails similar to a normal distribution (mesokurtic, kurtosis: {kurtosis:.2f}).")

        # Variability insights
        cv = std_val / mean_val if mean_val != 0 else np.inf
        if not np.isinf(cv):
            if cv > 1:
                insights.append(f"High variability relative to the mean (coefficient of variation: {cv:.2f}).")
            elif cv < 0.5:
                insights.append(f"Low variability relative to the mean (coefficient of variation: {cv:.2f}).")
        else:
            insights.append("Mean is zero or undefined, coefficient of variation is not applicable.")

        # Range insights
        data_range = clean_data.max() - clean_data.min()
        if data_range == 0 and len(clean_data) > 1:
            insights.append("All values are identical, indicating a constant column.")

        return insights

    def _generate_categorical_insights(self, data: pd.Series, column: str) -> List[str]:
        """Generate insights for categorical columns"""
        insights = []
        unique_count = data.nunique()
        total_count = len(data)

        if total_count == 0:
            return ["No valid categorical data to generate insights."]

        value_counts = data.value_counts()

        # Cardinality insights
        if unique_count == total_count:
            insights.append("Every value is unique. This column might be an identifier or contain high cardinality data.")
        elif unique_count / total_count > 0.8:
            insights.append(f"Very high cardinality: {unique_count} unique values out of {total_count} total. Consider grouping rare categories.")
        elif unique_count <= 10:
            insights.append(f"Low cardinality: {unique_count} unique values. Suitable for one-hot encoding or label encoding.")
        elif unique_count <= 50:
             insights.append(f"Moderate cardinality: {unique_count} unique values. Consider grouping rare categories if needed.")

        # Distribution insights
        if not value_counts.empty:
            most_frequent_pct = (value_counts.iloc[0] / total_count) * 100
            if most_frequent_pct > 90:
                insights.append(f"Highly concentrated: The top category '{value_counts.index[0]}' accounts for {most_frequent_pct:.1f}% of the data.")
            elif most_frequent_pct < 5:
                insights.append("Distribution appears relatively uniform with no single dominant category.")
            elif most_frequent_pct > 50:
                insights.append(f"The dominant category '{value_counts.index[0]}' accounts for {most_frequent_pct:.1f}% of the data.")

        return insights

    def _generate_temporal_insights(self, data: pd.Series, column: str) -> List[str]:
        """Generate insights for temporal columns"""
        insights = []
        data_clean = data.dropna()
        if len(data_clean) == 0:
            return ["No valid datetime values found to generate insights."]

        date_range_days = (data_clean.max() - data_clean.min()).days
        insights.append(f"The date range spans {date_range_days} days.")

        # Check for patterns
        years_present = data_clean.dt.year.nunique()
        if years_present == 1:
            insights.append("All dates fall within the same year.")
        elif years_present < 5:
            insights.append(f"Data covers {years_present} years, which is a limited time span.")

        # Check common temporal patterns (e.g., day of week, month)
        day_of_week_counts = data_clean.dt.dayofweek.value_counts().sort_index()
        if len(day_of_week_counts) > 0 and day_of_week_counts.max() / len(data_clean) > 0.2:
            most_common_dow = day_of_week_counts.idxmax()
            insights.append(f"There's a noticeable pattern in the day of the week, with {['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'][most_common_dow]} being more frequent.")

        month_counts = data_clean.dt.month.value_counts().sort_index()
        if len(month_counts) > 0 and month_counts.max() / len(data_clean) > 0.2:
            most_common_month = month_counts.idxmax()
            insights.append(f"There's a noticeable pattern in the month, with month {most_common_month} being more frequent.")

        return insights

    def _generate_column_recommendations(self, data: pd.Series, column: str, analysis: Dict[str, Any]) -> List[str]:
        """Generate recommendations for column based on univariate analysis"""
        recommendations = []
        basic_info = analysis.get('basic_info', {})
        missing_pct = basic_info.get('null_percentage', 0)
        unique_pct = basic_info.get('unique_percentage', 0)

        # Missing values
        if missing_pct > 20:
            recommendations.append("Consider imputation strategies (e.g., mean, median, mode) or removing rows/columns with high missing values.")
        elif missing_pct > 5:
            recommendations.append("Investigate missing value patterns. Consider simple imputation or more advanced methods if patterns are found.")

        # Data type specific recommendations
        if pd.api.types.is_numeric_dtype(data):
            distribution = analysis.get('distribution_analysis', {})
            skewness = distribution.get('skewness', 0)
            if abs(skewness) > 1:
                recommendations.append("The distribution is highly skewed. Consider applying transformations (e.g., log, square root) to normalize it.")
            elif abs(skewness) > 0.5:
                recommendations.append("The distribution shows moderate skewness. Transformations might improve model performance.")

            outlier_summary = analysis.get('outlier_analysis', {})
            if outlier_summary and 'iqr_method' in outlier_summary:
                outlier_pct = outlier_summary['iqr_method'].get('percentage', 0)
                if outlier_pct > 5:
                    recommendations.append("A significant percentage of outliers were detected. Investigate their cause and consider appropriate handling (e.g., capping, removal, transformation).")

            normality_tests = analysis.get('normality_tests', {})
            if 'shapiro_wilk' in normality_tests and normality_tests['shapiro_wilk'].get('p_value', 1) < 0.05:
                recommendations.append("Normality tests suggest the data is not normally distributed. Consider transformations or non-parametric methods.")

        elif data.dtype == 'object' or pd.api.types.is_categorical_dtype(data):
            if unique_pct > 80:
                recommendations.append("High cardinality detected. Consider grouping rare categories, using target encoding, or feature hashing.")
            elif unique_pct > 50:
                recommendations.append("Moderate to high cardinality. Grouping rare categories or using target encoding might be beneficial.")
            elif unique_pct < 10:
                recommendations.append("Low cardinality detected. One-hot encoding or label encoding are suitable options.")

        if basic_info.get('unique_count', 0) == len(data) and len(data) > 1:
            recommendations.append("All values are unique. This column might be an identifier and could potentially be removed if not used as a feature.")

        return recommendations

    # Additional helper methods for complex analyses
    def _determine_relationship_type(self, data1: pd.Series, data2: pd.Series) -> str:
        """Determine the type of relationship between two variables"""
        is_num1 = pd.api.types.is_numeric_dtype(data1)
        is_num2 = pd.api.types.is_numeric_dtype(data2)
        if is_num1 and is_num2:
            return 'numeric_numeric'
        elif is_num1 or is_num2:
            return 'numeric_categorical'
        else:
            return 'categorical_categorical'

    def _analyze_numeric_correlation(self, data1: pd.Series, data2: pd.Series) -> Dict[str, Any]:
        """Analyze correlation between numeric variables"""
        pearson_corr, pearson_p = np.nan, np.nan
        spearman_corr, spearman_p = np.nan, np.nan
        correlation_strength = 'weak'

        try:
            if data1.nunique() > 1 and data2.nunique() > 1:
                pearson_corr, pearson_p = stats.pearsonr(data1, data2)
                correlation_strength = self._interpret_correlation_strength(abs(pearson_corr))
            else:
                correlation_strength = 'undefined (constant data)'

            if data1.nunique() > 1 and data2.nunique() > 1:
                spearman_corr, spearman_p = stats.spearmanr(data1, data2)
            else:
                 spearman_corr, spearman_p = np.nan, np.nan # Handle constant data

        except Exception as e:
            self.logger.warning(f"Correlation calculation failed: {e}")

        return {
            'pearson': {
                'correlation': float(pearson_corr) if not np.isnan(pearson_corr) else None,
                'p_value': float(pearson_p) if not np.isnan(pearson_p) else None,
                'significant': pearson_p < 0.05 if not np.isnan(pearson_p) else False
            },
            'spearman': {
                'correlation': float(spearman_corr) if not np.isnan(spearman_corr) else None,
                'p_value': float(spearman_p) if not np.isnan(spearman_p) else None,
                'significant': spearman_p < 0.05 if not np.isnan(spearman_p) else False
            },
            'correlation_strength': correlation_strength
        }

    def _interpret_correlation_strength(self, correlation: float) -> str:
        """Interpret correlation strength"""
        if pd.isna(correlation):
            return 'N/A'
        if correlation < 0.3:
            return 'weak'
        elif correlation < 0.7:
            return 'moderate'
        else:
            return 'strong'

    # Placeholder methods for complex analyses (can be expanded)
    def _run_numeric_tests(self, data1: pd.Series, data2: pd.Series) -> Dict[str, Any]:
        """Run statistical tests for numeric variables"""
        # Example: Independent t-test if data2 is binary categorical
        if data1.nunique() > 1 and data2.nunique() == 2:
            try:
                group1 = data1[data2 == data2.unique()[0]]
                group2 = data1[data2 == data2.unique()[1]]
                if len(group1) > 1 and len(group2) > 1:
                    ttest_stat, ttest_p = stats.ttest_ind(group1, group2, equal_var=False) # Welch's t-test
                    return {
                        'welch_ttest': {
                            'statistic': float(ttest_stat),
                            'p_value': float(ttest_p),
                            'significant': ttest_p < 0.05
                        }
                    }
                else:
                    return {'note': 'Not enough data in one or both groups for t-test.'}
            except Exception as e:
                return {'error': f'T-test calculation failed: {str(e)}'}
        return {'note': 'Advanced statistical tests implementation pending (e.g., ANOVA for >2 groups)'}

    def _analyze_numeric_categorical(self, data1: pd.Series, data2: pd.Series, col1: str, col2: str) -> Dict[str, Any]:
        """Analyze relationship between numeric and categorical variables"""
        results = {}
        # Get summary stats of numeric variable per category
        results['summary_by_category'] = data1.groupby(data2).agg(['mean', 'median', 'std', 'count']).to_dict('index')
        # Example: ANOVA if categorical has > 2 levels
        if data1.nunique() > 1 and data2.nunique() > 2:
            try:
                groups = [data1[data2 == cat] for cat in data2.unique()]
                # Remove empty groups to avoid errors in f_oneway
                groups = [g for g in groups if len(g) > 0]
                if len(groups) > 1:
                    f_stat, f_p = stats.f_oneway(*groups)
                    results['anova_test'] = {
                        'statistic': float(f_stat),
                        'p_value': float(f_p),
                        'significant': f_p < 0.05
                    }
                else:
                    results['anova_test'] = {'note': 'Not enough valid groups for ANOVA.'}
            except Exception as e:
                results['anova_test'] = {'error': f'ANOVA calculation failed: {str(e)}'}
        return results

    def _run_numeric_categorical_tests(self, data1: pd.Series, data2: pd.Series, col1: str, col2: str) -> Dict[str, Any]:
        """Run tests for numeric-categorical relationship"""
        return self._run_numeric_tests(data1, data2) # Reuse numeric test logic for the moment

    def _analyze_categorical_association(self, data1: pd.Series, data2: pd.Series) -> Dict[str, Any]:
        """Analyze association between categorical variables"""
        results = {}
        contingency_table = pd.crosstab(data1, data2)
        results['contingency_table'] = contingency_table.applymap(int).to_dict('index') # Convert to int for JSON

        # Chi-squared test for independence
        try:
            if contingency_table.shape[0] > 1 and contingency_table.shape[1] > 1:
                chi2, p_value, dof, expected = stats.chi2_contingency(contingency_table)
                results['chi_squared_test'] = {
                    'statistic': float(chi2),
                    'p_value': float(p_value),
                    'degrees_of_freedom': int(dof),
                    'significant': p_value < 0.05
                }
            else:
                results['chi_squared_test'] = {'note': 'Contingency table too small for Chi-squared test.'}
        except Exception as e:
            results['chi_squared_test'] = {'error': f'Chi-squared test failed: {str(e)}'}

        # Cramer's V for effect size
        if 'chi_squared_test' in results and results['chi_squared_test'].get('statistic') is not None:
            try:
                # Handle cases where n is 0
                n = contingency_table.sum().sum()
                if n > 0:
                    chi2_val = results['chi_squared_test']['statistic']
                    min_dim = min(contingency_table.shape) - 1
                    cramers_v = np.sqrt(chi2_val / (n * min_dim)) if min_dim > 0 else 0
                    results['cramers_v'] = float(cramers_v)
                else:
                    results['cramers_v'] = 0.0
            except Exception as e:
                results['cramers_v'] = {'error': f'Cramer\'s V calculation failed: {str(e)}'}

        return results

    def _run_categorical_tests(self, data1: pd.Series, data2: pd.Series) -> Dict[str, Any]:
        """Run tests for categorical variables"""
        return self._analyze_categorical_association(data1, data2) # Reuse association logic

    def _generate_numeric_bivariate_insights(self, data1: pd.Series, data2: pd.Series, col1: str, col2: str) -> List[str]:
        """Generate insights for numeric bivariate analysis"""
        insights = []
        corr_analysis = self._analyze_numeric_correlation(data1, data2)
        correlation = corr_analysis.get('pearson', {}).get('correlation')
        significance = corr_analysis.get('pearson', {}).get('significant')

        if correlation is not None:
            strength = self._interpret_correlation_strength(abs(correlation))
            if strength == 'strong':
                insights.append(f"Strong {('positive' if correlation > 0 else 'negative')} linear relationship between {col1} and {col2}.")
            elif strength == 'moderate':
                insights.append(f"Moderate {('positive' if correlation > 0 else 'negative')} linear relationship between {col1} and {col2}.")
            else:
                insights.append(f"Weak {('positive' if correlation > 0 else 'negative')} linear relationship between {col1} and {col2}.")

            if significance:
                insights.append(f"The relationship between {col1} and {col2} is statistically significant.")
            else:
                insights.append(f"The relationship between {col1} and {col2} is not statistically significant.")
        return insights

    def _generate_numeric_categorical_insights(self, data1: pd.Series, data2: pd.Series, col1: str, col2: str) -> List[str]:
        """Generate insights for numeric-categorical analysis"""
        insights = []
        num_data, cat_data = (data1, data2) if pd.api.types.is_numeric_dtype(data1) else (data2, data1)
        num_col, cat_col = (col1, col2) if pd.api.types.is_numeric_dtype(data1) else (col2, col1)

        # Group numeric values by each category
        groups = [num_data[cat_data == cat].dropna() for cat in cat_data.unique()]

        # Check for differences in means/medians
        if len(groups) > 1 and all(len(g) > 1 for g in groups):
            stat, p_value = kruskal(*groups)
            if p_value < 0.05:
               insights.append(f"The median of {num_col} differs significantly across categories of {cat_col} (Kruskal-Wallis p={p_value:.4f}).")
        # If ANOVA was performed and significant
        anova_results = self._analyze_numeric_categorical(num_data, cat_data, num_col, cat_col)
        if 'anova_test' in anova_results and anova_results['anova_test'].get('significant'):
            insights.append(f"ANOVA indicates a statistically significant difference in {num_col} across the categories of {cat_col}.")
        return insights

    def _generate_categorical_bivariate_insights(self, data1: pd.Series, data2: pd.Series, col1: str, col2: str) -> List[str]:
        """Generate insights for categorical bivariate analysis"""
        insights = []
        association_results = self._analyze_categorical_association(data1, data2)

        if 'chi_squared_test' in association_results:
            chi2_info = association_results['chi_squared_test']
            if chi2_info.get('significant'):
                insights.append(f"There is a statistically significant association between {col1} and {col2}.")
            else:
                insights.append(f"There is no statistically significant association between {col1} and {col2}.")

        if 'cramers_v' in association_results:
            cramers_v = association_results['cramers_v']
            if isinstance(cramers_v, (int, float)):
                if cramers_v > 0.5:
                    insights.append(f"Strong association detected between {col1} and {col2} (Cramer's V = {cramers_v:.2f}).")
                elif cramers_v > 0.3:
                    insights.append(f"Moderate association detected between {col1} and {col2} (Cramer's V = {cramers_v:.2f}).")
                elif cramers_v > 0:
                    insights.append(f"Weak association detected between {col1} and {col2} (Cramer's V = {cramers_v:.2f}).")
                else:
                    insights.append(f"No significant association detected between {col1} and {col2} (Cramer's V = {cramers_v:.2f}).")
        return insights

    def _generate_bivariate_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate recommendations for bivariate analysis"""
        recommendations = []
        rel_type = analysis['relationship_type']
        insights = analysis['insights']

        if rel_type == 'numeric_numeric':
            if any("strong" in insight.lower() for insight in insights) and \
               any("significant" in insight.lower() for insight in insights):
                recommendations.append("Consider the strong correlation for feature engineering or modeling.")
            if any("outlier" in insight.lower() for insight in insights):
                recommendations.append("Investigate outliers and their potential impact on the correlation.")

        elif rel_type == 'numeric_categorical':
            if any("significant difference" in insight.lower() or "significant" in insight.lower() for insight in insights):
                recommendations.append("The numeric variable differs significantly across categories. Useful for predictive modeling.")
            else:
                recommendations.append("No significant difference observed in the numeric variable across categories. May not be a strong predictor.")

        elif rel_type == 'categorical_categorical':
            if any("significant association" in insight.lower() or "strong association" in insight.lower() for insight in insights):
                recommendations.append("The categorical variables are associated. Useful for modeling or understanding relationships.")
            elif any("weak association" in insight.lower() for insight in insights):
                recommendations.append("The association between categories is weak. May have limited predictive power.")
            else:
                recommendations.append("No significant association found between the categories. They might be independent.")

        # General recommendation based on missing values from the bivariate context
        if analysis.get('error') == 'No valid pairs after removing missing values':
            recommendations.append("High amount of missing data between these columns hinders analysis. Consider imputation or data cleaning.")

        return recommendations

    # Additional placeholder methods
    def _find_high_correlations(self, corr_matrix: pd.DataFrame) -> List[Dict[str, Any]]:
        """Find high correlations in matrix"""
        high_corrs = []
        # Use stack to get pairs and values, then filter
        stacked_corr = corr_matrix.stack()
        # Filter out self-correlations and duplicates (upper triangle)
        pairs = stacked_corr.reset_index()
        pairs.columns = ['col1', 'col2', 'correlation']
        pairs = pairs[pairs['col1'] < pairs['col2']] # Consider only upper triangle

        for _, row in pairs.iterrows():
            if abs(row['correlation']) >= 0.7: # Threshold for high correlation
                high_corrs.append({
                    'column1': row['col1'],
                    'column2': row['col2'],
                    'correlation': float(row['correlation']),
                    'strength': self._interpret_correlation_strength(abs(row['correlation']))
                })
        return high_corrs

    def _detect_multicollinearity(self, corr_matrix: pd.DataFrame) -> Dict[str, Any]:
        """Detect multicollinearity"""
        # A simple approach using correlation matrix: identify highly correlated pairs
        high_correlations = self._find_high_correlations(corr_matrix)
        if high_correlations:
            return {
                'issue': 'High multicollinearity detected between some predictor variables.',
                'details': high_correlations,
                'recommendation': 'Consider removing one of the highly correlated features, using dimensionality reduction techniques (e.g., PCA), or employing regularization methods.'
            }
        else:
            return {'issue': 'No significant multicollinearity detected based on pairwise correlations (threshold >= 0.7).'}

    def _calculate_feature_importance(self, columns: List[str], target_column: str) -> Dict[str, Any]:
        """Calculate feature importance"""
        # This is a complex task requiring a model. Providing a placeholder.
        # A simple approach would be using mutual information for classification/regression.
        feature_importance = {}
        try:
            X = self.df[columns]
            y = self.df[target_column]

            # Handle non-numeric features for mutual info
            X_numeric = X.select_dtypes(include=[np.number])
            X_categorical = X.select_dtypes(include=['object', 'category'])

            # For classification: Mutual Information
            if pd.api.types.is_categorical_dtype(y) or y.dtype == 'object':
                # Label encode y for mutual_info_classif
                le = LabelEncoder()
                y_encoded = le.fit_transform(y)

                # For numeric features
                if not X_numeric.empty:
                    mi_scores_num = mutual_info_classif(X_numeric, y_encoded, random_state=42)
                    for i, col in enumerate(X_numeric.columns):
                        feature_importance[col] = float(mi_scores_num[i])

                # For categorical features (need to encode them first)
                if not X_categorical.empty:
                    X_cat_encoded = pd.get_dummies(X_categorical, drop_first=True)
                    if not X_cat_encoded.empty:
                        mi_scores_cat = mutual_info_classif(X_cat_encoded, y_encoded, random_state=42)
                        for i, col in enumerate(X_cat_encoded.columns):
                            feature_importance[col] = float(mi_scores_cat[i])

            # For regression: Mutual Information
            else:
                if not X_numeric.empty:
                    mi_scores_num = mutual_info_regression(X_numeric, y, random_state=42)
                    for i, col in enumerate(X_numeric.columns):
                        feature_importance[col] = float(mi_scores_num[i])

                if not X_categorical.empty:
                    X_cat_encoded = pd.get_dummies(X_categorical, drop_first=True)
                    if not X_cat_encoded.empty:
                        mi_scores_cat = mutual_info_regression(X_cat_encoded, y, random_state=42)
                        for i, col in enumerate(X_cat_encoded.columns):
                            feature_importance[col] = float(mi_scores_cat[i])

            # Sort by importance
            sorted_importance = dict(sorted(feature_importance.items(), key=lambda item: item[1], reverse=True))
            return {'method': 'mutual_information', 'scores': sorted_importance}

        except Exception as e:
            return {'error': f'Feature importance calculation failed: {str(e)}'}

    def _analyze_feature_interactions(self, columns: List[str], target_column: str = None) -> Dict[str, Any]:
        """Analyze feature interactions"""
        # This is a complex task, often done through model-based analysis (e.g., interaction terms).
        # A simpler approach might involve looking at conditional statistics or correlations.
        # For now, providing a placeholder.
        return {'note': 'Feature interaction analysis implementation pending. Consider using models that capture interactions (e.g., tree-based models, polynomial features).'}

    def _analyze_dimensionality(self, columns: List[str]) -> Dict[str, Any]:
        """Analyze dimensionality"""
        num_features = len(columns)
        high_dim = num_features > 50 # Arbitrary threshold
        return {
            'number_of_features': num_features,
            'is_high_dimensional': high_dim,
            'recommendations': ['Consider dimensionality reduction techniques (e.g., PCA, feature selection) if the number of features is high.'] if high_dim else []
        }

    def _generate_multivariate_insights(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate multivariate insights"""
        insights = []
        if analysis.get('correlation_matrix') and analysis['correlation_matrix'].get('high_correlations'):
            insights.append("High pairwise correlations were detected among some features, suggesting potential multicollinearity.")
        if analysis.get('feature_importance'):
            top_features = list(analysis['feature_importance'].get('scores', {}).keys())[:3]
            if top_features:
                insights.append(f"Top features for prediction seem to be: {', '.join(top_features)}.")
        return insights

    def _generate_multivariate_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate multivariate recommendations"""
        recommendations = []
        if analysis.get('correlation_matrix') and analysis['correlation_matrix'].get('multicollinearity', {}).get('issue'):
            recommendations.append(f"Address multicollinearity: {analysis['correlation_matrix']['multicollinearity'].get('recommendation')}")
        if analysis.get('dimensionality_analysis', {}).get('is_high_dimensional'):
            recommendations.append(f"Reduce dimensionality: {analysis['dimensionality_analysis'].get('recommendations')[0]}")
        if analysis.get('feature_importance'):
            recommendations.append("Utilize the identified important features for model building. Consider feature selection based on importance scores.")
        return recommendations

    # Additional analysis methods (simplified for space)
    def _detect_outliers_method(self, data: pd.Series, method: str) -> Dict[str, Any]:
        """Detect outliers using specific method"""
        clean_data = data.dropna()
        n_obs = len(clean_data)
        if n_obs == 0:
            return {'count': 0, 'percentage': 0.0, 'lower_bound': None, 'upper_bound': None}

        if method == 'iqr':
            Q1 = clean_data.quantile(0.25)
            Q3 = clean_data.quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            outliers = clean_data[(clean_data < lower_bound) | (clean_data > upper_bound)]
            return {
                'count': len(outliers),
                'percentage': (len(outliers) / n_obs) * 100,
                'lower_bound': float(lower_bound),
                'upper_bound': float(upper_bound)
            }
        elif method == 'zscore':
            z_scores = np.abs(stats.zscore(clean_data))
            outliers = clean_data[z_scores > 3]
            return {
                'count': len(outliers),
                'percentage': (len(outliers) / n_obs) * 100
            }
        elif method == 'modified_zscore':
            median = clean_data.median()
            try:
                mad = stats.median_abs_deviation(clean_data)
                if mad == 0: # Handle constant data
                    modified_z_scores = np.zeros_like(clean_data)
                else:
                    modified_z_scores = 0.6745 * (clean_data - median) / mad
                outliers = clean_data[np.abs(modified_z_scores) > 3.5]
                return {
                    'count': len(outliers),
                    'percentage': (len(outliers) / n_obs) * 100
                }
            except Exception as e: # Catch potential division by zero or MAD issues
                return {'error': f'Calculation failed: {str(e)}'}
        # Add other methods like Isolation Forest if needed (requires sklearn)
        # elif method == 'isolation_forest':
        #     from sklearn.ensemble import IsolationForest
        #     iso_forest = IsolationForest(contamination='auto', random_state=42)
        #     predictions = iso_forest.fit_predict(clean_data.values.reshape(-1, 1))
        #     outlier_indices = np.where(predictions == -1)[0]
        #     return {
        #         'count': len(outlier_indices),
        #         'percentage': (len(outlier_indices) / n_obs) * 100
        #     }
        else:
            return {'error': f'Unsupported outlier detection method: {method}'}

    def _analyze_outlier_impact(self, data: pd.Series, outlier_detections: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze impact of outliers"""
        clean_data = data.dropna()
        n_obs = len(clean_data)
        if n_obs == 0:
            return {'impact_on_mean': None, 'impact_on_std': None}

        impact = {}
        
        # Check if IQR method results are valid and contain the required keys
        iqr_results = outlier_detections.get('iqr_method', {})
        if isinstance(iqr_results, dict) and 'lower_bound' in iqr_results and 'upper_bound' in iqr_results and 'error' not in iqr_results:
            # Impact on mean
            mean_all = clean_data.mean()
            try:
                # Filter outliers based on IQR bounds
                iqr_outliers = clean_data[(clean_data < iqr_results['lower_bound']) | (clean_data > iqr_results['upper_bound'])]
                if len(iqr_outliers) > 0:
                    # Remove outliers and calculate new mean
                    data_without_outliers = clean_data[~clean_data.index.isin(iqr_outliers.index)]
                    if len(data_without_outliers) > 0:
                        mean_without_outliers = data_without_outliers.mean()
                        impact_mean = mean_all - mean_without_outliers
                        impact['impact_on_mean'] = float(impact_mean)
                    else:
                        impact['impact_on_mean'] = 0.0
                else:
                    impact['impact_on_mean'] = 0.0

                # Impact on std deviation
                std_all = clean_data.std()
                if len(iqr_outliers) > 0:
                    data_without_outliers = clean_data[~clean_data.index.isin(iqr_outliers.index)]
                    if len(data_without_outliers) > 1:  # Need at least 2 points for std
                        std_without_outliers = data_without_outliers.std()
                        impact_std = std_all - std_without_outliers
                        impact['impact_on_std'] = float(impact_std)
                    else:
                        impact['impact_on_std'] = 0.0
                else:
                    impact['impact_on_std'] = 0.0
                    
            except Exception as e:
                # If there's any error in the calculation, set default values
                impact['impact_on_mean'] = 0.0
                impact['impact_on_std'] = 0.0
                impact['error'] = f'Impact calculation failed: {str(e)}'
        else:
            # If IQR results are not valid, set default values
            impact['impact_on_mean'] = 0.0
            impact['impact_on_std'] = 0.0
            impact['note'] = 'Impact analysis not available due to outlier detection errors'

        return impact

    def _generate_outlier_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate outlier recommendations"""
        recommendations = []
        outlier_detections = analysis.get('outlier_detection', {})

        # Check which methods detected outliers and the percentage
        for method, detection_info in outlier_detections.items():
            if isinstance(detection_info, dict) and 'percentage' in detection_info and 'error' not in detection_info:
                outlier_percentage = detection_info['percentage']
                if outlier_percentage > 5:
                    recommendations.append(f"Significant outliers detected by '{method}' ({outlier_percentage:.1f}%). Consider investigating and handling them (e.g., capping, transformation, removal).")
                elif outlier_percentage > 1:
                    recommendations.append(f"Moderate outliers detected by '{method}' ({outlier_percentage:.1f}%). Review their presence and potential impact.")

        # Check outlier impact information
        impact = analysis.get('outlier_impact', {})
        if impact.get('impact_on_mean') is not None and impact.get('impact_on_mean') != 0:
            recommendations.append("Outliers appear to be influencing the mean. Consider robust statistical methods or outlier treatment.")
        if impact.get('impact_on_std') is not None and impact.get('impact_on_std') != 0:
            recommendations.append("Outliers appear to be influencing the standard deviation. Consider robust statistical methods or outlier treatment.")

        # General recommendations if outliers were detected
        if any(isinstance(detection_info, dict) and detection_info.get('percentage', 0) > 0 for detection_info in outlier_detections.values()):
            recommendations.append("Consider the context and domain knowledge when deciding how to handle outliers.")
            recommendations.append("Options include: removal, capping/winsorizing, transformation, or using robust algorithms.")

        return recommendations

    def _analyze_missing_patterns(self, column: str) -> Dict[str, Any]:
        """Analyze missing value patterns"""
        # This is a complex task, often requiring looking at patterns across multiple columns.
        # A simple approach for a single column could be to check if missingness is random.
        return {'note': 'Missing value pattern analysis across multiple columns is complex and not fully implemented here.'}

    def _suggest_imputation_methods(self, data: pd.Series) -> List[str]:
        """Suggest imputation methods"""
        methods = []
        if data.isnull().sum() > 0:
            if pd.api.types.is_numeric_dtype(data):
                methods.append("Mean imputation (for normally distributed data without significant outliers)")
                methods.append("Median imputation (robust to outliers)")
                methods.append("Linear interpolation (for time series or ordered data)")
            elif pd.api.types.is_categorical_dtype(data) or data.dtype == 'object':
                methods.append("Mode imputation (most frequent category)")
                methods.append("Constant value imputation (e.g., 'Unknown', 'Missing')")
            # More advanced methods like KNN imputation or regression imputation could be suggested
            methods.append("Consider advanced imputation techniques (e.g., KNN Imputer, IterativeImputer) if simple methods are insufficient.")
        return methods

    def _analyze_missing_impact(self, column: str) -> Dict[str, Any]:
        """Analyze impact of missing values"""
        # This requires comparing analyses with and without missing data, or on imputed data.
        return {'note': 'Impact analysis of missing values requires comparison with complete data, not implemented here.'}

    def _generate_missing_value_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate missing value recommendations"""
        recommendations = []
        missing_info = analysis.get('missing_info', {})
        missing_percentage = missing_info.get('missing_percentage', 0)

        if missing_percentage > 20:
            recommendations.append("High missing percentage (>20%). Consider removing the column if it cannot be reliably imputed or if it significantly biases the data.")
        elif missing_percentage > 5:
            recommendations.append("Moderate missing percentage (5-20%). Explore imputation strategies suitable for the data type and distribution.")
        elif missing_percentage > 0:
            recommendations.append("Low missing percentage (<5%). Simple imputation (mean, median, mode) or dropping missing values might be sufficient.")

        if missing_percentage > 0:
            recommendations.append("Review the suggested imputation methods and choose one that best fits the data characteristics.")
        else:
            recommendations.append("No missing values detected. Data is complete for this column.")
        return recommendations

    def _identify_distribution_type(self, data: pd.Series) -> str:
        """Identify distribution type"""
        if pd.api.types.is_numeric_dtype(data):
            return 'continuous'
        elif pd.api.types.is_categorical_dtype(data) or data.dtype == 'object':
            return 'categorical'
        elif pd.api.types.is_datetime64_any_dtype(data):
            return 'temporal'
        else:
            return 'other'

    def _calculate_distribution_parameters(self, data: pd.Series) -> Dict[str, Any]:
        """Calculate distribution parameters"""
        if pd.api.types.is_numeric_dtype(data):
            return self._analyze_numeric_distribution(data)
        else:
            return self._analyze_categorical_distribution(data)

    def _test_distribution_fit(self, data: pd.Series) -> Dict[str, Any]:
        """Test distribution fit"""
        # This is complex and depends on what distributions to test against.
        # Can include normality tests, or tests against specific known distributions.
        # For now, linking to normality tests as a common requirement.
        if pd.api.types.is_numeric_dtype(data):
            return self._test_normality(data)
        return {'note': 'Distribution fit testing for non-normal distributions not implemented.'}

    def _analyze_transformations(self, data: pd.Series) -> Dict[str, Any]:
        """Analyze potential transformations"""
        recommendations = []
        clean_data = data.dropna()
        if len(clean_data) == 0:
            return {'recommendations': [], 'notes': 'No data for transformation analysis.'}

        if pd.api.types.is_numeric_dtype(data):
            skewness = stats.skew(clean_data)
            if abs(skewness) > 1:
                recommendations.append("Log transformation (ln(x+c)) can help reduce positive skewness.")
                recommendations.append("Square root transformation (sqrt(x)) can also reduce positive skewness.")
            if skewness < -1:
                recommendations.append("Box-Cox transformation can handle both positive and negative skewness.")
                recommendations.append("Reciprocal transformation (1/x) can help reduce negative skewness.")

            # Check for variance stabilizing transformations
            mean_val = clean_data.mean()
            std_val = clean_data.std()
            if mean_val > 0 and std_val / mean_val > 1: # High CV might benefit from variance stabilization
                recommendations.append("Variance stabilizing transformations like log or square root might be beneficial.")

        return {'recommendations': recommendations}

    def _generate_distribution_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate distribution recommendations"""
        recommendations = []
        dist_params = analysis.get('distribution_parameters', {})
        normality = analysis.get('goodness_of_fit', {})

        # Numeric distribution recommendations
        if 'skewness' in dist_params and abs(dist_params['skewness']) > 1:
            recommendations.append("Consider transformations (log, sqrt, Box-Cox) to normalize the distribution due to high skewness.")
        if 'kurtosis' in dist_params and abs(dist_params['kurtosis']) > 1:
            recommendations.append("The distribution has heavy/light tails. Transformations might help moderate extreme values.")

        # Normality test recommendations
        if normality and 'shapiro_wilk' in normality and normality['shapiro_wilk'].get('p_value', 1) < 0.05:
            recommendations.append("Normality tests indicate non-normality. This might affect models assuming normality.")
        if normality and 'anderson_darling' in normality and not normality['anderson_darling'].get('is_normal_at_5_percent'):
            recommendations.append("Anderson-Darling test suggests non-normality. Consider transformations or non-parametric methods.")

        # Categorical distribution recommendations
        if 'concentration' in dist_params and dist_params['concentration'] > 0.7:
            recommendations.append("High concentration in categories. Consider grouping rare categories or simplifying the variable.")

        return recommendations

    def _analyze_encoding_needs(self, data: pd.Series) -> Dict[str, Any]:
        """Analyze encoding needs for categorical data"""
        unique_count = data.nunique()
        total_count = len(data)
        result = {}

        if total_count == 0:
            return {'recommended_encoding': 'N/A', 'reason': 'No data available'}

        if unique_count == 0:
            return {'recommended_encoding': 'N/A', 'reason': 'No unique values found'}
        elif unique_count == 1:
            return {'recommended_encoding': 'constant', 'reason': 'Column has only one unique value'}
        elif unique_count == 2:
            result['recommended_encoding'] = 'label'
            result['reason'] = 'Binary categorical feature. Label encoding is efficient.'
        elif unique_count <= 10:
            result['recommended_encoding'] = 'onehot'
            result['reason'] = f'Low cardinality ({unique_count} categories). One-hot encoding is suitable and manageable.'
        else:
            result['recommended_encoding'] = 'target_or_other'
            result['reason'] = f'High cardinality ({unique_count} categories). Consider target encoding, feature hashing, or grouping rare categories.'
        return result

    def _analyze_cardinality(self, data: pd.Series) -> Dict[str, Any]:
        """Analyze cardinality of categorical data"""
        unique_count = data.nunique()
        total_count = len(data)

        if total_count == 0:
            return {
                'cardinality_level': 'N/A',
                'unique_ratio': 0.0,
                'recommended_action': 'N/A'
            }

        unique_ratio = unique_count / total_count

        cardinality_level = 'low'
        recommended_action = 'standard_encoding'
        if unique_count == 0:
            cardinality_level = 'none'
            recommended_action = 'no_encoding_needed'
        elif unique_count == 1:
            cardinality_level = 'constant'
            recommended_action = 'no_encoding_needed'
        elif unique_ratio > 0.8 or unique_count > 50:
            cardinality_level = 'high'
            recommended_action = 'group_rare_categories_or_target_encode'
        elif unique_ratio > 0.5 or unique_count > 10:
            cardinality_level = 'medium'
            recommended_action = 'consider_grouping_rare_categories'
        else:
            cardinality_level = 'low'
            recommended_action = 'onehot_or_label_encode'

        return {
            'cardinality_level': cardinality_level,
            'unique_ratio': float(unique_ratio),
            'recommended_action': recommended_action
        }

    def _generate_categorical_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate categorical recommendations"""
        recommendations = []
        cardinality_info = analysis.get('cardinality_analysis', {})
        encoding_info = analysis.get('encoding_analysis', {})

        cardinality_level = cardinality_info.get('cardinality_level')
        recommended_encoding = encoding_info.get('recommended_encoding')
        encoding_reason = encoding_info.get('reason')

        if cardinality_level == 'high':
            recommendations.append(f"High cardinality ({analysis.get('category_info', {}).get('unique_values', 'N/A')} categories). {encoding_reason}")
        elif cardinality_level == 'medium':
            recommendations.append(f"Medium cardinality ({analysis.get('category_info', {}).get('unique_values', 'N/A')} categories). {encoding_reason}")
        elif cardinality_level == 'low':
            recommendations.append(f"Low cardinality ({analysis.get('category_info', {}).get('unique_values', 'N/A')} categories). {encoding_reason}")
        elif cardinality_level == 'constant':
            recommendations.append("The column contains only one category. It provides no discriminative power and can be removed.")

        # Add specific recommendation based on encoding analysis
        if recommended_encoding and recommended_encoding != 'N/A' and recommended_encoding != 'constant':
            if 'target_or_other' in recommended_encoding:
                recommendations.append("For high cardinality, explore target encoding or grouping rare categories to create more manageable features.")
            elif recommended_encoding == 'onehot':
                recommendations.append("One-hot encoding is recommended. Be mindful of potential dimensionality increase if the number of categories grows.")
            elif recommended_encoding == 'label':
                recommendations.append("Label encoding is suitable for binary or ordinal categorical data. Ensure no artificial order is implied for nominal data.")

        return recommendations

    def _analyze_temporal_patterns(self, data: pd.Series) -> Dict[str, Any]:
        """Analyze temporal patterns"""
        data_clean = data.dropna()
        if len(data_clean) == 0:
            return {
                'date_range': {'start': None, 'end': None, 'span_days': None},
                'patterns': {'years': 0, 'months': 0, 'days_of_week': 0, 'hours': 0}
            }

        min_date = data_clean.min()
        max_date = data_clean.max()
        span_days = (max_date - min_date).days if pd.notna(min_date) and pd.notna(max_date) else None

        return {
            'date_range': {
                'start': str(min_date) if pd.notna(min_date) else None,
                'end': str(max_date) if pd.notna(max_date) else None,
                'span_days': span_days
            },
            'patterns': {
                'years_present': data_clean.dt.year.nunique(),
                'months_present': data_clean.dt.month.nunique(),
                'days_of_week_present': data_clean.dt.dayofweek.nunique(),
                'hours_present': data_clean.dt.hour.nunique() if pd.api.types.is_datetime64_ns_dtype(data) else 0 # Check if time component exists
            }
        }

    def _analyze_seasonality(self, data: pd.Series) -> Dict[str, Any]:
        """Analyze seasonality in temporal data"""
        # Basic seasonality check: look for dominant months or days of week
        data_clean = data.dropna()
        if len(data_clean) < 2:
            return {'seasonal_pattern': 'insufficient_data', 'details': 'Need at least two valid dates.'}

        month_counts = data_clean.dt.month.value_counts(normalize=True).sort_index()
        day_of_week_counts = data_clean.dt.dayofweek.value_counts(normalize=True).sort_index()

        seasonal_pattern = "no_strong_seasonality"
        details = {}

        if not month_counts.empty and month_counts.max() > 0.3: # Threshold for dominant month
            most_common_month = month_counts.idxmax()
            seasonal_pattern = "monthly_seasonality"
            details['most_frequent_month'] = most_common_month
            details['frequency'] = float(month_counts.max())

        if not day_of_week_counts.empty and day_of_week_counts.max() > 0.2: # Threshold for dominant day
            most_common_dow_code = day_of_week_counts.idxmax()
            dow_map = {0: 'Monday', 1: 'Tuesday', 2: 'Wednesday', 3: 'Thursday', 4: 'Friday', 5: 'Saturday', 6: 'Sunday'}
            most_common_dow = dow_map.get(most_common_dow_code, 'Unknown')

            if seasonal_pattern == "monthly_seasonality":
                seasonal_pattern = "monthly_and_weekly_seasonality"
                details['most_frequent_day_of_week'] = most_common_dow
                details['frequency'] = float(day_of_week_counts.max())
            else:
                seasonal_pattern = "weekly_seasonality"
                details['most_frequent_day_of_week'] = most_common_dow
                details['frequency'] = float(day_of_week_counts.max())

        return {'seasonal_pattern': seasonal_pattern, 'details': details}

    def _analyze_trends(self, data: pd.Series) -> Dict[str, Any]:
        """Analyze trends in temporal data"""
        # A very basic trend analysis: check if the data generally increases or decreases over time.
        # This assumes the data is ordered, or we should sort it.
        # For simplicity, assuming the DataFrame is indexed chronologically for this column.
        data_clean = data.dropna()
        if len(data_clean) < 2:
            return {'trend': 'insufficient_data', 'details': 'Need at least two valid dates.'}

        # Calculate trend using linear regression slope on time index
        try:
            # Use the index as a proxy for time if it's numeric or convertible
            time_index = data_clean.index
            # Ensure index is numeric or can be treated as such for regression
            if not pd.api.types.is_numeric_dtype(time_index):
                # If index is datetime, convert to ordinal days for slope calculation
                if pd.api.types.is_datetime64_any_dtype(time_index):
                    time_values = (time_index - time_index.min()).days
                else:
                    return {'trend': 'unsupported_index_type', 'details': 'Index is not temporal or numeric.'}
            else:
                time_values = time_index

            # Ensure we have at least two distinct time points
            if len(np.unique(time_values)) < 2:
                return {'trend': 'constant_time', 'details': 'All time points are the same.'}

            # Calculate slope of the best fit line
            slope, _, r_value, p_value, _ = stats.linregress(time_values, data_clean.values)

            trend_type = "no_significant_trend"
            if p_value < 0.05: # Significant trend
                if slope > 0.01 * data_clean.abs().mean(): # Heuristic for significant positive slope
                    trend_type = "increasing"
                elif slope < -0.01 * data_clean.abs().mean(): # Heuristic for significant negative slope
                    trend_type = "decreasing"

            return {
                'trend': trend_type,
                'slope': float(slope),
                'p_value': float(p_value),
                'r_squared': float(r_value**2)
            }
        except Exception as e:
            return {'trend': 'error', 'details': f'Trend calculation failed: {str(e)}'}


    def _generate_temporal_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate temporal recommendations"""
        recommendations = []
        temporal_patterns = analysis.get('temporal_patterns', {})
        seasonality = analysis.get('seasonality', {})
        trends = analysis.get('trends', {})

        if temporal_patterns.get('date_range', {}).get('span_days', 0) < 30:
            recommendations.append("The time span is very short. Temporal analysis might be limited.")

        if seasonality.get('seasonal_pattern') != 'insufficient_data' and seasonality.get('seasonal_pattern') != 'no_strong_seasonality':
            recommendations.append("Seasonality detected. Consider extracting seasonal features (e.g., month of year, day of week) or using time series models that handle seasonality.")
        elif seasonality.get('seasonal_pattern') == 'monthly_seasonality' or seasonality.get('seasonal_pattern') == 'weekly_seasonality':
             recommendations.append("A dominant seasonal pattern was found. Feature engineering for these periods could be beneficial.")

        if trends.get('trend') == 'increasing':
            recommendations.append("An increasing trend was detected. Consider modeling this trend or using differencing if applicable.")
        elif trends.get('trend') == 'decreasing':
            recommendations.append("A decreasing trend was detected. Consider modeling this trend or using differencing if applicable.")

        recommendations.append("Extracting temporal features (year, month, day, hour, day of week, etc.) can be beneficial for predictive modeling.")
        recommendations.append("Consider cyclical encoding for temporal features like month or day of week to capture their cyclical nature.")

        return recommendations

    def _get_quality_metrics(self, data: pd.Series) -> Dict[str, Any]:
        """Get data quality metrics"""
        total_count = len(data)
        non_null_count = data.count()
        completeness_score = (non_null_count / total_count) * 100 if total_count > 0 else 100.0
        uniqueness_score = (data.nunique() / total_count) * 100 if total_count > 0 else 100.0

        # Simplified consistency and validity (can be expanded with regex, domain checks etc.)
        consistency_score = 100.0
        validity_score = 100.0
        accuracy_score = 100.0 # Accuracy is hard to measure without ground truth

        return {
            'completeness': float(completeness_score),
            'consistency': float(consistency_score),
            'validity': float(validity_score),
            'accuracy': float(accuracy_score), # Placeholder
            'uniqueness': float(uniqueness_score)
        }

    def _get_outlier_summary(self, data: pd.Series) -> Dict[str, Any]:
        """Get outlier summary"""
        return self._analyze_outliers(data)

    def _assess_normality(self, data: pd.Series) -> Dict[str, Any]:
        """Assess normality"""
        return self._test_normality(data)

    def _assess_cardinality(self, data: pd.Series) -> Dict[str, Any]:
        """Assess cardinality"""
        return self._analyze_cardinality(data)

    def _get_temporal_summary(self, data: pd.Series) -> Dict[str, Any]:
        """Get temporal summary"""
        return self._analyze_temporal_patterns(data)

    def _generate_comprehensive_recommendations(self, data: pd.Series, column: str, summary: Dict[str, Any]) -> List[str]:
        """Generate comprehensive recommendations"""
        recommendations = []
        quality_metrics = summary.get('quality_metrics', {})
        insights = summary.get('insights', [])

        # Quality-based recommendations
        if quality_metrics.get('completeness', 100) < 95:
            recommendations.append("Improve data completeness by addressing missing values.")
        if quality_metrics.get('uniqueness', 100) < 50 and pd.api.types.is_numeric_dtype(data) and len(data.dropna()) > 1:
            recommendations.append("Low uniqueness detected. Investigate for potential data entry errors or identify if it's an identifier.")
        if quality_metrics.get('uniqueness', 100) < 90 and (pd.api.types.is_categorical_dtype(data) or data.dtype == 'object') and len(data.dropna()) > 1:
             recommendations.append("Consider strategies for managing high cardinality in categorical data.")

        # Insight-based recommendations
        if any("skewed" in insight.lower() for insight in insights):
            recommendations.append("Apply transformations to address data skewness for better model performance.")
        if any("outlier" in insight.lower() for insight in insights):
            recommendations.append("Investigate and handle outliers appropriately.")
        if any("unique" in insight.lower() and "identifier" in insight.lower() for insight in insights):
            recommendations.append("If identified as an identifier, consider removing this column before modeling unless it serves a specific purpose.")

        # Type-specific recommendations
        if pd.api.types.is_numeric_dtype(data):
            normality_assessment = summary.get('normality_assessment', {})
            if normality_assessment.get('shapiro_wilk', {}).get('p_value', 1) < 0.05 or \
               not normality_assessment.get('anderson_darling', {}).get('is_normal_at_5_percent', True):
                recommendations.append("Data is not normally distributed. Consider transformations or models robust to non-normality.")
        elif data.dtype == 'object' or pd.api.types.is_categorical_dtype(data):
            cardinality_assessment = summary.get('cardinality_assessment', {})
            if cardinality_assessment.get('cardinality_level') == 'high':
                recommendations.append("High cardinality: consider grouping rare categories or using target encoding.")
            elif cardinality_assessment.get('cardinality_level') == 'constant':
                recommendations.append("Constant categorical column: provides no information and can be removed.")
        elif pd.api.types.is_datetime64_any_dtype(data):
            recommendations.extend(self._generate_temporal_recommendations(summary.get('temporal_summary', {})))

        return recommendations

    def _calculate_analysis_completeness(self, summary: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate analysis completeness score"""
        completed_sections = 0
        total_sections = 0

        # Define key sections that should ideally be present and non-empty
        sections_to_check = {
            'basic_statistics': summary.get('basic_statistics'),
            'quality_metrics': summary.get('quality_metrics'),
            'distribution_summary': summary.get('distribution_summary'),
            'insights': summary.get('insights'),
            'recommendations': summary.get('recommendations')
        }

        # Add type-specific sections if applicable
        data_type = summary.get('data_type')
        if data_type == 'numeric':
            sections_to_check['outlier_summary'] = summary.get('outlier_summary')
            sections_to_check['normality_assessment'] = summary.get('normality_assessment')
        elif data_type == 'categorical':
            sections_to_check['cardinality_assessment'] = summary.get('cardinality_assessment')
        elif data_type == 'temporal':
            sections_to_check['temporal_summary'] = summary.get('temporal_summary')

        total_sections = len(sections_to_check)
        for section_name, section_data in sections_to_check.items():
            # Consider a section complete if it exists and is not empty or just contains notes/errors
            if section_data:
                if isinstance(section_data, dict):
                    # Check if the dict is not empty and not just placeholder notes/errors
                    is_empty_or_error = all(
                        isinstance(v, (str, dict)) and ('note' in str(v).lower() or 'error' in str(v).lower() or v is None)
                        for v in section_data.values()
                    )
                    if not is_empty_or_error and len(section_data) > 0:
                         # Special check for insights/recommendations: non-empty list counts as complete
                        if section_name in ['insights', 'recommendations'] and len(section_data) > 0:
                            completed_sections += 1
                        elif section_name not in ['insights', 'recommendations']:
                            completed_sections += 1
                elif isinstance(section_data, list):
                    if len(section_data) > 0:
                        completed_sections += 1
                elif isinstance(section_data, (int, float)): # e.g. score
                    completed_sections +=1

        score = (completed_sections / total_sections) * 100 if total_sections > 0 else 0.0

        return {
            'score': float(score),
            'completed_sections': int(completed_sections),
            'total_sections': int(total_sections)
        }

    # Data quality assessment methods
    def _assess_completeness(self, data: pd.Series) -> Dict[str, Any]:
        """Assess data completeness"""
        total_count = len(data)
        non_null_count = data.count()
        completeness_score = (non_null_count / total_count) * 100 if total_count > 0 else 100.0
        issues = []
        if completeness_score < 95:
            issues.append(f"High missing values detected ({100 - completeness_score:.1f}%).")
        elif completeness_score < 100:
            issues.append("Missing values detected.")
        return {
            'score': float(completeness_score),
            'issues': issues,
            'description': f'{completeness_score:.1f}% of values are present'
        }

    def _assess_consistency(self, data: pd.Series) -> Dict[str, Any]:
        """Assess data consistency"""
        # Simplified consistency check: look for common issues in categorical data
        issues = []
        if data.dtype == 'object' or pd.api.types.is_categorical_dtype(data):
            # Check for leading/trailing whitespace
            if data.astype(str).str.strip().nunique() < data.nunique():
                issues.append("Inconsistent formatting: presence of leading/trailing whitespace.")
            # Check for case inconsistencies if expected to be uniform
            if data.astype(str).str.lower().nunique() < data.nunique() and data.nunique() > 1:
                 issues.append("Inconsistent casing: values appear in different cases (e.g., 'Apple' vs 'apple').")

        score = 100.0 if not issues else 80.0 # Reduce score if inconsistencies found
        return {
            'score': float(score),
            'issues': issues,
            'description': 'Data format appears consistent' if not issues else 'Potential formatting inconsistencies found.'
        }

    def _assess_validity(self, data: pd.Series) -> Dict[str, Any]:
        """Assess data validity"""
        # Validity check: are values within expected ranges or formats?
        issues = []
        if pd.api.types.is_numeric_dtype(data):
            min_val = data.min()
            max_val = data.max()
            # Example: Check for unrealistic values (e.g., negative age)
            if min_val < 0 and 'age' in data.name.lower(): # Domain specific check example
                issues.append("Negative values found for a column typically expected to be non-negative (e.g., age).")
        elif pd.api.types.is_datetime64_any_dtype(data):
            min_date = data.min()
            max_date = data.max()
            # Example: Check if dates are within a reasonable range
            current_year = pd.Timestamp.now().year
            if pd.notna(min_date) and min_date.year < 1900: # Example: Dates before 1900
                issues.append("Dates appear to be in an unusually early range.")
            if pd.notna(max_date) and max_date.year > current_year + 5: # Example: Dates far in the future
                issues.append("Dates appear to be in an unusually future range.")
        elif data.dtype == 'object' or pd.api.types.is_categorical_dtype(data):
            # Check for invalid categories if a known list exists (not available here)
            pass # Placeholder for known category checks

        score = 100.0 if not issues else 70.0 # Reduce score if invalid values found
        return {
            'score': float(score),
            'issues': issues,
            'description': 'Data values appear valid' if not issues else 'Potential invalid values found.'
        }

    def _assess_accuracy(self, data: pd.Series) -> Dict[str, Any]:
        """Assess data accuracy"""
        # Accuracy is the degree to which data correctly reflects the 'real world' object or event.
        # This is typically very hard to measure without external reference data or domain knowledge.
        return {
            'score': 50.0, # Low default score as it's usually unknown
            'issues': ["Accuracy cannot be determined without ground truth or reference data."],
            'description': 'Accuracy assessment requires external validation.'
        }

    def _assess_uniqueness(self, data: pd.Series) -> Dict[str, Any]:
        """Assess data uniqueness"""
        total_count = len(data)
        unique_count = data.nunique()
        uniqueness_score = (unique_count / total_count) * 100 if total_count > 0 else 100.0
        issues = []
        if uniqueness_score < 50 and unique_count < total_count and unique_count > 0 : # Exclude constant columns from duplication issues
            issues.append("High duplication detected. Consider if duplicates should be removed or if they represent distinct entities.")
        elif unique_count == total_count and total_count > 1:
            issues.append("All values are unique. This may indicate an identifier column.")

        return {
            'score': float(uniqueness_score),
            'issues': issues,
            'description': f'{uniqueness_score:.1f}% of values are unique'
        }

    def _generate_quality_recommendations(self, quality_analysis: Dict[str, Any]) -> List[str]:
        """Generate quality recommendations"""
        recommendations = []
        overall_score = quality_analysis.get('overall_score', 0)

        if overall_score < 70:
            recommendations.append("Overall data quality is low. Prioritize addressing data quality issues.")
        elif overall_score < 85:
            recommendations.append("Data quality is moderate. Focus on improving specific dimensions like completeness or validity.")

        if quality_analysis['completeness']['score'] < 90:
            recommendations.append("Improve data completeness by addressing the high percentage of missing values.")
        elif quality_analysis['completeness']['score'] < 98:
            recommendations.append("Address the moderate amount of missing values to enhance data quality.")

        if quality_analysis['validity']['score'] < 80:
            recommendations.append("Investigate and correct invalid data values to ensure data validity.")

        if quality_analysis['uniqueness']['score'] < 80 and quality_analysis['uniqueness']['issues']:
            recommendations.append("Address detected duplications or consider the implications of unique identifiers.")

        if quality_analysis['consistency']['score'] < 80:
            recommendations.append("Rectify formatting inconsistencies to improve data consistency.")

        return recommendations

    # Statistical analysis methods
    def _get_descriptive_statistics(self, data: pd.Series) -> Dict[str, Any]:
        """Get descriptive statistics"""
        if pd.api.types.is_numeric_dtype(data):
            return self._analyze_numeric_distribution(data)
        else:
            return self._analyze_categorical_distribution(data)

    def _get_inferential_statistics(self, data: pd.Series) -> Dict[str, Any]:
        """Get inferential statistics"""
        # This is broad. Could include population estimates from sample data.
        # For now, linking to confidence intervals as a primary inferential statistic.
        return self._calculate_confidence_intervals(data)

    def _run_hypothesis_tests(self, data: pd.Series) -> Dict[str, Any]:
        """Run hypothesis tests"""
        # This is typically done for comparing groups. For a single column, normality tests are most relevant.
        # If this method is called within a context comparing two columns, it would be different.
        # Assuming single column context here, returning normality tests.
        if pd.api.types.is_numeric_dtype(data):
            return self._test_normality(data)
        else:
            return {'note': 'Hypothesis tests for categorical data (e.g., Chi-squared) require comparison with another variable.'}

    def _calculate_confidence_intervals(self, data: pd.Series) -> Dict[str, Any]:
        """Calculate confidence intervals"""
        clean_data = data.dropna()
        n_obs = len(clean_data)

        if n_obs < 2:
            return {'error': 'Insufficient data for confidence interval calculation (need at least 2 observations).'}

        mean_val = clean_data.mean()
        std_err = stats.sem(clean_data) # Standard error of the mean

        # Calculate 95% confidence interval for the mean
        if std_err > 0:
            # Using t-distribution as sample size might be small or population std unknown
            try:
                ci_95 = stats.t.interval(0.95, n_obs-1, loc=mean_val, scale=std_err)
                return {
                    'mean_95_ci': {
                        'lower': float(ci_95[0]),
                        'upper': float(ci_95[1]),
                        'margin_of_error': float(ci_95[0] - mean_val) # or mean_val - ci_95[0]
                    }
                }
            except Exception as e:
                return {'error': f'Confidence interval calculation failed: {str(e)}'}
        else:
            return {'mean_95_ci': {'lower': float(mean_val), 'upper': float(mean_val), 'margin_of_error': 0.0}} # If std_err is 0 (constant data)

    def _calculate_effect_sizes(self, data: pd.Series) -> Dict[str, Any]:
        """Calculate effect sizes"""
        # Effect size is context-dependent and usually related to comparisons.
        # For a single variable, Cohen's d isn't directly applicable without a comparison group.
        # Could relate to skewness/kurtosis magnitudes as measures of distribution shape deviation.
        return {'note': 'Effect size calculation is context-dependent and typically applied when comparing groups. Skewness and Kurtosis values already provide shape deviation insights.'}

    def _get_categorical_statistics(self, data: pd.Series) -> Dict[str, Any]:
        """Get categorical statistics"""
        return self._analyze_categorical_distribution(data)

    def _run_categorical_tests(self, data: pd.Series) -> Dict[str, Any]:
        """Run categorical tests"""
        # As mentioned in _run_hypothesis_tests, these typically require comparison with another variable.
        return {'note': 'Categorical statistical tests typically require comparison with another variable (e.g., Chi-squared test for independence).'}

    def _generate_statistical_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate statistical recommendations"""
        recommendations = []
        descriptive = analysis.get('descriptive_statistics', {})
        normality = analysis.get('hypothesis_tests', {}).get('shapiro_wilk', {}) # Assuming hypothesis_tests are normality tests for numeric

        if descriptive:
            if 'skewness' in descriptive and abs(descriptive['skewness']) > 1:
                recommendations.append("Consider transformations to normalize the distribution due to high skewness.")
            if 'kurtosis' in descriptive and abs(descriptive['kurtosis']) > 1:
                recommendations.append("The distribution has heavy/light tails; transformations might help manage extreme values.")

        if normality.get('p_value', 1) < 0.05:
            recommendations.append("Normality tests indicate the data is not normally distributed. This might affect the validity of statistical methods assuming normality.")

        ci = analysis.get('confidence_intervals', {}).get('mean_95_ci')
        if ci and ci['margin_of_error'] is not None and ci['margin_of_error'] > 0:
            recommendations.append(f"The mean is estimated with a 95% confidence interval. The margin of error is {ci['margin_of_error']:.3f}.")

        return recommendations

    def generate_chart(self, file_path: str, column: str, chart_type: str) -> Dict[str, Any]:
        """Generate chart for column analysis"""
        try:
            self._load_dataframe(file_path)
            if column not in self.df.columns:
                raise ValueError(f"Column {column} not found")
            data = self.df[column]

            # Basic validation for chart types
            if pd.api.types.is_numeric_dtype(data):
                if chart_type not in ['histogram', 'boxplot', 'value_counts']:
                    return {
                        'success': False,
                        'error': f'Unsupported chart type "{chart_type}" for numeric column.',
                        'chart_html': f'<div class="error">Unsupported chart type "{chart_type}" for numeric column.</div>'
                    }
                return self._generate_numeric_chart(data, chart_type, column)
            elif pd.api.types.is_categorical_dtype(data) or data.dtype == 'object':
                if chart_type not in ['value_counts']:
                    return {
                        'success': False,
                        'error': f'Unsupported chart type "{chart_type}" for categorical column. Only "value_counts" is supported.',
                        'chart_html': f'<div class="error">Unsupported chart type "{chart_type}" for categorical column. Only "value_counts" is supported.</div>'
                    }
                return self._create_categorical_value_counts(data, column)
            elif pd.api.types.is_datetime64_any_dtype(data):
                 # Placeholder for temporal charts (e.g., time series plot)
                return {
                    'success': False,
                    'error': f'Chart generation for temporal data type "{chart_type}" is not yet implemented.',
                    'chart_html': f'<div class="error">Chart generation for temporal data type "{chart_type}" is not yet implemented.</div>'
                }
            else:
                return {
                    'success': False,
                    'error': f'Chart generation not supported for data type: {data.dtype}',
                    'chart_html': f'<div class="error">Chart generation not supported for data type: {data.dtype}</div>'
                }
        except Exception as e:
            self.logger.error(f"Error generating chart for column {column} with type {chart_type}: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'chart_html': f'<div class="error">Failed to generate {chart_type} chart: {str(e)}</div>'
            }

    def _generate_numeric_chart(self, data: pd.Series, chart_type: str, column_name: str) -> Dict[str, Any]:
        """Generate charts for numeric data"""
        clean_data = data.dropna()
        if len(clean_data) == 0:
            return {
                'success': False,
                'error': 'No valid data points',
                'chart_html': '<div class="error">No valid data points for chart generation</div>'
            }
        if chart_type == 'histogram':
            return self._create_histogram(clean_data, column_name)
        elif chart_type == 'boxplot':
            return self._create_boxplot(clean_data, column_name)
        elif chart_type == 'value_counts':
            return self._create_numeric_value_counts(clean_data, column_name)
        else: # Should not reach here due to validation in generate_chart
            return {
                'success': False,
                'error': f'Internal error: Unexpected chart type {chart_type}',
                'chart_html': f'<div class="error">Internal error: Unexpected chart type {chart_type}</div>'
            }

    def _generate_categorical_chart(self, data: pd.Series, chart_type: str, column_name: str) -> Dict[str, Any]:
        """Generate charts for categorical data"""
        clean_data = data.dropna()
        if len(clean_data) == 0:
            return {
                'success': False,
                'error': 'No valid data points',
                'chart_html': '<div class="error">No valid data points for chart generation</div>'
            }
        # Only value_counts is supported for categorical for now
        return self._create_categorical_value_counts(clean_data, column_name)

    def _create_histogram(self, data: pd.Series, column_name: str) -> Dict[str, Any]:
        """Create histogram"""
        try:
            fig, ax = plt.subplots(figsize=(10, 6))
            n_bins = min(50, max(10, int(np.sqrt(len(data)))))
            counts, bins, patches = ax.hist(data, bins=n_bins, alpha=0.7, color='skyblue', edgecolor='black')
            ax.set_title(f'Histogram of {column_name}', fontsize=14, fontweight='bold')
            ax.set_xlabel(column_name, fontsize=12)
            ax.set_ylabel('Frequency', fontsize=12)
            ax.grid(True, alpha=0.3)

            # Add basic statistics to the plot
            mean_val = data.mean()
            median_val = data.median()
            std_val = data.std()
            stats_text = f'Mean: {mean_val:.2f}\nMedian: {median_val:.2f}\nStd: {std_val:.2f}\nCount: {len(data)}'
            ax.text(0.02, 0.98, stats_text, transform=ax.transAxes, fontsize=10,
                   verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))

            plt.tight_layout()
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
            img_buffer.seek(0)
            img_base64 = base64.b64encode(img_buffer.getvalue()).decode()
            plt.close(fig)

            skewness = stats.skew(data)
            kurtosis = stats.kurtosis(data)
            interpretation = self._interpret_histogram(data, skewness, kurtosis)

            chart_html = f'''
            <div class="chart-result">
                <h6>📊 Histogram - {column_name}</h6>
                <div class="chart-content">
                    <img src="data:image/png;base64,{img_base64}" style="max-width: 100%; height: auto;" />
                </div>
                <div class="chart-interpretation">
                    <h6>📈 Interpretation:</h6>
                    <p>{interpretation}</p>
                    <div class="stats-summary">
                        <span><strong>Skewness:</strong> {skewness:.3f}</span>
                        <span><strong>Kurtosis:</strong> {kurtosis:.3f}</span>
                        <span><strong>Distribution:</strong> {"Right-skewed" if skewness > 0.5 else "Left-skewed" if skewness < -0.5 else "Approximately symmetric"}</span>
                    </div>
                </div>
            </div>
            '''
            return {
                'success': True,
                'chart_html': chart_html,
                'chart_type': 'histogram',
                'statistics': {
                    'mean': float(mean_val),
                    'median': float(median_val),
                    'std': float(std_val),
                    'skewness': float(skewness),
                    'kurtosis': float(kurtosis),
                    'count': len(data)
                }
            }
        except Exception as e:
            self.logger.error(f"Error creating histogram for {column_name}: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'chart_html': f'<div class="error">Failed to create histogram: {str(e)}</div>'
            }

    def _create_boxplot(self, data: pd.Series, column_name: str) -> Dict[str, Any]:
        """Create box plot"""
        try:
            fig, ax = plt.subplots(figsize=(10, 6))
            bp = ax.boxplot(data, patch_artist=True, labels=[column_name])
            bp['boxes'][0].set_facecolor('lightblue')
            bp['boxes'][0].set_alpha(0.7)
            ax.set_title(f'Box Plot of {column_name}', fontsize=14, fontweight='bold')
            ax.set_ylabel(column_name, fontsize=12)
            ax.grid(True, alpha=0.3)

            # Add summary statistics to the plot
            q1 = data.quantile(0.25)
            q2 = data.median()
            q3 = data.quantile(0.75)
            iqr = q3 - q1
            lower_whisker = max(data.min(), q1 - 1.5 * iqr)
            upper_whisker = min(data.max(), q3 + 1.5 * iqr)
            stats_text = f'Q1: {q1:.2f}\nMedian: {q2:.2f}\nQ3: {q3:.2f}\nIQR: {iqr:.2f}'
            ax.text(0.02, 0.98, stats_text, transform=ax.transAxes, fontsize=10,
                   verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))

            plt.tight_layout()
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
            img_buffer.seek(0)
            img_base64 = base64.b64encode(img_buffer.getvalue()).decode()
            plt.close(fig)

            outliers = data[(data < lower_whisker) | (data > upper_whisker)]
            outlier_percentage = (len(outliers) / len(data)) * 100
            interpretation = self._interpret_boxplot(data, q1, q2, q3, iqr, outlier_percentage)

            chart_html = f'''
            <div class="chart-result">
                <h6>📦 Box Plot - {column_name}</h6>
                <div class="chart-content">
                    <img src="data:image/png;base64,{img_base64}" style="max-width: 100%; height: auto;" />
                </div>
                <div class="chart-interpretation">
                    <h6>📊 Interpretation:</h6>
                    <p>{interpretation}</p>
                    <div class="stats-summary">
                        <span><strong>Q1:</strong> {q1:.3f}</span>
                        <span><strong>Median:</strong> {q2:.3f}</span>
                        <span><strong>Q3:</strong> {q3:.3f}</span>
                        <span><strong>IQR:</strong> {iqr:.3f}</span>
                        <span><strong>Outliers:</strong> {len(outliers)} ({outlier_percentage:.1f}%)</span>
                    </div>
                </div>
            </div>
            '''
            return {
                'success': True,
                'chart_html': chart_html,
                'chart_type': 'boxplot',
                'statistics': {
                    'q1': float(q1),
                    'median': float(q2),
                    'q3': float(q3),
                    'iqr': float(iqr),
                    'outliers_count': len(outliers),
                    'outliers_percentage': float(outlier_percentage)
                }
            }
        except Exception as e:
            self.logger.error(f"Error creating boxplot for {column_name}: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'chart_html': f'<div class="error">Failed to create box plot: {str(e)}</div>'
            }

    def _create_numeric_value_counts(self, data: pd.Series, column_name: str) -> Dict[str, Any]:
        """Create value counts chart for numeric data (binned)"""
        try:
            n_bins = min(20, max(5, int(np.sqrt(len(data)))))
            # Use pd.cut to create bins, handling potential errors with small ranges or unique values
            try:
                bins = pd.cut(data, bins=n_bins, include_lowest=True)
            except ValueError: # Handle cases where data range is too small for desired bins
                if len(data.unique()) <= n_bins: # If fewer unique values than bins, use unique values directly
                    bins = pd.Series(data.values, index=data.index) # Treat each unique as a category
                else:
                    bins = pd.cut(data, bins=max(10, len(data.unique()) // 2), include_lowest=True) # Adjust bins if range is problematic

            value_counts = bins.value_counts().sort_index()
            total_count = len(data)

            fig, ax = plt.subplots(figsize=(12, max(6, len(value_counts) * 0.4)))
            y_pos = np.arange(len(value_counts))
            bars = ax.barh(y_pos, value_counts.values, color='lightcoral', alpha=0.7)
            labels = [str(interval) for interval in value_counts.index] # Convert intervals to strings
            ax.set_yticks(y_pos)
            ax.set_yticklabels(labels, fontsize=9)
            ax.set_xlabel('Frequency', fontsize=12)
            ax.set_title(f'Binned Value Counts of {column_name}', fontsize=14, fontweight='bold')
            ax.grid(True, alpha=0.3, axis='x')

            # Add counts to bars
            for i, bar in enumerate(bars):
                width = bar.get_width()
                ax.text(width + max(value_counts.values) * 0.01, bar.get_y() + bar.get_height()/2,
                       f'{value_counts.values[i]}', ha='left', va='center', fontsize=9)

            plt.tight_layout()
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
            img_buffer.seek(0)
            img_base64 = base64.b64encode(img_buffer.getvalue()).decode()
            plt.close(fig)

            chart_html = f'''
            <div class="chart-result">
                <h6>📊 Binned Value Counts - {column_name}</h6>
                <div class="chart-content">
                    <img src="data:image/png;base64,{img_base64}" style="max-width: 100%; height: auto;" />
                </div>
                <div class="chart-interpretation">
                    <h6>📈 Summary:</h6>
                    <p>This chart shows the frequency distribution of {column_name} grouped into approximately {n_bins} bins. The data ranges from {data.min():.2f} to {data.max():.2f}.</p>
                </div>
            </div>
            '''
            return {
                'success': True,
                'chart_html': chart_html,
                'chart_type': 'value_counts',
                'statistics': {
                    'bins_count': n_bins,
                    'total_values': len(data),
                    'min_value': float(data.min()) if not data.empty else None,
                    'max_value': float(data.max()) if not data.empty else None
                }
            }
        except Exception as e:
            self.logger.error(f"Error creating numeric value counts for {column_name}: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'chart_html': f'<div class="error">Failed to create value counts chart: {str(e)}</div>'
            }

    def _create_categorical_value_counts(self, data: pd.Series, column_name: str) -> Dict[str, Any]:
        """Create value counts chart for categorical data"""
        try:
            value_counts = data.value_counts().head(20) # Limit to top 20 categories for clarity
            total_count = len(data)
            percentages = (value_counts / total_count * 100).round(1)

            fig, ax = plt.subplots(figsize=(12, max(6, len(value_counts) * 0.4)))
            y_pos = np.arange(len(value_counts))
            bars = ax.barh(y_pos, value_counts.values, color='lightgreen', alpha=0.7)
            ax.set_yticks(y_pos)
            ax.set_yticklabels(value_counts.index, fontsize=9) # Use category names as labels
            ax.set_xlabel('Frequency', fontsize=12)
            ax.set_title(f'Value Counts of {column_name}', fontsize=14, fontweight='bold')
            ax.grid(True, alpha=0.3, axis='x')

            # Add counts and percentages to bars
            for i, (bar, count, pct) in enumerate(zip(bars, value_counts.values, percentages.values)):
                width = bar.get_width()
                ax.text(width + max(value_counts.values) * 0.01, bar.get_y() + bar.get_height()/2,
                       f'{count} ({pct}%)', ha='left', va='center', fontsize=9)

            plt.tight_layout()
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
            img_buffer.seek(0)
            img_base64 = base64.b64encode(img_buffer.getvalue()).decode()
            plt.close(fig)

            top_category_pct = percentages.iloc[0] if not percentages.empty else 0
            concentration_level = "High" if top_category_pct > 50 else "Medium" if top_category_pct > 20 else "Low"
            unique_categories_total = data.nunique()
            displayed_categories = len(value_counts)

            chart_html = f'''
            <div class="chart-result">
                <h6>📊 Value Counts - {column_name}</h6>
                <div class="chart-content">
                    <img src="data:image/png;base64,{img_base64}" style="max-width: 100%; height: auto;" />
                </div>
                <div class="chart-interpretation">
                    <h6>📈 Analysis:</h6>
                    <p>This chart displays the frequency distribution of categories in {column_name}. The top category is "{value_counts.index[0]}" ({top_category_pct:.1f}%).</p>
                    <div class="stats-summary">
                        <span><strong>Unique Categories:</strong> {unique_categories_total}</span>
                        <span><strong>Most Frequent Category:</strong> {value_counts.index[0]} ({top_category_pct:.1f}%)</span>
                        <span><strong>Concentration:</strong> {concentration_level}</span>
                        <span><strong>Showing:</strong> Top {displayed_categories} of {unique_categories_total} categories</span>
                    </div>
                </div>
            </div>
            '''
            return {
                'success': True,
                'chart_html': chart_html,
                'chart_type': 'value_counts',
                'statistics': {
                    'unique_categories': data.nunique(),
                    'most_frequent_category': value_counts.index[0] if not value_counts.empty else None,
                    'most_frequent_count': int(value_counts.iloc[0]) if not value_counts.empty else 0,
                    'most_frequent_percentage': float(top_category_pct),
                    'concentration_level': concentration_level,
                    'displayed_categories': displayed_categories
                }
            }
        except Exception as e:
            self.logger.error(f"Error creating categorical value counts for {column_name}: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'chart_html': f'<div class="error">Failed to create value counts chart: {str(e)}</div>'
            }

    def _interpret_histogram(self, data: pd.Series, skewness: float, kurtosis: float) -> str:
        """Generate interpretation for histogram"""
        interpretation = []
        if abs(skewness) < 0.5:
            interpretation.append("The distribution appears approximately symmetric.")
        elif skewness > 0.5:
            interpretation.append("The distribution is right-skewed, with a longer tail extending to higher values. This might indicate potential outliers on the higher end.")
        else: # skewness < -0.5
            interpretation.append("The distribution is left-skewed, with a longer tail extending to lower values. This might indicate potential outliers on the lower end.")

        if abs(kurtosis) < 0.5:
             interpretation.append("The tail behavior is similar to a normal distribution (mesokurtic).")
        elif kurtosis > 0.5:
            interpretation.append("The distribution has heavier tails than normal (leptokurtic), suggesting more extreme values or outliers.")
        else: # kurtosis < -0.5
            interpretation.append("The distribution has lighter tails than normal (platykurtic), suggesting fewer extreme values.")

        mean_val = data.mean()
        median_val = data.median()
        std_val = data.std()
        if std_val > 0 and abs(mean_val - median_val) / std_val > 0.5:
            interpretation.append("A notable difference between the mean and median suggests the distribution is significantly skewed.")

        return " ".join(interpretation)

    def _interpret_boxplot(self, data: pd.Series, q1: float, q2: float, q3: float, iqr: float, outlier_pct: float) -> str:
        """Generate interpretation for box plot"""
        interpretation = []
        interpretation.append(f"The median value (Q2) is {q2:.2f}, indicating the center of the data.")
        interpretation.append(f"The interquartile range (IQR) is {iqr:.2f}, representing the spread of the middle 50% of the data.")
        interpretation.append(f"The first quartile (Q1) is {q1:.2f} and the third quartile (Q3) is {q3:.2f}.")

        cv = data.std() / data.mean() if data.mean() != 0 and data.std() is not None else 0
        if cv > 0.5:
            interpretation.append("The coefficient of variation suggests high variability relative to the mean.")
        elif cv < 0.1:
            interpretation.append("The coefficient of variation suggests low variability relative to the mean.")
        else:
            interpretation.append("The variability relative to the mean is moderate.")

        if outlier_pct > 5:
            interpretation.append(f"A significant portion of the data ({outlier_pct:.1f}%) falls outside the whiskers, indicating potential outliers that warrant further investigation.")
        elif outlier_pct > 1:
            interpretation.append(f"A small percentage of potential outliers ({outlier_pct:.1f}%) are present, which is typical for many datasets.")
        else:
            interpretation.append("Very few or no outliers were detected by the box plot's whiskers.")

        if (q3 - q2) > (q2 - q1):
            interpretation.append("The upper half of the middle 50% of the data is more spread out than the lower half.")
        elif (q2 - q1) > (q3 - q2):
            interpretation.append("The lower half of the middle 50% of the data is more spread out than the upper half.")
        else:
            interpretation.append("The middle 50% of the data is relatively evenly spread around the median.")

        return " ".join(interpretation)
