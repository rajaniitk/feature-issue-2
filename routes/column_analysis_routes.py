from flask import Blueprint, request, jsonify, session
from services.column_analysis import ColumnAnalysis
from database import db
from models import Dataset, Analysis
import logging
import pandas as pd

column_analysis_bp = Blueprint('column_analysis', __name__, url_prefix='/api/column_analysis')

@column_analysis_bp.route('/datasets')
def get_datasets():
    """Get all available datasets for analysis operations"""
    try:
        # Query all datasets from the database
        datasets = Dataset.query.all()
        dataset_list = []

        # Iterate through each dataset and format the data for JSON response
        for dataset in datasets:
            dataset_list.append({
                'id': dataset.id,
                'filename': dataset.filename,
                'rows': dataset.num_rows,
                'columns': dataset.num_columns,
                'file_size': dataset.file_size,
                # Safely format the upload timestamp:
                # If dataset.created_at is None, assign None. Otherwise, call isoformat().
                'created_at': dataset.upload_timestamp.isoformat() if dataset.upload_timestamp else None
            })

        # Return a successful JSON response with the list of datasets
        return jsonify({
            'success': True,
            'datasets': dataset_list
        })

    except Exception as e:
        # Log the error on the server side for debugging
        logging.error(f"Error fetching datasets: {str(e)}")
        # Return a JSON response indicating failure and the error message, with a 500 status code
        return jsonify({'success': False, 'error': f"An internal server error occurred while retrieving datasets: {str(e)}"}), 500

@column_analysis_bp.route('/summary/<int:dataset_id>')
def get_column_summary(dataset_id):
    try:
        dataset = Dataset.query.get_or_404(dataset_id)
        analyzer = ColumnAnalysis()
        
        column = request.args.get('column')
        
        if not column:
            return jsonify({'error': 'Column parameter is required'}), 400
        
        summary = analyzer.get_column_summary(dataset.file_path, column)
        
        return jsonify({
            'success': True,
            'summary': summary
        })
        
    except Exception as e:
        logging.error(f"Column summary error: {str(e)}")
        return jsonify({'error': f"An unexpected server error occurred: {str(e)}"}), 500

@column_analysis_bp.route('/outliers/<int:dataset_id>')
def detect_outliers(dataset_id):
    try:
        dataset = Dataset.query.get_or_404(dataset_id)
        analyzer = ColumnAnalysis()
        
        column = request.args.get('column')
        method = request.args.get('method', 'iqr')
        
        if not column:
            return jsonify({'error': 'Column parameter is required'}), 400
        
        outliers = analyzer.detect_outliers(dataset.file_path, column, method)
        
        return jsonify({
            'success': True,
            'outliers': outliers
        })
        
    except Exception as e:
        logging.error(f"Outlier detection error: {str(e)}")
        return jsonify({'error': f"An unexpected server error occurred: {str(e)}"}), 500

@column_analysis_bp.route('/distribution/<int:dataset_id>')
def analyze_distribution(dataset_id):
    try:
        dataset = Dataset.query.get_or_404(dataset_id)
        analyzer = ColumnAnalysis()
        
        column = request.args.get('column')
        
        if not column:
            return jsonify({'error': 'Column parameter is required'}), 400
        
        distribution = analyzer.analyze_distribution(dataset.file_path, column)
        
        return jsonify({
            'success': True,
            'distribution': distribution
        })
        
    except Exception as e:
        logging.error(f"Distribution analysis error: {str(e)}")
        return jsonify({'error': f"An unexpected server error occurred: {str(e)}"}), 500

@column_analysis_bp.route('/missing_values/<int:dataset_id>')
def analyze_missing_values(dataset_id):
    try:
        dataset = Dataset.query.get_or_404(dataset_id)
        analyzer = ColumnAnalysis()
        
        column = request.args.get('column')
        
        if not column:
            return jsonify({'error': 'Column parameter is required'}), 400
        
        missing_analysis = analyzer.analyze_missing_values(dataset.file_path, column)
        
        return jsonify({
            'success': True,
            'missing_analysis': missing_analysis
        })
        
    except Exception as e:
        logging.error(f"Missing values analysis error: {str(e)}")
        return jsonify({'error': f"An unexpected server error occurred: {str(e)}"}), 500

