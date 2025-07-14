import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor, GradientBoostingClassifier, GradientBoostingRegressor
from sklearn.ensemble import ExtraTreesClassifier, ExtraTreesRegressor, AdaBoostClassifier, AdaBoostRegressor
from sklearn.ensemble import VotingClassifier, VotingRegressor, BaggingClassifier, BaggingRegressor
from sklearn.linear_model import LogisticRegression, LinearRegression, Ridge, Lasso, ElasticNet
from sklearn.svm import SVC, SVR
from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor
from sklearn.naive_bayes import GaussianNB, MultinomialNB
from sklearn.neighbors import KNeighborsClassifier, KNeighborsRegressor
from sklearn.neural_network import MLPClassifier, MLPRegressor
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV, learning_curve
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score, explained_variance_score
import xgboost as xgb
import lightgbm as lgb
import logging
from datetime import datetime
import pickle
import os
from models import Dataset, MLModel, db
from services.data_processor import DataProcessor
from flask import current_app
import json
import time

class MLEngine:
    def __init__(self):
        self.data_processor = DataProcessor()
        self.random_state = 42
        self.models_dir = 'models'
        self.ensure_models_dir()
        
        # Define available models
        self.classification_models = {
            'random_forest': RandomForestClassifier(n_estimators=100, random_state=self.random_state),
            'gradient_boosting': GradientBoostingClassifier(n_estimators=100, random_state=self.random_state),
            'extra_trees': ExtraTreesClassifier(n_estimators=100, random_state=self.random_state),
            'logistic_regression': LogisticRegression(random_state=self.random_state),
            'svm': SVC(random_state=self.random_state),
            'decision_tree': DecisionTreeClassifier(random_state=self.random_state),
            'naive_bayes': GaussianNB(),
            'knn': KNeighborsClassifier(),
            'mlp': MLPClassifier(random_state=self.random_state),
            'adaboost': AdaBoostClassifier(random_state=self.random_state),
            'xgboost': xgb.XGBClassifier(random_state=self.random_state),
            'lightgbm': lgb.LGBMClassifier(random_state=self.random_state)
        }
        
        self.regression_models = {
            'random_forest': RandomForestRegressor(n_estimators=100, random_state=self.random_state),
            'gradient_boosting': GradientBoostingRegressor(n_estimators=100, random_state=self.random_state),
            'extra_trees': ExtraTreesRegressor(n_estimators=100, random_state=self.random_state),
            'linear_regression': LinearRegression(),
            'ridge': Ridge(random_state=self.random_state),
            'lasso': Lasso(random_state=self.random_state),
            'elastic_net': ElasticNet(random_state=self.random_state),
            'svm': SVR(),
            'decision_tree': DecisionTreeRegressor(random_state=self.random_state),
            'knn': KNeighborsRegressor(),
            'mlp': MLPRegressor(random_state=self.random_state),
            'adaboost': AdaBoostRegressor(random_state=self.random_state),
            'xgboost': xgb.XGBRegressor(random_state=self.random_state),
            'lightgbm': lgb.LGBMRegressor(random_state=self.random_state)
        }
    
    def ensure_models_dir(self):
        if not os.path.exists(self.models_dir):
            os.makedirs(self.models_dir)
    
    def train_model(self, dataset_id, model_type, target_column, features=None, parameters=None):
        try:
            start_time = time.time()
            
            dataset = Dataset.query.get_or_404(dataset_id)
            df = self.data_processor.load_dataset(dataset)
            
            if target_column not in df.columns:
                return {'success': False, 'error': f'Target column {target_column} not found'}
            
            # Prepare features
            if features is None:
                features = [col for col in df.columns if col != target_column]
            
            # Filter to numeric features for now
            numeric_features = df[features].select_dtypes(include=[np.number]).columns.tolist()
            
            X = df[numeric_features].fillna(df[numeric_features].mean())
            y = df[target_column]
            
            # Remove rows with missing target values
            mask = ~y.isna()
            X = X[mask]
            y = y[mask]
            
            # Determine if classification or regression
            is_classification = not pd.api.types.is_numeric_dtype(y) or y.nunique() <= 10
            
            # Encode target if classification
            if is_classification and not pd.api.types.is_numeric_dtype(y):
                le = LabelEncoder()
                y = le.fit_transform(y.astype(str))
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=self.random_state, stratify=y if is_classification else None
            )
            
            # Scale features if needed
            if model_type in ['svm', 'logistic_regression', 'mlp', 'knn']:
                scaler = StandardScaler()
                X_train = scaler.fit_transform(X_train)
                X_test = scaler.transform(X_test)
            
            # Get model
            if is_classification:
                model = self.classification_models.get(model_type)
            else:
                model = self.regression_models.get(model_type)
            
            if model is None:
                return {'success': False, 'error': f'Unknown model type: {model_type}'}
            
            # Apply custom parameters
            if parameters:
                model.set_params(**parameters)
            
            # Train model
            model.fit(X_train, y_train)
            
            # Make predictions
            y_pred = model.predict(X_test)
            
            # Calculate metrics
            if is_classification:
                metrics = self.calculate_classification_metrics(y_test, y_pred)
            else:
                metrics = self.calculate_regression_metrics(y_test, y_pred)
            
            # Feature importance
            feature_importance = self.get_model_feature_importance(model, numeric_features)
            
            training_time = time.time() - start_time
            
            # Save model
            model_filename = f'model_{dataset_id}_{model_type}_{int(time.time())}.pkl'
            model_path = os.path.join(self.models_dir, model_filename)
            
            model_data = {
                'model': model,
                'features': numeric_features,
                'target_column': target_column,
                'is_classification': is_classification,
                'scaler': scaler if model_type in ['svm', 'logistic_regression', 'mlp', 'knn'] else None,
                'label_encoder': le if is_classification and not pd.api.types.is_numeric_dtype(df[target_column]) else None
            }
            
            with open(model_path, 'wb') as f:
                pickle.dump(model_data, f)
            
            # Save to database
            ml_model = MLModel(
                dataset_id=dataset_id,
                model_type=model_type,
                target_column=target_column,
                features=numeric_features,
                parameters=parameters or {},
                performance_metrics=metrics,
                feature_importance=feature_importance,
                training_time=training_time,
                status='completed'
            )
            
            db.session.add(ml_model)
            db.session.commit()
            
            return {
                'success': True,
                'model_id': ml_model.id,
                'metrics': metrics,
                'feature_importance': feature_importance,
                'training_time': training_time,
                'model_path': model_path
            }
            
        except Exception as e:
            current_app.logger.error(f"Model training error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def calculate_classification_metrics(self, y_true, y_pred):
        try:
            return {
                'accuracy': float(accuracy_score(y_true, y_pred)),
                'precision': float(precision_score(y_true, y_pred, average='weighted')),
                'recall': float(recall_score(y_true, y_pred, average='weighted')),
                'f1_score': float(f1_score(y_true, y_pred, average='weighted')),
                'confusion_matrix': confusion_matrix(y_true, y_pred).tolist()
            }
        except Exception as e:
            current_app.logger.error(f"Classification metrics error: {str(e)}")
            return {}
    
    def calculate_regression_metrics(self, y_true, y_pred):
        try:
            return {
                'mse': float(mean_squared_error(y_true, y_pred)),
                'rmse': float(np.sqrt(mean_squared_error(y_true, y_pred))),
                'mae': float(mean_absolute_error(y_true, y_pred)),
                'r2_score': float(r2_score(y_true, y_pred)),
                'explained_variance': float(explained_variance_score(y_true, y_pred))
            }
        except Exception as e:
            current_app.logger.error(f"Regression metrics error: {str(e)}")
            return {}
    
    def get_model_feature_importance(self, model, feature_names):
        try:
            if hasattr(model, 'feature_importances_'):
                importances = model.feature_importances_
                return dict(zip(feature_names, importances.tolist()))
            elif hasattr(model, 'coef_'):
                coefficients = model.coef_
                if coefficients.ndim == 1:
                    return dict(zip(feature_names, coefficients.tolist()))
                else:
                    return dict(zip(feature_names, coefficients[0].tolist()))
            else:
                return {}
        except Exception as e:
            current_app.logger.error(f"Feature importance error: {str(e)}")
            return {}
    
    def evaluate_model(self, model_id):
        try:
            ml_model = MLModel.query.get_or_404(model_id)
            
            # Load model
            model_path = os.path.join(self.models_dir, f'model_{ml_model.dataset_id}_{ml_model.model_type}_{model_id}.pkl')
            
            if not os.path.exists(model_path):
                return {'success': False, 'error': 'Model file not found'}
            
            with open(model_path, 'rb') as f:
                model_data = pickle.load(f)
            
            # Get dataset
            dataset = Dataset.query.get_or_404(ml_model.dataset_id)
            df = self.data_processor.load_dataset(dataset)
            
            # Prepare data
            X = df[model_data['features']].fillna(df[model_data['features']].mean())
            y = df[ml_model.target_column]
            
            # Remove rows with missing target values
            mask = ~y.isna()
            X = X[mask]
            y = y[mask]
            
            # Apply transformations
            if model_data.get('label_encoder'):
                y = model_data['label_encoder'].transform(y.astype(str))
            
            if model_data.get('scaler'):
                X = model_data['scaler'].transform(X)
            
            # Make predictions
            y_pred = model_data['model'].predict(X)
            
            # Calculate metrics
            if model_data['is_classification']:
                metrics = self.calculate_classification_metrics(y, y_pred)
            else:
                metrics = self.calculate_regression_metrics(y, y_pred)
            
            # Cross-validation
            cv_scores = cross_val_score(model_data['model'], X, y, cv=5)
            
            return {
                'success': True,
                'metrics': metrics,
                'cv_scores': cv_scores.tolist(),
                'cv_mean': float(cv_scores.mean()),
                'cv_std': float(cv_scores.std())
            }
            
        except Exception as e:
            current_app.logger.error(f"Model evaluation error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def predict(self, model_id, input_data):
        try:
            ml_model = MLModel.query.get_or_404(model_id)
            
            # Load model
            model_path = os.path.join(self.models_dir, f'model_{ml_model.dataset_id}_{ml_model.model_type}_{model_id}.pkl')
            
            if not os.path.exists(model_path):
                return {'success': False, 'error': 'Model file not found'}
            
            with open(model_path, 'rb') as f:
                model_data = pickle.load(f)
            
            # Prepare input data
            if isinstance(input_data, dict):
                input_df = pd.DataFrame([input_data])
            else:
                input_df = pd.DataFrame(input_data)
            
            # Ensure all required features are present
            for feature in model_data['features']:
                if feature not in input_df.columns:
                    input_df[feature] = 0  # Default value
            
            X = input_df[model_data['features']].fillna(0)
            
            # Apply transformations
            if model_data.get('scaler'):
                X = model_data['scaler'].transform(X)
            
            # Make prediction
            predictions = model_data['model'].predict(X)
            
            # Get prediction probabilities if classification
            probabilities = None
            if model_data['is_classification'] and hasattr(model_data['model'], 'predict_proba'):
                probabilities = model_data['model'].predict_proba(X).tolist()
            
            # Transform predictions back if needed
            if model_data.get('label_encoder'):
                predictions = model_data['label_encoder'].inverse_transform(predictions)
            
            return {
                'success': True,
                'predictions': predictions.tolist(),
                'probabilities': probabilities
            }
            
        except Exception as e:
            current_app.logger.error(f"Prediction error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def get_feature_importance(self, model_id):
        try:
            ml_model = MLModel.query.get_or_404(model_id)
            
            return {
                'success': True,
                'feature_importance': ml_model.feature_importance or {}
            }
            
        except Exception as e:
            current_app.logger.error(f"Feature importance error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def hyperparameter_tuning(self, dataset_id, model_type, target_column, features=None, param_grid=None, cv=5):
        try:
            dataset = Dataset.query.get_or_404(dataset_id)
            df = self.data_processor.load_dataset(dataset)
            
            if target_column not in df.columns:
                return {'success': False, 'error': f'Target column {target_column} not found'}
            
            # Prepare features
            if features is None:
                features = [col for col in df.columns if col != target_column]
            
            numeric_features = df[features].select_dtypes(include=[np.number]).columns.tolist()
            
            X = df[numeric_features].fillna(df[numeric_features].mean())
            y = df[target_column]
            
            # Remove rows with missing target values
            mask = ~y.isna()
            X = X[mask]
            y = y[mask]
            
            # Determine if classification or regression
            is_classification = not pd.api.types.is_numeric_dtype(y) or y.nunique() <= 10
            
            # Encode target if classification
            if is_classification and not pd.api.types.is_numeric_dtype(y):
                le = LabelEncoder()
                y = le.fit_transform(y.astype(str))
            
            # Get model
            if is_classification:
                model = self.classification_models.get(model_type)
            else:
                model = self.regression_models.get(model_type)
            
            if model is None:
                return {'success': False, 'error': f'Unknown model type: {model_type}'}
            
            # Default parameter grids
            if param_grid is None:
                param_grid = self.get_default_param_grid(model_type, is_classification)
            
            # Scale features if needed
            if model_type in ['svm', 'logistic_regression', 'mlp', 'knn']:
                scaler = StandardScaler()
                X = scaler.fit_transform(X)
            
            # Grid search
            grid_search = GridSearchCV(
                model, param_grid, cv=cv, 
                scoring='accuracy' if is_classification else 'r2',
                n_jobs=-1
            )
            
            grid_search.fit(X, y)
            
            return {
                'success': True,
                'best_params': grid_search.best_params_,
                'best_score': float(grid_search.best_score_),
                'cv_results': {
                    'mean_test_score': grid_search.cv_results_['mean_test_score'].tolist(),
                    'std_test_score': grid_search.cv_results_['std_test_score'].tolist(),
                    'params': grid_search.cv_results_['params']
                }
            }
            
        except Exception as e:
            current_app.logger.error(f"Hyperparameter tuning error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def get_default_param_grid(self, model_type, is_classification):
        param_grids = {
            'random_forest': {
                'n_estimators': [50, 100, 200],
                'max_depth': [None, 10, 20],
                'min_samples_split': [2, 5, 10]
            },
            'gradient_boosting': {
                'n_estimators': [50, 100, 200],
                'learning_rate': [0.01, 0.1, 0.2],
                'max_depth': [3, 5, 7]
            },
            'svm': {
                'C': [0.1, 1, 10],
                'gamma': ['scale', 'auto'],
                'kernel': ['rbf', 'linear']
            },
            'logistic_regression': {
                'C': [0.1, 1, 10],
                'penalty': ['l1', 'l2'],
                'solver': ['liblinear', 'lbfgs']
            },
            'knn': {
                'n_neighbors': [3, 5, 7, 9],
                'weights': ['uniform', 'distance'],
                'metric': ['euclidean', 'manhattan']
            }
        }
        
        return param_grids.get(model_type, {})
    
    def compare_models(self, dataset_id, model_types, target_column, features=None):
        try:
            results = {}
            
            for model_type in model_types:
                result = self.train_model(dataset_id, model_type, target_column, features)
                if result['success']:
                    results[model_type] = {
                        'metrics': result['metrics'],
                        'training_time': result['training_time'],
                        'model_id': result['model_id']
                    }
                else:
                    results[model_type] = {'error': result['error']}
            
            # Determine best model
            best_model = None
            best_score = -float('inf')
            
            for model_type, result in results.items():
                if 'metrics' in result:
                    # Use accuracy for classification, r2 for regression
                    score = result['metrics'].get('accuracy', result['metrics'].get('r2_score', 0))
                    if score > best_score:
                        best_score = score
                        best_model = model_type
            
            return {
                'success': True,
                'results': results,
                'best_model': best_model,
                'best_score': best_score
            }
            
        except Exception as e:
            current_app.logger.error(f"Model comparison error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def cross_validation(self, dataset_id, model_type, target_column, features=None, cv=5):
        try:
            dataset = Dataset.query.get_or_404(dataset_id)
            df = self.data_processor.load_dataset(dataset)
            
            if target_column not in df.columns:
                return {'success': False, 'error': f'Target column {target_column} not found'}
            
            # Prepare features
            if features is None:
                features = [col for col in df.columns if col != target_column]
            
            numeric_features = df[features].select_dtypes(include=[np.number]).columns.tolist()
            
            X = df[numeric_features].fillna(df[numeric_features].mean())
            y = df[target_column]
            
            # Remove rows with missing target values
            mask = ~y.isna()
            X = X[mask]
            y = y[mask]
            
            # Determine if classification or regression
            is_classification = not pd.api.types.is_numeric_dtype(y) or y.nunique() <= 10
            
            # Encode target if classification
            if is_classification and not pd.api.types.is_numeric_dtype(y):
                le = LabelEncoder()
                y = le.fit_transform(y.astype(str))
            
            # Get model
            if is_classification:
                model = self.classification_models.get(model_type)
            else:
                model = self.regression_models.get(model_type)
            
            if model is None:
                return {'success': False, 'error': f'Unknown model type: {model_type}'}
            
            # Scale features if needed
            if model_type in ['svm', 'logistic_regression', 'mlp', 'knn']:
                scaler = StandardScaler()
                X = scaler.fit_transform(X)
            
            # Cross-validation
            scoring = 'accuracy' if is_classification else 'r2'
            cv_scores = cross_val_score(model, X, y, cv=cv, scoring=scoring)
            
            return {
                'success': True,
                'cv_scores': cv_scores.tolist(),
                'cv_mean': float(cv_scores.mean()),
                'cv_std': float(cv_scores.std()),
                'scoring': scoring
            }
            
        except Exception as e:
            current_app.logger.error(f"Cross validation error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def learning_curve(self, dataset_id, model_type, target_column, features=None):
        try:
            dataset = Dataset.query.get_or_404(dataset_id)
            df = self.data_processor.load_dataset(dataset)
            
            if target_column not in df.columns:
                return {'success': False, 'error': f'Target column {target_column} not found'}
            
            # Prepare features
            if features is None:
                features = [col for col in df.columns if col != target_column]
            
            numeric_features = df[features].select_dtypes(include=[np.number]).columns.tolist()
            
            X = df[numeric_features].fillna(df[numeric_features].mean())
            y = df[target_column]
            
            # Remove rows with missing target values
            mask = ~y.isna()
            X = X[mask]
            y = y[mask]
            
            # Determine if classification or regression
            is_classification = not pd.api.types.is_numeric_dtype(y) or y.nunique() <= 10
            
            # Encode target if classification
            if is_classification and not pd.api.types.is_numeric_dtype(y):
                le = LabelEncoder()
                y = le.fit_transform(y.astype(str))
            
            # Get model
            if is_classification:
                model = self.classification_models.get(model_type)
            else:
                model = self.regression_models.get(model_type)
            
            if model is None:
                return {'success': False, 'error': f'Unknown model type: {model_type}'}
            
            # Scale features if needed
            if model_type in ['svm', 'logistic_regression', 'mlp', 'knn']:
                scaler = StandardScaler()
                X = scaler.fit_transform(X)
            
            # Learning curve
            train_sizes = np.linspace(0.1, 1.0, 10)
            train_sizes_abs, train_scores, val_scores = learning_curve(
                model, X, y, train_sizes=train_sizes, cv=5,
                scoring='accuracy' if is_classification else 'r2'
            )
            
            return {
                'success': True,
                'train_sizes': train_sizes_abs.tolist(),
                'train_scores_mean': train_scores.mean(axis=1).tolist(),
                'train_scores_std': train_scores.std(axis=1).tolist(),
                'val_scores_mean': val_scores.mean(axis=1).tolist(),
                'val_scores_std': val_scores.std(axis=1).tolist()
            }
            
        except Exception as e:
            current_app.logger.error(f"Learning curve error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def delete_model(self, model_id):
        try:
            ml_model = MLModel.query.get_or_404(model_id)
            
            # Delete model file
            model_path = os.path.join(self.models_dir, f'model_{ml_model.dataset_id}_{ml_model.model_type}_{model_id}.pkl')
            if os.path.exists(model_path):
                os.remove(model_path)
            
            # Delete database record
            db.session.delete(ml_model)
            db.session.commit()
            
            return {'success': True, 'message': 'Model deleted successfully'}
            
        except Exception as e:
            current_app.logger.error(f"Delete model error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def ensemble_model(self, dataset_id, model_types, target_column, features=None, ensemble_method='voting'):
        try:
            dataset = Dataset.query.get_or_404(dataset_id)
            df = self.data_processor.load_dataset(dataset)
            
            if target_column not in df.columns:
                return {'success': False, 'error': f'Target column {target_column} not found'}
            
            # Prepare features
            if features is None:
                features = [col for col in df.columns if col != target_column]
            
            numeric_features = df[features].select_dtypes(include=[np.number]).columns.tolist()
            
            X = df[numeric_features].fillna(df[numeric_features].mean())
            y = df[target_column]
            
            # Remove rows with missing target values
            mask = ~y.isna()
            X = X[mask]
            y = y[mask]
            
            # Determine if classification or regression
            is_classification = not pd.api.types.is_numeric_dtype(y) or y.nunique() <= 10
            
            # Encode target if classification
            if is_classification and not pd.api.types.is_numeric_dtype(y):
                le = LabelEncoder()
                y = le.fit_transform(y.astype(str))
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=self.random_state
            )
            
            # Prepare models
            models = []
            for model_type in model_types:
                if is_classification:
                    model = self.classification_models.get(model_type)
                else:
                    model = self.regression_models.get(model_type)
                
                if model:
                    models.append((model_type, model))
            
            if not models:
                return {'success': False, 'error': 'No valid models found'}
            
            # Create ensemble
            if ensemble_method == 'voting':
                if is_classification:
                    ensemble = VotingClassifier(estimators=models, voting='soft')
                else:
                    ensemble = VotingRegressor(estimators=models)
            else:
                return {'success': False, 'error': f'Unknown ensemble method: {ensemble_method}'}
            
            # Train ensemble
            ensemble.fit(X_train, y_train)
            
            # Make predictions
            y_pred = ensemble.predict(X_test)
            
            # Calculate metrics
            if is_classification:
                metrics = self.calculate_classification_metrics(y_test, y_pred)
            else:
                metrics = self.calculate_regression_metrics(y_test, y_pred)
            
            return {
                'success': True,
                'metrics': metrics,
                'ensemble_method': ensemble_method,
                'models_used': model_types
            }
            
        except Exception as e:
            current_app.logger.error(f"Ensemble model error: {str(e)}")
            return {'success': False, 'error': str(e)}
