from datetime import datetime
from sqlalchemy import Text, JSON
from database import db

class Dataset(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_type = db.Column(db.String(50), nullable=False)
    file_size = db.Column(db.Integer, nullable=False)
    upload_timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Dataset metadata
    num_rows = db.Column(db.Integer)
    num_columns = db.Column(db.Integer)
    column_names = db.Column(JSON)
    column_types = db.Column(JSON)
    missing_values = db.Column(JSON)
    
    # Relationships
    analyses = db.relationship('Analysis', backref='dataset', lazy=True, cascade='all, delete-orphan')
    features = db.relationship('Feature', backref='dataset', lazy=True, cascade='all, delete-orphan')
    models = db.relationship('MLModel', backref='dataset', lazy=True, cascade='all, delete-orphan')

class Analysis(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    dataset_id = db.Column(db.Integer, db.ForeignKey('dataset.id'), nullable=False)
    analysis_type = db.Column(db.String(100), nullable=False)  # 'eda', 'statistical_test', 'visualization'
    analysis_name = db.Column(db.String(200), nullable=False)
    parameters = db.Column(JSON)
    results = db.Column(JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    visualizations = db.relationship('Visualization', backref='analysis', lazy=True, cascade='all, delete-orphan')

class Feature(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    dataset_id = db.Column(db.Integer, db.ForeignKey('dataset.id'), nullable=False)
    feature_name = db.Column(db.String(200), nullable=False)
    original_name = db.Column(db.String(200))
    feature_type = db.Column(db.String(50), nullable=False)  # 'numerical', 'categorical', 'datetime', 'text'
    transformation_type = db.Column(db.String(100))  # 'scaling', 'encoding', 'binning', etc.
    transformation_params = db.Column(JSON)
    is_target = db.Column(db.Boolean, default=False)
    is_selected = db.Column(db.Boolean, default=True)
    importance_score = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Visualization(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    analysis_id = db.Column(db.Integer, db.ForeignKey('analysis.id'), nullable=False)
    viz_type = db.Column(db.String(100), nullable=False)  # 'histogram', 'boxplot', 'scatter', etc.
    title = db.Column(db.String(300), nullable=False)
    data = db.Column(JSON)  # Plotly JSON data
    layout = db.Column(JSON)  # Plotly layout
    config = db.Column(JSON)  # Plotly config
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class MLModel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    dataset_id = db.Column(db.Integer, db.ForeignKey('dataset.id'), nullable=False)
    model_name = db.Column(db.String(200), nullable=False)
    model_type = db.Column(db.String(100), nullable=False)  # 'classification', 'regression', 'clustering'
    algorithm = db.Column(db.String(100), nullable=False)
    hyperparameters = db.Column(JSON)
    training_score = db.Column(db.Float)
    validation_score = db.Column(db.Float)
    test_score = db.Column(db.Float)
    feature_importance = db.Column(JSON)
    model_metrics = db.Column(JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Report(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    dataset_id = db.Column(db.Integer, db.ForeignKey('dataset.id'), nullable=False)
    report_type = db.Column(db.String(100), nullable=False)  # 'eda', 'full_analysis', 'custom'
    title = db.Column(db.String(300), nullable=False)
    content = db.Column(Text)
    file_path = db.Column(db.String(500))
    format = db.Column(db.String(50))  # 'html', 'pdf'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Insight(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    dataset_id = db.Column(db.Integer, db.ForeignKey('dataset.id'), nullable=False)
    insight_type = db.Column(db.String(100), nullable=False)  # 'correlation', 'outlier', 'missing_data', etc.
    title = db.Column(db.String(300), nullable=False)
    description = db.Column(Text, nullable=False)
    severity = db.Column(db.String(50))  # 'low', 'medium', 'high', 'critical'
    recommendations = db.Column(JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class FeatureEngineering(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    dataset_id = db.Column(db.Integer, db.ForeignKey('dataset.id'), nullable=False)
    column_name = db.Column(db.String(500), nullable=False)  # Can be multiple columns
    transformation_type = db.Column(db.String(100), nullable=False)  # 'scaling', 'encoding', 'binning', etc.
    parameters = db.Column(JSON)
    before_stats = db.Column(JSON)
    after_stats = db.Column(JSON)
    transformation_info = db.Column(JSON)
    is_applied = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class ComparisonResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    dataset_id = db.Column(db.Integer, db.ForeignKey('dataset.id'), nullable=False)
    column1 = db.Column(db.String(200), nullable=False)
    column2 = db.Column(db.String(200), nullable=False)
    comparison_type = db.Column(db.String(100), nullable=False)  # 'correlation', 'anova', 'chi_square', etc.
    test_statistic = db.Column(db.Float)
    p_value = db.Column(db.Float)
    effect_size = db.Column(db.Float)
    interpretation = db.Column(Text)
    recommendations = db.Column(JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)