@column_analysis_bp.route('/unique_values/<int:dataset_id>')
def analyze_unique_values(dataset_id):
    try:
        dataset = Dataset.query.get_or_404(dataset_id)
        analyzer = ColumnAnalysis()
        
        column = request.args.get('column')
        
        if not column:
            return jsonify({'error': 'Column parameter is required'}), 400
        
        unique_analysis = analyzer.analyze_unique_values(dataset.file_path, column)
        
        return jsonify({
            'success': True,
            'unique_analysis': unique_analysis
        })
        
    except Exception as e:
        logging.error(f"Unique values analysis error: {str(e)}")
        return jsonify({'error': f"An unexpected server error occurred: {str(e)}"}), 500

@column_analysis_bp.route('/data_quality/<int:dataset_id>')
def assess_data_quality(dataset_id):
    try:
        dataset = Dataset.query.get_or_404(dataset_id)
        analyzer = ColumnAnalysis()
        
        column = request.args.get('column')
        
        if not column:
            return jsonify({'error': 'Column parameter is required'}), 400
        
        quality = analyzer.assess_data_quality(dataset.file_path, column)
        
        return jsonify({
            'success': True,
            'quality': quality
        })
        
    except Exception as e:
        logging.error(f"Data quality assessment error: {str(e)}")
        return jsonify({'error': f"An unexpected server error occurred: {str(e)}"}), 500

@column_analysis_bp.route('/patterns/<int:dataset_id>')
def detect_patterns(dataset_id):
    try:
        dataset = Dataset.query.get_or_404(dataset_id)
        analyzer = ColumnAnalysis()
        
        column = request.args.get('column')
        
        if not column:
            return jsonify({'error': 'Column parameter is required'}), 400
        
        patterns = analyzer.detect_patterns(dataset.file_path, column)
        
        return jsonify({
            'success': True,
            'patterns': patterns
        })
        
    except Exception as e:
        logging.error(f"Pattern detection error: {str(e)}")
        return jsonify({'error': f"An unexpected server error occurred: {str(e)}"}), 500

@column_analysis_bp.route('/temporal_analysis/<int:dataset_id>')
def temporal_analysis(dataset_id):
    try:
        dataset = Dataset.query.get_or_404(dataset_id)
        analyzer = ColumnAnalysis()
        
        column = request.args.get('column')
        
        if not column:
            return jsonify({'error': 'Column parameter is required'}), 400
        
        temporal = analyzer.perform_temporal_analysis(dataset.file_path, column)
        
        return jsonify({
            'success': True,
            'temporal': temporal
        })
        
    except Exception as e:
        logging.error(f"Temporal analysis error: {str(e)}")
        return jsonify({'error': f"An unexpected server error occurred: {str(e)}"}), 500

@column_analysis_bp.route('/categorical_analysis/<int:dataset_id>')
def categorical_analysis(dataset_id):
    try:
        dataset = Dataset.query.get_or_404(dataset_id)
        analyzer = ColumnAnalysis()
        
        column = request.args.get('column')
        
        if not column:
            return jsonify({'error': 'Column parameter is required'}), 400
        
        categorical = analyzer.perform_categorical_analysis(dataset.file_path, column)
        
        return jsonify({
            'success': True,
            'categorical': categorical
        })
        
    except Exception as e:
        logging.error(f"Categorical analysis error: {str(e)}")
        return jsonify({'error': f"An unexpected server error occurred: {str(e)}"}), 500

@column_analysis_bp.route('/numerical_analysis/<int:dataset_id>')
def numerical_analysis(dataset_id):
    try:
        dataset = Dataset.query.get_or_404(dataset_id)
        analyzer = ColumnAnalysis()
        
        column = request.args.get('column')
        
        if not column:
            return jsonify({'error': 'Column parameter is required'}), 400
        
        numerical = analyzer.perform_numerical_analysis(dataset.file_path, column)
        
        return jsonify({
            'success': True,
            'numerical': numerical
        })
        
    except Exception as e:
        logging.error(f"Numerical analysis error: {str(e)}")
        return jsonify({'error': f"An unexpected server error occurred: {str(e)}"}), 500

