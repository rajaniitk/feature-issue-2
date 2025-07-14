from flask import Blueprint, request, jsonify, session, send_file
from services.report_generator import ReportGenerator
from database import db
from models import Dataset, Report
import logging
import os

report_generator_bp = Blueprint('report_generator', __name__, url_prefix='/api/reports')

@report_generator_bp.route('/datasets', methods=['GET'])
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

@report_generator_bp.route('/generate/<int:dataset_id>', methods=['POST'])
def generate_report(dataset_id):
    try:
        dataset = Dataset.query.get_or_404(dataset_id)
        generator = ReportGenerator()
        
        report_type = request.json.get('report_type', 'comprehensive')
        format_type = request.json.get('format', 'html')
        sections = request.json.get('sections', [])
        
        result = generator.generate_report(dataset.file_path, dataset_id, report_type, format_type, sections)
        
        if result['success']:
            # Save report to database
            report = Report(
                dataset_id=dataset_id,
                report_type=report_type,
                title=result['title'],
                content=result['content'],
                file_path=result['file_path'],
                format=format_type
            )
            db.session.add(report)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'report_id': report.id,
                'file_path': result['file_path'],
                'title': result['title']
            })
        else:
            return jsonify({'error': result['error']}), 400
            
    except Exception as e:
        logging.error(f"Generate report error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@report_generator_bp.route('/download/<int:report_id>')
def download_report(report_id):
    try:
        report = Report.query.get_or_404(report_id)
        
        if not os.path.exists(report.file_path):
            return jsonify({'error': 'Report file not found'}), 404
        
        return send_file(
            report.file_path,
            as_attachment=True,
            download_name=f"{report.title}.{report.format}",
            mimetype='application/octet-stream'
        )
        
    except Exception as e:
        logging.error(f"Download report error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@report_generator_bp.route('/eda/<int:dataset_id>')
def generate_eda_report(dataset_id):
    try:
        dataset = Dataset.query.get_or_404(dataset_id)
        generator = ReportGenerator()
        
        report = generator.generate_eda_report(dataset.file_path, dataset_id)
        
        return jsonify({
            'success': True,
            'report': report
        })
        
    except Exception as e:
        logging.error(f"Generate EDA report error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@report_generator_bp.route('/statistical/<int:dataset_id>')
def generate_statistical_report(dataset_id):
    try:
        dataset = Dataset.query.get_or_404(dataset_id)
        generator = ReportGenerator()
        
        report = generator.generate_statistical_report(dataset.file_path, dataset_id)
        
        return jsonify({
            'success': True,
            'report': report
        })
        
    except Exception as e:
        logging.error(f"Generate statistical report error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@report_generator_bp.route('/ml/<int:dataset_id>')
def generate_ml_report(dataset_id):
    try:
        dataset = Dataset.query.get_or_404(dataset_id)
        generator = ReportGenerator()
        
        report = generator.generate_ml_report(dataset.file_path, dataset_id)
        
        return jsonify({
            'success': True,
            'report': report
        })
        
    except Exception as e:
        logging.error(f"Generate ML report error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@report_generator_bp.route('/custom/<int:dataset_id>', methods=['POST'])
def generate_custom_report(dataset_id):
    try:
        dataset = Dataset.query.get_or_404(dataset_id)
        generator = ReportGenerator()
        
        sections = request.json.get('sections', [])
        title = request.json.get('title', 'Custom Report')
        
        report = generator.generate_custom_report(dataset.file_path, dataset_id, sections, title)
        
        return jsonify({
            'success': True,
            'report': report
        })
        
    except Exception as e:
        logging.error(f"Generate custom report error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@report_generator_bp.route('/pdf/<int:dataset_id>', methods=['POST'])
def generate_pdf_report(dataset_id):
    try:
        dataset = Dataset.query.get_or_404(dataset_id)
        generator = ReportGenerator()
        
        report_type = request.json.get('report_type', 'comprehensive')
        
        result = generator.generate_pdf_report(dataset.file_path, dataset_id, report_type)
        
        if result['success']:
            return jsonify({
                'success': True,
                'file_path': result['file_path'],
                'title': result['title']
            })
        else:
            return jsonify({'error': result['error']}), 400
            
    except Exception as e:
        logging.error(f"Generate PDF report error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@report_generator_bp.route('/list/<int:dataset_id>')
def list_reports(dataset_id):
    try:
        reports = Report.query.filter_by(dataset_id=dataset_id).all()
        
        report_list = []
        for report in reports:
            report_list.append({
                'id': report.id,
                'type': report.report_type,
                'title': report.title,
                'format': report.format,
                'created_at': report.created_at.isoformat()
            })
        
        return jsonify({
            'success': True,
            'reports': report_list
        })
        
    except Exception as e:
        logging.error(f"List reports error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@report_generator_bp.route('/templates')
def get_report_templates():
    try:
        generator = ReportGenerator()
        templates = generator.get_report_templates()
        
        return jsonify({
            'success': True,
            'templates': templates
        })
        
    except Exception as e:
        logging.error(f"Get report templates error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@report_generator_bp.route('/preview/<int:dataset_id>', methods=['POST'])
def preview_report(dataset_id):
    try:
        dataset = Dataset.query.get_or_404(dataset_id)
        generator = ReportGenerator()
        
        report_type = request.json.get('report_type', 'comprehensive')
        sections = request.json.get('sections', [])
        
        preview = generator.preview_report(dataset.file_path, dataset_id, report_type, sections)
        
        return jsonify({
            'success': True,
            'preview': preview
        })
        
    except Exception as e:
        logging.error(f"Preview report error: {str(e)}")
        return jsonify({'error': str(e)}), 500
