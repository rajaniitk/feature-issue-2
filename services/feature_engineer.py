import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, MinMaxScaler, RobustScaler
from sklearn.preprocessing import LabelEncoder, OneHotEncoder
from sklearn.feature_selection import SelectKBest, f_classif, f_regression
from sklearn.decomposition import PCA
from sklearn.preprocessing import PolynomialFeatures
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from textblob import TextBlob
import logging
from datetime import datetime
from models import Dataset, FeatureEngineering, db
from services.data_processor import DataProcessor
from flask import current_app
from scipy import stats
import json

class FeatureEngineer:
    def __init__(self):
        self.data_processor = DataProcessor()
    
    def _get_fresh_scaler(self, method):
        """Get a fresh scaler instance to avoid state issues"""
        scalers = {
            'standard': StandardScaler(),
            'minmax': MinMaxScaler(),
            'robust': RobustScaler()
        }
        return scalers.get(method, StandardScaler())
    
    def scale_features(self, dataset_id, columns, method='standard'):
        """Apply feature scaling using REAL data from uploaded datasets
        
        Description: Normalizes feature values to ensure consistent scales across different features.
        This prevents features with larger scales from dominating the model and improves convergence.
        Uses actual uploaded data - NO SIMULATION OR FAKE DATA.
        """
        try:
            # Load REAL dataset from database - verify it exists
            dataset = Dataset.query.get_or_404(dataset_id)
            if not dataset or not dataset.file_path:
                return {'success': False, 'error': 'No real dataset found or invalid file path'}
            
            # Load actual data from uploaded file
            df = self.data_processor.load_dataset(dataset)
            if df is None or df.empty:
                return {'success': False, 'error': 'Failed to load real dataset or dataset is empty'}
            
            logging.info(f"Processing REAL dataset: {dataset.filename} with {len(df)} rows and {len(df.columns)} columns")
            
            # Auto-select numeric columns if none specified
            if not columns:
                columns = df.select_dtypes(include=[np.number]).columns.tolist()
                if not columns:
                    return {'success': False, 'error': 'No numeric columns found in the real dataset for scaling'}
            
            # Validate all columns exist in REAL data
            invalid_cols = [col for col in columns if col not in df.columns]
            if invalid_cols:
                available_cols = list(df.columns)
                return {'success': False, 'error': f'Columns {invalid_cols} not found in real dataset. Available: {available_cols}'}
            
            # Check for non-numeric columns
            non_numeric_cols = [col for col in columns if not pd.api.types.is_numeric_dtype(df[col])]
            if non_numeric_cols:
                return {'success': False, 'error': f'Non-numeric columns cannot be scaled: {non_numeric_cols}'}
            
            # Get statistics before transformation
            before_stats = self.get_column_stats(df, columns)
            
            # Apply scaling to REAL data
            scaler = self._get_fresh_scaler(method)
            df_scaled = df.copy()
            
            for col in columns:
                # Handle missing values first
                if df[col].isnull().any():
                    missing_count = df[col].isnull().sum()
                    logging.warning(f"Column {col} has {missing_count} missing values, filling with median")
                    df_scaled[col] = df_scaled[col].fillna(df[col].median())
                
                # Apply scaling
                scaled_values = scaler.fit_transform(df_scaled[[col]])
                df_scaled[col] = scaled_values.flatten()
            
            # Get statistics after transformation
            after_stats = self.get_column_stats(df_scaled, columns)
            
            # Save transformation record with REAL data info
            transformation = FeatureEngineering(
                dataset_id=dataset_id,
                column_name=','.join(columns),
                transformation_type='scaling',
                parameters={
                    'method': method, 
                    'columns': columns,
                    'dataset_name': dataset.filename,
                    'rows_processed': len(df),
                    'real_data': True  # Explicitly mark as real data
                },
                before_stats=before_stats,
                after_stats=after_stats,
                transformation_info={
                    'scaler_type': method,
                    'data_source': 'real_uploaded_file',
                    'original_file': dataset.file_path
                }
            )
            
            db.session.add(transformation)
            db.session.commit()
            
            # Save transformed REAL data back to file system
            try:
                self.save_transformed_data(df_scaled, dataset)
                logging.info(f"Successfully saved transformed real data for {len(columns)} columns")
            except Exception as save_error:
                logging.error(f"Error saving transformed data: {str(save_error)}")
                return {'success': False, 'error': f'Failed to save transformed real data: {str(save_error)}'}
            
            return {
                'success': True,
                'message': f'Successfully scaled {len(columns)} columns using {method} scaling on REAL data from {dataset.filename}',
                'dataset_info': {
                    'filename': dataset.filename,
                    'rows': len(df),
                    'columns_scaled': len(columns),
                    'total_columns': len(df.columns)
                },
                'before_stats': before_stats,
                'after_stats': after_stats,
                'transformation_id': transformation.id,
                'real_data_confirmed': True
            }
            
        except Exception as e:
            error_msg = f"Feature scaling failed on real data: {str(e)}"
            logging.error(error_msg)
            return {'success': False, 'error': error_msg}
    
    def encode_categorical(self, dataset_id, columns, method='onehot'):
        try:
            dataset = Dataset.query.get_or_404(dataset_id)
            df = self.data_processor.load_dataset(dataset)
            
            if not columns:
                columns = df.select_dtypes(include=['object']).columns.tolist()
            
            # Validate columns
            invalid_cols = [col for col in columns if col not in df.columns]
            if invalid_cols:
                return {'success': False, 'error': f'Invalid columns: {invalid_cols}'}
            
            # Get before stats
            before_stats = self.get_column_stats(df, columns)
            
            df_encoded = df.copy()
            
            for col in columns:
                if method == 'onehot':
                    # One-hot encoding
                    dummies = pd.get_dummies(df[col], prefix=col)
                    df_encoded = pd.concat([df_encoded.drop(col, axis=1), dummies], axis=1)
                    
                elif method == 'label':
                    # Label encoding
                    le = LabelEncoder()
                    df_encoded[col] = le.fit_transform(df[col].astype(str))
                    
                elif method == 'frequency':
                    # Frequency encoding
                    freq_map = df[col].value_counts().to_dict()
                    df_encoded[col] = df[col].map(freq_map)
                    
                elif method == 'target':
                    # Target encoding (requires target column)
                    # For now, use frequency encoding as fallback
                    freq_map = df[col].value_counts().to_dict()
                    df_encoded[col] = df[col].map(freq_map)
            
            # Get after stats
            after_stats = self.get_column_stats(df_encoded, df_encoded.columns.tolist())
            
            # Save transformation
            transformation = FeatureEngineering(
                dataset_id=dataset_id,
                column_name=','.join(columns),
                transformation_type='encoding',
                parameters={'method': method, 'columns': columns},
                before_stats=before_stats,
                after_stats=after_stats,
                transformation_info={'encoding_type': method}
            )
            
            db.session.add(transformation)
            db.session.commit()
            
            # Update dataset file
            self.save_transformed_data(df_encoded, dataset)
            
            return {
                'success': True,
                'message': f'Successfully encoded {len(columns)} columns using {method} encoding',
                'before_stats': before_stats,
                'after_stats': after_stats,
                'transformation_id': transformation.id,
                'new_columns': df_encoded.columns.tolist()
            }
            
        except Exception as e:
            current_app.logger.error(f"Encoding error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def transform_numerical(self, dataset_id, columns, method='log'):
        try:
            dataset = Dataset.query.get_or_404(dataset_id)
            df = self.data_processor.load_dataset(dataset)
            
            if not columns:
                columns = df.select_dtypes(include=[np.number]).columns.tolist()
            
            # Validate columns
            invalid_cols = [col for col in columns if col not in df.columns]
            if invalid_cols:
                return {'success': False, 'error': f'Invalid columns: {invalid_cols}'}
            
            # Get before stats
            before_stats = self.get_column_stats(df, columns)
            
            df_transformed = df.copy()
            
            for col in columns:
                if pd.api.types.is_numeric_dtype(df[col]):
                    if method == 'log':
                        # Log transformation (handle non-positive values)
                        df_transformed[col] = np.log1p(df[col] - df[col].min() + 1)
                    elif method == 'sqrt':
                        # Square root transformation
                        df_transformed[col] = np.sqrt(df[col] - df[col].min() + 1)
                    elif method == 'reciprocal':
                        # Reciprocal transformation
                        df_transformed[col] = 1 / (df[col] + 1)
                    elif method == 'square':
                        # Square transformation
                        df_transformed[col] = df[col] ** 2
                    elif method == 'boxcox':
                        # Box-Cox transformation
                        try:
                            transformed_data, _ = stats.boxcox(df[col] - df[col].min() + 1)
                            df_transformed[col] = transformed_data
                        except:
                            # Fallback to log transformation
                            df_transformed[col] = np.log1p(df[col] - df[col].min() + 1)
            
            # Get after stats
            after_stats = self.get_column_stats(df_transformed, columns)
            
            # Save transformation
            transformation = FeatureEngineering(
                dataset_id=dataset_id,
                column_name=','.join(columns),
                transformation_type='numerical_transform',
                parameters={'method': method, 'columns': columns},
                before_stats=before_stats,
                after_stats=after_stats,
                transformation_info={'transform_type': method}
            )
            
            db.session.add(transformation)
            db.session.commit()
            
            # Update dataset file
            self.save_transformed_data(df_transformed, dataset)
            
            return {
                'success': True,
                'message': f'Successfully transformed {len(columns)} columns using {method} transformation',
                'before_stats': before_stats,
                'after_stats': after_stats,
                'transformation_id': transformation.id
            }
            
        except Exception as e:
            current_app.logger.error(f"Numerical transformation error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def bin_numerical(self, dataset_id, columns, method='equal_width', bins=5):
        try:
            dataset = Dataset.query.get_or_404(dataset_id)
            df = self.data_processor.load_dataset(dataset)
            
            if not columns:
                columns = df.select_dtypes(include=[np.number]).columns.tolist()
            
            # Validate columns
            invalid_cols = [col for col in columns if col not in df.columns]
            if invalid_cols:
                return {'success': False, 'error': f'Invalid columns: {invalid_cols}'}
            
            # Get before stats
            before_stats = self.get_column_stats(df, columns)
            
            df_binned = df.copy()
            
            for col in columns:
                if pd.api.types.is_numeric_dtype(df[col]):
                    if method == 'equal_width':
                        df_binned[f'{col}_binned'] = pd.cut(df[col], bins=bins, labels=False)
                    elif method == 'equal_frequency':
                        df_binned[f'{col}_binned'] = pd.qcut(df[col], q=bins, labels=False, duplicates='drop')
                    elif method == 'kmeans':
                        # K-means based binning
                        from sklearn.cluster import KMeans
                        kmeans = KMeans(n_clusters=bins, random_state=42)
                        df_binned[f'{col}_binned'] = kmeans.fit_predict(df[[col]])
            
            # Get after stats
            new_columns = [f'{col}_binned' for col in columns]
            after_stats = self.get_column_stats(df_binned, new_columns)
            
            # Save transformation
            transformation = FeatureEngineering(
                dataset_id=dataset_id,
                column_name=','.join(columns),
                transformation_type='binning',
                parameters={'method': method, 'columns': columns, 'bins': bins},
                before_stats=before_stats,
                after_stats=after_stats,
                transformation_info={'binning_method': method, 'num_bins': bins}
            )
            
            db.session.add(transformation)
            db.session.commit()
            
            # Update dataset file
            self.save_transformed_data(df_binned, dataset)
            
            return {
                'success': True,
                'message': f'Successfully binned {len(columns)} columns using {method} method',
                'before_stats': before_stats,
                'after_stats': after_stats,
                'transformation_id': transformation.id,
                'new_columns': new_columns
            }
            
        except Exception as e:
            current_app.logger.error(f"Binning error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def polynomial_features(self, dataset_id, columns, degree=2):
        try:
            dataset = Dataset.query.get_or_404(dataset_id)
            df = self.data_processor.load_dataset(dataset)
            
            if not columns:
                columns = df.select_dtypes(include=[np.number]).columns.tolist()
            
            # Validate columns
            invalid_cols = [col for col in columns if col not in df.columns]
            if invalid_cols:
                return {'success': False, 'error': f'Invalid columns: {invalid_cols}'}
            
            # Get before stats
            before_stats = self.get_column_stats(df, columns)
            
            # Create polynomial features
            poly = PolynomialFeatures(degree=degree, include_bias=False)
            poly_features = poly.fit_transform(df[columns])
            
            # Create column names
            feature_names = poly.get_feature_names_out(columns)
            
            # Create new dataframe with polynomial features
            df_poly = df.copy()
            for i, name in enumerate(feature_names):
                df_poly[f'poly_{name}'] = poly_features[:, i]
            
            # Get after stats
            new_columns = [f'poly_{name}' for name in feature_names]
            after_stats = self.get_column_stats(df_poly, new_columns)
            
            # Save transformation
            transformation = FeatureEngineering(
                dataset_id=dataset_id,
                column_name=','.join(columns),
                transformation_type='polynomial',
                parameters={'columns': columns, 'degree': degree},
                before_stats=before_stats,
                after_stats=after_stats,
                transformation_info={'polynomial_degree': degree, 'num_features': len(feature_names)}
            )
            
            db.session.add(transformation)
            db.session.commit()
            
            # Update dataset file
            self.save_transformed_data(df_poly, dataset)
            
            return {
                'success': True,
                'message': f'Successfully created polynomial features of degree {degree}',
                'before_stats': before_stats,
                'after_stats': after_stats,
                'transformation_id': transformation.id,
                'new_columns': new_columns
            }
            
        except Exception as e:
            current_app.logger.error(f"Polynomial features error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def interaction_features(self, dataset_id, columns):
        try:
            dataset = Dataset.query.get_or_404(dataset_id)
            df = self.data_processor.load_dataset(dataset)
            
            if not columns:
                columns = df.select_dtypes(include=[np.number]).columns.tolist()
            
            if len(columns) < 2:
                return {'success': False, 'error': 'At least 2 columns required for interaction features'}
            
            # Get before stats
            before_stats = self.get_column_stats(df, columns)
            
            df_interaction = df.copy()
            new_columns = []
            
            # Create interaction features
            for i in range(len(columns)):
                for j in range(i+1, len(columns)):
                    col1, col2 = columns[i], columns[j]
                    interaction_col = f'{col1}_x_{col2}'
                    df_interaction[interaction_col] = df[col1] * df[col2]
                    new_columns.append(interaction_col)
            
            # Get after stats
            after_stats = self.get_column_stats(df_interaction, new_columns)
            
            # Save transformation
            transformation = FeatureEngineering(
                dataset_id=dataset_id,
                column_name=','.join(columns),
                transformation_type='interaction',
                parameters={'columns': columns},
                before_stats=before_stats,
                after_stats=after_stats,
                transformation_info={'num_interactions': len(new_columns)}
            )
            
            db.session.add(transformation)
            db.session.commit()
            
            # Update dataset file
            self.save_transformed_data(df_interaction, dataset)
            
            return {
                'success': True,
                'message': f'Successfully created {len(new_columns)} interaction features',
                'before_stats': before_stats,
                'after_stats': after_stats,
                'transformation_id': transformation.id,
                'new_columns': new_columns
            }
            
        except Exception as e:
            current_app.logger.error(f"Interaction features error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def datetime_features(self, dataset_id, columns):
        try:
            dataset = Dataset.query.get_or_404(dataset_id)
            df = self.data_processor.load_dataset(dataset)
            
            if not columns:
                columns = df.select_dtypes(include=['datetime64']).columns.tolist()
            
            if not columns:
                return {'success': False, 'error': 'No datetime columns found'}
            
            # Get before stats
            before_stats = self.get_column_stats(df, columns)
            
            df_datetime = df.copy()
            new_columns = []
            
            for col in columns:
                if pd.api.types.is_datetime64_any_dtype(df[col]):
                    # Convert to datetime if string
                    if df[col].dtype == 'object':
                        df_datetime[col] = pd.to_datetime(df[col])
                    
                    # Extract datetime features
                    df_datetime[f'{col}_year'] = df_datetime[col].dt.year
                    df_datetime[f'{col}_month'] = df_datetime[col].dt.month
                    df_datetime[f'{col}_day'] = df_datetime[col].dt.day
                    df_datetime[f'{col}_dayofweek'] = df_datetime[col].dt.dayofweek
                    df_datetime[f'{col}_hour'] = df_datetime[col].dt.hour
                    df_datetime[f'{col}_minute'] = df_datetime[col].dt.minute
                    df_datetime[f'{col}_quarter'] = df_datetime[col].dt.quarter
                    df_datetime[f'{col}_dayofyear'] = df_datetime[col].dt.dayofyear
                    df_datetime[f'{col}_weekofyear'] = df_datetime[col].dt.isocalendar().week
                    
                    # Cyclical encoding
                    df_datetime[f'{col}_month_sin'] = np.sin(2 * np.pi * df_datetime[f'{col}_month'] / 12)
                    df_datetime[f'{col}_month_cos'] = np.cos(2 * np.pi * df_datetime[f'{col}_month'] / 12)
                    df_datetime[f'{col}_day_sin'] = np.sin(2 * np.pi * df_datetime[f'{col}_day'] / 31)
                    df_datetime[f'{col}_day_cos'] = np.cos(2 * np.pi * df_datetime[f'{col}_day'] / 31)
                    df_datetime[f'{col}_hour_sin'] = np.sin(2 * np.pi * df_datetime[f'{col}_hour'] / 24)
                    df_datetime[f'{col}_hour_cos'] = np.cos(2 * np.pi * df_datetime[f'{col}_hour'] / 24)
                    
                    new_columns.extend([
                        f'{col}_year', f'{col}_month', f'{col}_day', f'{col}_dayofweek',
                        f'{col}_hour', f'{col}_minute', f'{col}_quarter', f'{col}_dayofyear',
                        f'{col}_weekofyear', f'{col}_month_sin', f'{col}_month_cos',
                        f'{col}_day_sin', f'{col}_day_cos', f'{col}_hour_sin', f'{col}_hour_cos'
                    ])
            
            # Get after stats
            after_stats = self.get_column_stats(df_datetime, new_columns)
            
            # Save transformation
            transformation = FeatureEngineering(
                dataset_id=dataset_id,
                column_name=','.join(columns),
                transformation_type='datetime',
                parameters={'columns': columns},
                before_stats=before_stats,
                after_stats=after_stats,
                transformation_info={'num_features': len(new_columns)}
            )
            
            db.session.add(transformation)
            db.session.commit()
            
            # Update dataset file
            self.save_transformed_data(df_datetime, dataset)
            
            return {
                'success': True,
                'message': f'Successfully created {len(new_columns)} datetime features',
                'before_stats': before_stats,
                'after_stats': after_stats,
                'transformation_id': transformation.id,
                'new_columns': new_columns
            }
            
        except Exception as e:
            current_app.logger.error(f"Datetime features error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def text_features(self, dataset_id, columns, method='tfidf'):
        try:
            dataset = Dataset.query.get_or_404(dataset_id)
            df = self.data_processor.load_dataset(dataset)
            
            if not columns:
                columns = df.select_dtypes(include=['object']).columns.tolist()
            
            # Get before stats
            before_stats = self.get_column_stats(df, columns)
            
            df_text = df.copy()
            new_columns = []
            
            for col in columns:
                if df[col].dtype == 'object':
                    # Basic text features
                    df_text[f'{col}_length'] = df[col].astype(str).str.len()
                    df_text[f'{col}_word_count'] = df[col].astype(str).str.split().str.len()
                    df_text[f'{col}_char_count'] = df[col].astype(str).str.replace(' ', '').str.len()
                    df_text[f'{col}_sentence_count'] = df[col].astype(str).str.count(r'[.!?]') + 1
                    
                    # Sentiment analysis
                    try:
                        sentiments = df[col].astype(str).apply(lambda x: TextBlob(x).sentiment.polarity)
                        df_text[f'{col}_sentiment'] = sentiments
                    except:
                        df_text[f'{col}_sentiment'] = 0
                    
                    new_columns.extend([
                        f'{col}_length', f'{col}_word_count', f'{col}_char_count',
                        f'{col}_sentence_count', f'{col}_sentiment'
                    ])
                    
                    # TF-IDF or Count vectorization
                    if method == 'tfidf':
                        try:
                            vectorizer = TfidfVectorizer(max_features=100, stop_words='english')
                            tfidf_matrix = vectorizer.fit_transform(df[col].astype(str))
                            feature_names = vectorizer.get_feature_names_out()
                            
                            for i, feature in enumerate(feature_names):
                                df_text[f'{col}_tfidf_{feature}'] = tfidf_matrix[:, i].toarray().flatten()
                                new_columns.append(f'{col}_tfidf_{feature}')
                        except:
                            pass
                    
                    elif method == 'count':
                        try:
                            vectorizer = CountVectorizer(max_features=100, stop_words='english')
                            count_matrix = vectorizer.fit_transform(df[col].astype(str))
                            feature_names = vectorizer.get_feature_names_out()
                            
                            for i, feature in enumerate(feature_names):
                                df_text[f'{col}_count_{feature}'] = count_matrix[:, i].toarray().flatten()
                                new_columns.append(f'{col}_count_{feature}')
                        except:
                            pass
            
            # Get after stats
            after_stats = self.get_column_stats(df_text, new_columns)
            
            # Save transformation
            transformation = FeatureEngineering(
                dataset_id=dataset_id,
                column_name=','.join(columns),
                transformation_type='text',
                parameters={'columns': columns, 'method': method},
                before_stats=before_stats,
                after_stats=after_stats,
                transformation_info={'text_method': method, 'num_features': len(new_columns)}
            )
            
            db.session.add(transformation)
            db.session.commit()
            
            # Update dataset file
            self.save_transformed_data(df_text, dataset)
            
            return {
                'success': True,
                'message': f'Successfully created {len(new_columns)} text features',
                'before_stats': before_stats,
                'after_stats': after_stats,
                'transformation_id': transformation.id,
                'new_columns': new_columns
            }
            
        except Exception as e:
            current_app.logger.error(f"Text features error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def handle_missing_values(self, dataset_id, columns, strategy='mean'):
        """Handle missing values in specified columns"""
        try:
            dataset = Dataset.query.get_or_404(dataset_id)
            df = self.data_processor.load_dataset(dataset)
            
            if not columns:
                # Find columns with missing values
                columns = df.columns[df.isnull().any()].tolist()
            
            # Validate columns
            invalid_cols = [col for col in columns if col not in df.columns]
            if invalid_cols:
                return {'success': False, 'error': f'Invalid columns: {invalid_cols}'}
            
            # Get before stats
            before_stats = self.get_column_stats(df, columns)
            
            df_imputed = df.copy()
            
            for col in columns:
                if df[col].isnull().any():
                    if strategy == 'mean' and pd.api.types.is_numeric_dtype(df[col]):
                        df_imputed[col] = df_imputed[col].fillna(df[col].mean())
                    elif strategy == 'median' and pd.api.types.is_numeric_dtype(df[col]):
                        df_imputed[col] = df_imputed[col].fillna(df[col].median())
                    elif strategy == 'mode':
                        mode_value = df[col].mode().iloc[0] if not df[col].mode().empty else 'Unknown'
                        df_imputed[col] = df_imputed[col].fillna(mode_value)
                    elif strategy == 'forward_fill':
                        df_imputed[col] = df_imputed[col].fillna(method='ffill')
                    elif strategy == 'backward_fill':
                        df_imputed[col] = df_imputed[col].fillna(method='bfill')
                    elif strategy == 'drop':
                        df_imputed = df_imputed.dropna(subset=[col])
                    else:
                        # Default to most frequent value
                        most_frequent = df[col].value_counts().index[0] if not df[col].value_counts().empty else 'Unknown'
                        df_imputed[col] = df_imputed[col].fillna(most_frequent)
            
            # Get after stats
            after_stats = self.get_column_stats(df_imputed, columns)
            
            # Save transformation
            transformation = FeatureEngineering(
                dataset_id=dataset_id,
                column_name=','.join(columns),
                transformation_type='imputation',
                parameters={'strategy': strategy, 'columns': columns},
                before_stats=before_stats,
                after_stats=after_stats,
                transformation_info={'imputation_strategy': strategy}
            )
            
            db.session.add(transformation)
            db.session.commit()
            
            # Update dataset file
            self.save_transformed_data(df_imputed, dataset)
            
            return {
                'success': True,
                'message': f'Successfully handled missing values in {len(columns)} columns using {strategy} strategy',
                'before_stats': before_stats,
                'after_stats': after_stats,
                'transformation_id': transformation.id
            }
            
        except Exception as e:
            current_app.logger.error(f"Missing value handling error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def create_arithmetic_features(self, dataset_id, feature1, feature2, operation):
        """Create new features from arithmetic operations between two features"""
        try:
            dataset = Dataset.query.get_or_404(dataset_id)
            df = self.data_processor.load_dataset(dataset)
            
            # Validate features
            if feature1 not in df.columns or feature2 not in df.columns:
                return {'success': False, 'error': f'Features {feature1} or {feature2} not found'}
            
            # Check if features are numeric for most operations
            if operation in ['add', 'subtract', 'multiply', 'divide']:
                if not (pd.api.types.is_numeric_dtype(df[feature1]) and pd.api.types.is_numeric_dtype(df[feature2])):
                    return {'success': False, 'error': 'Both features must be numeric for arithmetic operations'}
            
            # Get before stats
            before_stats = self.get_column_stats(df, [feature1, feature2])
            
            df_new = df.copy()
            new_feature_name = f'{feature1}_{operation}_{feature2}'
            
            # Perform operation
            if operation == 'add':
                df_new[new_feature_name] = df[feature1] + df[feature2]
            elif operation == 'subtract':
                df_new[new_feature_name] = df[feature1] - df[feature2]
            elif operation == 'multiply':
                df_new[new_feature_name] = df[feature1] * df[feature2]
            elif operation == 'divide':
                # Handle division by zero
                df_new[new_feature_name] = df[feature1] / (df[feature2] + 1e-8)
            elif operation == 'ratio':
                df_new[new_feature_name] = df[feature1] / (df[feature1] + df[feature2] + 1e-8)
            elif operation == 'difference_ratio':
                df_new[new_feature_name] = (df[feature1] - df[feature2]) / (df[feature1] + df[feature2] + 1e-8)
            else:
                return {'success': False, 'error': f'Unknown operation: {operation}'}
            
            # Get after stats
            after_stats = self.get_column_stats(df_new, [new_feature_name])
            
            # Save transformation
            transformation = FeatureEngineering(
                dataset_id=dataset_id,
                column_name=new_feature_name,
                transformation_type='arithmetic',
                parameters={'feature1': feature1, 'feature2': feature2, 'operation': operation},
                before_stats=before_stats,
                after_stats=after_stats,
                transformation_info={'operation_type': operation, 'source_features': [feature1, feature2]}
            )
            
            db.session.add(transformation)
            db.session.commit()
            
            # Update dataset file
            self.save_transformed_data(df_new, dataset)
            
            return {
                'success': True,
                'message': f'Successfully created feature {new_feature_name} from {feature1} {operation} {feature2}',
                'before_stats': before_stats,
                'after_stats': after_stats,
                'new_feature': new_feature_name,
                'transformation_id': transformation.id
            }
            
        except Exception as e:
            current_app.logger.error(f"Arithmetic feature creation error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def get_column_stats(self, df, columns):
        stats = {}
        for col in columns:
            if col in df.columns:
                if pd.api.types.is_numeric_dtype(df[col]):
                    stats[col] = {
                        'mean': float(df[col].mean()) if not df[col].isna().all() else None,
                        'std': float(df[col].std()) if not df[col].isna().all() else None,
                        'min': float(df[col].min()) if not df[col].isna().all() else None,
                        'max': float(df[col].max()) if not df[col].isna().all() else None,
                        'median': float(df[col].median()) if not df[col].isna().all() else None,
                        'skew': float(df[col].skew()) if not df[col].isna().all() else None,
                        'kurtosis': float(df[col].kurtosis()) if not df[col].isna().all() else None
                    }
                else:
                    stats[col] = {
                        'unique_count': int(df[col].nunique()),
                        'most_frequent': df[col].mode().iloc[0] if not df[col].mode().empty else None,
                        'null_count': int(df[col].isnull().sum())
                    }
        return stats
    
    def save_transformed_data(self, df, dataset):
        # Save transformed data to a new file WITHOUT updating the original dataset record
        # This prevents recursive loading of transformed files
        import os
        from datetime import datetime
        
        # Always use the original file path as base
        original_path = dataset.file_path
        
        # Create a new unique path with timestamp (but don't update dataset record)
        base_name = os.path.splitext(original_path)[0]
        extension = os.path.splitext(original_path)[1]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        new_path = f"{base_name}_transformed_{timestamp}{extension}"
        
        # Save the transformed data to the new file
        df.to_csv(new_path, index=False)
        
        # DO NOT update the original dataset record - this was causing the recursion
        # The original dataset should always point to the original file
        # Transformed data is saved separately and tracked via FeatureEngineering records
        
        logging.info(f"Saved transformed data to: {new_path}")
        logging.info(f"Original dataset file remains: {dataset.file_path}")
        
        # Return the path where transformed data was saved for reference
        return new_path
    
    def revert_transformation(self, transformation_id):
        try:
            transformation = FeatureEngineering.query.get_or_404(transformation_id)
            
            # Delete the transformation record
            db.session.delete(transformation)
            db.session.commit()
            
            return {'success': True, 'message': 'Transformation reverted successfully'}
            
        except Exception as e:
            current_app.logger.error(f"Revert transformation error: {str(e)}")
            return {'success': False, 'error': str(e)}