@column_analysis_bp.route('/recommendations/<int:dataset_id>')
def get_recommendations(dataset_id):
    try:
        dataset = Dataset.query.get_or_404(dataset_id)
        analyzer = ColumnAnalysis()
        
        column = request.args.get('column')
        
        if not column:
            return jsonify({'error': 'Column parameter is required'}), 400
        
        recommendations = analyzer.get_recommendations(dataset.file_path, column)
        
        return jsonify({
            'success': True,
            'recommendations': recommendations
        })
        
    except Exception as e:
        logging.error(f"Recommendations error: {str(e)}")
        return jsonify({'error': f"An unexpected server error occurred: {str(e)}"}), 500

@column_analysis_bp.route('/transform/<int:dataset_id>', methods=['POST'])
def transform_column(dataset_id):
    try:
        dataset = Dataset.query.get_or_404(dataset_id)
        analyzer = ColumnAnalysis()
        
        column = request.json.get('column')
        transformation_type = request.json.get('transformation_type', 'standardize')
        
        if not column:
            return jsonify({'error': 'Column parameter is required'}), 400
        
        # Load the data to check the column
        analyzer._load_dataframe(dataset.file_path)
        if column not in analyzer.df.columns:
            return jsonify({'error': f'Column "{column}" not found in dataset'}), 400
        
        data = analyzer.df[column]
        
        # Check if column is numeric for transformation
        if not pd.api.types.is_numeric_dtype(data):
            return jsonify({'error': f'Column "{column}" is not numeric. Transformations only apply to numeric columns.'}), 400
        
        # Analyze the data before transformation
        original_stats = {
            'mean': float(data.mean()),
            'std': float(data.std()),
            'min': float(data.min()),
            'max': float(data.max()),
            'skewness': float(data.skew())
        }
        
        # Simulate transformation analysis
        transformation_info = {
            'standardize': 'Standardizes data to have mean=0, std=1',
            'normalize': 'Normalizes data to range [0, 1]',
            'log': 'Applies logarithmic transformation (log(x+1))',
            'sqrt': 'Applies square root transformation'
        }
        
        return jsonify({
            'success': True,
            'message': f'Column "{column}" transformation analysis completed',
            'transformation_analysis': {
                'column': column,
                'method': transformation_type,
                'description': transformation_info.get(transformation_type, 'Unknown transformation'),
                'original_stats': original_stats,
                'recommendation': f'{transformation_type.capitalize()} transformation recommended for this column',
                'status': 'analysis_completed'
            }
        })
        
    except Exception as e:
        logging.error(f"Transform column error: {str(e)}")
        return jsonify({'error': f"An unexpected server error occurred: {str(e)}"}), 500

@column_analysis_bp.route('/clean/<int:dataset_id>', methods=['POST'])
def clean_column(dataset_id):
    try:
        dataset = Dataset.query.get_or_404(dataset_id)
        analyzer = ColumnAnalysis()
        
        column = request.json.get('column')
        cleaning_options = request.json.get('options', {})
        
        if not column:
            return jsonify({'error': 'Column parameter is required'}), 400
        
        # Load the data to analyze cleaning impact
        analyzer._load_dataframe(dataset.file_path)
        if column not in analyzer.df.columns:
            return jsonify({'error': f'Column "{column}" not found in dataset'}), 400
        
        data = analyzer.df[column]
        original_count = len(data)
        
        # Analyze what would be cleaned
        cleaning_analysis = {
            'original_count': original_count,
            'null_count': int(data.isnull().sum()),
            'duplicate_count': int(original_count - data.nunique()),
            'outlier_count': 0
        }
        
        # Calculate outliers if numeric
        if pd.api.types.is_numeric_dtype(data):
            Q1 = data.quantile(0.25)
            Q3 = data.quantile(0.75)
            IQR = Q3 - Q1
            outliers = data[(data < Q1 - 1.5 * IQR) | (data > Q3 + 1.5 * IQR)]
            cleaning_analysis['outlier_count'] = len(outliers)
        
        # Calculate impact of cleaning options
        records_to_remove = 0
        cleaning_actions = []
        
        if cleaning_options.get('remove_nulls', False):
            records_to_remove += cleaning_analysis['null_count']
            cleaning_actions.append(f"Remove {cleaning_analysis['null_count']} null values")
        
        if cleaning_options.get('remove_duplicates', False):
            records_to_remove += cleaning_analysis['duplicate_count']
            cleaning_actions.append(f"Remove {cleaning_analysis['duplicate_count']} duplicate values")
        
        if cleaning_options.get('remove_outliers', False):
            records_to_remove += cleaning_analysis['outlier_count']
            cleaning_actions.append(f"Remove {cleaning_analysis['outlier_count']} outlier values")
        
        remaining_count = max(0, original_count - records_to_remove)
        impact_percentage = ((records_to_remove / original_count) * 100) if original_count > 0 else 0
        
        return jsonify({
            'success': True,
            'message': f'Column "{column}" cleaning analysis completed',
            'cleaning_analysis': {
                'column': column,
                'options_applied': cleaning_options,
                'original_count': original_count,
                'records_to_remove': records_to_remove,
                'remaining_count': remaining_count,
                'impact_percentage': round(impact_percentage, 2),
                'cleaning_actions': cleaning_actions,
                'recommendation': 'Review the impact before applying changes to the dataset',
                'status': 'analysis_completed'
            }
        })
        
    except Exception as e:
        logging.error(f"Clean column error: {str(e)}")
        return jsonify({'error': f"An unexpected server error occurred: {str(e)}"}), 500

