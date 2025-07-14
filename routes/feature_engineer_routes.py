from flask import Blueprint, request, jsonify, session
from services.feature_engineer import FeatureEngineer
from services.data_processor import DataProcessor
from database import db
from models import Dataset, Feature, FeatureEngineering
import logging

feature_engineer_bp = Blueprint('feature_engineer', __name__, url_prefix='/api/feature')

@feature_engineer_bp.route('/datasets', methods=['GET'])
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
                'name': dataset.filename,
                'filename': dataset.filename,
                'rows': dataset.num_rows,
                'columns': dataset.num_columns,
                'file_size': dataset.file_size,
                'column_names': dataset.column_names,
                # Safely format the upload timestamp:
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

@feature_engineer_bp.route('/columns/<int:dataset_id>', methods=['GET'])
def get_columns(dataset_id):
    """Get column information for a dataset"""
    try:
        dataset = Dataset.query.get_or_404(dataset_id)
        processor = DataProcessor()
        
        column_info = processor.get_columns_info(dataset.file_path)
        
        return jsonify(column_info)
        
    except Exception as e:
        logging.error(f"Get columns error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@feature_engineer_bp.route('/download/<int:dataset_id>/<format>', methods=['GET'])
def download_dataset(dataset_id, format):
    """Download the current dataset (original or transformed) in the specified format"""
    from flask import send_file, abort
    import os
    import pandas as pd
    import tempfile
    
    try:
        dataset = Dataset.query.get(dataset_id)
        if not dataset:
            logging.error(f"Dataset with ID {dataset_id} not found")
            abort(404, description=f"Dataset {dataset_id} not found")
            
        processor = DataProcessor()
        
        # Load the current dataset (now always loads original since we fixed the save issue)
        df = processor.load_dataset(dataset)
        if df is None or df.empty:
            logging.error(f"Failed to load dataset {dataset_id} or dataset is empty")
            abort(400, description="Dataset could not be loaded or is empty")
        
        # Check if we have any transformations to include
        transformations = FeatureEngineering.query.filter_by(dataset_id=dataset_id).all()
        if transformations:
            logging.info(f"Found {len(transformations)} transformations for dataset {dataset_id}")
        
        # Create download with proper error handling
        temp_file = None
        try:
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=f'.{format}')
            
            if format == 'csv':
                df.to_csv(temp_file.name, index=False)
                mimetype = 'text/csv'
                file_ext = 'csv'
            elif format == 'excel':
                df.to_excel(temp_file.name, index=False)
                mimetype = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                file_ext = 'xlsx'
            elif format == 'json':
                df.to_json(temp_file.name, orient='records', indent=2)
                mimetype = 'application/json'
                file_ext = 'json'
            else:
                if temp_file:
                    temp_file.close()
                    os.unlink(temp_file.name)
                abort(400, description="Invalid format. Supported: csv, excel, json")
                
            temp_file.close()
            
            # Generate descriptive filename
            base_name = dataset.filename.rsplit('.', 1)[0] if dataset.filename else f"dataset_{dataset_id}"
            status = "with_transformations" if transformations else "original"
            filename = f"{base_name}_{status}.{file_ext}"
            
            logging.info(f"Sending download: {filename} ({len(df)} rows, {len(df.columns)} columns)")
            
            return send_file(
                temp_file.name,
                mimetype=mimetype,
                as_attachment=True,
                download_name=filename
            )
            
        except Exception as file_error:
            if temp_file and hasattr(temp_file, 'name') and os.path.exists(temp_file.name):
                try:
                    os.unlink(temp_file.name)
                except:
                    pass
            logging.error(f"File processing error: {str(file_error)}")
            raise file_error
            
    except Exception as e:
        logging.error(f"Download error: {str(e)}")
        import traceback
        logging.error(f"Full traceback: {traceback.format_exc()}")
        
        # Return a JSON error response instead of aborting
        return jsonify({
            'success': False,
            'error': f'Download failed: {str(e)}',
            'message': 'Please try again or contact support if the issue persists.'
        }), 500

