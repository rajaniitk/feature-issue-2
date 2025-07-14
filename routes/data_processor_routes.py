from flask import Blueprint, request, jsonify, session, redirect, url_for, render_template
import os
import pandas as pd
import numpy as np
from werkzeug.utils import secure_filename
from services.data_processor import DataProcessor # Assuming your service class is here
from database import db # Assuming db is initialized in database.py
from models import Dataset # Import your Dataset model
import logging

# Configure the blueprint
# The url_prefix '/api/data' means all routes here will be like /api/data/route_name
data_processor_bp = Blueprint('data_processor', __name__, url_prefix='/api/data')

# Define allowed extensions based on your service
ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'json', 'parquet'}

def allowed_file(filename):
    """Checks if the filename has an allowed extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@data_processor_bp.route('/datasets', methods=['GET'])
def get_datasets():
    """Get all available datasets"""
    try:
        datasets = Dataset.query.all()
        dataset_list = []
        
        for dataset in datasets:
            dataset_list.append({
                'id': dataset.id,
                'name': dataset.original_filename,
                'filename': dataset.filename,
                'rows': dataset.num_rows,
                'columns': dataset.num_columns,
                'file_size': dataset.file_size,
                'column_names': dataset.column_names,
                'upload_date': dataset.upload_timestamp.isoformat() if dataset.upload_timestamp else None
            })
        
        return jsonify({
            'success': True,
            'datasets': dataset_list
        })
        
    except Exception as e:
        logging.error(f"Get datasets error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@data_processor_bp.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # --- Handle POST request for file upload ---
        file = request.files.get('file') # Use .get() for safer access
        dataset_name = request.form.get('dataset_name') # Optional dataset name from form
        dataset_description = request.form.get('dataset_description') # Optional description

        # 1. Validate File Presence and Type
        if not file:
            logging.error("Upload error: No file part in the request.")
            return jsonify({'success': False, 'error': 'No file part in the request'}), 400
        
        if file.filename == '':
            logging.error("Upload error: No file selected.")
            return jsonify({'success': False, 'error': 'No selected file'}), 400
        
        if not allowed_file(file.filename):
            logging.error(f"Upload error: Invalid file type '{file.filename}'.")
            return jsonify({'success': False, 'error': 'Invalid file type. Supported: CSV, XLSX, JSON, Parquet'}), 400
        
        # 2. Secure Filename and Prepare Path
        filename = secure_filename(file.filename)
        upload_folder = 'uploads' # Make sure this matches your app config if different
        file_path = os.path.join(upload_folder, filename)
        
        # Ensure upload directory exists
        try:
            os.makedirs(upload_folder, exist_ok=True)
        except OSError as e:
            logging.error(f"Error creating upload directory '{upload_folder}': {e}", exc_info=True)
            return jsonify({'success': False, 'error': f"Server error: Could not create upload directory."}), 500

        # 3. Save the File
        try:
            file.save(file_path)
        except Exception as e:
            logging.error(f"Error saving file '{filename}' to '{file_path}': {e}", exc_info=True)
            return jsonify({'success': False, 'error': f'Could not save file: {e}'}), 500

        # 4. Process File using DataProcessor Service
        processor = DataProcessor()
        # Assuming process_upload expects the file object itself, or file_path and filename.
        # Let's assume it's expecting the file object, based on your DataProcessor class signature.
        # If process_upload expects file_path and filename, change the call.
        # Example: result = processor.process_upload(file_path, filename)
        result = processor.process_upload(file) 
        
        # 5. Handle Service Result and Database Operation
        if result and result.get('success'):
            try:
                # Extract info from the service result
                # IMPORTANT: Ensure the keys returned by processor.process_upload match what Dataset model expects
                dataset = Dataset(
                    filename=filename, # The secure_filename
                    original_filename=file.filename, # The original user-provided name
                    file_path=file_path, # Path on disk relative to app root
                    file_type=result.get('file_type', filename.rsplit('.', 1)[1].lower()),
                    file_size=os.path.getsize(file_path),
                    num_rows=result.get('rows'), # Assuming service returns 'rows'
                    num_columns=result.get('columns'), # Assuming service returns 'columns'
                    column_names=result.get('column_names'), # Assuming service returns 'column_names'
                    column_types=result.get('data_types'), # Assuming service returns 'data_types'
                    missing_values=result.get('missing_values'), # Assuming service returns 'missing_values'
                    # Add dataset_name and dataset_description if your Dataset model has these fields
                    # dataset_name=dataset_name,
                    # dataset_description=dataset_description,
                )
                db.session.add(dataset)
                db.session.commit()
                
                # Store dataset ID in session for future operations
                session['dataset_id'] = dataset.id
                
                # Return success response
                return jsonify({
                    'success': True,
                    'dataset_id': dataset.id,
                    'message': f"File '{file.filename}' uploaded and processed successfully.",
                    'preview': result.get('preview'), # Service should return preview data
                    'info': result.get('info') # Service should return dataset info
                })
            
            except Exception as db_e:
                # Rollback DB session if commit fails
                db.session.rollback()
                logging.error(f"Database error during dataset save for '{filename}': {db_e}", exc_info=True)
                # Clean up the saved file if DB insertion fails
                if os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                    except OSError as cleanup_e:
                        logging.error(f"Error cleaning up file '{file_path}' after DB error: {cleanup_e}", exc_info=True)
                return jsonify({'success': False, 'error': f'Database error: {db_e}'}), 500
        else:
            # Service processing failed
            error_msg = result.get('error', 'Unknown processing error from service') if result else 'Unknown processing error'
            logging.error(f"DataProcessor service failed for '{filename}': {error_msg}")
            # Clean up the saved file if processing failed
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except OSError as cleanup_e:
                    logging.error(f"Error cleaning up file '{file_path}' after service error: {cleanup_e}", exc_info=True)
            return jsonify({'success': False, 'error': error_msg}), 500
            
    # --- Handle GET request ---
    # If the request method is GET, render the upload form template
    return render_template('upload.html')



@data_processor_bp.route('/preview/<int:dataset_id>')
def get_preview(dataset_id):
    try:
        dataset = Dataset.query.get_or_404(dataset_id)
        processor = DataProcessor()
        preview = processor.get_preview(dataset.file_path)
        return jsonify(preview)
    except Exception as e:
        logging.error(f"Preview error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@data_processor_bp.route('/info/<int:dataset_id>')
def get_info(dataset_id):
    try:
        dataset = Dataset.query.get_or_404(dataset_id)
        processor = DataProcessor()
        info = processor.get_dataset_info(dataset.file_path)
        return jsonify(info)
    except Exception as e:
        logging.error(f"Info error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@data_processor_bp.route('/clean', methods=['POST'])
def clean_data():
    try:
        dataset_id = request.json.get('dataset_id')
        cleaning_options = request.json.get('options', {})
        
        dataset = Dataset.query.get_or_404(dataset_id)
        processor = DataProcessor()
        
        result = processor.clean_data(dataset.file_path, cleaning_options)
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': 'Data cleaned successfully',
                'stats': result['stats']
            })
        else:
            return jsonify({'error': result['error']}), 400
            
    except Exception as e:
        logging.error(f"Clean data error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@data_processor_bp.route('/columns/<int:dataset_id>', methods=['GET'])
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

@data_processor_bp.route('/sample/<int:dataset_id>')
def get_sample(dataset_id):
    try:
        dataset = Dataset.query.get_or_404(dataset_id)
        processor = DataProcessor()
        sample = processor.get_sample_data(dataset.file_path)
        return jsonify(sample)
    except Exception as e:
        logging.error(f"Sample error: {str(e)}")
        return jsonify({'error': str(e)}), 500