@column_analysis_bp.route('/encode/<int:dataset_id>', methods=['POST'])
def encode_column(dataset_id):
    try:
        dataset = Dataset.query.get_or_404(dataset_id)
        analyzer = ColumnAnalysis()
        
        column = request.json.get('column')
        encoding_type = request.json.get('encoding_type', 'label')
        
        if not column:
            return jsonify({'error': 'Column parameter is required'}), 400
        
        # Load the data to analyze encoding
        analyzer._load_dataframe(dataset.file_path)
        if column not in analyzer.df.columns:
            return jsonify({'error': f'Column "{column}" not found in dataset'}), 400
        
        data = analyzer.df[column]
        
        # Check if column is categorical
        if pd.api.types.is_numeric_dtype(data):
            return jsonify({'error': f'Column "{column}" is numeric. Encoding applies to categorical columns.'}), 400
        
        # Analyze the categorical data
        unique_values = data.nunique()
        value_counts = data.value_counts()
        
        # Provide encoding recommendations and analysis
        encoding_info = {
            'label': {
                'description': 'Assigns integer labels to categories',
                'suitable_for': 'Ordinal data or when preserving order',
                'output_columns': 1,
                'memory_efficient': True
            },
            'onehot': {
                'description': 'Creates binary columns for each category',
                'suitable_for': 'Nominal data with low cardinality',
                'output_columns': unique_values,
                'memory_efficient': unique_values <= 10
            },
            'target': {
                'description': 'Encodes based on target variable statistics',
                'suitable_for': 'High cardinality categorical features',
                'output_columns': 1,
                'memory_efficient': True
            },
            'ordinal': {
                'description': 'Maps categories to ordered integers',
                'suitable_for': 'Naturally ordered categories',
                'output_columns': 1,
                'memory_efficient': True
            }
        }
        
        selected_encoding = encoding_info.get(encoding_type, encoding_info['label'])
        
        # Generate recommendations
        recommendations = []
        if unique_values == 2:
            recommendations.append("Binary encoding or label encoding recommended for binary categorical data")
        elif unique_values <= 10:
            recommendations.append("One-hot encoding suitable for low cardinality")
        elif unique_values > 50:
            recommendations.append("Target encoding recommended for high cardinality")
        else:
            recommendations.append("Label encoding or ordinal encoding suitable for medium cardinality")
        
        # Convert numpy types to native Python types for JSON serialization
        encoding_analysis = {
            'column': column,
            'encoding_method': encoding_type,
            'column_info': {
                'unique_values': int(unique_values),
                'most_frequent': str(value_counts.index[0]) if len(value_counts) > 0 else None,
                'data_type': str(data.dtype)
            },
            'encoding_details': {
                'description': selected_encoding['description'],
                'suitable_for': selected_encoding['suitable_for'],
                'output_columns': int(selected_encoding['output_columns']),
                'memory_efficient': bool(selected_encoding['memory_efficient'])
            },
            'recommendations': recommendations,
            'preview_mapping': {str(k): int(v) for k, v in value_counts.head(10).items()},
            'status': 'analysis_completed'
        }
        
        return jsonify({
            'success': True,
            'message': f'Column "{column}" encoding analysis completed',
            'encoding_analysis': analyzer._convert_numpy_types(encoding_analysis)
        })
        
    except Exception as e:
        logging.error(f"Encode column error: {str(e)}")
        return jsonify({'error': f"An unexpected server error occurred: {str(e)}"}), 500