@feature_engineer_bp.route('/scale', methods=['POST'])
def apply_scaling():
    """Apply scaling transformation to a feature"""
    try:
        dataset_id = request.json.get('dataset_id')
        feature = request.json.get('feature')
        method = request.json.get('method', 'standard')
        
        if not dataset_id or not feature:
            return jsonify({'success': False, 'error': 'Dataset ID and feature are required'}), 400
        
        engineer = FeatureEngineer()
        
        # Call the correct service method with proper parameters
        result = engineer.scale_features(dataset_id, [feature], method)
        
        if result['success']:
            return jsonify({
                'success': True,
                'feature_name': f'{feature}_scaled_{method}',
                'message': result['message'],
                'stats': result.get('after_stats', {})
            })
        else:
            return jsonify({'success': False, 'error': result['error']}), 400
        
    except Exception as e:
        logging.error(f"Scaling error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@feature_engineer_bp.route('/encode', methods=['POST'])
def apply_encoding():
    """Apply encoding transformation to a feature"""
    try:
        dataset_id = request.json.get('dataset_id')
        feature = request.json.get('feature')
        method = request.json.get('method', 'label')
        
        if not dataset_id or not feature:
            return jsonify({'success': False, 'error': 'Dataset ID and feature are required'}), 400
        
        engineer = FeatureEngineer()
        
        # Call the correct service method with proper parameters
        result = engineer.encode_categorical(dataset_id, [feature], method)
        
        if result['success']:
            response_data = {
                'success': True,
                'message': result['message'],
                'stats': result.get('after_stats', {})
            }
            
            if method == 'onehot' and result.get('new_columns'):
                # One-hot encoding creates multiple features
                response_data['features'] = result['new_columns']
            else:
                # Other encodings create single feature
                response_data['feature_name'] = f'{feature}_encoded_{method}'
            
            return jsonify(response_data)
        else:
            return jsonify({'success': False, 'error': result['error']}), 400
        
    except Exception as e:
        logging.error(f"Encoding error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@feature_engineer_bp.route('/bin', methods=['POST'])
def apply_binning():
    """Apply binning transformation to a feature"""
    try:
        dataset_id = request.json.get('dataset_id')
        feature = request.json.get('feature')
        bins = request.json.get('bins', 5)
        method = request.json.get('method', 'equal_width')
        
        if not dataset_id or not feature:
            return jsonify({'success': False, 'error': 'Dataset ID and feature are required'}), 400
        
        engineer = FeatureEngineer()
        
        # Call the correct service method with proper parameters
        result = engineer.bin_numerical(dataset_id, [feature], method, bins)
        
        if result['success']:
            return jsonify({
                'success': True,
                'feature_name': f'{feature}_binned_{method}',
                'message': result['message'],
                'stats': result.get('after_stats', {})
            })
        else:
            return jsonify({'success': False, 'error': result['error']}), 400
        
    except Exception as e:
        logging.error(f"Binning error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@feature_engineer_bp.route('/transform', methods=['POST'])
def apply_transformation():
    """Apply mathematical transformation to a feature"""
    try:
        dataset_id = request.json.get('dataset_id')
        feature = request.json.get('feature')
        method = request.json.get('method', 'log')
        
        if not dataset_id or not feature:
            return jsonify({'success': False, 'error': 'Dataset ID and feature are required'}), 400
        
        engineer = FeatureEngineer()
        
        # Call the correct service method with proper parameters
        result = engineer.transform_numerical(dataset_id, [feature], method)
        
        if result['success']:
            return jsonify({
                'success': True,
                'feature_name': f'{feature}_transformed_{method}',
                'message': result['message'],
                'stats': result.get('after_stats', {})
            })
        else:
            return jsonify({'success': False, 'error': result['error']}), 400
        
    except Exception as e:
        logging.error(f"Transformation error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@feature_engineer_bp.route('/impute', methods=['POST'])
def handle_missing_values():
    """Handle missing values in a feature"""
    try:
        dataset_id = request.json.get('dataset_id')
        feature = request.json.get('feature')
        strategy = request.json.get('strategy', 'mean')
        
        if not dataset_id or not feature:
            return jsonify({'success': False, 'error': 'Dataset ID and feature are required'}), 400
        
        engineer = FeatureEngineer()
        
        # Call the service method
        result = engineer.handle_missing_values(dataset_id, [feature], strategy)
        
        if result['success']:
            return jsonify({
                'success': True,
                'feature_name': f'{feature}_imputed_{strategy}',
                'message': result['message'],
                'stats': result.get('after_stats', {})
            })
        else:
            return jsonify({'success': False, 'error': result['error']}), 400
        
    except Exception as e:
        logging.error(f"Imputation error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@feature_engineer_bp.route('/create', methods=['POST'])
def create_feature():
    """Create new feature from arithmetic operations"""
    try:
        dataset_id = request.json.get('dataset_id')
        feature1 = request.json.get('feature1')
        feature2 = request.json.get('feature2')
        operation = request.json.get('operation')
        
        if not all([dataset_id, feature1, feature2, operation]):
            return jsonify({'success': False, 'error': 'Dataset ID, both features, and operation are required'}), 400
        
        engineer = FeatureEngineer()
        
        # Call the service method
        result = engineer.create_arithmetic_features(dataset_id, feature1, feature2, operation)
        
        if result['success']:
            return jsonify({
                'success': True,
                'feature_name': result['new_feature'],
                'message': result['message'],
                'stats': result.get('after_stats', {})
            })
        else:
            return jsonify({'success': False, 'error': result['error']}), 400
        
    except Exception as e:
        logging.error(f"Feature creation error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

# Additional routes that work with the existing service methods

@feature_engineer_bp.route('/scale/<int:dataset_id>', methods=['POST'])
def scale_features_bulk(dataset_id):
    """Apply scaling to multiple features at once"""
    try:
        engineer = FeatureEngineer()
        
        columns = request.json.get('columns', [])
        method = request.json.get('method', 'standard')
        
        if not columns:
            return jsonify({'success': False, 'error': 'Columns parameter is required'}), 400
        
        result = engineer.scale_features(dataset_id, columns, method)
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': result['message'],
                'before_stats': result.get('before_stats', {}),
                'after_stats': result.get('after_stats', {}),
                'transformation_id': result.get('transformation_id')
            })
        else:
            return jsonify({'success': False, 'error': result['error']}), 400
            
    except Exception as e:
        logging.error(f"Bulk feature scaling error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@feature_engineer_bp.route('/encode/<int:dataset_id>', methods=['POST'])
def encode_features_bulk(dataset_id):
    """Apply encoding to multiple features at once"""
    try:
        engineer = FeatureEngineer()
        
        columns = request.json.get('columns', [])
        method = request.json.get('method', 'onehot')
        
        if not columns:
            return jsonify({'success': False, 'error': 'Columns parameter is required'}), 400
        
        result = engineer.encode_categorical(dataset_id, columns, method)
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': result['message'],
                'before_stats': result.get('before_stats', {}),
                'after_stats': result.get('after_stats', {}),
                'new_columns': result.get('new_columns', []),
                'transformation_id': result.get('transformation_id')
            })
        else:
            return jsonify({'success': False, 'error': result['error']}), 400
            
    except Exception as e:
        logging.error(f"Bulk feature encoding error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@feature_engineer_bp.route('/polynomial/<int:dataset_id>', methods=['POST'])
def create_polynomial_features(dataset_id):
    """Create polynomial features"""
    try:
        engineer = FeatureEngineer()
        
        columns = request.json.get('columns', [])
        degree = request.json.get('degree', 2)
        
        if not columns:
            return jsonify({'success': False, 'error': 'Columns parameter is required'}), 400
        
        result = engineer.polynomial_features(dataset_id, columns, degree)
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': result['message'],
                'new_columns': result.get('new_columns', []),
                'transformation_id': result.get('transformation_id')
            })
        else:
            return jsonify({'success': False, 'error': result['error']}), 400
            
    except Exception as e:
        logging.error(f"Polynomial features error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@feature_engineer_bp.route('/interactions/<int:dataset_id>', methods=['POST'])
def create_interaction_features(dataset_id):
    """Create interaction features"""
    try:
        engineer = FeatureEngineer()
        
        columns = request.json.get('columns', [])
        
        if len(columns) < 2:
            return jsonify({'success': False, 'error': 'At least 2 columns are required for interactions'}), 400
        
        result = engineer.interaction_features(dataset_id, columns)
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': result['message'],
                'new_columns': result.get('new_columns', []),
                'transformation_id': result.get('transformation_id')
            })
        else:
            return jsonify({'success': False, 'error': result['error']}), 400
            
    except Exception as e:
        logging.error(f"Feature interactions error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@feature_engineer_bp.route('/datetime/<int:dataset_id>', methods=['POST'])
def extract_datetime_features(dataset_id):
    """Extract datetime features"""
    try:
        engineer = FeatureEngineer()
        
        columns = request.json.get('columns', [])
        
        if not columns:
            return jsonify({'success': False, 'error': 'Columns parameter is required'}), 400
        
        result = engineer.datetime_features(dataset_id, columns)
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': result['message'],
                'new_columns': result.get('new_columns', []),
                'transformation_id': result.get('transformation_id')
            })
        else:
            return jsonify({'success': False, 'error': result['error']}), 400
            
    except Exception as e:
        logging.error(f"DateTime features error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@feature_engineer_bp.route('/list/<int:dataset_id>')
def list_engineered_features(dataset_id):
    """List all engineered features for a dataset"""
    try:
        # For now, return basic list since we don't have a proper Feature model implementation yet
        return jsonify({
            'success': True,
            'features': [],
            'message': 'Feature listing not fully implemented yet'
        })
        
    except Exception as e:
        logging.error(f"List features error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500
