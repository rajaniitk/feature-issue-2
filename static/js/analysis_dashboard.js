document.addEventListener('DOMContentLoaded', function() {
    // Global variables
    let currentDatasetId = null;
    let currentDataset = null;
    
    // DOM Elements
    const datasetSelect = document.getElementById('dataset-select');
    const refreshButton = document.getElementById('refresh-datasets');
    const datasetInfo = document.getElementById('dataset-info');
    const dataPreview = document.getElementById('data-preview');
    
    // Analysis buttons
    const generateStatsBtn = document.getElementById('generate-stats');
    const showTypesBtn = document.getElementById('show-types');
    const analyzeMissingBtn = document.getElementById('analyze-missing');
    const generateCorrelationBtn = document.getElementById('generate-correlation');
    
    // Preview buttons
    const showHeadBtn = document.getElementById('show-head');
    const showTailBtn = document.getElementById('show-tail');
    const showSampleBtn = document.getElementById('show-sample');
    
    // Loading modal
    const loadingModal = document.getElementById('loading-modal');
    
    // Initialize
    loadDatasets();
    
    // Event listeners
    refreshButton.addEventListener('click', loadDatasets);
    datasetSelect.addEventListener('change', handleDatasetSelection);
    
    generateStatsBtn.addEventListener('click', generateBasicStats);
    showTypesBtn.addEventListener('click', showDataTypes);
    analyzeMissingBtn.addEventListener('click', analyzeMissingValues);
    generateCorrelationBtn.addEventListener('click', generateCorrelation);
    
    showHeadBtn.addEventListener('click', () => showDataPreview('head'));
    showTailBtn.addEventListener('click', () => showDataPreview('tail'));
    showSampleBtn.addEventListener('click', () => showDataPreview('sample'));
    
    // Functions
    async function loadDatasets() {
        try {
            showLoading();
            
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
            hideDatasetInfo();
            return;
        }
        
        currentDatasetId = selectedId;
        await loadDatasetInfo(selectedId);
    }
    
    async function loadDatasetInfo(datasetId) {
        showLoading();
        
        try {
            // Fetch real dataset information from API
            const response = await fetch(`/api/data/info/${datasetId}`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            
            if (data.success && data.info) {
                currentDataset = data.info;
                showDatasetInfo(data.info);
                enableAnalysisButtons();
            } else {
                throw new Error(data.error || 'Failed to load dataset information');
            }
            
        } catch (error) {
            console.error('Error loading dataset info:', error);
            showError('Failed to load dataset information: ' + error.message);
        } finally {
            hideLoading();
        }
    }
    
    function showDatasetInfo(dataset) {
        document.getElementById('rows-count').textContent = dataset.rows.toLocaleString();
        document.getElementById('columns-count').textContent = dataset.columns;
        
        // Calculate total missing values
        const totalMissing = Object.values(dataset.missing_values || {}).reduce((sum, count) => sum + count, 0);
        document.getElementById('missing-count').textContent = totalMissing.toLocaleString();
        
        document.getElementById('file-size').textContent = formatFileSize(dataset.file_size);
        
        datasetInfo.style.display = 'block';
        dataPreview.style.display = 'block';
    }
    
    function formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
    
    function hideDatasetInfo() {
        datasetInfo.style.display = 'none';
        dataPreview.style.display = 'none';
        disableAnalysisButtons();
    }
    
    function enableAnalysisButtons() {
        generateStatsBtn.disabled = false;
        showTypesBtn.disabled = false;
        analyzeMissingBtn.disabled = false;
        generateCorrelationBtn.disabled = false;
    }
    
    function disableAnalysisButtons() {
        generateStatsBtn.disabled = true;
        showTypesBtn.disabled = true;
        analyzeMissingBtn.disabled = true;
        generateCorrelationBtn.disabled = true;
    }
    
    async function generateBasicStats() {
        if (!currentDatasetId) return;
        
        showLoading();
        
        try {
            // Fetch real statistics from API
            const response = await fetch(`/api/analysis/stats/${currentDatasetId}`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            
            if (data.success && data.statistics) {
                displayBasicStats(data.statistics);
            } else {
                throw new Error(data.error || 'Failed to generate statistics');
            }
            
        } catch (error) {
            console.error('Error generating statistics:', error);
            showError('Failed to generate statistics: ' + error.message);
        } finally {
            hideLoading();
        }
    }
    
    function displayBasicStats(stats) {
        const content = document.getElementById('basic-stats');
        
        if (!stats || (!stats.numeric && !stats.categorical)) {
            content.innerHTML = '<p>No statistical data available for this dataset.</p>';
            return;
        }
        
        let html = '<div class="stats-table-container">';
        
        // Display numeric statistics
        if (stats.numeric) {
            html += '<h4>Numeric Columns</h4>';
            html += '<table class="stats-table">';
            html += '<thead><tr><th>Column</th><th>Count</th><th>Mean</th><th>Std</th><th>Min</th><th>25%</th><th>50%</th><th>75%</th><th>Max</th></tr></thead>';
            html += '<tbody>';
            
            for (const [column, data] of Object.entries(stats.numeric)) {
                html += `<tr>
                    <td><strong>${column}</strong></td>
                    <td>${data.count ? data.count.toFixed(0) : 'N/A'}</td>
                    <td>${data.mean ? data.mean.toFixed(2) : 'N/A'}</td>
                    <td>${data.std ? data.std.toFixed(2) : 'N/A'}</td>
                    <td>${data.min ? data.min.toFixed(2) : 'N/A'}</td>
                    <td>${data['25%'] ? data['25%'].toFixed(2) : 'N/A'}</td>
                    <td>${data['50%'] ? data['50%'].toFixed(2) : 'N/A'}</td>
                    <td>${data['75%'] ? data['75%'].toFixed(2) : 'N/A'}</td>
                    <td>${data.max ? data.max.toFixed(2) : 'N/A'}</td>
                </tr>`;
            }
            
            html += '</tbody></table>';
        }
        
        // Display categorical statistics
        if (stats.categorical) {
            html += '<h4>Categorical Columns</h4>';
            html += '<table class="stats-table">';
            html += '<thead><tr><th>Column</th><th>Count</th><th>Unique</th><th>Top</th><th>Freq</th></tr></thead>';
            html += '<tbody>';
            
            for (const [column, data] of Object.entries(stats.categorical)) {
                html += `<tr>
                    <td><strong>${column}</strong></td>
                    <td>${data.count || 'N/A'}</td>
                    <td>${data.unique || 'N/A'}</td>
                    <td>${data.top || 'N/A'}</td>
                    <td>${data.freq || 'N/A'}</td>
                </tr>`;
            }
            
            html += '</tbody></table>';
        }
        
        html += '</div>';
        content.innerHTML = html;
    }
    
    async function showDataTypes() {
        if (!currentDatasetId) return;
        
        showLoading();
        
        try {
            // Use the already loaded dataset info for data types
            if (currentDataset && currentDataset.data_types) {
                displayDataTypes(currentDataset.data_types);
            } else {
                throw new Error('Dataset information not available');
            }
            
        } catch (error) {
            console.error('Error showing data types:', error);
            showError('Failed to load data types: ' + error.message);
        } finally {
            hideLoading();
        }
    }
    
    function displayDataTypes(types) {
        const content = document.getElementById('data-types');
        
        let html = '<div class="types-grid">';
        
        for (const [column, type] of Object.entries(types)) {
            const typeClass = getTypeClass(type);
            html += `<div class="type-item ${typeClass}">
                <strong>${column}</strong>
                <span class="type-badge">${type}</span>
            </div>`;
        }
        
        html += '</div>';
        content.innerHTML = html;
    }
    
    function getTypeClass(type) {
        if (type.includes('int') || type.includes('float')) return 'numeric';
        if (type.includes('object') || type.includes('string')) return 'categorical';
        if (type.includes('bool')) return 'boolean';
        if (type.includes('datetime')) return 'datetime';
        return 'other';
    }
    
    async function analyzeMissingValues() {
        if (!currentDatasetId) return;
        
        showLoading();
        
        try {
            // Use the already loaded dataset info for missing values
            if (currentDataset && currentDataset.missing_values) {
                const totalRows = currentDataset.rows;
                const missingWithPercentages = {};
                
                for (const [column, missing] of Object.entries(currentDataset.missing_values)) {
                    missingWithPercentages[column] = {
                        missing: missing,
                        percentage: totalRows > 0 ? (missing / totalRows * 100).toFixed(1) : 0
                    };
                }
                
                displayMissingAnalysis(missingWithPercentages);
            } else {
                throw new Error('Dataset information not available');
            }
            
        } catch (error) {
            console.error('Error analyzing missing values:', error);
            showError('Failed to analyze missing values: ' + error.message);
        } finally {
            hideLoading();
        }
    }
    
    function displayMissingAnalysis(missing) {
        const content = document.getElementById('missing-analysis');
        
        let html = '<div class="missing-chart">';
        
        for (const [column, data] of Object.entries(missing)) {
            const barWidth = Math.max(parseFloat(data.percentage), 1); // Minimum 1% for visibility
            const colorClass = data.percentage > 5 ? 'high' : data.percentage > 1 ? 'medium' : 'low';
            
            html += `<div class="missing-item">
                <div class="missing-label">${column}</div>
                <div class="missing-bar-container">
                    <div class="missing-bar ${colorClass}" style="width: ${barWidth}%"></div>
                    <span class="missing-text">${data.missing} (${data.percentage}%)</span>
                </div>
            </div>`;
        }
        
        html += '</div>';
        content.innerHTML = html;
    }
    
    async function generateCorrelation() {
        if (!currentDatasetId) return;
        
        showLoading();
        
        try {
            // Fetch real correlation matrix from API
            const response = await fetch(`/api/analysis/correlation/${currentDatasetId}`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            
            if (data.success && data.correlation) {
                displayCorrelationMatrix(data.correlation);
            } else {
                throw new Error(data.error || 'Failed to generate correlation matrix');
            }
            
        } catch (error) {
            console.error('Error generating correlation:', error);
            showError('Failed to generate correlation matrix: ' + error.message);
        } finally {
            hideLoading();
        }
    }
    
    function displayCorrelationMatrix(correlationData) {
        const content = document.getElementById('correlation-matrix');
        
        if (!correlationData || Object.keys(correlationData).length === 0) {
            content.innerHTML = '<p>No correlation data available. This dataset may not have numeric columns.</p>';
            return;
        }
        
        // Extract column names and correlation matrix
        const columns = Object.keys(correlationData);
        
        let html = '<div class="correlation-table-container">';
        html += '<table class="correlation-table">';
        html += '<thead><tr><th></th>';
        
        columns.forEach(col => {
            html += `<th>${col}</th>`;
        });
        html += '</tr></thead><tbody>';
        
        columns.forEach(row => {
            html += `<tr><th>${row}</th>`;
            columns.forEach(col => {
                const value = correlationData[row] && correlationData[row][col] ? correlationData[row][col] : 0;
                const intensity = Math.abs(value);
                const color = value > 0 ? 'positive' : 'negative';
                html += `<td class="corr-cell ${color}" data-value="${value.toFixed(3)}" style="opacity: ${intensity}">${value.toFixed(3)}</td>`;
            });
            html += '</tr>';
        });
        
        html += '</tbody></table></div>';
        content.innerHTML = html;
    }
    
    async function showDataPreview(type) {
        if (!currentDatasetId) return;
        
        showLoading();
        
        try {
            let endpoint = '';
            switch(type) {
                case 'head':
                case 'tail':
                    endpoint = `/api/data/preview/${currentDatasetId}`;
                    break;
                case 'sample':
                    endpoint = `/api/data/sample/${currentDatasetId}`;
                    break;
                default:
                    throw new Error('Invalid preview type');
            }
            
            const response = await fetch(endpoint);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            
            if (data.success) {
                if (type === 'sample') {
                    displayDataPreview({ 
                        data: data.sample, 
                        columns: data.columns 
                    }, type);
                } else {
                    displayDataPreview(data.preview, type);
                }
            } else {
                throw new Error(data.error || 'Failed to load data preview');
            }
            
        } catch (error) {
            console.error('Error showing data preview:', error);
            showError('Failed to load data preview: ' + error.message);
        } finally {
            hideLoading();
        }
    }
    
    function displayDataPreview(preview, type) {
        const content = document.getElementById('preview-content');
        
        let html = `<h4>Data Preview - ${type.charAt(0).toUpperCase() + type.slice(1)}</h4>`;
        html += '<div class="preview-table-container">';
        html += '<table class="preview-table">';
        html += '<thead><tr>';
        
        let dataToShow = [];
        let columns = [];
        
        if (type === 'sample') {
            dataToShow = preview.data;
            columns = preview.columns;
        } else {
            dataToShow = preview[type] || [];
            columns = preview.columns || [];
        }
        
        columns.forEach(col => {
            html += `<th>${col}</th>`;
        });
        html += '</tr></thead><tbody>';
        
        dataToShow.forEach(row => {
            html += '<tr>';
            columns.forEach(col => {
                const cellValue = row[col];
                const displayValue = cellValue !== null && cellValue !== undefined ? cellValue : 'N/A';
                html += `<td>${displayValue}</td>`;
            });
            html += '</tr>';
        });
        
        html += '</tbody></table></div>';
        content.innerHTML = html;
    }
    
    function showLoading() {
        loadingModal.style.display = 'flex';
    }
    
    function hideLoading() {
        loadingModal.style.display = 'none';
    }
    
    function showError(message) {
        alert(message); // In a real app, use a proper notification system
    }
});

// Add CSS for additional styling
const additionalCSS = `
<style>
.types-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
    gap: 15px;
}

.type-item {
    padding: 15px;
    border-radius: 8px;
    background: white;
    border: 1px solid #e2e8f0;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.type-item.numeric {
    border-left: 4px solid #10b981;
}

.type-item.categorical {
    border-left: 4px solid #f59e0b;
}

.type-item.boolean {
    border-left: 4px solid #8b5cf6;
}

.type-item.datetime {
    border-left: 4px solid #06b6d4;
}

.type-badge {
    background: #f1f5f9;
    padding: 4px 8px;
    border-radius: 4px;
    font-size: 0.85em;
    font-weight: 500;
    color: #64748b;
}

.missing-chart {
    display: flex;
    flex-direction: column;
    gap: 10px;
}

.missing-item {
    display: flex;
    align-items: center;
    gap: 15px;
}

.missing-label {
    min-width: 80px;
    font-weight: 500;
}

.missing-bar-container {
    flex: 1;
    position: relative;
    height: 24px;
    background: #f1f5f9;
    border-radius: 4px;
    display: flex;
    align-items: center;
}

.missing-bar {
    height: 100%;
    border-radius: 4px;
    min-width: 2px;
}

.missing-bar.low {
    background: #10b981;
}

.missing-bar.medium {
    background: #f59e0b;
}

.missing-bar.high {
    background: #ef4444;
}

.missing-text {
    position: absolute;
    right: 10px;
    font-size: 0.85em;
    font-weight: 500;
    color: #374151;
}

.correlation-table {
    width: 100%;
    border-collapse: collapse;
}

.correlation-table th,
.correlation-table td {
    padding: 8px;
    text-align: center;
    border: 1px solid #e2e8f0;
}

.correlation-table th {
    background: #f8fafc;
    font-weight: 600;
}

.corr-cell.positive {
    background: rgba(59, 130, 246, 0.1);
}

.corr-cell.negative {
    background: rgba(239, 68, 68, 0.1);
}
</style>
`;

// Inject additional CSS
document.head.insertAdjacentHTML('beforeend', additionalCSS);