@column_analysis_bp.route('/clean_data/<int:dataset_id>', methods=['POST'])
def export_cleaned_data(dataset_id):
    try:
        dataset = Dataset.query.get_or_404(dataset_id)
        analyzer = ColumnAnalysis()
        
        column = request.args.get('column')
        export_format = request.args.get('format', 'csv')
        
        # Get cleaning options from request body
        cleaning_options = request.json or {}
        remove_nulls = cleaning_options.get('remove_nulls', True)
        remove_duplicates = cleaning_options.get('remove_duplicates', True)
        remove_outliers = cleaning_options.get('remove_outliers', False)
        apply_transformations = cleaning_options.get('apply_transformations', False)
        
        if not column:
            return jsonify({'error': 'Column parameter is required'}), 400
        
        # Load the data
        analyzer._load_dataframe(dataset.file_path)
        if column not in analyzer.df.columns:
            return jsonify({'error': f'Column "{column}" not found in dataset'}), 400
        
        # Get original data stats
        original_rows = len(analyzer.df)
        
        # Create a copy for cleaning
        cleaned_df = analyzer.df.copy()
        
        # Apply cleaning operations
        rows_removed_breakdown = {
            'nulls': 0,
            'duplicates': 0,
            'outliers': 0
        }
        
        # Remove null values if requested
        if remove_nulls:
            null_mask = cleaned_df[column].isnull()
            rows_removed_breakdown['nulls'] = null_mask.sum()
            cleaned_df = cleaned_df[~null_mask]
        
        # Remove duplicates if requested
        if remove_duplicates:
            before_dup_removal = len(cleaned_df)
            cleaned_df = cleaned_df.drop_duplicates(subset=[column])
            rows_removed_breakdown['duplicates'] = before_dup_removal - len(cleaned_df)
        
        # Remove outliers if requested (only for numeric columns)
        if remove_outliers and pd.api.types.is_numeric_dtype(cleaned_df[column]):
            before_outlier_removal = len(cleaned_df)
            Q1 = cleaned_df[column].quantile(0.25)
            Q3 = cleaned_df[column].quantile(0.75)
            IQR = Q3 - Q1
            outlier_mask = (cleaned_df[column] < Q1 - 1.5 * IQR) | (cleaned_df[column] > Q3 + 1.5 * IQR)
            cleaned_df = cleaned_df[~outlier_mask]
            rows_removed_breakdown['outliers'] = before_outlier_removal - len(cleaned_df)
        
        # Calculate final stats
        cleaned_rows = len(cleaned_df)
        total_rows_removed = original_rows - cleaned_rows
        reduction_percentage = round((total_rows_removed / original_rows) * 100, 2) if original_rows > 0 else 0
        quality_improvement = min(100, round(reduction_percentage * 1.5, 1))  # Estimate quality improvement
        
        # Convert to CSV format
        if export_format.lower() == 'csv':
            cleaned_data = cleaned_df.to_csv(index=False)
        else:
            cleaned_data = cleaned_df.to_json(orient='records', indent=2)
        
        # Prepare statistics
        stats = {
            'original_rows': original_rows,
            'cleaned_rows': cleaned_rows,
            'rows_removed': total_rows_removed,
            'reduction_percentage': reduction_percentage,
            'quality_improvement': quality_improvement,
            'breakdown': rows_removed_breakdown
        }
        
        return jsonify({
            'success': True,
            'message': f'Cleaned data for column "{column}" generated successfully',
            'cleaned_data': cleaned_data,
            'stats': stats,
            'cleaning_applied': {
                'remove_nulls': remove_nulls,
                'remove_duplicates': remove_duplicates,
                'remove_outliers': remove_outliers,
                'apply_transformations': apply_transformations
            }
        })
        
    except Exception as e:
        logging.error(f"Export cleaned data error: {str(e)}")
        return jsonify({'error': f"An unexpected server error occurred: {str(e)}"}), 500

