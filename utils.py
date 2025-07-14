import json
import numpy as np
import pandas as pd
from datetime import datetime, date
from decimal import Decimal

class SafeJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles NaN, None, and other special values"""
    
    def default(self, obj):
        if pd.isna(obj) or obj is None:
            return None
        elif isinstance(obj, np.floating):
            if np.isnan(obj) or np.isinf(obj):
                return None
            return float(obj)
        elif isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, (datetime, date)):
            return obj.isoformat()
        elif isinstance(obj, Decimal):
            return float(obj)
        elif hasattr(obj, 'tolist'):  # pandas Series
            return obj.tolist()
        return super().default(obj)

def safe_json_response(data):
    """Convert data to JSON-safe format"""
    if isinstance(data, dict):
        return {k: safe_json_response(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [safe_json_response(item) for item in data]
    elif isinstance(data, pd.DataFrame):
        return data.fillna('').to_dict('records')
    elif isinstance(data, pd.Series):
        return data.fillna('').to_dict()
    elif pd.isna(data) or data is None:
        return None
    elif isinstance(data, (np.floating, float)):
        return None if (np.isnan(data) or np.isinf(data)) else float(data)
    elif isinstance(data, (np.integer, int)):
        return int(data)
    elif isinstance(data, np.ndarray):
        return np.nan_to_num(data, nan=0.0, posinf=0.0, neginf=0.0).tolist()
    elif isinstance(data, (datetime, date)):
        return data.isoformat()
    elif isinstance(data, Decimal):
        return float(data)
    return data

def dataframe_to_dict(df, orient='records'):
    """Convert DataFrame to dictionary with safe JSON serialization"""
    if df is None or df.empty:
        return {}
    
    # Replace NaN with None, infinity with None
    df_clean = df.replace([np.inf, -np.inf], np.nan).fillna('')
    
    if orient == 'records':
        return df_clean.to_dict('records')
    elif orient == 'dict':
        return df_clean.to_dict()
    elif orient == 'list':
        return df_clean.to_dict('list')
    else:
        return df_clean.to_dict(orient)

def get_safe_stats(df, columns=None):
    """Get basic statistics for columns with safe JSON serialization"""
    if df is None or df.empty:
        return {}
    
    if columns is None:
        columns = df.columns.tolist()
    
    stats = {}
    for col in columns:
        if col not in df.columns:
            continue
            
        col_stats = {}
        try:
            if pd.api.types.is_numeric_dtype(df[col]):
                col_stats.update({
                    'count': int(df[col].count()),
                    'mean': safe_json_response(df[col].mean()),
                    'std': safe_json_response(df[col].std()),
                    'min': safe_json_response(df[col].min()),
                    'max': safe_json_response(df[col].max()),
                    'median': safe_json_response(df[col].median()),
                    'q25': safe_json_response(df[col].quantile(0.25)),
                    'q75': safe_json_response(df[col].quantile(0.75)),
                    'null_count': int(df[col].isnull().sum()),
                    'data_type': 'numeric'
                })
            else:
                col_stats.update({
                    'count': int(df[col].count()),
                    'unique': int(df[col].nunique()),
                    'null_count': int(df[col].isnull().sum()),
                    'most_frequent': str(df[col].mode().iloc[0]) if not df[col].mode().empty else '',
                    'data_type': 'categorical'
                })
        except Exception as e:
            col_stats = {
                'error': str(e),
                'count': int(df[col].count()) if col in df.columns else 0,
                'data_type': 'unknown'
            }
        
        stats[col] = col_stats
    
    return stats

def create_response(success=True, message='', data=None, error=None, **kwargs):
    """Create standardized API response"""
    response = {
        'success': success,
        'message': message
    }
    
    if data is not None:
        response['data'] = safe_json_response(data)
    
    if error:
        response['error'] = str(error)
        response['success'] = False
    
    # Add any additional fields
    for key, value in kwargs.items():
        response[key] = safe_json_response(value)
    
    return response

def validate_columns(df, columns, required=True):
    """Validate that columns exist in DataFrame"""
    if not columns and required:
        return False, "Columns parameter is required"
    
    if not columns:
        return True, ""
    
    missing_cols = [col for col in columns if col not in df.columns]
    if missing_cols:
        return False, f"Invalid columns: {missing_cols}"
    
    return True, ""

def safe_divide(a, b, default=0):
    """Safe division that handles division by zero"""
    try:
        if b == 0 or pd.isna(b) or pd.isna(a):
            return default
        result = a / b
        return default if (np.isnan(result) or np.isinf(result)) else result
    except:
        return default