import pandas as pd
import numpy as np
import os
import json
import logging
from datetime import datetime
from werkzeug.utils import secure_filename
from models import Dataset, db
from flask import current_app
import pyarrow.parquet as pq
import openpyxl
from utils import safe_json_response


class DataProcessor:
    def __init__(self):
        self.allowed_extensions = {'csv', 'xlsx', 'json', 'parquet'}
        self.upload_folder = 'uploads'
        self.ensure_upload_folder()
    
    def ensure_upload_folder(self):
        if not os.path.exists(self.upload_folder):
            os.makedirs(self.upload_folder)
    
    def allowed_file(self, filename):
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in self.allowed_extensions
    
    def process_upload(self, file):
        try:
            if not file or not self.allowed_file(file.filename):
                return {'success': False, 'error': 'Invalid file type'}
            
            filename = secure_filename(file.filename)
            file_path = os.path.join(self.upload_folder, filename)
            
            # Note: File is already saved by the route, so we just parse it
            # Parse the file
            df = self.parse_file(file_path, filename)
            if df is None:
                return {'success': False, 'error': 'Failed to parse file'}
            
            # Get data info that matches the model structure
            column_info = self.get_column_info(df)
            data_types = df.dtypes.astype(str).to_dict()
            missing_values = df.isnull().sum().to_dict()
            
            return safe_json_response({
                'success': True,
                'file_type': filename.rsplit('.', 1)[1].lower(),
                'rows': len(df),
                'columns': len(df.columns),
                'column_names': df.columns.tolist(),
                'data_types': data_types,
                'missing_values': missing_values,
                'preview': self.get_preview_data(df),
                'info': {
                    'filename': file.filename,
                    'rows': len(df),
                    'columns': len(df.columns),
                    'file_size': os.path.getsize(file_path) if os.path.exists(file_path) else 0,
                    'missing_values': missing_values,
                    'data_types': data_types,
                    'column_names': df.columns.tolist()
                }
            })
            
        except Exception as e:
            logging.error(f"Upload processing error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def parse_file(self, file_path, filename):
        try:
            file_ext = filename.rsplit('.', 1)[1].lower()
            
            if file_ext == 'csv':
                return pd.read_csv(file_path, encoding='utf-8')
            elif file_ext == 'xlsx':
                return pd.read_excel(file_path)
            elif file_ext == 'json':
                return pd.read_json(file_path)
            elif file_ext == 'parquet':
                return pd.read_parquet(file_path)
            else:
                return None
                
        except Exception as e:
            logging.error(f"File parsing error: {str(e)}")
            return None
    
    def get_column_info(self, df):
        column_info = {}
        for col in df.columns:
            column_info[col] = {
                'dtype': str(df[col].dtype),
                'non_null_count': int(df[col].count()),
                'null_count': int(df[col].isnull().sum()),
                'unique_count': int(df[col].nunique()),
                'memory_usage': int(df[col].memory_usage(deep=True))
            }
        return safe_json_response(column_info)
    
    def get_preview_data(self, df):
        return safe_json_response({
            'head': df.head(10).to_dict('records'),
            'tail': df.tail(10).to_dict('records'),
            'columns': df.columns.tolist(),
            'shape': df.shape,
            'dtypes': df.dtypes.astype(str).to_dict()
        })
    
    def get_preview(self, file_path):
        try:
            # Use file_path directly instead of dataset_id
            filename = os.path.basename(file_path)
            df = self.parse_file(file_path, filename)
            if df is None:
                return {'success': False, 'error': 'Failed to load dataset'}
            return {
                'success': True,
                'preview': self.get_preview_data(df)
            }
        except Exception as e:
            logging.error(f"Preview error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def get_dataset_info(self, file_path):
        try:
            filename = os.path.basename(file_path)
            df = self.parse_file(file_path, filename)
            if df is None:
                return {'success': False, 'error': 'Failed to load dataset'}
            return safe_json_response({
                'success': True,
                'info': {
                    'filename': filename,
                    'rows': len(df),
                    'columns': len(df.columns),
                    'file_size': os.path.getsize(file_path),
                    'missing_values': df.isnull().sum().to_dict(),
                    'data_types': df.dtypes.astype(str).to_dict(),
                    'column_names': df.columns.tolist()
                }
            })
        except Exception as e:
            logging.error(f"Dataset info error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def get_columns_info(self, file_path):
        try:
            filename = os.path.basename(file_path)
            df = self.parse_file(file_path, filename)
            if df is None:
                return {'success': False, 'error': 'Failed to load dataset'}
            
            columns_info = []
            for col in df.columns:
                col_info = {
                    'name': col,
                    'dtype': str(df[col].dtype),
                    'non_null_count': int(df[col].count()),
                    'null_count': int(df[col].isnull().sum()),
                    'unique_count': int(df[col].nunique()),
                    'is_numeric': pd.api.types.is_numeric_dtype(df[col]),
                    'is_categorical': pd.api.types.is_categorical_dtype(df[col]) or df[col].dtype == 'object',
                    'is_datetime': pd.api.types.is_datetime64_any_dtype(df[col])
                }
                columns_info.append(col_info)
            
            return safe_json_response({
                'success': True,
                'columns': columns_info
            })
        except Exception as e:
            logging.error(f"Columns error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def get_sample_data(self, file_path):
        try:
            filename = os.path.basename(file_path)
            df = self.parse_file(file_path, filename)
            if df is None:
                return {'success': False, 'error': 'Failed to load dataset'}
            
            sample_size = min(100, len(df))
            sample_df = df.sample(n=sample_size)
            
            return safe_json_response({
                'success': True,
                'sample': sample_df.to_dict('records'),
                'columns': df.columns.tolist(),
                'sample_size': sample_size,
                'total_rows': len(df)
            })
        except Exception as e:
            logging.error(f"Sample data error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def clean_data(self, file_path, options):
        try:
            filename = os.path.basename(file_path)
            df = self.parse_file(file_path, filename)
            if df is None:
                return {'success': False, 'error': 'Failed to load dataset'}
            
            stats = {'original_shape': df.shape}
            
            # Handle missing values
            if options.get('handle_missing'):
                method = options.get('missing_method', 'drop')
                if method == 'drop':
                    df = df.dropna()
                elif method == 'fill_mean':
                    numeric_cols = df.select_dtypes(include=[np.number]).columns
                    df[numeric_cols] = df[numeric_cols].fillna(df[numeric_cols].mean())
                elif method == 'fill_median':
                    numeric_cols = df.select_dtypes(include=[np.number]).columns
                    df[numeric_cols] = df[numeric_cols].fillna(df[numeric_cols].median())
                elif method == 'fill_mode':
                    for col in df.columns:
                        df[col] = df[col].fillna(df[col].mode()[0] if not df[col].mode().empty else 0)
            
            # Handle duplicates
            if options.get('remove_duplicates'):
                df = df.drop_duplicates()
            
            # Handle outliers
            if options.get('handle_outliers'):
                method = options.get('outlier_method', 'iqr')
                if method == 'iqr':
                    numeric_cols = df.select_dtypes(include=[np.number]).columns
                    for col in numeric_cols:
                        Q1 = df[col].quantile(0.25)
                        Q3 = df[col].quantile(0.75)
                        IQR = Q3 - Q1
                        lower_bound = Q1 - 1.5 * IQR
                        upper_bound = Q3 + 1.5 * IQR
                        df = df[(df[col] >= lower_bound) & (df[col] <= upper_bound)]
            
            stats['cleaned_shape'] = df.shape
            stats['rows_removed'] = stats['original_shape'][0] - stats['cleaned_shape'][0]
            
            # Save cleaned data (overwrites original for simplicity)
            if file_path.endswith('.csv'):
                df.to_csv(file_path, index=False)
            elif file_path.endswith('.xlsx'):
                df.to_excel(file_path, index=False)
            elif file_path.endswith('.json'):
                df.to_json(file_path, orient='records')
            elif file_path.endswith('.parquet'):
                df.to_parquet(file_path, index=False)
            
            return safe_json_response({
                'success': True,
                'stats': stats
            })
            
        except Exception as e:
            logging.error(f"Data cleaning error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def load_dataset(self, dataset):
        """Load dataset from file path and return pandas DataFrame"""
        try:
            if hasattr(dataset, 'file_path'):
                file_path = dataset.file_path
            else:
                file_path = dataset
                
            filename = os.path.basename(file_path)
            df = self.parse_file(file_path, filename)
            if df is None:
                raise Exception('Failed to parse dataset file')
            return df
        except Exception as e:
            logging.error(f"Load dataset error: {str(e)}")
            raise e
    
    def get_column_information(self, file_path):
        """Get column information for a dataset - wrapper for get_columns_info"""
        return self.get_columns_info(file_path)