@column_analysis_bp.route('/export/<int:dataset_id>')
def export_analysis(dataset_id):
    try:
        dataset = Dataset.query.get_or_404(dataset_id)
        analyzer = ColumnAnalysis()
        
        column = request.args.get('column')
        export_format = request.args.get('format', 'json')
        
        if not column:
            return jsonify({'error': 'Column parameter is required'}), 400
        
        # Generate comprehensive analysis for export
        analyzer._load_dataframe(dataset.file_path)
        if column not in analyzer.df.columns:
            return jsonify({'error': f'Column "{column}" not found in dataset'}), 400
        
        # Get comprehensive analysis
        analysis_summary = analyzer.comprehensive_column_summary(column)
        converted_summary = analyzer._convert_numpy_types(analysis_summary)
        
        # Prepare export metadata
        from datetime import datetime
        export_metadata = {
            'export_timestamp': datetime.now().isoformat(),
            'dataset_name': dataset.filename,
            'dataset_id': dataset_id,
            'column_analyzed': column,
            'export_format': export_format,
            'analysis_version': '1.0'
        }
        
        # Create export data structure
        export_data = {
            'metadata': export_metadata,
            'column_analysis': converted_summary
        }
        
        # Calculate export statistics
        analysis_sections = [
            'basic_statistics', 'quality_metrics', 'distribution_summary', 
            'insights', 'recommendations'
        ]
        
        export_stats = {
            'total_sections': len(analysis_sections),
            'completed_sections': sum(1 for section in analysis_sections if section in converted_summary and converted_summary[section]),
            'data_points_analyzed': len(analyzer.df[column]),
            'analysis_completeness': round((sum(1 for section in analysis_sections if section in converted_summary and converted_summary[section]) / len(analysis_sections)) * 100, 1)
        }
        
        return jsonify({
            'success': True,
            'message': f'Analysis for column "{column}" prepared for export',
            'export_info': {
                'column': column,
                'format': export_format,
                'export_stats': export_stats,
                'file_size_estimate': f"{len(str(export_data)) / 1024:.2f} KB",
                'status': 'ready_for_download',
                'download_instructions': f'Use the provided export data or implement download endpoint for {export_format} format'
            },
            'export_data': export_data if export_format == 'json' else None,
            'download_suggestion': f'Save the export_data as {column}_analysis.{export_format}'
        })
        
    except Exception as e:
        logging.error(f"Export analysis error: {str(e)}")
        return jsonify({'error': f"An unexpected server error occurred: {str(e)}"}), 500

@column_analysis_bp.route('/relationships/<int:dataset_id>')
def analyze_relationships(dataset_id):
    try:
        dataset = Dataset.query.get_or_404(dataset_id)
        analyzer = ColumnAnalysis()
        
        column1 = request.args.get('column1')
        column2 = request.args.get('column2')
        
        if not column1 or not column2:
            return jsonify({'error': 'Both column1 and column2 parameters are required'}), 400
        
        analyzer._load_dataframe(dataset.file_path)
        analysis = analyzer.bivariate_analysis(column1, column2)
        
        return jsonify({
            'success': True,
            'analysis': analyzer._convert_numpy_types(analysis)
        })
        
    except Exception as e:
        logging.error(f"Relationship analysis error: {str(e)}")
        return jsonify({'error': f"An unexpected server error occurred: {str(e)}"}), 500

@column_analysis_bp.route('/generate_chart/<int:dataset_id>')
def generate_chart(dataset_id):
    try:
        dataset = Dataset.query.get_or_404(dataset_id)
        analyzer = ColumnAnalysis()
        
        column = request.args.get('column')
        chart_type = request.args.get('chart_type', 'histogram')
        
        if not column:
            return jsonify({'error': 'Column parameter is required'}), 400
        
        chart_result = analyzer.generate_chart(dataset.file_path, column, chart_type)
        
        return jsonify({
            'success': chart_result.get('success', True),
            'chart': chart_result
        })
        
    except Exception as e:
        logging.error(f"Chart generation error: {str(e)}")
        return jsonify({'error': f"An unexpected server error occurred: {str(e)}"}), 500
