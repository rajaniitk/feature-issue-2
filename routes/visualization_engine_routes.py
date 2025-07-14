from flask import Blueprint, request, jsonify, session, redirect, url_for
from services.visualization_engine import VisualizationEngine
from database import db
from models import Dataset, Visualization
import logging

visualization_engine_bp = Blueprint('visualization', __name__, url_prefix='/api/visualization')

@visualization_engine_bp.route('/datasets', methods=['GET'])
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
                'column_names': dataset.column_names,  # Include column names for visualization
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
    
# fectch column names for visualization
@visualization_engine_bp.route('/columns/<int:dataset_id>', methods=['GET'])
def get_columns(dataset_id):
    """Get column names for a specific dataset"""
    try:
        dataset = Dataset.query.get_or_404(dataset_id)
        return jsonify({
            'success': True,
            'columns': dataset.column_names  # Assuming column_names is a list of column names
        })
    except Exception as e:
        logging.error(f"Error fetching columns for dataset {dataset_id}: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@visualization_engine_bp.route('/chart', methods=['POST'])
def create_chart():
    """Create a chart from dataset data"""
    try:
        dataset_id = request.json.get('dataset_id')
        chart_type = request.json.get('chart_type')
        x_column = request.json.get('x_column')
        y_column = request.json.get('y_column')
        color_column = request.json.get('color_column')
        
        if not dataset_id or not chart_type or not x_column:
            return jsonify({'success': False, 'error': 'Dataset ID, chart type, and x column are required'}), 400
        
        dataset = Dataset.query.get_or_404(dataset_id)
        engine = VisualizationEngine()
        
        chart_data = engine.generate_chart_data(
            dataset.file_path, 
            chart_type, 
            x_column, 
            y_column, 
            color_column
        )
        
        return jsonify({
            'success': True,
            'chart_data': chart_data
        })
        
    except Exception as e:
        logging.error(f"Create chart error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@visualization_engine_bp.route('/save', methods=['POST'])
def save_chart():
    """Save a chart configuration"""
    try:
        title = request.json.get('title')
        chart_type = request.json.get('type')
        dataset_id = request.json.get('dataset_id')
        x_column = request.json.get('x_column')
        y_column = request.json.get('y_column')
        color_column = request.json.get('color_column')
        theme = request.json.get('theme')
        
        if not title or not chart_type or not dataset_id:
            return jsonify({'success': False, 'error': 'Title, chart type, and dataset ID are required'}), 400
        
        # Save chart configuration to database
        chart = Visualization(
            dataset_id=dataset_id,
            chart_title=title,
            chart_type=chart_type,
            x_column=x_column,
            y_column=y_column,
            color_column=color_column,
            chart_config={'theme': theme}
        )
        db.session.add(chart)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'chart_id': chart.id,
            'message': 'Chart saved successfully'
        })
        
    except Exception as e:
        logging.error(f"Save chart error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@visualization_engine_bp.route('/saved', methods=['GET'])
def get_saved_charts():
    """Get all saved charts"""
    try:
        charts = Visualization.query.all()
        chart_list = []
        
        for chart in charts:
            chart_list.append({
                'id': chart.id,
                'title': chart.chart_title,
                'type': chart.chart_type,
                'dataset_id': chart.dataset_id,
                'x_column': chart.x_column,
                'y_column': chart.y_column,
                'color_column': chart.color_column,
                'theme': chart.chart_config.get('theme') if chart.chart_config else 'plotly',
                'created_at': chart.created_at.isoformat() if chart.created_at else None
            })
        
        return jsonify({
            'success': True,
            'charts': chart_list
        })
        
    except Exception as e:
        logging.error(f"Get saved charts error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@visualization_engine_bp.route('/load/<int:chart_id>', methods=['GET'])
def load_chart(chart_id):
    """Load a saved chart configuration"""
    try:
        chart = Visualization.query.get_or_404(chart_id)
        
        chart_data = {
            'id': chart.id,
            'title': chart.chart_title,
            'type': chart.chart_type,
            'dataset_id': chart.dataset_id,
            'x_column': chart.x_column,
            'y_column': chart.y_column,
            'color_column': chart.color_column,
            'theme': chart.chart_config.get('theme') if chart.chart_config else 'plotly'
        }
        
        return jsonify({
            'success': True,
            'chart': chart_data
            
        })
        
    except Exception as e:
        logging.error(f"Load chart error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@visualization_engine_bp.route('/delete/<int:chart_id>', methods=['DELETE'])
def delete_chart(chart_id):
    """Delete a saved chart"""
    try:
        chart = Visualization.query.get_or_404(chart_id)
        db.session.delete(chart)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Chart deleted successfully'
        })
        
    except Exception as e:
        logging.error(f"Delete chart error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@visualization_engine_bp.route('/histogram/<int:dataset_id>', methods=['POST'])
def create_histogram(dataset_id):
    try:
        dataset = Dataset.query.get_or_404(dataset_id)
        viz_engine = VisualizationEngine()
        
        column = request.json.get('column')
        bins = request.json.get('bins', 30)
        
        if not column:
            return jsonify({'error': 'Column parameter is required'}), 400
        
        result = viz_engine.create_histogram(dataset.file_path, column, bins)
        
        if result['success']:
            # Save visualization to database
            viz = Visualization(
                analysis_id=None,  # Can be linked to analysis later
                viz_type='histogram',
                title=f'Histogram of {column}',
                data=result['data'],
                layout=result['layout'],
                config=result['config']
            )
            db.session.add(viz)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'visualization_id': viz.id,
                'plot': result
            })
        else:
            return jsonify({'error': result['error']}), 400
            
    except Exception as e:
        logging.error(f"Histogram error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@visualization_engine_bp.route('/boxplot/<int:dataset_id>', methods=['POST'])
def create_boxplot(dataset_id):
    try:
        dataset = Dataset.query.get_or_404(dataset_id)
        viz_engine = VisualizationEngine()
        
        column = request.json.get('column')
        by_column = request.json.get('by_column')
        
        if not column:
            return jsonify({'error': 'Column parameter is required'}), 400
        
        result = viz_engine.create_boxplot(dataset.file_path, column, by_column)
        
        if result['success']:
            # Save visualization to database
            viz = Visualization(
                analysis_id=None,
                viz_type='boxplot',
                title=f'Boxplot of {column}',
                data=result['data'],
                layout=result['layout'],
                config=result['config']
            )
            db.session.add(viz)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'visualization_id': viz.id,
                'plot': result
            })
        else:
            return jsonify({'error': result['error']}), 400
            
    except Exception as e:
        logging.error(f"Boxplot error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@visualization_engine_bp.route('/scatter/<int:dataset_id>', methods=['POST'])
def create_scatter(dataset_id):
    try:
        dataset = Dataset.query.get_or_404(dataset_id)
        viz_engine = VisualizationEngine()
        
        x_column = request.json.get('x_column')
        y_column = request.json.get('y_column')
        color_column = request.json.get('color_column')
        size_column = request.json.get('size_column')
        
        if not x_column or not y_column:
            return jsonify({'error': 'Both x_column and y_column parameters are required'}), 400
        
        result = viz_engine.create_scatter(dataset.file_path, x_column, y_column, color_column, size_column)
        
        if result['success']:
            # Save visualization to database
            viz = Visualization(
                analysis_id=None,
                viz_type='scatter',
                title=f'Scatter plot: {x_column} vs {y_column}',
                data=result['data'],
                layout=result['layout'],
                config=result['config']
            )
            db.session.add(viz)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'visualization_id': viz.id,
                'plot': result
            })
        else:
            return jsonify({'error': result['error']}), 400
            
    except Exception as e:
        logging.error(f"Scatter plot error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@visualization_engine_bp.route('/correlation_heatmap/<int:dataset_id>', methods=['POST'])
def create_correlation_heatmap(dataset_id):
    try:
        dataset = Dataset.query.get_or_404(dataset_id)
        viz_engine = VisualizationEngine()
        
        columns = request.json.get('columns', [])
        method = request.json.get('method', 'pearson')
        
        result = viz_engine.create_correlation_heatmap(dataset.file_path, columns, method)
        
        if result['success']:
            # Save visualization to database
            viz = Visualization(
                analysis_id=None,
                viz_type='correlation_heatmap',
                title=f'Correlation Heatmap ({method})',
                data=result['data'],
                layout=result['layout'],
                config=result['config']
            )
            db.session.add(viz)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'visualization_id': viz.id,
                'plot': result
            })
        else:
            return jsonify({'error': result['error']}), 400
            
    except Exception as e:
        logging.error(f"Correlation heatmap error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@visualization_engine_bp.route('/bar_chart/<int:dataset_id>', methods=['POST'])
def create_bar_chart(dataset_id):
    try:
        dataset = Dataset.query.get_or_404(dataset_id)
        viz_engine = VisualizationEngine()
        
        column = request.json.get('column')
        sort_by = request.json.get('sort_by', 'value')
        top_n = request.json.get('top_n', 20)
        
        if not column:
            return jsonify({'error': 'Column parameter is required'}), 400
        
        result = viz_engine.create_bar_chart(dataset.file_path, column, sort_by, top_n)
        
        if result['success']:
            # Save visualization to database
            viz = Visualization(
                analysis_id=None,
                viz_type='bar_chart',
                title=f'Bar Chart of {column}',
                data=result['data'],
                layout=result['layout'],
                config=result['config']
            )
            db.session.add(viz)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'visualization_id': viz.id,
                'plot': result
            })
        else:
            return jsonify({'error': result['error']}), 400
            
    except Exception as e:
        logging.error(f"Bar chart error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@visualization_engine_bp.route('/line_chart/<int:dataset_id>', methods=['POST'])
def create_line_chart(dataset_id):
    try:
        dataset = Dataset.query.get_or_404(dataset_id)
        viz_engine = VisualizationEngine()
        
        x_column = request.json.get('x_column')
        y_column = request.json.get('y_column')
        group_column = request.json.get('group_column')
        
        if not x_column or not y_column:
            return jsonify({'error': 'Both x_column and y_column parameters are required'}), 400
        
        result = viz_engine.create_line_chart(dataset.file_path, x_column, y_column, group_column)
        
        if result['success']:
            # Save visualization to database
            viz = Visualization(
                analysis_id=None,
                viz_type='line_chart',
                title=f'Line Chart: {x_column} vs {y_column}',
                data=result['data'],
                layout=result['layout'],
                config=result['config']
            )
            db.session.add(viz)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'visualization_id': viz.id,
                'plot': result
            })
        else:
            return jsonify({'error': result['error']}), 400
            
    except Exception as e:
        logging.error(f"Line chart error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@visualization_engine_bp.route('/pie_chart/<int:dataset_id>', methods=['POST'])
def create_pie_chart(dataset_id):
    try:
        dataset = Dataset.query.get_or_404(dataset_id)
        viz_engine = VisualizationEngine()
        
        column = request.json.get('column')
        top_n = request.json.get('top_n', 10)
        
        if not column:
            return jsonify({'error': 'Column parameter is required'}), 400
        
        result = viz_engine.create_pie_chart(dataset.file_path, column, top_n)
        
        if result['success']:
            # Save visualization to database
            viz = Visualization(
                analysis_id=None,
                viz_type='pie_chart',
                title=f'Pie Chart of {column}',
                data=result['data'],
                layout=result['layout'],
                config=result['config']
            )
            db.session.add(viz)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'visualization_id': viz.id,
                'plot': result
            })
        else:
            return jsonify({'error': result['error']}), 400
            
    except Exception as e:
        logging.error(f"Pie chart error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@visualization_engine_bp.route('/violin_plot/<int:dataset_id>', methods=['POST'])
def create_violin_plot(dataset_id):
    try:
        dataset = Dataset.query.get_or_404(dataset_id)
        viz_engine = VisualizationEngine()
        
        column = request.json.get('column')
        by_column = request.json.get('by_column')
        
        if not column:
            return jsonify({'error': 'Column parameter is required'}), 400
        
        result = viz_engine.create_violin_plot(dataset.file_path, column, by_column)
        
        if result['success']:
            # Save visualization to database
            viz = Visualization(
                analysis_id=None,
                viz_type='violin_plot',
                title=f'Violin Plot of {column}',
                data=result['data'],
                layout=result['layout'],
                config=result['config']
            )
            db.session.add(viz)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'visualization_id': viz.id,
                'plot': result
            })
        else:
            return jsonify({'error': result['error']}), 400
            
    except Exception as e:
        logging.error(f"Violin plot error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@visualization_engine_bp.route('/density_plot/<int:dataset_id>', methods=['POST'])
def create_density_plot(dataset_id):
    try:
        dataset = Dataset.query.get_or_404(dataset_id)
        viz_engine = VisualizationEngine()
        
        column = request.json.get('column')
        by_column = request.json.get('by_column')
        
        if not column:
            return jsonify({'error': 'Column parameter is required'}), 400
        
        result = viz_engine.create_density_plot(dataset.file_path, column, by_column)
        
        if result['success']:
            # Save visualization to database
            viz = Visualization(
                analysis_id=None,
                viz_type='density_plot',
                title=f'Density Plot of {column}',
                data=result['data'],
                layout=result['layout'],
                config=result['config']
            )
            db.session.add(viz)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'visualization_id': viz.id,
                'plot': result
            })
        else:
            return jsonify({'error': result['error']}), 400
            
    except Exception as e:
        logging.error(f"Density plot error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@visualization_engine_bp.route('/pairplot/<int:dataset_id>', methods=['POST'])
def create_pairplot(dataset_id):
    try:
        dataset = Dataset.query.get_or_404(dataset_id)
        viz_engine = VisualizationEngine()
        
        columns = request.json.get('columns', [])
        hue_column = request.json.get('hue_column')
        
        result = viz_engine.create_pairplot(dataset.file_path, columns, hue_column)
        
        if result['success']:
            # Save visualization to database
            viz = Visualization(
                analysis_id=None,
                viz_type='pairplot',
                title='Pair Plot',
                data=result['data'],
                layout=result['layout'],
                config=result['config']
            )
            db.session.add(viz)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'visualization_id': viz.id,
                'plot': result
            })
        else:
            return jsonify({'error': result['error']}), 400
            
    except Exception as e:
        logging.error(f"Pairplot error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@visualization_engine_bp.route('/available_plots')
def get_available_plots():
    try:
        viz_engine = VisualizationEngine()
        plots = viz_engine.get_available_plots()
        
        return jsonify({
            'success': True,
            'plots': plots
        })
        
    except Exception as e:
        logging.error(f"Get available plots error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@visualization_engine_bp.route('/list/<int:dataset_id>')
def list_visualizations(dataset_id):
    try:
        visualizations = Visualization.query.join(Analysis).filter(
            Analysis.dataset_id == dataset_id
        ).all()
        
        viz_list = []
        for viz in visualizations:
            viz_list.append({
                'id': viz.id,
                'type': viz.viz_type,
                'title': viz.title,
                'created_at': viz.created_at.isoformat()
            })
        
        return jsonify({
            'success': True,
            'visualizations': viz_list
        })
        
    except Exception as e:
        logging.error(f"List visualizations error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@visualization_engine_bp.route('/get/<int:viz_id>')
def get_visualization(viz_id):
    try:
        viz = Visualization.query.get_or_404(viz_id)
        
        return jsonify({
            'success': True,
            'visualization': {
                'id': viz.id,
                'type': viz.viz_type,
                'title': viz.title,
                'data': viz.data,
                'layout': viz.layout,
                'config': viz.config
            }
        })
        
    except Exception as e:
        logging.error(f"Get visualization error: {str(e)}")
        return jsonify({'error': str(e)}), 500
