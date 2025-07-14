import pandas as pd
import numpy as np
from sklearn.decomposition import PCA, TruncatedSVD, FastICA, FactorAnalysis
from sklearn.manifold import TSNE, MDS, Isomap
from sklearn.feature_selection import RFE, SelectKBest, SelectPercentile, VarianceThreshold
from sklearn.feature_selection import f_classif, f_regression, chi2, mutual_info_classif, mutual_info_regression
from sklearn.cluster import KMeans, DBSCAN, AgglomerativeClustering
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.linear_model import LogisticRegression, LinearRegression
from sklearn.svm import SVC, SVR
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.metrics import silhouette_score, calinski_harabasz_score, davies_bouldin_score
from sklearn.preprocessing import StandardScaler
from statsmodels.stats.outliers_influence import variance_inflation_factor
import umap
import logging
from datetime import datetime
from models import Dataset, Analysis, db
from services.data_processor import DataProcessor
from flask import current_app
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json

class AdvanceFeatureEngineering:
    def __init__(self):
        self.data_processor = DataProcessor()
        self.random_state = 42
    
    def pca_analysis(self, dataset_id, n_components=None, columns=None):
        try:
            dataset = Dataset.query.get_or_404(dataset_id)
            df = self.data_processor.load_dataset(dataset)
            
            if columns is None:
                columns = df.select_dtypes(include=[np.number]).columns.tolist()
            
            # Remove columns with all NaN values
            columns = [col for col in columns if not df[col].isna().all()]
            
            if len(columns) < 2:
                return {'success': False, 'error': 'At least 2 numeric columns required for PCA'}
            
            # Prepare data
            X = df[columns].fillna(df[columns].mean())
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)
            
            # Determine number of components
            if n_components is None:
                n_components = min(len(columns), len(df))
            
            # Apply PCA
            pca = PCA(n_components=n_components, random_state=self.random_state)
            X_pca = pca.fit_transform(X_scaled)
            
            # Calculate explained variance
            explained_variance = pca.explained_variance_ratio_
            cumulative_variance = np.cumsum(explained_variance)
            
            # Create PCA dataframe
            pca_columns = [f'PC{i+1}' for i in range(n_components)]
            df_pca = pd.DataFrame(X_pca, columns=pca_columns)
            
            # Component loadings
            loadings = pd.DataFrame(
                pca.components_.T,
                columns=pca_columns,
                index=columns
            )
            
            results = {
                'pca_data': df_pca.to_dict('records'),
                'explained_variance': explained_variance.tolist(),
                'cumulative_variance': cumulative_variance.tolist(),
                'loadings': loadings.to_dict(),
                'component_names': pca_columns,
                'original_columns': columns,
                'n_components': n_components,
                'total_variance_explained': float(cumulative_variance[-1])
            }
            
            # Save analysis
            analysis = Analysis(
                dataset_id=dataset_id,
                analysis_type='pca',
                parameters={'n_components': n_components, 'columns': columns},
                results=results,
                status='completed'
            )
            db.session.add(analysis)
            db.session.commit()
            
            return {'success': True, 'results': results}
            
        except Exception as e:
            current_app.logger.error(f"PCA analysis error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def rfe_analysis(self, dataset_id, target_column, n_features=10, estimator='random_forest'):
        try:
            dataset = Dataset.query.get_or_404(dataset_id)
            df = self.data_processor.load_dataset(dataset)
            
            if target_column not in df.columns:
                return {'success': False, 'error': f'Target column {target_column} not found'}
            
            # Prepare features and target
            feature_columns = [col for col in df.columns if col != target_column]
            numeric_features = df[feature_columns].select_dtypes(include=[np.number]).columns.tolist()
            
            if len(numeric_features) < n_features:
                n_features = len(numeric_features)
            
            X = df[numeric_features].fillna(df[numeric_features].mean())
            y = df[target_column]
            
            # Handle missing values in target
            mask = ~y.isna()
            X = X[mask]
            y = y[mask]
            
            # Choose estimator
            if pd.api.types.is_numeric_dtype(y):
                # Regression
                if estimator == 'random_forest':
                    est = RandomForestRegressor(n_estimators=100, random_state=self.random_state)
                elif estimator == 'linear':
                    est = LinearRegression()
                elif estimator == 'svm':
                    est = SVR()
                else:
                    est = RandomForestRegressor(n_estimators=100, random_state=self.random_state)
            else:
                # Classification
                if estimator == 'random_forest':
                    est = RandomForestClassifier(n_estimators=100, random_state=self.random_state)
                elif estimator == 'logistic':
                    est = LogisticRegression(random_state=self.random_state)
                elif estimator == 'svm':
                    est = SVC(random_state=self.random_state)
                else:
                    est = RandomForestClassifier(n_estimators=100, random_state=self.random_state)
            
            # Apply RFE
            rfe = RFE(estimator=est, n_features_to_select=n_features)
            rfe.fit(X, y)
            
            # Get selected features
            selected_features = X.columns[rfe.support_].tolist()
            feature_ranking = dict(zip(X.columns, rfe.ranking_))
            
            # Get feature importance if available
            feature_importance = {}
            if hasattr(rfe.estimator_, 'feature_importances_'):
                feature_importance = dict(zip(selected_features, rfe.estimator_.feature_importances_))
            
            results = {
                'selected_features': selected_features,
                'feature_ranking': feature_ranking,
                'feature_importance': feature_importance,
                'n_features_selected': n_features,
                'total_features': len(numeric_features),
                'estimator_used': estimator,
                'target_column': target_column
            }
            
            # Save analysis
            analysis = Analysis(
                dataset_id=dataset_id,
                analysis_type='rfe',
                parameters={'target_column': target_column, 'n_features': n_features, 'estimator': estimator},
                results=results,
                status='completed'
            )
            db.session.add(analysis)
            db.session.commit()
            
            return {'success': True, 'results': results}
            
        except Exception as e:
            current_app.logger.error(f"RFE analysis error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def clustering_analysis(self, dataset_id, algorithm='kmeans', n_clusters=3, columns=None):
        try:
            dataset = Dataset.query.get_or_404(dataset_id)
            df = self.data_processor.load_dataset(dataset)
            
            if columns is None:
                columns = df.select_dtypes(include=[np.number]).columns.tolist()
            
            # Remove columns with all NaN values
            columns = [col for col in columns if not df[col].isna().all()]
            
            if len(columns) < 2:
                return {'success': False, 'error': 'At least 2 numeric columns required for clustering'}
            
            # Prepare data
            X = df[columns].fillna(df[columns].mean())
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)
            
            # Apply clustering
            if algorithm == 'kmeans':
                clusterer = KMeans(n_clusters=n_clusters, random_state=self.random_state)
                labels = clusterer.fit_predict(X_scaled)
                centers = clusterer.cluster_centers_
            elif algorithm == 'dbscan':
                clusterer = DBSCAN(eps=0.5, min_samples=5)
                labels = clusterer.fit_predict(X_scaled)
                centers = None
                n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
            elif algorithm == 'hierarchical':
                clusterer = AgglomerativeClustering(n_clusters=n_clusters)
                labels = clusterer.fit_predict(X_scaled)
                centers = None
            else:
                return {'success': False, 'error': f'Unknown clustering algorithm: {algorithm}'}
            
            # Calculate clustering metrics
            metrics = {}
            if n_clusters > 1:
                try:
                    metrics['silhouette_score'] = float(silhouette_score(X_scaled, labels))
                    metrics['calinski_harabasz_score'] = float(calinski_harabasz_score(X_scaled, labels))
                    metrics['davies_bouldin_score'] = float(davies_bouldin_score(X_scaled, labels))
                except:
                    pass
            
            # Create clustered dataframe
            df_clustered = df.copy()
            df_clustered['cluster'] = labels
            
            # Cluster statistics
            cluster_stats = {}
            for cluster_id in set(labels):
                if cluster_id != -1:  # Exclude noise points in DBSCAN
                    cluster_mask = labels == cluster_id
                    cluster_data = X[cluster_mask]
                    cluster_stats[f'cluster_{cluster_id}'] = {
                        'size': int(np.sum(cluster_mask)),
                        'percentage': float(np.sum(cluster_mask) / len(labels) * 100),
                        'centroid': cluster_data.mean().to_dict() if len(cluster_data) > 0 else {}
                    }
            
            results = {
                'labels': labels.tolist(),
                'n_clusters': n_clusters,
                'algorithm': algorithm,
                'cluster_stats': cluster_stats,
                'metrics': metrics,
                'columns_used': columns,
                'cluster_centers': centers.tolist() if centers is not None else None
            }
            
            # Save analysis
            analysis = Analysis(
                dataset_id=dataset_id,
                analysis_type='clustering',
                parameters={'algorithm': algorithm, 'n_clusters': n_clusters, 'columns': columns},
                results=results,
                status='completed'
            )
            db.session.add(analysis)
            db.session.commit()
            
            return {'success': True, 'results': results}
            
        except Exception as e:
            current_app.logger.error(f"Clustering analysis error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def dimensionality_reduction(self, dataset_id, method='tsne', n_components=2, columns=None):
        try:
            dataset = Dataset.query.get_or_404(dataset_id)
            df = self.data_processor.load_dataset(dataset)
            
            if columns is None:
                columns = df.select_dtypes(include=[np.number]).columns.tolist()
            
            # Remove columns with all NaN values
            columns = [col for col in columns if not df[col].isna().all()]
            
            if len(columns) < 2:
                return {'success': False, 'error': 'At least 2 numeric columns required for dimensionality reduction'}
            
            # Prepare data
            X = df[columns].fillna(df[columns].mean())
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)
            
            # Apply dimensionality reduction
            if method == 'tsne':
                reducer = TSNE(n_components=n_components, random_state=self.random_state)
                X_reduced = reducer.fit_transform(X_scaled)
            elif method == 'umap':
                reducer = umap.UMAP(n_components=n_components, random_state=self.random_state)
                X_reduced = reducer.fit_transform(X_scaled)
            elif method == 'mds':
                reducer = MDS(n_components=n_components, random_state=self.random_state)
                X_reduced = reducer.fit_transform(X_scaled)
            elif method == 'isomap':
                reducer = Isomap(n_components=n_components)
                X_reduced = reducer.fit_transform(X_scaled)
            elif method == 'pca':
                reducer = PCA(n_components=n_components, random_state=self.random_state)
                X_reduced = reducer.fit_transform(X_scaled)
            else:
                return {'success': False, 'error': f'Unknown dimensionality reduction method: {method}'}
            
            # Create reduced dataframe
            component_names = [f'{method.upper()}_{i+1}' for i in range(n_components)]
            df_reduced = pd.DataFrame(X_reduced, columns=component_names)
            
            results = {
                'reduced_data': df_reduced.to_dict('records'),
                'method': method,
                'n_components': n_components,
                'original_dimensions': len(columns),
                'component_names': component_names,
                'columns_used': columns
            }
            
            # Add method-specific results
            if method == 'pca' and hasattr(reducer, 'explained_variance_ratio_'):
                results['explained_variance'] = reducer.explained_variance_ratio_.tolist()
                results['cumulative_variance'] = np.cumsum(reducer.explained_variance_ratio_).tolist()
            
            # Save analysis
            analysis = Analysis(
                dataset_id=dataset_id,
                analysis_type='dimensionality_reduction',
                parameters={'method': method, 'n_components': n_components, 'columns': columns},
                results=results,
                status='completed'
            )
            db.session.add(analysis)
            db.session.commit()
            
            return {'success': True, 'results': results}
            
        except Exception as e:
            current_app.logger.error(f"Dimensionality reduction error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def feature_selection(self, dataset_id, target_column, method='selectkbest', k=10):
        try:
            dataset = Dataset.query.get_or_404(dataset_id)
            df = self.data_processor.load_dataset(dataset)
            
            if target_column not in df.columns:
                return {'success': False, 'error': f'Target column {target_column} not found'}
            
            # Prepare features and target
            feature_columns = [col for col in df.columns if col != target_column]
            numeric_features = df[feature_columns].select_dtypes(include=[np.number]).columns.tolist()
            
            X = df[numeric_features].fillna(df[numeric_features].mean())
            y = df[target_column]
            
            # Handle missing values in target
            mask = ~y.isna()
            X = X[mask]
            y = y[mask]
            
            # Choose scoring function
            if pd.api.types.is_numeric_dtype(y):
                score_func = f_regression
            else:
                score_func = f_classif
            
            # Apply feature selection
            if method == 'selectkbest':
                selector = SelectKBest(score_func=score_func, k=min(k, len(numeric_features)))
            elif method == 'selectpercentile':
                selector = SelectPercentile(score_func=score_func, percentile=k)
            elif method == 'variancethreshold':
                selector = VarianceThreshold(threshold=0.0)
            else:
                return {'success': False, 'error': f'Unknown feature selection method: {method}'}
            
            X_selected = selector.fit_transform(X, y)
            
            # Get selected features
            if hasattr(selector, 'get_support'):
                selected_features = X.columns[selector.get_support()].tolist()
            else:
                selected_features = X.columns.tolist()
            
            # Get feature scores
            feature_scores = {}
            if hasattr(selector, 'scores_'):
                feature_scores = dict(zip(X.columns, selector.scores_))
            
            results = {
                'selected_features': selected_features,
                'feature_scores': feature_scores,
                'n_features_selected': len(selected_features),
                'total_features': len(numeric_features),
                'method': method,
                'target_column': target_column,
                'selection_parameter': k
            }
            
            # Save analysis
            analysis = Analysis(
                dataset_id=dataset_id,
                analysis_type='feature_selection',
                parameters={'target_column': target_column, 'method': method, 'k': k},
                results=results,
                status='completed'
            )
            db.session.add(analysis)
            db.session.commit()
            
            return {'success': True, 'results': results}
            
        except Exception as e:
            current_app.logger.error(f"Feature selection error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def feature_extraction(self, dataset_id, method='lda', n_components=2, target_column=None):
        try:
            dataset = Dataset.query.get_or_404(dataset_id)
            df = self.data_processor.load_dataset(dataset)
            
            # Prepare data
            numeric_columns = df.select_dtypes(include=[np.number]).columns.tolist()
            
            if target_column and target_column in numeric_columns:
                numeric_columns.remove(target_column)
            
            X = df[numeric_columns].fillna(df[numeric_columns].mean())
            
            # Apply feature extraction
            if method == 'lda' and target_column:
                y = df[target_column]
                mask = ~y.isna()
                X = X[mask]
                y = y[mask]
                
                extractor = LinearDiscriminantAnalysis(n_components=n_components)
                X_extracted = extractor.fit_transform(X, y)
            elif method == 'ica':
                extractor = FastICA(n_components=n_components, random_state=self.random_state)
                X_extracted = extractor.fit_transform(X)
            elif method == 'factor_analysis':
                extractor = FactorAnalysis(n_components=n_components, random_state=self.random_state)
                X_extracted = extractor.fit_transform(X)
            elif method == 'truncated_svd':
                extractor = TruncatedSVD(n_components=n_components, random_state=self.random_state)
                X_extracted = extractor.fit_transform(X)
            else:
                return {'success': False, 'error': f'Unknown feature extraction method: {method}'}
            
            # Create extracted features dataframe
            feature_names = [f'{method.upper()}_{i+1}' for i in range(n_components)]
            df_extracted = pd.DataFrame(X_extracted, columns=feature_names)
            
            results = {
                'extracted_features': df_extracted.to_dict('records'),
                'method': method,
                'n_components': n_components,
                'original_features': len(numeric_columns),
                'feature_names': feature_names,
                'target_column': target_column
            }
            
            # Add method-specific results
            if hasattr(extractor, 'explained_variance_ratio_'):
                results['explained_variance'] = extractor.explained_variance_ratio_.tolist()
            
            # Save analysis
            analysis = Analysis(
                dataset_id=dataset_id,
                analysis_type='feature_extraction',
                parameters={'method': method, 'n_components': n_components, 'target_column': target_column},
                results=results,
                status='completed'
            )
            db.session.add(analysis)
            db.session.commit()
            
            return {'success': True, 'results': results}
            
        except Exception as e:
            current_app.logger.error(f"Feature extraction error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def vif_analysis(self, dataset_id):
        try:
            dataset = Dataset.query.get_or_404(dataset_id)
            df = self.data_processor.load_dataset(dataset)
            
            # Get numeric columns
            numeric_columns = df.select_dtypes(include=[np.number]).columns.tolist()
            
            if len(numeric_columns) < 2:
                return {'success': False, 'error': 'At least 2 numeric columns required for VIF analysis'}
            
            # Prepare data
            X = df[numeric_columns].fillna(df[numeric_columns].mean())
            
            # Calculate VIF for each feature
            vif_data = []
            for i in range(len(numeric_columns)):
                vif_value = variance_inflation_factor(X.values, i)
                vif_data.append({
                    'feature': numeric_columns[i],
                    'vif': float(vif_value) if not np.isnan(vif_value) else 0.0
                })
            
            # Sort by VIF value
            vif_data.sort(key=lambda x: x['vif'], reverse=True)
            
            # Identify high VIF features
            high_vif_features = [item for item in vif_data if item['vif'] > 10]
            moderate_vif_features = [item for item in vif_data if 5 <= item['vif'] <= 10]
            low_vif_features = [item for item in vif_data if item['vif'] < 5]
            
            results = {
                'vif_values': vif_data,
                'high_vif_features': high_vif_features,
                'moderate_vif_features': moderate_vif_features,
                'low_vif_features': low_vif_features,
                'recommendations': self.generate_vif_recommendations(vif_data)
            }
            
            # Save analysis
            analysis = Analysis(
                dataset_id=dataset_id,
                analysis_type='vif',
                results=results,
                status='completed'
            )
            db.session.add(analysis)
            db.session.commit()
            
            return {'success': True, 'results': results}
            
        except Exception as e:
            current_app.logger.error(f"VIF analysis error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def generate_vif_recommendations(self, vif_data):
        recommendations = []
        
        high_vif = [item for item in vif_data if item['vif'] > 10]
        if high_vif:
            recommendations.append({
                'type': 'high_multicollinearity',
                'message': f"Features with high VIF (>10): {', '.join([item['feature'] for item in high_vif])}",
                'action': 'Consider removing or combining these features'
            })
        
        moderate_vif = [item for item in vif_data if 5 <= item['vif'] <= 10]
        if moderate_vif:
            recommendations.append({
                'type': 'moderate_multicollinearity',
                'message': f"Features with moderate VIF (5-10): {', '.join([item['feature'] for item in moderate_vif])}",
                'action': 'Monitor these features for potential multicollinearity issues'
            })
        
        if not high_vif and not moderate_vif:
            recommendations.append({
                'type': 'low_multicollinearity',
                'message': 'All features have acceptable VIF values (<5)',
                'action': 'No multicollinearity concerns detected'
            })
        
        return recommendations
    
    def variance_threshold(self, dataset_id, threshold=0.0):
        try:
            dataset = Dataset.query.get_or_404(dataset_id)
            df = self.data_processor.load_dataset(dataset)
            
            # Get numeric columns
            numeric_columns = df.select_dtypes(include=[np.number]).columns.tolist()
            
            if len(numeric_columns) == 0:
                return {'success': False, 'error': 'No numeric columns found'}
            
            # Prepare data
            X = df[numeric_columns].fillna(df[numeric_columns].mean())
            
            # Apply variance threshold
            selector = VarianceThreshold(threshold=threshold)
            X_selected = selector.fit_transform(X)
            
            # Get selected features
            selected_features = X.columns[selector.get_support()].tolist()
            removed_features = X.columns[~selector.get_support()].tolist()
            
            # Get variance values
            variances = X.var().to_dict()
            
            results = {
                'selected_features': selected_features,
                'removed_features': removed_features,
                'variances': variances,
                'threshold': threshold,
                'n_features_removed': len(removed_features),
                'n_features_selected': len(selected_features)
            }
            
            # Save analysis
            analysis = Analysis(
                dataset_id=dataset_id,
                analysis_type='variance_threshold',
                parameters={'threshold': threshold},
                results=results,
                status='completed'
            )
            db.session.add(analysis)
            db.session.commit()
            
            return {'success': True, 'results': results}
            
        except Exception as e:
            current_app.logger.error(f"Variance threshold error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def mutual_info_analysis(self, dataset_id, target_column):
        try:
            dataset = Dataset.query.get_or_404(dataset_id)
            df = self.data_processor.load_dataset(dataset)
            
            if target_column not in df.columns:
                return {'success': False, 'error': f'Target column {target_column} not found'}
            
            # Prepare features and target
            feature_columns = [col for col in df.columns if col != target_column]
            numeric_features = df[feature_columns].select_dtypes(include=[np.number]).columns.tolist()
            
            X = df[numeric_features].fillna(df[numeric_features].mean())
            y = df[target_column]
            
            # Handle missing values in target
            mask = ~y.isna()
            X = X[mask]
            y = y[mask]
            
            # Calculate mutual information
            if pd.api.types.is_numeric_dtype(y):
                mi_scores = mutual_info_regression(X, y, random_state=self.random_state)
            else:
                mi_scores = mutual_info_classif(X, y, random_state=self.random_state)
            
            # Create mutual information dataframe
            mi_data = list(zip(numeric_features, mi_scores))
            mi_data.sort(key=lambda x: x[1], reverse=True)
            
            results = {
                'mutual_info_scores': [{'feature': feature, 'score': float(score)} for feature, score in mi_data],
                'target_column': target_column,
                'top_features': [item[0] for item in mi_data[:10]],
                'low_info_features': [item[0] for item in mi_data if item[1] < 0.01]
            }
            
            # Save analysis
            analysis = Analysis(
                dataset_id=dataset_id,
                analysis_type='mutual_info',
                parameters={'target_column': target_column},
                results=results,
                status='completed'
            )
            db.session.add(analysis)
            db.session.commit()
            
            return {'success': True, 'results': results}
            
        except Exception as e:
            current_app.logger.error(f"Mutual information analysis error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def autoencoder_features(self, dataset_id, encoding_dim=32, epochs=100):
        try:
            # This would require TensorFlow/Keras
            # For now, return a placeholder implementation
            return {
                'success': False,
                'error': 'Autoencoder feature engineering requires TensorFlow/Keras installation'
            }
            
        except Exception as e:
            current_app.logger.error(f"Autoencoder features error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def time_series_features(self, dataset_id, column, features):
        try:
            dataset = Dataset.query.get_or_404(dataset_id)
            df = self.data_processor.load_dataset(dataset)
            
            if column not in df.columns:
                return {'success': False, 'error': f'Column {column} not found'}
            
            # Try to convert to datetime if not already
            try:
                df[column] = pd.to_datetime(df[column])
            except:
                return {'success': False, 'error': f'Column {column} cannot be converted to datetime'}
            
            new_features = {}
            feature_names = []
            
            for feature_type in features:
                if feature_type == 'hour':
                    new_col = f'{column}_hour'
                    new_features[new_col] = df[column].dt.hour
                    feature_names.append(new_col)
                elif feature_type == 'day':
                    new_col = f'{column}_day'
                    new_features[new_col] = df[column].dt.day
                    feature_names.append(new_col)
                elif feature_type == 'month':
                    new_col = f'{column}_month'
                    new_features[new_col] = df[column].dt.month
                    feature_names.append(new_col)
                elif feature_type == 'year':
                    new_col = f'{column}_year'
                    new_features[new_col] = df[column].dt.year
                    feature_names.append(new_col)
                elif feature_type == 'weekday':
                    new_col = f'{column}_weekday'
                    new_features[new_col] = df[column].dt.dayofweek
                    feature_names.append(new_col)
                elif feature_type == 'quarter':
                    new_col = f'{column}_quarter'
                    new_features[new_col] = df[column].dt.quarter
                    feature_names.append(new_col)
                elif feature_type == 'week':
                    new_col = f'{column}_week'
                    new_features[new_col] = df[column].dt.isocalendar().week
                    feature_names.append(new_col)
                elif feature_type == 'is_weekend':
                    new_col = f'{column}_is_weekend'
                    new_features[new_col] = (df[column].dt.dayofweek >= 5).astype(int)
                    feature_names.append(new_col)
                elif feature_type == 'is_month_start':
                    new_col = f'{column}_is_month_start'
                    new_features[new_col] = df[column].dt.is_month_start.astype(int)
                    feature_names.append(new_col)
                elif feature_type == 'is_month_end':
                    new_col = f'{column}_is_month_end'
                    new_features[new_col] = df[column].dt.is_month_end.astype(int)
                    feature_names.append(new_col)
            
            if not new_features:
                return {'success': False, 'error': 'No valid time features selected'}
            
            # Convert to regular Python types for JSON serialization
            for key, series in new_features.items():
                new_features[key] = series.astype(float).tolist()
            
            results = {
                'new_features': new_features,
                'feature_names': feature_names,
                'source_column': column,
                'features_extracted': len(feature_names),
                'feature_types': features
            }
            
            # Save analysis
            analysis = Analysis(
                dataset_id=dataset_id,
                analysis_type='time_series_features',
                parameters={'column': column, 'features': features},
                results=results,
                status='completed'
            )
            db.session.add(analysis)
            db.session.commit()
            
            return {'success': True, 'results': results}
            
        except Exception as e:
            current_app.logger.error(f"Time series features error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def text_features(self, dataset_id, column, features):
        try:
            dataset = Dataset.query.get_or_404(dataset_id)
            df = self.data_processor.load_dataset(dataset)
            
            if column not in df.columns:
                return {'success': False, 'error': f'Column {column} not found'}
            
            # Ensure column is string type
            text_series = df[column].astype(str)
            
            new_features = {}
            feature_names = []
            
            for feature_type in features:
                if feature_type == 'length':
                    new_col = f'{column}_length'
                    new_features[new_col] = text_series.str.len()
                    feature_names.append(new_col)
                elif feature_type == 'word_count':
                    new_col = f'{column}_word_count'
                    new_features[new_col] = text_series.str.split().str.len()
                    feature_names.append(new_col)
                elif feature_type == 'char_count':
                    new_col = f'{column}_char_count'
                    new_features[new_col] = text_series.str.len()
                    feature_names.append(new_col)
                elif feature_type == 'digit_count':
                    new_col = f'{column}_digit_count'
                    new_features[new_col] = text_series.str.count(r'\d')
                    feature_names.append(new_col)
                elif feature_type == 'upper_count':
                    new_col = f'{column}_upper_count'
                    new_features[new_col] = text_series.str.count(r'[A-Z]')
                    feature_names.append(new_col)
                elif feature_type == 'lower_count':
                    new_col = f'{column}_lower_count'
                    new_features[new_col] = text_series.str.count(r'[a-z]')
                    feature_names.append(new_col)
                elif feature_type == 'space_count':
                    new_col = f'{column}_space_count'
                    new_features[new_col] = text_series.str.count(' ')
                    feature_names.append(new_col)
                elif feature_type == 'special_char_count':
                    new_col = f'{column}_special_char_count'
                    new_features[new_col] = text_series.str.count(r'[^\w\s]')
                    feature_names.append(new_col)
                elif feature_type == 'avg_word_length':
                    new_col = f'{column}_avg_word_length'
                    word_lengths = text_series.str.split().apply(lambda x: np.mean([len(word) for word in x]) if x else 0)
                    new_features[new_col] = word_lengths
                    feature_names.append(new_col)
                elif feature_type == 'sentence_count':
                    new_col = f'{column}_sentence_count'
                    new_features[new_col] = text_series.str.count(r'[.!?]+')
                    feature_names.append(new_col)
                elif feature_type == 'unique_words':
                    new_col = f'{column}_unique_words'
                    unique_word_counts = text_series.str.split().apply(lambda x: len(set(x)) if x else 0)
                    new_features[new_col] = unique_word_counts
                    feature_names.append(new_col)
                elif feature_type == 'readability':
                    # Simple readability score based on average sentence and word length
                    new_col = f'{column}_readability'
                    avg_sentence_length = text_series.str.split('.').str.len()
                    avg_word_length = text_series.str.split().apply(lambda x: np.mean([len(word) for word in x]) if x else 0)
                    readability = 206.835 - (1.015 * avg_sentence_length) - (84.6 * avg_word_length)
                    new_features[new_col] = readability.fillna(0)
                    feature_names.append(new_col)
            
            if not new_features:
                return {'success': False, 'error': 'No valid text features selected'}
            
            # Convert to regular Python types for JSON serialization
            for key, series in new_features.items():
                new_features[key] = series.fillna(0).astype(float).tolist()
            
            results = {
                'new_features': new_features,
                'feature_names': feature_names,
                'source_column': column,
                'features_extracted': len(feature_names),
                'feature_types': features
            }
            
            # Save analysis
            analysis = Analysis(
                dataset_id=dataset_id,
                analysis_type='text_features',
                parameters={'column': column, 'features': features},
                results=results,
                status='completed'
            )
            db.session.add(analysis)
            db.session.commit()
            
            return {'success': True, 'results': results}
            
        except Exception as e:
            current_app.logger.error(f"Text features error: {str(e)}")
            return {'success': False, 'error': str(e)}
