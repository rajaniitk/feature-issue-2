from flask import Blueprint, request, jsonify, session
from services.ml_engine import MLEngine
from database import db
from models import Dataset, MLModel
import logging

ml_engine_bp = Blueprint('ml_engine', __name__, url_prefix='/api/ml')

@ml_engine_bp.route('/datasets', methods=['GET'])
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

@ml_engine_bp.route('/train', methods=['POST'])
def train_model_new():
    """Train a new ML model with the updated API structure"""
    try:
        dataset_id = request.json.get('dataset_id')
        features = request.json.get('features', [])
        target = request.json.get('target')
        algorithm = request.json.get('algorithm', 'random_forest')
        problem_type = request.json.get('problem_type', 'classification')
        test_size = request.json.get('test_size', 0.2)
        hyperparameters = request.json.get('hyperparameters', {})
        
        if not dataset_id or not features or not target:
            return jsonify({'success': False, 'error': 'Dataset ID, features, and target are required'}), 400
        
        dataset = Dataset.query.get_or_404(dataset_id)
        engine = MLEngine()
        
        result = engine.train_model(
            dataset_id, 
            algorithm, 
            target, 
            features, 
            hyperparameters
        )
        
        if result['success']:
            # Save model to database
            ml_model = MLModel(
                dataset_id=dataset_id,
                model_name=f"{algorithm}_{problem_type}",
                model_type=problem_type,
                algorithm=algorithm,
                hyperparameters=hyperparameters,
                training_score=result.get('training_score'),
                validation_score=result.get('validation_score'),
                test_score=result.get('test_score'),
                feature_importance=result.get('feature_importance'),
                model_metrics=result.get('metrics')
            )
            db.session.add(ml_model)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'model_id': ml_model.id,
                'training_score': result.get('training_score'),
                'validation_score': result.get('validation_score'),
                'test_score': result.get('test_score'),
                'metrics': result.get('metrics'),
                'feature_importance': result.get('feature_importance')
            })
        else:
            return jsonify({'success': False, 'error': result.get('error', 'Training failed')}), 400
            
    except Exception as e:
        logging.error(f"Train model error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@ml_engine_bp.route('/evaluate/<int:model_id>')
def evaluate_model(model_id):
    try:
        model = MLModel.query.get_or_404(model_id)
        engine = MLEngine()
        
        evaluation = engine.evaluate_model(model.dataset.file_path, model.id)
        
        return jsonify({
            'success': True,
            'evaluation': evaluation
        })
        
    except Exception as e:
        logging.error(f"Evaluate model error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@ml_engine_bp.route('/predict/<int:model_id>', methods=['POST'])
def predict(model_id):
    try:
        model = MLModel.query.get_or_404(model_id)
        engine = MLEngine()
        
        data = request.json.get('data', {})
        
        if not data:
            return jsonify({'error': 'Data parameter is required'}), 400
        
        predictions = engine.predict(model.id, data)
        
        return jsonify({
            'success': True,
            'predictions': predictions
        })
        
    except Exception as e:
        logging.error(f"Predict error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@ml_engine_bp.route('/compare/<int:dataset_id>', methods=['POST'])
def compare_models(dataset_id):
    try:
        dataset = Dataset.query.get_or_404(dataset_id)
        engine = MLEngine()
        
        features = request.json.get('features', [])
        target = request.json.get('target')
        model_type = request.json.get('model_type', 'classification')
        algorithms = request.json.get('algorithms', ['random_forest', 'logistic_regression', 'svm'])
        
        if not features or not target:
            return jsonify({'error': 'Features and target parameters are required'}), 400
        
        comparison = engine.compare_models(dataset.file_path, features, target, model_type, algorithms)
        
        return jsonify({
            'success': True,
            'comparison': comparison
        })
        
    except Exception as e:
        logging.error(f"Compare models error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@ml_engine_bp.route('/cross-validate', methods=['POST'])
def cross_validate_new():
    """Perform cross-validation with the updated API structure"""
    try:
        dataset_id = request.json.get('dataset_id')
        features = request.json.get('features', [])
        target = request.json.get('target')
        algorithm = request.json.get('algorithm', 'random_forest')
        problem_type = request.json.get('problem_type', 'classification')
        cv_folds = request.json.get('cv_folds', 5)
        hyperparameters = request.json.get('hyperparameters', {})
        
        if not dataset_id or not features or not target:
            return jsonify({'success': False, 'error': 'Dataset ID, features, and target are required'}), 400
        
        dataset = Dataset.query.get_or_404(dataset_id)
        engine = MLEngine()
        
        result = engine.cross_validation(
            dataset.file_path, 
            features, 
            target, 
            algorithm, 
            cv_folds,
            hyperparameters
        )
        
        return jsonify({
            'success': True,
            'mean_score': result.get('mean_score'),
            'std_score': result.get('std_score'),
            'scores': result.get('scores', [])
        })
        
    except Exception as e:
        logging.error(f"Cross validation error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@ml_engine_bp.route('/tune-hyperparameters', methods=['POST'])
def tune_hyperparameters_new():
    """Tune hyperparameters with the updated API structure"""
    try:
        dataset_id = request.json.get('dataset_id')
        features = request.json.get('features', [])
        target = request.json.get('target')
        algorithm = request.json.get('algorithm', 'random_forest')
        problem_type = request.json.get('problem_type', 'classification')
        
        if not dataset_id or not features or not target:
            return jsonify({'success': False, 'error': 'Dataset ID, features, and target are required'}), 400
        
        dataset = Dataset.query.get_or_404(dataset_id)
        engine = MLEngine()
        
        # Define default parameter grids for different algorithms
        param_grids = {
            'random_forest': {
                'n_estimators': [50, 100, 200],
                'max_depth': [5, 10, 15, None],
                'min_samples_split': [2, 5, 10]
            },
            'logistic_regression': {
                'C': [0.1, 1.0, 10.0],
                'solver': ['liblinear', 'lbfgs']
            },
            'svm': {
                'C': [0.1, 1.0, 10.0],
                'kernel': ['linear', 'rbf'],
                'gamma': ['scale', 'auto']
            }
        }
        
        param_grid = param_grids.get(algorithm, {})
        
        result = engine.hyperparameter_tuning(
            dataset.file_path, 
            features, 
            target, 
            algorithm, 
            param_grid
        )
        
        return jsonify({
            'success': True,
            'best_params': result.get('best_params', {}),
            'best_score': result.get('best_score'),
            'results': result.get('results', {})
        })
        
    except Exception as e:
        logging.error(f"Hyperparameter tuning error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@ml_engine_bp.route('/feature_importance/<int:model_id>')
def get_feature_importance(model_id):
    try:
        model = MLModel.query.get_or_404(model_id)
        engine = MLEngine()
        
        importance = engine.get_feature_importance(model.id)
        
        return jsonify({
            'success': True,
            'feature_importance': importance
        })
        
    except Exception as e:
        logging.error(f"Feature importance error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@ml_engine_bp.route('/learning_curve/<int:dataset_id>', methods=['POST'])
def learning_curve(dataset_id):
    try:
        dataset = Dataset.query.get_or_404(dataset_id)
        engine = MLEngine()
        
        features = request.json.get('features', [])
        target = request.json.get('target')
        algorithm = request.json.get('algorithm', 'random_forest')
        
        if not features or not target:
            return jsonify({'error': 'Features and target parameters are required'}), 400
        
        result = engine.generate_learning_curve(dataset.file_path, features, target, algorithm)
        
        return jsonify({
            'success': True,
            'train_sizes': result['train_sizes'],
            'train_scores': result['train_scores'],
            'val_scores': result['val_scores']
        })
        
    except Exception as e:
        logging.error(f"Learning curve error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@ml_engine_bp.route('/list/<int:dataset_id>')
def list_models(dataset_id):
    try:
        models = MLModel.query.filter_by(dataset_id=dataset_id).all()
        
        model_list = []
        for model in models:
            model_list.append({
                'id': model.id,
                'name': model.model_name,
                'type': model.model_type,
                'algorithm': model.algorithm,
                'training_score': model.training_score,
                'validation_score': model.validation_score,
                'test_score': model.test_score,
                'created_at': model.created_at.isoformat()
            })
        
        return jsonify({
            'success': True,
            'models': model_list
        })
        
    except Exception as e:
        logging.error(f"List models error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@ml_engine_bp.route('/clustering/<int:dataset_id>', methods=['POST'])
def clustering_analysis(dataset_id):
    try:
        dataset = Dataset.query.get_or_404(dataset_id)
        engine = MLEngine()
        
        features = request.json.get('features', [])
        algorithm = request.json.get('algorithm', 'kmeans')
        n_clusters = request.json.get('n_clusters', 3)
        
        if not features:
            return jsonify({'error': 'Features parameter is required'}), 400
        
        result = engine.perform_clustering(dataset.file_path, features, algorithm, n_clusters)
        
        return jsonify({
            'success': True,
            'labels': result['labels'],
            'centers': result.get('centers'),
            'metrics': result['metrics']
        })
        
    except Exception as e:
        logging.error(f"Clustering analysis error: {str(e)}")
        return jsonify({'error': str(e)}), 500
