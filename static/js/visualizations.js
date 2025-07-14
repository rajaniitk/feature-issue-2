document.addEventListener('DOMContentLoaded', function() {
    // Global variables
    let currentDatasetId = null;
    let currentColumns = [];
    
    // DOM Elements
    const datasetSelect = document.getElementById('viz-dataset-select');
    const refreshButton = document.getElementById('refresh-viz-datasets');
    const vizControls = document.getElementById('viz-controls');
    const chartTypeSelect = document.getElementById('chart-type');
    const xColumnSelect = document.getElementById('x-column');
    const yColumnSelect = document.getElementById('y-column');
    const colorColumnSelect = document.getElementById('color-column');
    const chartTitleInput = document.getElementById('chart-title');
    const chartThemeSelect = document.getElementById('chart-theme');
    const createChartBtn = document.getElementById('create-chart');
    const saveChartBtn = document.getElementById('save-chart');
    const clearChartBtn = document.getElementById('clear-chart');
    const chartDisplay = document.getElementById('chart-display');
    const loadingModal = document.getElementById('viz-loading-modal');
    
    // Initialize
    loadDatasets();
    
    // Event listeners
    refreshButton.addEventListener('click', loadDatasets);
    datasetSelect.addEventListener('change', handleDatasetSelection);
    chartTypeSelect.addEventListener('change', handleChartTypeChange);
    createChartBtn.addEventListener('click', createChart);
    saveChartBtn.addEventListener('click', saveChart);
    clearChartBtn.addEventListener('click', clearChart);
    
    // Functions
    async function loadDatasets() {
        try {
            showLoading('Loading datasets...');
            
            // Fetch real datasets from the API
            const response = await fetch('/api/data/datasets');
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            
            datasetSelect.innerHTML = '<option value="">Choose a dataset...</option>';
            
            if (data.success && data.datasets) {
                data.datasets.forEach(dataset => {
                    const option = document.createElement('option');
                    option.value = dataset.id;
                    option.textContent = `${dataset.filename} (${dataset.rows} rows, ${dataset.columns} cols)`;
                    datasetSelect.appendChild(option);
                });
            } else {
                showError('No datasets found. Please upload a dataset first.');
            }
            
        } catch (error) {
            console.error('Error loading datasets:', error);
            showError('Failed to load datasets. Please check your connection.');
        } finally {
            hideLoading();
        }
    }
    
    async function handleDatasetSelection() {
        const selectedId = datasetSelect.value;
        
        if (!selectedId) {
            vizControls.style.display = 'none';
            return;
        }
        
        currentDatasetId = selectedId;
        await loadDatasetColumns(selectedId);
        vizControls.style.display = 'block';
    }
    
    async function loadDatasetColumns(datasetId) {
        showLoading('Loading dataset columns...');
        
        try {
            // Fetch real columns from the API
            const response = await fetch(`/api/data/columns/${datasetId}`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            
            if (data.success && data.columns) {
                currentColumns = data.columns;
                populateColumnSelects(data.columns);
            } else {
                throw new Error(data.error || 'Failed to load columns');
            }
            
        } catch (error) {
            console.error('Error loading columns:', error);
            showError('Failed to load dataset columns: ' + error.message);
        } finally {
            hideLoading();
        }
    }
    
    function populateColumnSelects(columns) {
        // Clear all selects
        xColumnSelect.innerHTML = '<option value="">Select column...</option>';
        yColumnSelect.innerHTML = '<option value="">Select column...</option>';
        colorColumnSelect.innerHTML = '<option value="">None</option>';
        
        // Populate with columns
        columns.forEach(column => {
            const xOption = document.createElement('option');
            xOption.value = column.name;
            xOption.textContent = `${column.name} (${column.dtype})`;
            xColumnSelect.appendChild(xOption);
            
            const yOption = document.createElement('option');
            yOption.value = column.name;
            yOption.textContent = `${column.name} (${column.dtype})`;
            yColumnSelect.appendChild(yOption);
            
            const colorOption = document.createElement('option');
            colorOption.value = column.name;
            colorOption.textContent = `${column.name} (${column.dtype})`;
            colorColumnSelect.appendChild(colorOption);
        });
    }
    
    function handleChartTypeChange() {
        const chartType = chartTypeSelect.value;
        const yColumnGroup = document.getElementById('y-column-group');
        const colorColumnGroup = document.getElementById('color-column-group');
        
        // Show/hide Y column based on chart type
        if (['histogram', 'box', 'violin'].includes(chartType)) {
            yColumnGroup.style.display = 'none';
        } else {
            yColumnGroup.style.display = 'block';
        }
        
        // Show/hide color column for appropriate chart types
        if (['scatter', 'line', 'bar'].includes(chartType)) {
            colorColumnGroup.style.display = 'block';
        } else {
            colorColumnGroup.style.display = 'none';
        }
    }
    
    async function createChart() {
        if (!currentDatasetId) {
            showError('Please select a dataset first');
            return;
        }
        
        const chartType = chartTypeSelect.value;
        const xColumn = xColumnSelect.value;
        const yColumn = yColumnSelect.value;
        const colorColumn = colorColumnSelect.value;
        const title = chartTitleInput.value || `${chartType.charAt(0).toUpperCase() + chartType.slice(1)} Chart`;
        const theme = chartThemeSelect.value;
        
        if (!xColumn) {
            showError('Please select an X-axis column');
            return;
        }
        
        if (!['histogram', 'box', 'violin', 'pie'].includes(chartType) && !yColumn) {
            showError('Please select a Y-axis column for this chart type');
            return;
        }
        
        showLoading('Generating chart with real data...');
        
        try {
            // Get real chart data from API
            const response = await fetch('/api/visualization/chart', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    dataset_id: currentDatasetId,
                    chart_type: chartType,
                    x_column: xColumn,
                    y_column: yColumn,
                    color_column: colorColumn
                })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const result = await response.json();
            
            if (result.success && result.chart_data) {
                const plotData = createPlotlyData(chartType, result.chart_data, xColumn, yColumn, colorColumn);
                const layout = createPlotlyLayout(title, theme, xColumn, yColumn, chartType);
                
                await Plotly.newPlot(chartDisplay, plotData, layout, {
                    responsive: true,
                    displayModeBar: true
                });
                
                saveChartBtn.disabled = false;
                showSuccess('Chart created successfully with real data!');
            } else {
                throw new Error(result.error || 'Failed to generate chart data');
            }
            
        } catch (error) {
            console.error('Error creating chart:', error);
            showError('Failed to create chart: ' + error.message);
        } finally {
            hideLoading();
        }
    }
    
    function createPlotlyData(chartType, data, xColumn, yColumn, colorColumn) {
        const plotData = [];
        
        switch (chartType) {
            case 'histogram':
                plotData.push({
                    x: data.x_values,
                    type: 'histogram',
                    name: xColumn,
                    marker: { color: '#3498db' },
                    nbinsx: 30
                });
                break;
                
            case 'scatter':
                const trace = {
                    x: data.x_values,
                    y: data.y_values,
                    mode: 'markers',
                    type: 'scatter',
                    name: `${xColumn} vs ${yColumn}`,
                    marker: { size: 8 }
                };
                
                if (colorColumn && data.color_values) {
                    trace.marker.color = data.color_values;
                    trace.marker.colorscale = 'Viridis';
                    trace.marker.showscale = true;
                    trace.marker.colorbar = { title: colorColumn };
                }
                
                plotData.push(trace);
                break;
                
            case 'box':
                if (data.groups) {
                    // Grouped box plot
                    Object.entries(data.groups).forEach(([group, values]) => {
                        plotData.push({
                            y: values,
                            type: 'box',
                            name: group,
                            boxpoints: 'outliers'
                        });
                    });
                } else {
                    // Single box plot
                    plotData.push({
                        y: data.x_values,
                        type: 'box',
                        name: xColumn,
                        boxpoints: 'outliers'
                    });
                }
                break;
                
            case 'bar':
                plotData.push({
                    x: data.categories || data.x_values,
                    y: data.counts || data.y_values,
                    type: 'bar',
                    name: xColumn,
                    marker: { color: '#e74c3c' }
                });
                break;
                
            case 'line':
                const lineTrace = {
                    x: data.x_values,
                    y: data.y_values,
                    type: 'scatter',
                    mode: 'lines+markers',
                    name: `${xColumn} vs ${yColumn}`,
                    line: { color: '#2ecc71', width: 2 },
                    marker: { size: 6 }
                };
                
                if (colorColumn && data.color_values) {
                    lineTrace.marker.color = data.color_values;
                    lineTrace.marker.colorscale = 'Viridis';
                    lineTrace.marker.showscale = true;
                }
                
                plotData.push(lineTrace);
                break;
                
            case 'pie':
                plotData.push({
                    labels: data.categories || data.labels,
                    values: data.counts || data.values,
                    type: 'pie',
                    name: xColumn,
                    textinfo: 'label+percent',
                    textposition: 'outside'
                });
                break;
                
            case 'violin':
                if (data.groups) {
                    // Grouped violin plot
                    Object.entries(data.groups).forEach(([group, values]) => {
                        plotData.push({
                            y: values,
                            type: 'violin',
                            name: group,
                            box: { visible: true },
                            meanline: { visible: true }
                        });
                    });
                } else {
                    // Single violin plot
                    plotData.push({
                        y: data.x_values,
                        type: 'violin',
                        name: xColumn,
                        box: { visible: true },
                        meanline: { visible: true }
                    });
                }
                break;
                
            case 'heatmap':
                plotData.push({
                    z: data.matrix,
                    x: data.x_labels,
                    y: data.y_labels,
                    type: 'heatmap',
                    colorscale: 'RdBu',
                    showscale: true,
                    colorbar: { title: 'Correlation' }
                });
                break;
        }
        
        return plotData;
    }
    
    function createPlotlyLayout(title, theme, xColumn, yColumn, chartType) {
        const layout = {
            title: {
                text: title,
                font: { size: 18 }
            },
            template: theme,
            font: { family: 'Segoe UI, Arial, sans-serif' },
            margin: { t: 80, l: 60, r: 60, b: 60 },
            showlegend: ['pie', 'box', 'violin'].includes(chartType)
        };
        
        if (xColumn && !['pie', 'heatmap'].includes(chartType)) {
            layout.xaxis = { 
                title: xColumn,
                titlefont: { size: 14 }
            };
        }
        
        if (yColumn && !['pie', 'heatmap'].includes(chartType)) {
            layout.yaxis = { 
                title: yColumn,
                titlefont: { size: 14 }
            };
        }
        
        // Special layout adjustments for specific chart types
        if (chartType === 'heatmap') {
            layout.xaxis = { side: 'bottom' };
            layout.yaxis = { side: 'left' };
        }
        
        return layout;
    }
    
    async function saveChart() {
        if (!currentDatasetId) {
            showError('No chart to save');
            return;
        }
        
        const chartData = {
            title: chartTitleInput.value || 'Untitled Chart',
            type: chartTypeSelect.value,
            dataset_id: currentDatasetId,
            x_column: xColumnSelect.value,
            y_column: yColumnSelect.value,
            color_column: colorColumnSelect.value,
            theme: chartThemeSelect.value
        };
        
        try {
            showLoading('Saving chart...');
            
            const response = await fetch('/api/visualization/save', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(chartData)
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const result = await response.json();
            
            if (result.success) {
                showSuccess('Chart saved successfully!');
                updateSavedChartsDisplay();
            } else {
                throw new Error(result.error || 'Failed to save chart');
            }
            
        } catch (error) {
            console.error('Error saving chart:', error);
            showError('Failed to save chart: ' + error.message);
        } finally {
            hideLoading();
        }
    }
    
    function clearChart() {
        Plotly.purge(chartDisplay);
        chartDisplay.innerHTML = `
            <div class="placeholder">
                <i class="icon">📊</i>
                <p>Select a dataset and configure your chart to begin visualization</p>
            </div>
        `;
        saveChartBtn.disabled = true;
    }
    
    async function updateSavedChartsDisplay() {
        try {
            const response = await fetch('/api/visualization/saved');
            if (!response.ok) {
                return; // Silently fail if can't load saved charts
            }
            
            const data = await response.json();
            
            if (data.success && data.charts) {
                const savedChartsContainer = document.getElementById('saved-charts');
                const chartsGallery = document.getElementById('charts-gallery');
                
                if (data.charts.length > 0) {
                    savedChartsContainer.style.display = 'block';
                    
                    let html = '';
                    data.charts.forEach(chart => {
                        html += `
                            <div class="chart-card">
                                <h4>${chart.title}</h4>
                                <p><strong>Type:</strong> ${chart.type}</p>
                                <p><strong>Dataset:</strong> ${chart.dataset_id}</p>
                                <p><strong>Created:</strong> ${new Date(chart.created_at).toLocaleDateString()}</p>
                                <div class="chart-actions">
                                    <button class="btn btn-secondary" onclick="loadChart(${chart.id})">Load</button>
                                    <button class="btn btn-secondary" onclick="deleteChart(${chart.id})">Delete</button>
                                </div>
                            </div>
                        `;
                    });
                    
                    chartsGallery.innerHTML = html;
                }
            }
        } catch (error) {
            console.error('Error loading saved charts:', error);
        }
    }
    
    function showLoading(message = 'Loading...') {
        loadingModal.style.display = 'flex';
        const modalContent = loadingModal.querySelector('.modal-content');
        if (modalContent) {
            modalContent.innerHTML = `
                <div class="modal-header">
                    <h3>${message}</h3>
                </div>
                <div class="modal-body">
                    <div class="spinner"></div>
                </div>
            `;
        }
    }
    
    function hideLoading() {
        loadingModal.style.display = 'none';
    }
    
    function showError(message) {
        alert(message); // In a real app, use a proper notification system
    }
    
    function showSuccess(message) {
        alert(message); // In a real app, use a proper notification system
    }
    
    // Initialize saved charts display
    updateSavedChartsDisplay();
});

// Global functions for chart management
async function loadChart(chartId) {
    try {
        const response = await fetch(`/api/visualization/load/${chartId}`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (data.success && data.chart) {
            const chart = data.chart;
            
            // Load chart configuration
            document.getElementById('viz-dataset-select').value = chart.dataset_id;
            document.getElementById('chart-type').value = chart.type;
            document.getElementById('x-column').value = chart.x_column;
            document.getElementById('y-column').value = chart.y_column;
            document.getElementById('color-column').value = chart.color_column;
            document.getElementById('chart-title').value = chart.title;
            document.getElementById('chart-theme').value = chart.theme;
            
            // Trigger dataset selection and recreate chart
            document.getElementById('viz-dataset-select').dispatchEvent(new Event('change'));
            setTimeout(() => {
                document.getElementById('create-chart').click();
            }, 500);
        }
    } catch (error) {
        console.error('Error loading chart:', error);
        alert('Failed to load chart');
    }
}

async function deleteChart(chartId) {
    if (confirm('Are you sure you want to delete this chart?')) {
        try {
            const response = await fetch(`/api/visualization/delete/${chartId}`, {
                method: 'DELETE'
            });
            
            if (response.ok) {
                updateSavedChartsDisplay();
                alert('Chart deleted successfully');
            } else {
                throw new Error('Failed to delete chart');
            }
        } catch (error) {
            console.error('Error deleting chart:', error);
            alert('Failed to delete chart');
        }
    }
}

// Add chart card styling
const chartCSS = `
<style>
.chart-card {
    background: white;
    padding: 20px;
    border-radius: 8px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    border: 1px solid #e2e8f0;
}

.chart-card h4 {
    margin: 0 0 15px 0;
    color: #1e293b;
}

.chart-card p {
    margin: 5px 0;
    color: #64748b;
    font-size: 0.9em;
}

.chart-actions {
    margin-top: 15px;
    display: flex;
    gap: 10px;
}

.chart-actions button {
    flex: 1;
    padding: 8px 16px;
    font-size: 0.9em;
}
</style>
`;

document.head.insertAdjacentHTML('beforeend', chartCSS);