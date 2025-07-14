from flask import Blueprint, request, jsonify, session
from services.insights_generator import InsightsGenerator
from database import db
from models import Dataset, Insight
import logging

insights_generator_bp = Blueprint('insights_generator', __name__, url_prefix='/api/insights')

@insights_generator_bp.route('/datasets', methods=['GET'])
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

@insights_generator_bp.route('/generate/<int:dataset_id>')
def generate_insights(dataset_id):
    try:
        dataset = Dataset.query.get_or_404(dataset_id)
        generator = InsightsGenerator()
        
        insights = generator.generate_comprehensive_insights(dataset.file_path)
        
        # Save insights to database
        for insight_data in insights:
            insight = Insight(
                dataset_id=dataset_id,
                insight_type=insight_data['type'],
                title=insight_data['title'],
                description=insight_data['description'],
                severity=insight_data['severity'],
                recommendations=insight_data['recommendations']
            )
            db.session.add(insight)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'insights': insights
        })
        
    except Exception as e:
        logging.error(f"Generate insights error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@insights_generator_bp.route('/correlation/<int:dataset_id>')
def correlation_insights(dataset_id):
    try:
        dataset = Dataset.query.get_or_404(dataset_id)
        generator = InsightsGenerator()
        
        insights = generator.generate_correlation_insights(dataset.file_path)
        
        return jsonify({
            'success': True,
            'insights': insights
        })
        
    except Exception as e:
        logging.error(f"Correlation insights error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@insights_generator_bp.route('/outliers/<int:dataset_id>')
def outlier_insights(dataset_id):
    try:
        dataset = Dataset.query.get_or_404(dataset_id)
        generator = InsightsGenerator()
        
        insights = generator.generate_outlier_insights(dataset.file_path)
        
        return jsonify({
            'success': True,
            'insights': insights
        })
        
    except Exception as e:
        logging.error(f"Outlier insights error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@insights_generator_bp.route('/missing_data/<int:dataset_id>')
def missing_data_insights(dataset_id):
    try:
        dataset = Dataset.query.get_or_404(dataset_id)
        generator = InsightsGenerator()
        
        insights = generator.generate_missing_data_insights(dataset.file_path)
        
        return jsonify({
            'success': True,
            'insights': insights
        })
        
    except Exception as e:
        logging.error(f"Missing data insights error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@insights_generator_bp.route('/distribution/<int:dataset_id>')
def distribution_insights(dataset_id):
    try:
        dataset = Dataset.query.get_or_404(dataset_id)
        generator = InsightsGenerator()
        
        insights = generator.generate_distribution_insights(dataset.file_path)
        
        return jsonify({
            'success': True,
            'insights': insights
        })
        
    except Exception as e:
        logging.error(f"Distribution insights error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@insights_generator_bp.route('/feature_importance/<int:dataset_id>')
def feature_importance_insights(dataset_id):
    try:
        dataset = Dataset.query.get_or_404(dataset_id)
        generator = InsightsGenerator()
        
        target_column = request.args.get('target_column')
        if not target_column:
            return jsonify({'error': 'Target column parameter is required'}), 400
        
        insights = generator.generate_feature_importance_insights(dataset.file_path, target_column)
        
        return jsonify({
            'success': True,
            'insights': insights
        })
        
    except Exception as e:
        logging.error(f"Feature importance insights error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@insights_generator_bp.route('/recommendations/<int:dataset_id>')
def get_recommendations(dataset_id):
    try:
        dataset = Dataset.query.get_or_404(dataset_id)
        generator = InsightsGenerator()
        
        recommendations = generator.generate_recommendations(dataset.file_path)
        
        return jsonify({
            'success': True,
            'recommendations': recommendations
        })
        
    except Exception as e:
        logging.error(f"Get recommendations error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@insights_generator_bp.route('/data_quality/<int:dataset_id>')
def data_quality_insights(dataset_id):
    try:
        dataset = Dataset.query.get_or_404(dataset_id)
        generator = InsightsGenerator()
        
        insights = generator.generate_data_quality_insights(dataset.file_path)
        
        return jsonify({
            'success': True,
            'insights': insights
        })
        
    except Exception as e:
        logging.error(f"Data quality insights error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@insights_generator_bp.route('/patterns/<int:dataset_id>')
def pattern_insights(dataset_id):
    try:
        dataset = Dataset.query.get_or_404(dataset_id)
        generator = InsightsGenerator()
        
        insights = generator.generate_pattern_insights(dataset.file_path)
        
        return jsonify({
            'success': True,
            'insights': insights
        })
        
    except Exception as e:
        logging.error(f"Pattern insights error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@insights_generator_bp.route('/list/<int:dataset_id>')
def list_insights(dataset_id):
    try:
        insights = Insight.query.filter_by(dataset_id=dataset_id).all()
        
        insight_list = []
        for insight in insights:
            insight_list.append({
                'id': insight.id,
                'type': insight.insight_type,
                'title': insight.title,
                'description': insight.description,
                'severity': insight.severity,
                'recommendations': insight.recommendations,
                'created_at': insight.created_at.isoformat()
            })
        
        return jsonify({
            'success': True,
            'insights': insight_list
        })
        
    except Exception as e:
        logging.error(f"List insights error: {str(e)}")
        return jsonify({'error': str(e)}), 500
