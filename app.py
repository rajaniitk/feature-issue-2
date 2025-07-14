import os
import logging
from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix
from database import init_app

# Set up logging
logging.basicConfig(level=logging.DEBUG)

# Create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configure the database
basedir = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(basedir, "instance", "eda_app.db")

# Ensure instance folder exists
os.makedirs(os.path.dirname(db_path), exist_ok=True)

app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", f"sqlite:///{db_path}")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["UPLOAD_FOLDER"] = "uploads"
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16MB max file size

# Ensure upload folder exists
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

# Initialize the database
db = init_app(app)

# Import and register blueprints
from routes.data_processor_routes import data_processor_bp
from routes.analysis_engine_routes import analysis_engine_bp
from routes.feature_engineer_routes import feature_engineer_bp
from routes.advance_feature_engineering_routes import advance_feature_engineering_bp
from routes.insights_generator_routes import insights_generator_bp
from routes.ml_engine_routes import ml_engine_bp
from routes.report_generator_routes import report_generator_bp
from routes.statistical_tests_routes import statistical_tests_bp
from routes.visualization_engine_routes import visualization_engine_bp
from routes.column_analysis_routes import column_analysis_bp
from routes.comparison_routes import comparison_bp

app.register_blueprint(data_processor_bp)
app.register_blueprint(analysis_engine_bp)
app.register_blueprint(feature_engineer_bp)
app.register_blueprint(advance_feature_engineering_bp)
app.register_blueprint(insights_generator_bp)
app.register_blueprint(ml_engine_bp)
app.register_blueprint(report_generator_bp)
app.register_blueprint(statistical_tests_bp)
app.register_blueprint(visualization_engine_bp)
app.register_blueprint(column_analysis_bp)
app.register_blueprint(comparison_bp)

# Main routes - only page routes, no API routes
from flask import render_template, redirect, url_for

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload')
def upload():
    return render_template('upload.html')

@app.route('/analysis_dashboard')
def analysis_dashboard():
    return render_template('analysis_dashboard.html')

@app.route('/visualization_dashboard')
def visualization_dashboard():
    return render_template('visualization_dashboard.html')

@app.route('/statistical_tests')
def statistical_tests():
    return render_template('statistical_tests.html')

@app.route('/feature_engineering')
def feature_engineering():
    return render_template('feature_engineering.html')

@app.route('/advance_feature_engineering')
def advance_feature_engineering():
    return render_template('advance_feature_engineering.html')

@app.route('/column_analysis')
def column_analysis():
    return render_template('column_analysis.html')

@app.route('/comparison')
def comparison():
    return render_template('comparison.html')

@app.route('/ml_models')
def ml_models():
    return render_template('ml_models.html')

@app.route('/reports')
def reports():
    return render_template('reports.html')

@app.route('/insights')
def insights():
    return render_template('insights.html')

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return render_template('index.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('index.html'), 500

with app.app_context():
    # Make sure to import the models here or their tables won't be created
    import models  # noqa: F401
    db.create_all()
