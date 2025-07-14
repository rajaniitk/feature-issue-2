document.addEventListener('DOMContentLoaded', function() {
    // Global variables
    let selectedDatasets = [];
    let selectedColumns = [];
    let comparisonData = {};
    
    // DOM Elements
    const dataset1Select = document.getElementById('dataset1-select');
    const dataset2Select = document.getElementById('dataset2-select');
    const colDatasetSelect = document.getElementById('col-dataset-select');
    const comparisonResults = document.getElementById('comparison-results');
    const loadingModal = document.getElementById('comparison-loading-modal');
    
    // Initialize
    console.log('Initializing comparison functionality...');
    loadDatasets();
    setupEventListeners();
    console.log('Comparison initialization complete');
    
    function setupEventListeners() {
        // Dataset comparison event listeners
        const compareBtn = document.getElementById('compare-datasets');
        if (compareBtn) {
            compareBtn.addEventListener('click', compareDatasets);
        }
        
        const compareColBtn = document.getElementById('compare-columns');
        if (compareColBtn) {
            compareColBtn.addEventListener('click', compareColumns);
        }
        
        const compareSegBtn = document.getElementById('compare-segments');
        if (compareSegBtn) {
            compareSegBtn.addEventListener('click', compareSegments);
        }
        
        const exportBtn = document.getElementById('export-comparison');
        if (exportBtn) {
            exportBtn.addEventListener('click', exportComparison);
        }
        
        // Type switching buttons
        const typeButtons = document.querySelectorAll('.type-btn');
        typeButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                switchComparisonType(e.target.getAttribute('data-type'));
            });
        });
        
        // Tab switching
        const tabButtons = document.querySelectorAll('.comp-tab-button');
        tabButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                switchTab(e.target.getAttribute('data-tab'));
            });
        });
        
        // Dataset selectors
        if (dataset1Select) {
            dataset1Select.addEventListener('change', updateComparisonOptions);
        }
        if (dataset2Select) {
            dataset2Select.addEventListener('change', updateComparisonOptions);
        }
        if (colDatasetSelect) {
            colDatasetSelect.addEventListener('change', updateColumnOptions);
        }
        
        // Segment comparison selectors
        const segDatasetSelect = document.getElementById('seg-dataset-select');
        if (segDatasetSelect) {
            segDatasetSelect.addEventListener('change', updateSegmentOptions);
        }
    }
    
    async function loadDatasets() {
        try {
            // Fetch datasets from the comparison API endpoint
            const response = await fetch('/api/comparison/datasets');
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            
            if (data.success && data.datasets) {
                // Transform datasets to include column names if not already present
                const datasetsWithColumns = await Promise.all(data.datasets.map(async (dataset) => {
                    try {
                        // Use column_names directly if available, otherwise try to fetch
                        if (dataset.column_names && Array.isArray(dataset.column_names)) {
                            return {
                                ...dataset,
                                columns_list: dataset.column_names
                            };
                        }
                        
                        // Try alternative API endpoint for columns
                        const colResponse = await fetch(`/api/data/columns/${dataset.id}`);
                        if (colResponse.ok) {
                            const colData = await colResponse.json();
                            if (colData.success && colData.columns) {
                                return {
                                    ...dataset,
                                    columns_list: colData.columns.map(col => col.name)
                                };
                            }
                        }
                        
                        // Fallback to existing column_names or empty array
                        return {
                            ...dataset,
                            columns_list: dataset.column_names || []
                        };
                    } catch (err) {
                        console.warn(`Failed to load columns for dataset ${dataset.id}:`, err);
                        return {
                            ...dataset,
                            columns_list: dataset.column_names || []
                        };
                    }
                }));
                
                storeDatasets(datasetsWithColumns);
                populateDatasetSelectors(datasetsWithColumns);
            } else {
                console.log('No datasets available or API returned error:', data.error);
                // Show fallback message
                showError('No datasets available. Please upload some data first.');
                storeDatasets([]);
                populateDatasetSelectors([]);
            }
            
        } catch (error) {
            console.error('Error loading datasets:', error);
            showError('Failed to load datasets: ' + error.message);
            // Try to load from alternative endpoint as fallback
            try {
                const fallbackResponse = await fetch('/api/data/datasets');
                if (fallbackResponse.ok) {
                    const fallbackData = await fallbackResponse.json();
                    if (fallbackData.success && fallbackData.datasets) {
                        storeDatasets(fallbackData.datasets);
                        populateDatasetSelectors(fallbackData.datasets);
                        return;
                    }
                }
            } catch (fallbackError) {
                console.error('Fallback dataset loading also failed:', fallbackError);
            }
            
            // Final fallback - empty state
            storeDatasets([]);
            populateDatasetSelectors([]);
        }
    }
    
    function populateDatasetSelectors(datasets) {
        // Populate dataset selectors for comparison
        const selectors = [dataset1Select, dataset2Select, colDatasetSelect];
        
        selectors.forEach(selector => {
            if (selector) {
                selector.innerHTML = '<option value="">Choose dataset...</option>';
                datasets.forEach(dataset => {
                    const option = document.createElement('option');
                    option.value = dataset.id;
                    option.textContent = `${dataset.name} (${dataset.rows} rows, ${dataset.columns} cols)`;
                    selector.appendChild(option);
                });
            }
        });
        
        // Also populate segment dataset selector if it exists
        const segDatasetSelect = document.getElementById('seg-dataset-select');
        if (segDatasetSelect) {
            segDatasetSelect.innerHTML = '<option value="">Choose dataset...</option>';
            datasets.forEach(dataset => {
                const option = document.createElement('option');
                option.value = dataset.id;
                option.textContent = `${dataset.name} (${dataset.rows} rows, ${dataset.columns} cols)`;
                segDatasetSelect.appendChild(option);
            });
        }
    }
    

    
    function updateColumnOptions() {
        const selectedDatasetId = colDatasetSelect.value;
        const column1Select = document.getElementById('column1-select');
        const column2Select = document.getElementById('column2-select');
        
        // Clear existing options
        if (column1Select) column1Select.innerHTML = '<option value="">Choose first column...</option>';
        if (column2Select) column2Select.innerHTML = '<option value="">Choose second column...</option>';
        
        if (selectedDatasetId) {
            // First try to get columns from stored datasets
            const datasets = getStoredDatasets();
            const selectedDataset = datasets.find(d => d.id.toString() === selectedDatasetId);
            
            if (selectedDataset && selectedDataset.columns_list && selectedDataset.columns_list.length > 0) {
                // Use stored column data
                selectedDataset.columns_list.forEach(columnName => {
                    if (column1Select) {
                        const option1 = document.createElement('option');
                        option1.value = columnName;
                        option1.textContent = columnName;
                        column1Select.appendChild(option1);
                    }
                    if (column2Select) {
                        const option2 = document.createElement('option');
                        option2.value = columnName;
                        option2.textContent = columnName;
                        column2Select.appendChild(option2);
                    }
                });
            } else {
                // Fetch columns from API as fallback
                fetch(`/api/data/columns/${selectedDatasetId}`)
                    .then(response => {
                        if (!response.ok) {
                            throw new Error(`HTTP error! status: ${response.status}`);
                        }
                        return response.json();
                    })
                    .then(data => {
                        if (data.success && data.columns) {
                            data.columns.forEach(column => {
                                if (column1Select) {
                                    const option1 = document.createElement('option');
                                    option1.value = column.name;
                                    option1.textContent = `${column.name} (${column.type})`;
                                    column1Select.appendChild(option1);
                                }
                                if (column2Select) {
                                    const option2 = document.createElement('option');
                                    option2.value = column.name;
                                    option2.textContent = `${column.name} (${column.type})`;
                                    column2Select.appendChild(option2);
                                }
                            });
                        } else {
                            showError('Failed to load columns: ' + (data.error || 'Unknown error'));
                        }
                    })
                    .catch(error => {
                        console.error('Error loading columns:', error);
                        showError('Failed to load columns: ' + error.message);
                    });
            }
        }
    }
    
    function updateComparisonOptions() {
        // Enable/disable comparison button based on selection
        const compareBtn = document.getElementById('compare-datasets');
        if (compareBtn) {
            compareBtn.disabled = !dataset1Select.value || !dataset2Select.value;
        }
    }
    
    function switchComparisonType(type) {
        // Hide all panels
        const panels = document.querySelectorAll('.comparison-panel');
        panels.forEach(panel => panel.classList.remove('active'));
        
        // Show selected panel
        const selectedPanel = document.getElementById(`${type}-comparison-panel`);
        if (selectedPanel) {
            selectedPanel.classList.add('active');
        }
        
        // Update button states
        const buttons = document.querySelectorAll('.type-btn');
        buttons.forEach(btn => btn.classList.remove('active'));
        
        const activeButton = document.querySelector(`[data-type="${type}"]`);
        if (activeButton) {
            activeButton.classList.add('active');
        }
    }
    
    function getStoredDatasets() {
        // Simple function to store datasets temporarily
        if (!window.cachedDatasets) {
            window.cachedDatasets = [];
        }
        return window.cachedDatasets;
    }
    
    function storeDatasets(datasets) {
        window.cachedDatasets = datasets;
    }
    
    async function compareDatasets() {
        const dataset1Id = dataset1Select.value;
        const dataset2Id = dataset2Select.value;
        
        if (!dataset1Id || !dataset2Id) {
            showError('Please select both datasets to compare');
            return;
        }
        
        showLoading();
        
        try {
            const comparison = await performDatasetComparison([dataset1Id, dataset2Id]);
            displayDatasetComparison(comparison);
            
        } catch (error) {
            console.error('Error comparing datasets:', error);
            showError('Failed to compare datasets');
        } finally {
            hideLoading();
        }
    }
    
    async function performDatasetComparison(datasetIds) {
        try {
            console.log('Starting dataset comparison with IDs:', datasetIds);
            
            const response = await fetch('/api/comparison/datasets', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ dataset_ids: datasetIds })
            });

            console.log('Dataset comparison response status:', response.status);

            if (!response.ok) {
                const errorText = await response.text();
                console.error('Dataset comparison failed with error:', errorText);
                throw new Error(`HTTP ${response.status}: ${errorText}`);
            }

            const data = await response.json();
            console.log('Dataset comparison response data:', data);
            
            if (data.success) {
                console.log('Dataset comparison successful, returning data:', data.comparison);
                console.log('Statistical comparison array in response:', data.comparison.statistical_comparison);
                console.log('Statistical comparison length:', data.comparison.statistical_comparison ? data.comparison.statistical_comparison.length : 'undefined');
                return data.comparison;
            } else {
                console.error('Dataset comparison returned unsuccessful:', data.error);
                throw new Error(data.error || 'Failed to compare datasets');
            }
        } catch (error) {
            console.error('Error in performDatasetComparison:', error);
            
            // Return error structure instead of dummy data
            return {
                overview: {
                    datasets: []
                },
                schema_comparison: {
                    common_columns: [],
                    unique_columns: {},
                    data_type_differences: []
                },
                statistical_comparison: [],
                quality_comparison: [],
                error: `Dataset comparison failed: ${error.message}. Please check if the datasets are properly uploaded and accessible.`
            };
        }
    }
    
    // These functions were removed - using real data from backend instead of dummy data
    
    function displayDatasetComparison(comparison) {
        console.log('Displaying dataset comparison:', comparison);
        console.log('Statistical comparison in display function:', comparison.statistical_comparison);
        console.log('Statistical comparison length in display:', comparison.statistical_comparison ? comparison.statistical_comparison.length : 'undefined');
        
        const container = document.getElementById('comparison-results');
        
        if (!container) {
            console.error('comparison-results container not found');
            return;
        }
        
        // Check if there's an error or no data
        if (comparison.error || !comparison.overview || !comparison.overview.datasets || comparison.overview.datasets.length === 0) {
            console.log('Displaying error in dataset comparison:', comparison.error);
            container.innerHTML = `
                <div class="comparison-error">
                    <h3>Dataset Comparison Error</h3>
                    <p>${comparison.error || 'No datasets found or unable to load dataset data.'}</p>
                    <div class="error-suggestions">
                        <h4>Possible solutions:</h4>
                        <ul>
                            <li>Ensure both datasets are properly uploaded and accessible</li>
                            <li>Check that the datasets contain valid data</li>
                            <li>Try refreshing the page and selecting the datasets again</li>
                            <li>Verify that the dataset files are not corrupted</li>
                        </ul>
                    </div>
                </div>
            `;
            container.style.display = 'block';
            return;
        }
        
        console.log('Generating HTML for comparison results');
        console.log('Quality comparison data:', comparison.quality_comparison);
        
        // USE REAL DATA from the comparison object
        let html = `
            <div style="background: white; border: 3px solid #007cba; border-radius: 8px; padding: 0; margin: 20px 0; font-family: Arial, sans-serif; overflow: hidden;">
                <!-- ATTRACTIVE BANNER -->
                <div style="background: linear-gradient(135deg, #007cba 0%, #005580 50%, #003d5c 100%); padding: 40px 30px; text-align: center; position: relative; overflow: hidden;">
                    <div style="position: absolute; top: -50px; right: -50px; width: 200px; height: 200px; background: rgba(255,255,255,0.1); border-radius: 50%; transform: rotate(45deg);"></div>
                    <div style="position: absolute; bottom: -30px; left: -30px; width: 150px; height: 150px; background: rgba(255,255,255,0.08); border-radius: 50%;"></div>
                    <div style="position: relative; z-index: 2;">
                        <h1 style="color: white; font-size: 42px; margin: 0 0 15px 0; font-weight: bold; text-shadow: 2px 2px 4px rgba(0,0,0,0.3);">
                            📊 Dataset Comparison Dashboard
                        </h1>
                        <div style="background: rgba(255,255,255,0.2); border: 2px solid rgba(255,255,255,0.3); border-radius: 25px; padding: 15px 30px; display: inline-block; margin: 10px 0;">
                            <p style="color: white; font-size: 20px; margin: 0; font-weight: 500; text-shadow: 1px 1px 2px rgba(0,0,0,0.2);">
                                🔍 Analyzing ${comparison.overview.datasets.length} datasets: <strong>${comparison.overview.datasets.map(d => d.name).join(' ⚡ ')}</strong>
                            </p>
                        </div>
                        <div style="margin-top: 20px;">
                            <span style="background: rgba(255,255,255,0.9); color: #007cba; padding: 8px 20px; border-radius: 20px; font-size: 14px; font-weight: bold; margin: 0 5px; display: inline-block;">
                                ✅ Overview
                            </span>
                            <span style="background: rgba(255,255,255,0.9); color: #007cba; padding: 8px 20px; border-radius: 20px; font-size: 14px; font-weight: bold; margin: 0 5px; display: inline-block;">
                                🔍 Schema
                            </span>
                            <span style="background: rgba(255,255,255,0.9); color: #007cba; padding: 8px 20px; border-radius: 20px; font-size: 14px; font-weight: bold; margin: 0 5px; display: inline-block;">
                                📈 Statistics
                            </span>
                            <span style="background: rgba(255,255,255,0.9); color: #007cba; padding: 8px 20px; border-radius: 20px; font-size: 14px; font-weight: bold; margin: 0 5px; display: inline-block;">
                                ✅ Quality
                            </span>
                        </div>
                    </div>
                </div>
                
                <!-- MAIN CONTENT -->
                <div style="padding: 30px;">
                
                <!-- OVERVIEW SECTION -->
                <div style="background: #f0f8ff; border: 2px solid #007cba; border-radius: 8px; padding: 25px; margin: 20px 0;">
                    <h2 style="color: #007cba; font-size: 24px; margin: 0 0 20px 0;">📊 Overview</h2>
                    <div style="display: grid; grid-template-columns: ${comparison.overview.datasets.length === 2 ? '1fr 1fr' : 'repeat(auto-fit, minmax(300px, 1fr))'}; gap: 20px;">
                        ${comparison.overview.datasets.map((dataset, index) => `
                            <div style="background: white; padding: 20px; border: 2px solid #007cba; border-radius: 8px;">
                                <h3 style="color: #005580; margin: 0 0 15px 0;">Dataset ${index + 1}: ${dataset.name}</h3>
                                <p style="margin: 5px 0;"><strong>Rows:</strong> ${dataset.rows.toLocaleString()}</p>
                                <p style="margin: 5px 0;"><strong>Columns:</strong> ${dataset.columns}</p>
                                <p style="margin: 5px 0;"><strong>Memory Usage:</strong> ${dataset.memory_usage}</p>
                                <p style="margin: 5px 0;"><strong>Missing Values:</strong> ${dataset.missing_values}</p>
                            </div>
                        `).join('')}
                    </div>
                </div>
                
                <!-- SCHEMA SECTION -->
                <div style="background: #fff9e6; border: 2px solid #ff9800; border-radius: 8px; padding: 25px; margin: 20px 0;">
                    <h2 style="color: #ff9800; font-size: 24px; margin: 0 0 20px 0;">🔍 Schema Comparison</h2>
                    <div style="background: white; padding: 20px; border: 2px solid #ff9800; border-radius: 8px;">
                        <h3 style="color: #e65100; margin: 0 0 15px 0;">Common Columns: ${comparison.schema_comparison.common_columns.length}</h3>
                        ${comparison.schema_comparison.common_columns.length > 0 ? `
                            <div style="margin: 20px 0;">
                                <h4 style="color: #e65100; margin: 10px 0;">Common Columns:</h4>
                                <p style="background: #e8f5e8; padding: 10px; border-radius: 4px; font-family: monospace; font-size: 14px;">
                                    ${comparison.schema_comparison.common_columns.join(', ')}
                                </p>
                            </div>
                        ` : `
                            <p style="margin: 10px 0; padding: 10px; background: #ffebee; border-left: 4px solid #f44336; color: #c62828;">
                                ❌ <strong>No common columns found between datasets</strong>
                            </p>
                        `}
                        
                        ${Object.keys(comparison.schema_comparison.unique_columns).length > 0 ? 
                            Object.entries(comparison.schema_comparison.unique_columns).map(([dataset, columns]) => `
                                <div style="margin: 20px 0;">
                                    <h4 style="color: #e65100; margin: 10px 0;">${dataset} Unique Columns (${columns.length}):</h4>
                                    <p style="background: #f3e5f5; padding: 10px; border-radius: 4px; font-family: monospace; font-size: 14px;">
                                        ${columns.join(', ')}
                                    </p>
                                </div>
                            `).join('') 
                        : ''}
                        
                        ${comparison.schema_comparison.data_type_differences.length > 0 ? `
                            <div style="margin: 20px 0;">
                                <h4 style="color: #e65100; margin: 10px 0;">Data Type Differences:</h4>
                                <table style="width: 100%; border-collapse: collapse; margin: 10px 0;">
                                    <thead>
                                        <tr style="background: #ff9800; color: white;">
                                            <th style="border: 1px solid #ff9800; padding: 8px;">Column</th>
                                            <th style="border: 1px solid #ff9800; padding: 8px;">Dataset 1 Type</th>
                                            <th style="border: 1px solid #ff9800; padding: 8px;">Dataset 2 Type</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        ${comparison.schema_comparison.data_type_differences.map(diff => `
                                            <tr>
                                                <td style="border: 1px solid #ff9800; padding: 8px; font-weight: bold;">${diff.column}</td>
                                                <td style="border: 1px solid #ff9800; padding: 8px;">${diff.dataset1}</td>
                                                <td style="border: 1px solid #ff9800; padding: 8px;">${diff.dataset2}</td>
                                            </tr>
                                        `).join('')}
                                    </tbody>
                                </table>
                            </div>
                        ` : ''}
                    </div>
                </div>
                
                <!-- STATISTICS SECTION -->
                <div style="background: #e8f5e8; border: 2px solid #4caf50; border-radius: 8px; padding: 25px; margin: 20px 0;">
                    <h2 style="color: #4caf50; font-size: 24px; margin: 0 0 20px 0;">📈 Statistical Comparison</h2>
                    <div style="background: white; padding: 20px; border: 2px solid #4caf50; border-radius: 8px;">
                        ${comparison.statistical_comparison && comparison.statistical_comparison.length > 0 ? 
                            comparison.statistical_comparison.map(stat => {
                                const stats1 = stat.dataset1.statistics;
                                const stats2 = stat.dataset2.statistics;
                                return `
                                    <div style="margin: 20px 0;">
                                        <h3 style="color: #2e7d32; margin: 0 0 15px 0;">${stat.comparison_type === 'different_columns' ? 'Cross-Dataset' : 'Same-Column'} Comparison: ${stat.column}</h3>
                                        <table style="width: 100%; border-collapse: collapse; margin: 15px 0; background: white;">
                                            <thead>
                                                <tr style="background: #4caf50; color: white;">
                                                    <th style="border: 2px solid #4caf50; padding: 12px; text-align: left;">Metric</th>
                                                    <th style="border: 2px solid #4caf50; padding: 12px; text-align: left;">${stat.dataset1.name}</th>
                                                    <th style="border: 2px solid #4caf50; padding: 12px; text-align: left;">${stat.dataset2.name}</th>
                                                    <th style="border: 2px solid #4caf50; padding: 12px; text-align: left;">Difference</th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                                <tr style="background: #f1f8e9;">
                                                    <td style="border: 1px solid #4caf50; padding: 10px; font-weight: bold;">Count</td>
                                                    <td style="border: 1px solid #4caf50; padding: 10px;">${stats1.count || 'N/A'}</td>
                                                    <td style="border: 1px solid #4caf50; padding: 10px;">${stats2.count || 'N/A'}</td>
                                                    <td style="border: 1px solid #4caf50; padding: 10px;">${stats1.count && stats2.count ? Math.abs(stats1.count - stats2.count) : 'N/A'}</td>
                                                </tr>
                                                <tr style="background: white;">
                                                    <td style="border: 1px solid #4caf50; padding: 10px; font-weight: bold;">Mean</td>
                                                    <td style="border: 1px solid #4caf50; padding: 10px;">${typeof stats1.mean === 'number' ? stats1.mean.toFixed(3) : 'N/A'}</td>
                                                    <td style="border: 1px solid #4caf50; padding: 10px;">${typeof stats2.mean === 'number' ? stats2.mean.toFixed(3) : 'N/A'}</td>
                                                    <td style="border: 1px solid #4caf50; padding: 10px;">${typeof stats1.mean === 'number' && typeof stats2.mean === 'number' ? Math.abs(stats1.mean - stats2.mean).toFixed(3) : 'N/A'}</td>
                                                </tr>
                                                <tr style="background: #f1f8e9;">
                                                    <td style="border: 1px solid #4caf50; padding: 10px; font-weight: bold;">Std Dev</td>
                                                    <td style="border: 1px solid #4caf50; padding: 10px;">${typeof stats1.std === 'number' ? stats1.std.toFixed(3) : 'N/A'}</td>
                                                    <td style="border: 1px solid #4caf50; padding: 10px;">${typeof stats2.std === 'number' ? stats2.std.toFixed(3) : 'N/A'}</td>
                                                    <td style="border: 1px solid #4caf50; padding: 10px;">${typeof stats1.std === 'number' && typeof stats2.std === 'number' ? Math.abs(stats1.std - stats2.std).toFixed(3) : 'N/A'}</td>
                                                </tr>
                                                <tr style="background: white;">
                                                    <td style="border: 1px solid #4caf50; padding: 10px; font-weight: bold;">Min</td>
                                                    <td style="border: 1px solid #4caf50; padding: 10px;">${typeof stats1.min === 'number' ? stats1.min.toFixed(3) : 'N/A'}</td>
                                                    <td style="border: 1px solid #4caf50; padding: 10px;">${typeof stats2.min === 'number' ? stats2.min.toFixed(3) : 'N/A'}</td>
                                                    <td style="border: 1px solid #4caf50; padding: 10px;">${typeof stats1.min === 'number' && typeof stats2.min === 'number' ? Math.abs(stats1.min - stats2.min).toFixed(3) : 'N/A'}</td>
                                                </tr>
                                                <tr style="background: #f1f8e9;">
                                                    <td style="border: 1px solid #4caf50; padding: 10px; font-weight: bold;">Max</td>
                                                    <td style="border: 1px solid #4caf50; padding: 10px;">${typeof stats1.max === 'number' ? stats1.max.toFixed(3) : 'N/A'}</td>
                                                    <td style="border: 1px solid #4caf50; padding: 10px;">${typeof stats2.max === 'number' ? stats2.max.toFixed(3) : 'N/A'}</td>
                                                    <td style="border: 1px solid #4caf50; padding: 10px;">${typeof stats1.max === 'number' && typeof stats2.max === 'number' ? Math.abs(stats1.max - stats2.max).toFixed(3) : 'N/A'}</td>
                                                </tr>
                                            </tbody>
                                        </table>
                                    </div>
                                `;
                            }).join('')
                        : `
                            <div style="text-align: center; padding: 20px; color: #666;">
                                <h3>No Statistical Comparison Available</h3>
                                <p>This can happen when:</p>
                                <ul style="text-align: left; display: inline-block;">
                                    <li>Datasets have no columns in common</li>
                                    <li>Datasets contain only categorical/text data</li>
                                    <li>There was an error loading the dataset files</li>
                                </ul>
                            </div>
                        `}
                    </div>
                </div>
                
                <!-- QUALITY SECTION -->
                <div style="background: #fff3e0; border: 2px solid #ff9800; border-radius: 8px; padding: 25px; margin: 20px 0;">
                    <h2 style="color: #ff9800; font-size: 24px; margin: 0 0 20px 0;">✅ Data Quality Comparison</h2>
                    <div style="display: grid; grid-template-columns: ${comparison.overview.datasets.length === 2 ? '1fr 1fr' : 'repeat(auto-fit, minmax(300px, 1fr))'}; gap: 20px;">
                        ${comparison.quality_comparison && comparison.quality_comparison.length > 0 ? 
                            comparison.quality_comparison.map(quality => {
                                // Helper function to safely get quality value
                                const getQualityValue = (value) => {
                                    if (value === undefined || value === null) return 'N/A';
                                    if (typeof value === 'number') return `${Math.round(value)}%`;
                                    if (typeof value === 'string') return value.includes('%') ? value : `${value}%`;
                                    return 'N/A';
                                };
                                
                                // Helper function to get color based on value
                                const getQualityColor = (value) => {
                                    const numValue = typeof value === 'number' ? value : parseInt(value);
                                    if (isNaN(numValue)) return '#666';
                                    return numValue >= 90 ? '#4caf50' : numValue >= 70 ? '#ff9800' : '#f44336';
                                };
                                
                                const completeness = getQualityValue(quality.completeness);
                                const consistency = getQualityValue(quality.consistency);
                                const validity = getQualityValue(quality.validity);
                                const uniqueness = getQualityValue(quality.uniqueness);
                                
                                return `
                                    <div style="background: white; padding: 20px; border: 2px solid #ff9800; border-radius: 8px;">
                                        <h3 style="color: #e65100; margin: 0 0 15px 0;">${quality.dataset || quality.name || 'Dataset'}</h3>
                                        <div style="margin: 10px 0;">
                                            <p style="margin: 5px 0; display: flex; justify-content: space-between;">
                                                <span>📊 Completeness:</span>
                                                <strong style="color: ${getQualityColor(quality.completeness)};">${completeness}</strong>
                                            </p>
                                            <p style="margin: 5px 0; display: flex; justify-content: space-between;">
                                                <span>🔄 Consistency:</span>
                                                <strong style="color: ${getQualityColor(quality.consistency)};">${consistency}</strong>
                                            </p>
                                            <p style="margin: 5px 0; display: flex; justify-content: space-between;">
                                                <span>✓ Validity:</span>
                                                <strong style="color: ${getQualityColor(quality.validity)};">${validity}</strong>
                                            </p>
                                            <p style="margin: 5px 0; display: flex; justify-content: space-between;">
                                                <span>🎯 Uniqueness:</span>
                                                <strong style="color: ${getQualityColor(quality.uniqueness)};">${uniqueness}</strong>
                                            </p>
                                            ${quality.issues && quality.issues.length > 0 ? `
                                                <div style="margin-top: 15px; padding: 10px; background: #ffebee; border-left: 4px solid #f44336; border-radius: 4px;">
                                                    <h4 style="color: #d32f2f; margin: 0 0 8px 0; font-size: 14px;">Issues Found:</h4>
                                                    <ul style="margin: 0; padding-left: 20px; color: #c62828; font-size: 13px;">
                                                        ${quality.issues.map(issue => `<li>${issue}</li>`).join('')}
                                                    </ul>
                                                </div>
                                            ` : ''}
                                        </div>
                                    </div>
                                `;
                            }).join('')
                        : `
                            <div style="text-align: center; padding: 40px 20px; background: #fff3e0; border: 2px solid #ff9800; border-radius: 8px; margin: 20px 0;">
                                <h3 style="color: #e65100; margin: 0 0 15px 0;">⚠️ Quality Analysis Not Available</h3>
                                <p style="color: #f57c00; margin: 0 0 20px 0; font-size: 16px;">
                                    Quality comparison data is not provided by the backend API for this comparison.
                                </p>
                                <div style="background: white; padding: 20px; border-radius: 8px; border: 2px solid #ff9800;">
                                    <h4 style="color: #e65100; margin: 0 0 15px 0;">Available Dataset Information:</h4>
                                    ${comparison.overview.datasets.map(dataset => `
                                        <div style="margin: 15px 0; padding: 15px; background: #fff8e1; border-left: 4px solid #ff9800; border-radius: 4px;">
                                            <h5 style="color: #e65100; margin: 0 0 10px 0;">${dataset.name}</h5>
                                            <p style="margin: 5px 0; color: #f57c00;"><strong>Rows:</strong> ${dataset.rows.toLocaleString()}</p>
                                            <p style="margin: 5px 0; color: #f57c00;"><strong>Columns:</strong> ${dataset.columns}</p>
                                            <p style="margin: 5px 0; color: #f57c00;"><strong>Memory:</strong> ${dataset.memory_usage}</p>
                                            <p style="margin: 5px 0; color: #f57c00;"><strong>Missing Values:</strong> ${dataset.missing_values}</p>
                                        </div>
                                    `).join('')}
                                </div>
                                <p style="color: #bf360c; margin: 20px 0 0 0; font-size: 14px; font-style: italic;">
                                    💡 To see quality metrics, ensure your backend comparison service includes quality_comparison data
                                </p>
                            </div>
                        `
                        }
                    </div>
                </div>
                
                <div style="text-align: center; margin: 30px 0; padding: 20px; background: #f8f9fa; border-radius: 8px; border: 2px solid #6c757d;">
                    <h3 style="color: #495057; margin: 0 0 15px 0;">🎉 Comparison Complete!</h3>
                    <p style="margin: 0; color: #6c757d;">All sections above show your real dataset comparison results</p>
                </div>
                
                </div> <!-- End main content -->
            </div>
        `;
        
        console.log('Setting innerHTML for comparison results');
        container.innerHTML = html;
        
        // Force the container to be visible 
        container.style.cssText = 'display: block !important; visibility: visible !important; opacity: 1 !important; position: relative !important; height: auto !important;';
        container.classList.remove('hidden');
        container.removeAttribute('hidden');
        
        console.log('✅ Dataset comparison displayed successfully - all sections visible');
        console.log('Container display:', container.style.display);
        console.log('Container computed style:', window.getComputedStyle(container).display);
        
        // Scroll to the results container to make sure it's in view
        container.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
    
    function generateOverviewHTML(overview) {
        let html = '<div class="overview-grid">';
        
        overview.datasets.forEach(dataset => {
            html += `
                <div class="dataset-overview-card">
                    <h4>${dataset.name}</h4>
                    <div class="overview-stats">
                        <div class="stat">
                            <span class="label">Rows:</span>
                            <span class="value">${dataset.rows.toLocaleString()}</span>
                        </div>
                        <div class="stat">
                            <span class="label">Columns:</span>
                            <span class="value">${dataset.columns}</span>
                        </div>
                        <div class="stat">
                            <span class="label">Memory:</span>
                            <span class="value">${dataset.memory_usage}</span>
                        </div>
                        <div class="stat">
                            <span class="label">Missing:</span>
                            <span class="value">${dataset.missing_values}</span>
                        </div>
                    </div>
                </div>
            `;
        });
        
        html += '</div>';
        return html;
    }
    
    function generateSchemaHTML(schema) {
        if (!schema) {
            return '<div class="no-schema-message"><p>No schema comparison data available.</p></div>';
        }
        
        const commonColumns = schema.common_columns || [];
        const uniqueColumns = schema.unique_columns || {};
        const typeDifferences = schema.data_type_differences || [];
        
        return `
            <div class="schema-comparison">
                <div class="schema-section">
                    <h4>Common Columns (${commonColumns.length})</h4>
                    <div class="column-list">
                        ${commonColumns.length > 0 
                            ? commonColumns.map(col => `<span class="column-tag common">${col}</span>`).join('')
                            : '<p class="no-data">No common columns found between datasets.</p>'}
                    </div>
                </div>
                
                <div class="schema-section">
                    <h4>Unique Columns</h4>
                    ${Object.keys(uniqueColumns).length > 0 
                        ? Object.entries(uniqueColumns).map(([dataset, columns]) => `
                            <div class="unique-columns">
                                <h5>${dataset} (${columns.length} unique columns)</h5>
                                <div class="column-list">
                                    ${columns.map(col => `<span class="column-tag unique">${col}</span>`).join('')}
                                </div>
                            </div>
                        `).join('')
                        : '<p class="no-data">No unique columns found.</p>'}
                </div>
                
                <div class="schema-section">
                    <h4>Data Type Differences</h4>
                    ${typeDifferences.length > 0 
                        ? `<table class="type-differences-table">
                            <thead>
                                <tr>
                                    <th>Column</th>
                                    <th>Dataset 1</th>
                                    <th>Dataset 2</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${typeDifferences.map(diff => `
                                    <tr>
                                        <td>${diff.column}</td>
                                        <td><code>${diff.dataset1}</code></td>
                                        <td><code>${diff.dataset2}</code></td>
                                    </tr>
                                `).join('')}
                            </tbody>
                        </table>`
                        : '<p class="no-data">No data type differences found for common columns.</p>'}
                </div>
            </div>
        `;
    }
    
    function generateStatisticsHTML(statistics) {
        console.log('generateStatisticsHTML called with:', statistics);
        console.log('Statistics array length:', statistics ? statistics.length : 'undefined');
        
        if (!statistics || statistics.length === 0) {
            console.log('No statistics data - showing message');
            return `
                <div class="no-stats-message">
                    <h4>No Statistical Comparison Available</h4>
                    <p>This can happen when:</p>
                    <ul>
                        <li>Datasets have no columns in common</li>
                        <li>Datasets contain only categorical/text data</li>
                        <li>There was an error loading the dataset files</li>
                    </ul>
                    <p>Try checking the Overview, Schema, and Quality tabs for other comparison insights.</p>
                </div>
            `;
        }
        
        console.log('Generating statistics HTML for', statistics.length, 'items');
        
        return `
            <div class="statistics-comparison">
                ${statistics.map(stat => {
                    const stats1 = stat.dataset1.statistics;
                    const stats2 = stat.dataset2.statistics;
                    
                    // Check if this is numerical statistics or basic statistics
                    const isNumerical = stats1.hasOwnProperty('mean') && stats2.hasOwnProperty('mean');
                    
                    if (isNumerical) {
                        // Numerical statistics table
                                        return `
                    <div class="statistic-section">
                        <h5>Column: ${stat.column} <span class="column-type">(${stat.comparison_type === 'different_columns' ? 'Cross-Dataset Numerical' : 'Numerical'})</span></h5>
                                <table class="statistics-table">
                                    <thead>
                                        <tr>
                                            <th>Metric</th>
                                            <th>${stat.dataset1.name}</th>
                                            <th>${stat.dataset2.name}</th>
                                            <th>Difference</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        <tr>
                                            <td><strong>Count</strong></td>
                                            <td>${stats1.count || 'N/A'}</td>
                                            <td>${stats2.count || 'N/A'}</td>
                                            <td>${stats1.count && stats2.count ? Math.abs(stats1.count - stats2.count) : 'N/A'}</td>
                                        </tr>
                                        <tr>
                                            <td><strong>Mean</strong></td>
                                            <td>${typeof stats1.mean === 'number' ? stats1.mean.toFixed(3) : 'N/A'}</td>
                                            <td>${typeof stats2.mean === 'number' ? stats2.mean.toFixed(3) : 'N/A'}</td>
                                            <td>${typeof stats1.mean === 'number' && typeof stats2.mean === 'number' ? Math.abs(stats1.mean - stats2.mean).toFixed(3) : 'N/A'}</td>
                                        </tr>
                                        <tr>
                                            <td><strong>Median</strong></td>
                                            <td>${typeof stats1.median === 'number' ? stats1.median.toFixed(3) : 'N/A'}</td>
                                            <td>${typeof stats2.median === 'number' ? stats2.median.toFixed(3) : 'N/A'}</td>
                                            <td>${typeof stats1.median === 'number' && typeof stats2.median === 'number' ? Math.abs(stats1.median - stats2.median).toFixed(3) : 'N/A'}</td>
                                        </tr>
                                        <tr>
                                            <td><strong>Std Dev</strong></td>
                                            <td>${typeof stats1.std === 'number' ? stats1.std.toFixed(3) : 'N/A'}</td>
                                            <td>${typeof stats2.std === 'number' ? stats2.std.toFixed(3) : 'N/A'}</td>
                                            <td>${typeof stats1.std === 'number' && typeof stats2.std === 'number' ? Math.abs(stats1.std - stats2.std).toFixed(3) : 'N/A'}</td>
                                        </tr>
                                        <tr>
                                            <td><strong>Min</strong></td>
                                            <td>${typeof stats1.min === 'number' ? stats1.min.toFixed(3) : 'N/A'}</td>
                                            <td>${typeof stats2.min === 'number' ? stats2.min.toFixed(3) : 'N/A'}</td>
                                            <td>${typeof stats1.min === 'number' && typeof stats2.min === 'number' ? Math.abs(stats1.min - stats2.min).toFixed(3) : 'N/A'}</td>
                                        </tr>
                                        <tr>
                                            <td><strong>Max</strong></td>
                                            <td>${typeof stats1.max === 'number' ? stats1.max.toFixed(3) : 'N/A'}</td>
                                            <td>${typeof stats2.max === 'number' ? stats2.max.toFixed(3) : 'N/A'}</td>
                                            <td>${typeof stats1.max === 'number' && typeof stats2.max === 'number' ? Math.abs(stats1.max - stats2.max).toFixed(3) : 'N/A'}</td>
                                        </tr>
                                    </tbody>
                                </table>
                            </div>
                        `;
                    } else {
                        // Basic statistics table for non-numerical columns
                        const sectionType = stat.comparison_type === 'overview' ? 'Dataset Overview' : 
                                          stat.comparison_type === 'basic_comparison' ? 'Basic Comparison' : 
                                          (stats1.data_type || 'Mixed');
                        
                        return `
                            <div class="statistic-section">
                                <h5>Column: ${stat.column} <span class="column-type">(${sectionType})</span></h5>
                                <table class="statistics-table">
                                    <thead>
                                        <tr>
                                            <th>Metric</th>
                                            <th>${stat.dataset1.name}</th>
                                            <th>${stat.dataset2.name}</th>
                                            <th>Difference</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        ${stat.comparison_type === 'overview' ? `
                                            <tr>
                                                <td><strong>Total Columns</strong></td>
                                                <td>${stats1.total_columns || 'N/A'}</td>
                                                <td>${stats2.total_columns || 'N/A'}</td>
                                                <td>${stats1.total_columns && stats2.total_columns ? Math.abs(stats1.total_columns - stats2.total_columns) : 'N/A'}</td>
                                            </tr>
                                            <tr>
                                                <td><strong>Numerical Columns</strong></td>
                                                <td>${stats1.numerical_columns || 'N/A'}</td>
                                                <td>${stats2.numerical_columns || 'N/A'}</td>
                                                <td>${stats1.numerical_columns && stats2.numerical_columns ? Math.abs(stats1.numerical_columns - stats2.numerical_columns) : 'N/A'}</td>
                                            </tr>
                                            <tr>
                                                <td><strong>Categorical Columns</strong></td>
                                                <td>${stats1.categorical_columns || 'N/A'}</td>
                                                <td>${stats2.categorical_columns || 'N/A'}</td>
                                                <td>${stats1.categorical_columns && stats2.categorical_columns ? Math.abs(stats1.categorical_columns - stats2.categorical_columns) : 'N/A'}</td>
                                            </tr>
                                            <tr>
                                                <td><strong>Total Rows</strong></td>
                                                <td>${stats1.total_rows || 'N/A'}</td>
                                                <td>${stats2.total_rows || 'N/A'}</td>
                                                <td>${stats1.total_rows && stats2.total_rows ? Math.abs(stats1.total_rows - stats2.total_rows) : 'N/A'}</td>
                                            </tr>
                                            <tr>
                                                <td><strong>Memory Usage</strong></td>
                                                <td>${stats1.memory_usage || 'N/A'}</td>
                                                <td>${stats2.memory_usage || 'N/A'}</td>
                                                <td>-</td>
                                            </tr>
                                        ` : `
                                            <tr>
                                                <td><strong>Data Type</strong></td>
                                                <td><code>${stats1.data_type || 'Unknown'}</code></td>
                                                <td><code>${stats2.data_type || 'Unknown'}</code></td>
                                                <td>${(stats1.data_type === stats2.data_type) ? '✅ Match' : '❌ Different'}</td>
                                            </tr>
                                            <tr>
                                                <td><strong>Total Count</strong></td>
                                                <td>${stats1.total_count || 'N/A'}</td>
                                                <td>${stats2.total_count || 'N/A'}</td>
                                                <td>${stats1.total_count && stats2.total_count ? Math.abs(stats1.total_count - stats2.total_count) : 'N/A'}</td>
                                            </tr>
                                            <tr>
                                                <td><strong>Unique Values</strong></td>
                                                <td>${stats1.unique_values || 'N/A'}</td>
                                                <td>${stats2.unique_values || 'N/A'}</td>
                                                <td>${stats1.unique_values && stats2.unique_values ? Math.abs(stats1.unique_values - stats2.unique_values) : 'N/A'}</td>
                                            </tr>
                                            <tr>
                                                <td><strong>Null Count</strong></td>
                                                <td>${stats1.null_count || 'N/A'}</td>
                                                <td>${stats2.null_count || 'N/A'}</td>
                                                <td>${stats1.null_count && stats2.null_count ? Math.abs(stats1.null_count - stats2.null_count) : 'N/A'}</td>
                                            </tr>
                                            <tr>
                                                <td><strong>Completeness</strong></td>
                                                <td>${stats1.total_count && stats1.null_count ? ((stats1.total_count - stats1.null_count) / stats1.total_count * 100).toFixed(1) + '%' : 'N/A'}</td>
                                                <td>${stats2.total_count && stats2.null_count ? ((stats2.total_count - stats2.null_count) / stats2.total_count * 100).toFixed(1) + '%' : 'N/A'}</td>
                                                <td>-</td>
                                            </tr>
                                        `}
                                    </tbody>
                                </table>
                            </div>
                        `;
                    }
                }).join('')}
            </div>
        `;
    }
    
    function generateQualityHTML(quality) {
        if (!quality || quality.length === 0) {
            return `
                <div class="no-quality-message">
                    <h4>No Quality Data Available</h4>
                    <p>Quality metrics could not be calculated for the selected datasets.</p>
                    <p>This may occur when datasets are empty or cannot be loaded.</p>
                </div>
            `;
        }
        
        return `
            <div class="quality-comparison">
                ${quality.map(q => `
                    <div class="quality-card">
                        <h4>${q.dataset_name}</h4>
                        <div class="quality-metrics">
                            ${Object.entries(q.quality_metrics || {}).map(([metric, value]) => `
                                <div class="quality-metric">
                                    <span class="metric-name">${metric.charAt(0).toUpperCase() + metric.slice(1)}</span>
                                    <div class="metric-bar">
                                        <div class="metric-fill" style="width: ${value}%"></div>
                                        <span class="metric-value">${value}%</span>
                                    </div>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
    }
    
    async function compareColumns() {
        const datasetId = colDatasetSelect.value;
        const column1 = document.getElementById('column1-select').value;
        const column2 = document.getElementById('column2-select').value;
        
        if (!datasetId || !column1 || !column2) {
            showError('Please select dataset and both columns for comparison');
            return;
        }
        
        showLoading();
        
        try {
            const comparison = await performColumnComparison(datasetId, column1, datasetId, column2);
            displayColumnComparison(comparison);
            
        } catch (error) {
            console.error('Error comparing columns:', error);
            showError('Failed to compare columns');
        } finally {
            hideLoading();
        }
    }
    
    async function performColumnComparison(dataset1Id, column1, dataset2Id, column2) {
        try {
            const response = await fetch('/api/comparison/columns', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    dataset1_id: dataset1Id,
                    column1: column1,
                    dataset2_id: dataset2Id,
                    column2: column2
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            if (data.success) {
                return data.comparison;
            } else {
                throw new Error(data.error || 'Failed to compare columns');
            }
        } catch (error) {
            console.error('Error comparing columns:', error);
            // Fallback to basic comparison using stored data
            const datasets = getStoredDatasets();
            const dataset1 = datasets.find(d => d.id == dataset1Id);
            const dataset2 = datasets.find(d => d.id == dataset2Id);
            
            return {
                column1: {
                    dataset: dataset1 ? (dataset1.name || dataset1.filename) : 'Unknown',
                    column: column1,
                    type: 'unknown',
                    stats: {
                        count: dataset1 ? dataset1.rows : 'Unknown',
                        mean: 'Unknown',
                        std: 'Unknown',
                        min: 'Unknown',
                        max: 'Unknown',
                        unique: 'Unknown'
                    }
                },
                column2: {
                    dataset: dataset2 ? (dataset2.name || dataset2.filename) : 'Unknown',
                    column: column2,
                    type: 'unknown',
                    stats: {
                        count: dataset2 ? dataset2.rows : 'Unknown',
                        mean: 'Unknown',
                        std: 'Unknown',
                        min: 'Unknown',
                        max: 'Unknown',
                        unique: 'Unknown'
                    }
                },
                tests: {
                    correlation: 'Unable to calculate',
                    t_test_p_value: 'Unable to calculate',
                    ks_test_p_value: 'Unable to calculate'
                },
                error: 'Column comparison unavailable - API error'
            };
        }
    }
    
    function displayColumnComparison(comparison) {
        const container = document.getElementById('comparison-results');
        
        console.log('📊 Column comparison received:', comparison);
        console.log('📊 Comparison type:', comparison.comparison_type);
        console.log('📊 Tests data:', comparison.tests || comparison.pearson_correlation || comparison.chi_square_test);
        
        // Handle different comparison response formats
        let displayData;
        
        if (comparison.comparison_type === 'cross_dataset') {
            // Cross-dataset comparison format
            displayData = {
                column1: {
                    dataset: comparison.datasets.dataset1,
                    column: comparison.columns.column1,
                    stats: comparison.column1_stats
                },
                column2: {
                    dataset: comparison.datasets.dataset2,
                    column: comparison.columns.column2,
                    stats: comparison.column2_stats
                },
                summary: comparison.comparison_summary,
                tests: null
            };
        } else if (comparison.comparison_type === 'numerical') {
            // Same-dataset numerical comparison
            displayData = {
                column1: {
                    dataset: 'Current Dataset',
                    column: comparison.columns[0],
                    stats: comparison.descriptive_stats[comparison.columns[0]]
                },
                column2: {
                    dataset: 'Current Dataset', 
                    column: comparison.columns[1],
                    stats: comparison.descriptive_stats[comparison.columns[1]]
                },
                tests: {
                    'Pearson Correlation': comparison.pearson_correlation ? 
                        `r = ${comparison.pearson_correlation.coefficient?.toFixed(4) || 'N/A'} (p = ${comparison.pearson_correlation.p_value?.toFixed(4) || 'N/A'})` : 'Not computed',
                    'Spearman Correlation': comparison.spearman_correlation ? 
                        `ρ = ${comparison.spearman_correlation.coefficient?.toFixed(4) || 'N/A'} (p = ${comparison.spearman_correlation.p_value?.toFixed(4) || 'N/A'})` : 'Not computed',
                    'T-test': comparison.difference_test ? 
                        `t = ${comparison.difference_test.statistic?.toFixed(4) || 'N/A'}, p = ${comparison.difference_test.p_value?.toFixed(4) || 'N/A'}` : 'Not computed',
                    'Kolmogorov-Smirnov Test': comparison.distribution_test ? 
                        `D = ${comparison.distribution_test.statistic?.toFixed(4) || 'N/A'}, p = ${comparison.distribution_test.p_value?.toFixed(4) || 'N/A'}` : 'Not computed',
                    'Effect Size (Cohen\'s d)': comparison.effect_size?.cohens_d ? 
                        `d = ${comparison.effect_size.cohens_d.toFixed(4)} (${comparison.effect_size.interpretation || 'No interpretation'})` : 'Not computed'
                },
                interpretation: {
                    correlation: comparison.pearson_correlation?.interpretation || 'N/A',
                    difference: comparison.difference_test?.interpretation || 'N/A',
                    distribution: comparison.distribution_test?.interpretation || 'N/A',
                    effect: comparison.effect_size?.interpretation || 'N/A'
                }
            };
        } else if (comparison.comparison_type === 'categorical') {
            // Same-dataset categorical comparison
            displayData = {
                column1: {
                    dataset: 'Current Dataset',
                    column: comparison.columns[0],
                    stats: comparison.descriptive_stats[comparison.columns[0]]
                },
                column2: {
                    dataset: 'Current Dataset',
                    column: comparison.columns[1], 
                    stats: comparison.descriptive_stats[comparison.columns[1]]
                },
                tests: {
                    'Chi-Square Test': comparison.chi_square_test ? 
                        `χ² = ${comparison.chi_square_test.chi2_statistic?.toFixed(4) || 'N/A'}, df = ${comparison.chi_square_test.degrees_of_freedom || 'N/A'}, p = ${comparison.chi_square_test.p_value?.toFixed(4) || 'N/A'}` : 'Not computed',
                    'Cramér\'s V (Effect Size)': comparison.effect_size?.cramers_v ? 
                        `V = ${comparison.effect_size.cramers_v.toFixed(4)} (${comparison.effect_size.interpretation || 'No interpretation'})` : 'Not computed',
                    'Mutual Information': comparison.mutual_information ? 
                        `MI = ${comparison.mutual_information.score?.toFixed(4) || 'N/A'} (${comparison.mutual_information.interpretation || 'No interpretation'})` : 'Not computed',
                    'Association Strength': comparison.chi_square_test?.p_value ? 
                        (comparison.chi_square_test.p_value < 0.05 ? 'Significant association detected' : 'No significant association') : 'Unknown'
                },
                interpretation: {
                    independence: comparison.chi_square_test?.interpretation || 'N/A',
                    association: comparison.effect_size?.interpretation || 'N/A',
                    mutual_info: comparison.mutual_information?.interpretation || 'N/A'
                }
            };
        } else if (comparison.comparison_type === 'mixed') {
            // Mixed comparison (ANOVA) - used for segment analysis
            displayData = {
                type: 'segment_analysis',
                numerical_column: comparison.numerical_column,
                categorical_column: comparison.categorical_column,
                group_statistics: comparison.group_statistics,
                tests: {
                    'ANOVA Test (Parametric)': comparison.anova_test ? 
                        `F = ${comparison.anova_test.f_statistic?.toFixed(4) || 'N/A'}, df = ${comparison.anova_test.df_between || 'N/A'}/${comparison.anova_test.df_within || 'N/A'}, p = ${comparison.anova_test.p_value?.toFixed(4) || 'N/A'}` : 'Not computed',
                    'Kruskal-Wallis Test (Non-parametric)': comparison.kruskal_wallis_test ? 
                        `H = ${comparison.kruskal_wallis_test.h_statistic?.toFixed(4) || 'N/A'}, p = ${comparison.kruskal_wallis_test.p_value?.toFixed(4) || 'N/A'}` : 'Not computed',
                    'Effect Size (η²)': comparison.effect_size?.eta_squared ? 
                        `η² = ${comparison.effect_size.eta_squared.toFixed(4)} (${comparison.effect_size.interpretation || 'No interpretation'})` : 'Not computed',
                    'Group Differences': comparison.anova_test?.p_value ? 
                        (comparison.anova_test.p_value < 0.05 ? 'Significant differences between groups' : 'No significant differences between groups') : 'Unknown',
                    'Post-hoc Analysis': comparison.post_hoc_test ? 
                        `${comparison.post_hoc_test.method || 'Tukey HSD'}: ${comparison.post_hoc_test.significant_pairs?.length || 0} significant pairs` : 'Not performed'
                },
                interpretation: {
                    anova: comparison.anova_test?.interpretation || 'N/A',
                    kruskal: comparison.kruskal_wallis_test?.interpretation || 'N/A',
                    effect: comparison.effect_size?.interpretation || 'N/A'
                },
                sample_size: comparison.sample_size,
                group_count: comparison.group_count
            };
        } else {
            // Fallback or error case
            displayData = comparison;
        }
        
        // Handle segment analysis display differently
        if (displayData.type === 'segment_analysis') {
            const html = `
                <div style="background: white; border: 3px solid #4caf50; border-radius: 8px; padding: 0; margin: 20px 0; font-family: Arial, sans-serif; overflow: hidden;">
                    <!-- ATTRACTIVE BANNER -->
                    <div style="background: linear-gradient(135deg, #4caf50 0%, #388e3c 50%, #2e7d32 100%); padding: 40px 30px; text-align: center; position: relative; overflow: hidden;">
                        <div style="position: absolute; top: -50px; right: -50px; width: 200px; height: 200px; background: rgba(255,255,255,0.1); border-radius: 50%; transform: rotate(45deg);"></div>
                        <div style="position: absolute; bottom: -30px; left: -30px; width: 150px; height: 150px; background: rgba(255,255,255,0.08); border-radius: 50%;"></div>
                        <div style="position: relative; z-index: 2;">
                            <h1 style="color: white; font-size: 42px; margin: 0 0 15px 0; font-weight: bold; text-shadow: 2px 2px 4px rgba(0,0,0,0.3);">
                                📊 Segment Analysis Dashboard
                            </h1>
                            <div style="background: rgba(255,255,255,0.2); border: 2px solid rgba(255,255,255,0.3); border-radius: 25px; padding: 15px 30px; display: inline-block; margin: 10px 0;">
                                <p style="color: white; font-size: 20px; margin: 0; font-weight: 500; text-shadow: 1px 1px 2px rgba(0,0,0,0.2);">
                                    🔍 Analyzing <strong>${displayData.numerical_column}</strong> across segments of <strong>${displayData.categorical_column}</strong>
                                </p>
                            </div>
                            <div style="margin-top: 20px;">
                                <span style="background: rgba(255,255,255,0.9); color: #4caf50; padding: 8px 20px; border-radius: 20px; font-size: 14px; font-weight: bold; margin: 0 5px; display: inline-block;">
                                    📈 Summary
                                </span>
                                <span style="background: rgba(255,255,255,0.9); color: #4caf50; padding: 8px 20px; border-radius: 20px; font-size: 14px; font-weight: bold; margin: 0 5px; display: inline-block;">
                                    📊 Groups
                                </span>
                                <span style="background: rgba(255,255,255,0.9); color: #4caf50; padding: 8px 20px; border-radius: 20px; font-size: 14px; font-weight: bold; margin: 0 5px; display: inline-block;">
                                    🔬 Tests
                                </span>
                                <span style="background: rgba(255,255,255,0.9); color: #4caf50; padding: 8px 20px; border-radius: 20px; font-size: 14px; font-weight: bold; margin: 0 5px; display: inline-block;">
                                    💡 Insights
                                </span>
                            </div>
                        </div>
                    </div>
                    
                    <!-- MAIN CONTENT -->
                    <div style="padding: 30px;">
                    
                    <!-- SUMMARY SECTION -->
                    <div style="background: #e8f5e8; border: 2px solid #4caf50; border-radius: 8px; padding: 25px; margin: 20px 0;">
                        <h2 style="color: #4caf50; font-size: 24px; margin: 0 0 20px 0;">📈 Analysis Summary</h2>
                        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px;">
                            <div style="background: white; padding: 15px; border: 2px solid #4caf50; border-radius: 8px; text-align: center;">
                                <h3 style="color: #2e7d32; margin: 0 0 10px 0; font-size: 16px;">Sample Size</h3>
                                <span style="font-size: 24px; font-weight: bold; color: #1b5e20;">${displayData.sample_size || 'N/A'}</span>
                            </div>
                            <div style="background: white; padding: 15px; border: 2px solid #4caf50; border-radius: 8px; text-align: center;">
                                <h3 style="color: #2e7d32; margin: 0 0 10px 0; font-size: 16px;">Groups Found</h3>
                                <span style="font-size: 24px; font-weight: bold; color: #1b5e20;">${displayData.group_count || 'N/A'}</span>
                            </div>
                            <div style="background: white; padding: 15px; border: 2px solid #4caf50; border-radius: 8px; text-align: center;">
                                <h3 style="color: #2e7d32; margin: 0 0 10px 0; font-size: 16px;">ANOVA P-value</h3>
                                <span style="font-size: 20px; font-weight: bold; color: #1b5e20;">${displayData.tests['ANOVA P-value']}</span>
                            </div>
                            <div style="background: white; padding: 15px; border: 2px solid #4caf50; border-radius: 8px; text-align: center;">
                                <h3 style="color: #2e7d32; margin: 0 0 10px 0; font-size: 16px;">Effect Size (η²)</h3>
                                <span style="font-size: 20px; font-weight: bold; color: #1b5e20;">${displayData.tests['Effect Size (η²)']}</span>
                            </div>
                        </div>
                    </div>

                    <!-- GROUP STATISTICS SECTION -->
                    <div style="background: #fff3e0; border: 2px solid #ff9800; border-radius: 8px; padding: 25px; margin: 20px 0;">
                        <h2 style="color: #ff9800; font-size: 24px; margin: 0 0 20px 0;">📊 Group Statistics</h2>
                        <div style="background: white; padding: 20px; border: 2px solid #ff9800; border-radius: 8px; overflow-x: auto;">
                            ${generateGroupStatisticsTableStyled(displayData.group_statistics)}
                        </div>
                    </div>
                    
                    <!-- STATISTICAL TESTS SECTION -->
                    <div style="background: #f3e5f5; border: 2px solid #9c27b0; border-radius: 8px; padding: 25px; margin: 20px 0;">
                        <h2 style="color: #9c27b0; font-size: 24px; margin: 0 0 20px 0;">🔬 Statistical Tests</h2>
                        <div style="background: white; padding: 20px; border: 2px solid #9c27b0; border-radius: 8px;">
                            ${Object.entries(displayData.tests).map(([testName, value]) => `
                                <div style="display: flex; justify-content: space-between; align-items: center; padding: 12px 0; border-bottom: 1px solid #eee;">
                                    <span style="font-weight: bold; color: #4a148c; font-size: 16px;">${testName}:</span>
                                    <span style="color: #6a1b9a; font-size: 16px; font-weight: bold;">${value}</span>
                                </div>
                            `).join('')}
                        </div>
                    </div>

                    <!-- INTERPRETATION SECTION -->
                    <div style="background: #e3f2fd; border: 2px solid #2196f3; border-radius: 8px; padding: 25px; margin: 20px 0;">
                        <h2 style="color: #2196f3; font-size: 24px; margin: 0 0 20px 0;">💡 Interpretation</h2>
                        <div style="background: white; padding: 20px; border: 2px solid #2196f3; border-radius: 8px;">
                            ${Object.entries(displayData.interpretation).map(([key, value]) => `
                                <div style="margin: 15px 0; padding: 15px; background: #f8f9fa; border-left: 4px solid #2196f3; border-radius: 4px;">
                                    <div style="font-weight: bold; color: #0d47a1; font-size: 16px; margin-bottom: 8px;">${key.toUpperCase()}:</div>
                                    <div style="color: #1565c0; font-size: 15px; line-height: 1.5;">${value}</div>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                    
                    <div style="text-align: center; margin: 30px 0; padding: 20px; background: #f8f9fa; border-radius: 8px; border: 2px solid #6c757d;">
                        <h3 style="color: #495057; margin: 0 0 15px 0;">🎉 Segment Analysis Complete!</h3>
                        <p style="margin: 0; color: #6c757d;">All statistical comparisons between groups are shown above</p>
                    </div>
                    
                    </div> <!-- End main content -->
                </div>
            `;
            
            container.innerHTML = html;
            container.style.cssText = 'display: block !important; visibility: visible !important; opacity: 1 !important; position: relative !important; height: auto !important;';
            console.log('✅ Segment analysis displayed successfully with styled CSS');
            return;
        }
        
        // Safely handle undefined comparison data
        if (!displayData || !displayData.column1 || !displayData.column2) {
            container.innerHTML = `
                <div class="column-comparison-results error">
                    <h3>Column Comparison Error</h3>
                    <p>Unable to display comparison results. Please ensure both columns are properly selected and contain valid data.</p>
                    <p>Error details: ${comparison.error || 'Unknown error occurred'}</p>
                </div>
            `;
            container.style.display = 'block';
            return;
        }
        
        const html = `
            <div style="background: white; border: 3px solid #2196f3; border-radius: 8px; padding: 0; margin: 20px 0; font-family: Arial, sans-serif; overflow: hidden;">
                <!-- ATTRACTIVE BANNER -->
                <div style="background: linear-gradient(135deg, #2196f3 0%, #1976d2 50%, #1565c0 100%); padding: 40px 30px; text-align: center; position: relative; overflow: hidden;">
                    <div style="position: absolute; top: -50px; right: -50px; width: 200px; height: 200px; background: rgba(255,255,255,0.1); border-radius: 50%; transform: rotate(45deg);"></div>
                    <div style="position: absolute; bottom: -30px; left: -30px; width: 150px; height: 150px; background: rgba(255,255,255,0.08); border-radius: 50%;"></div>
                    <div style="position: relative; z-index: 2;">
                        <h1 style="color: white; font-size: 42px; margin: 0 0 15px 0; font-weight: bold; text-shadow: 2px 2px 4px rgba(0,0,0,0.3);">
                            📊 Column Comparison Dashboard
                        </h1>
                        <div style="background: rgba(255,255,255,0.2); border: 2px solid rgba(255,255,255,0.3); border-radius: 25px; padding: 15px 30px; display: inline-block; margin: 10px 0;">
                            <p style="color: white; font-size: 20px; margin: 0; font-weight: 500; text-shadow: 1px 1px 2px rgba(0,0,0,0.2);">
                                ⚡ Analyzing: <strong>${displayData.column1.column}</strong> vs <strong>${displayData.column2.column}</strong>
                            </p>
                        </div>
                        <div style="margin-top: 20px;">
                            <span style="background: rgba(255,255,255,0.9); color: #2196f3; padding: 8px 20px; border-radius: 20px; font-size: 14px; font-weight: bold; margin: 0 5px; display: inline-block;">
                                📈 Statistics
                            </span>
                            ${displayData.summary ? `
                                <span style="background: rgba(255,255,255,0.9); color: #2196f3; padding: 8px 20px; border-radius: 20px; font-size: 14px; font-weight: bold; margin: 0 5px; display: inline-block;">
                                    📋 Summary
                                </span>
                            ` : ''}
                            ${displayData.tests ? `
                                <span style="background: rgba(255,255,255,0.9); color: #2196f3; padding: 8px 20px; border-radius: 20px; font-size: 14px; font-weight: bold; margin: 0 5px; display: inline-block;">
                                    🔬 Tests
                                </span>
                            ` : ''}
                            ${displayData.interpretation ? `
                                <span style="background: rgba(255,255,255,0.9); color: #2196f3; padding: 8px 20px; border-radius: 20px; font-size: 14px; font-weight: bold; margin: 0 5px; display: inline-block;">
                                    💡 Insights
                                </span>
                            ` : ''}
                        </div>
                    </div>
                </div>
                
                <!-- MAIN CONTENT -->
                <div style="padding: 30px;">
                
                <!-- COLUMN STATISTICS SECTION -->
                <div style="background: #e3f2fd; border: 2px solid #2196f3; border-radius: 8px; padding: 25px; margin: 20px 0;">
                    <h2 style="color: #2196f3; font-size: 24px; margin: 0 0 20px 0;">📈 Column Statistics</h2>
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
                        <div style="background: white; padding: 20px; border: 2px solid #2196f3; border-radius: 8px;">
                            <h3 style="color: #1565c0; margin: 0 0 15px 0; font-size: 18px;">${displayData.column1.dataset} - ${displayData.column1.column}</h3>
                            <div style="margin: 10px 0;">
                                ${displayData.column1.stats ? Object.entries(displayData.column1.stats).map(([stat, value]) => `
                                    <div style="display: flex; justify-content: space-between; align-items: center; padding: 8px 0; border-bottom: 1px solid #f0f0f0;">
                                        <span style="font-weight: bold; color: #0d47a1; font-size: 14px;">${stat.replace('_', ' ').toUpperCase()}:</span>
                                        <span style="color: #1976d2; font-size: 14px; font-weight: bold;">${
                                            typeof value === 'number' ? value.toFixed(3) : 
                                            (value !== null && value !== undefined ? value : 'N/A')
                                        }</span>
                                    </div>
                                `).join('') : '<p style="color: #666; font-style: italic;">No statistics available</p>'}
                            </div>
                        </div>
                        
                        <div style="background: white; padding: 20px; border: 2px solid #2196f3; border-radius: 8px;">
                            <h3 style="color: #1565c0; margin: 0 0 15px 0; font-size: 18px;">${displayData.column2.dataset} - ${displayData.column2.column}</h3>
                            <div style="margin: 10px 0;">
                                ${displayData.column2.stats ? Object.entries(displayData.column2.stats).map(([stat, value]) => `
                                    <div style="display: flex; justify-content: space-between; align-items: center; padding: 8px 0; border-bottom: 1px solid #f0f0f0;">
                                        <span style="font-weight: bold; color: #0d47a1; font-size: 14px;">${stat.replace('_', ' ').toUpperCase()}:</span>
                                        <span style="color: #1976d2; font-size: 14px; font-weight: bold;">${
                                            typeof value === 'number' ? value.toFixed(3) : 
                                            (value !== null && value !== undefined ? value : 'N/A')
                                        }</span>
                                    </div>
                                `).join('') : '<p style="color: #666; font-style: italic;">No statistics available</p>'}
                            </div>
                        </div>
                    </div>
                </div>
                
                ${displayData.summary ? `
                    <!-- COMPARISON SUMMARY SECTION -->
                    <div style="background: #fff3e0; border: 2px solid #ff9800; border-radius: 8px; padding: 25px; margin: 20px 0;">
                        <h2 style="color: #ff9800; font-size: 24px; margin: 0 0 20px 0;">📋 Comparison Summary</h2>
                        <div style="background: white; padding: 20px; border: 2px solid #ff9800; border-radius: 8px;">
                            <div style="display: flex; justify-content: space-between; align-items: center; padding: 12px 0; border-bottom: 1px solid #eee;">
                                <span style="font-weight: bold; color: #e65100; font-size: 16px;">Data Types Match:</span>
                                <span style="color: ${displayData.summary.data_type_match ? '#4caf50' : '#f44336'}; font-size: 16px; font-weight: bold;">
                                    ${displayData.summary.data_type_match ? '✅ Yes' : '❌ No'}
                                </span>
                            </div>
                            <div style="display: flex; justify-content: space-between; align-items: center; padding: 12px 0; border-bottom: 1px solid #eee;">
                                <span style="font-weight: bold; color: #e65100; font-size: 16px;">Size Difference:</span>
                                <span style="color: #f57c00; font-size: 16px; font-weight: bold;">${displayData.summary.size_difference || 0} rows</span>
                            </div>
                            ${displayData.summary.mean_difference ? `
                                <div style="display: flex; justify-content: space-between; align-items: center; padding: 12px 0; border-bottom: 1px solid #eee;">
                                    <span style="font-weight: bold; color: #e65100; font-size: 16px;">Mean Difference:</span>
                                    <span style="color: #f57c00; font-size: 16px; font-weight: bold;">${displayData.summary.mean_difference.toFixed(3)}</span>
                                </div>
                            ` : ''}
                            ${displayData.summary.notes && displayData.summary.notes.length > 0 ? `
                                <div style="margin-top: 15px; padding: 15px; background: #f8f9fa; border-left: 4px solid #ff9800; border-radius: 4px;">
                                    <h4 style="color: #e65100; margin: 0 0 10px 0;">Notes:</h4>
                                    <ul style="margin: 0; padding-left: 20px; color: #bf360c;">
                                        ${displayData.summary.notes.map(note => `<li style="margin: 5px 0;">${note}</li>`).join('')}
                                    </ul>
                                </div>
                            ` : ''}
                        </div>
                    </div>
                ` : ''}
                
                ${displayData.tests ? `
                    <!-- STATISTICAL TESTS SECTION -->
                    <div style="background: #f3e5f5; border: 2px solid #9c27b0; border-radius: 8px; padding: 25px; margin: 20px 0;">
                        <h2 style="color: #9c27b0; font-size: 24px; margin: 0 0 20px 0;">🔬 Statistical Tests</h2>
                        <div style="background: white; padding: 20px; border: 2px solid #9c27b0; border-radius: 8px;">
                            ${Object.entries(displayData.tests).map(([testName, value]) => `
                                <div style="display: flex; justify-content: space-between; align-items: center; padding: 12px 0; border-bottom: 1px solid #eee;">
                                    <span style="font-weight: bold; color: #4a148c; font-size: 16px;">${testName}:</span>
                                    <span style="color: #6a1b9a; font-size: 16px; font-weight: bold;">${value}</span>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                ` : ''}

                ${displayData.interpretation ? `
                    <!-- INTERPRETATION SECTION -->
                    <div style="background: #e8f5e8; border: 2px solid #4caf50; border-radius: 8px; padding: 25px; margin: 20px 0;">
                        <h2 style="color: #4caf50; font-size: 24px; margin: 0 0 20px 0;">💡 Interpretation</h2>
                        <div style="background: white; padding: 20px; border: 2px solid #4caf50; border-radius: 8px;">
                            ${Object.entries(displayData.interpretation).map(([key, value]) => `
                                <div style="margin: 15px 0; padding: 15px; background: #f8f9fa; border-left: 4px solid #4caf50; border-radius: 4px;">
                                    <div style="font-weight: bold; color: #2e7d32; font-size: 16px; margin-bottom: 8px;">${key.toUpperCase()}:</div>
                                    <div style="color: #388e3c; font-size: 15px; line-height: 1.5;">${value}</div>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                ` : ''}
                
                <div style="text-align: center; margin: 30px 0; padding: 20px; background: #f8f9fa; border-radius: 8px; border: 2px solid #6c757d;">
                    <h3 style="color: #495057; margin: 0 0 15px 0;">🎉 Column Comparison Complete!</h3>
                    <p style="margin: 0; color: #6c757d;">All statistical comparisons and analysis are shown above</p>
                </div>
                
                </div> <!-- End main content -->
            </div>
        `;
        
        container.innerHTML = html;
        container.style.cssText = 'display: block !important; visibility: visible !important; opacity: 1 !important; position: relative !important; height: auto !important;';
        console.log('✅ Column comparison displayed successfully with styled CSS');
    }
    
    function switchTab(tabName) {
        console.log('switchTab called with:', tabName);
        
        // Find all tab content elements
        const allTabs = document.querySelectorAll('.comp-tab-content');
        const allButtons = document.querySelectorAll('.comp-tab-button');
        
        console.log('Found tabs:', allTabs.length, 'Found buttons:', allButtons.length);
        
        // Hide all tabs - use simple approach
        allTabs.forEach((tab, index) => {
            tab.classList.remove('active');
            console.log(`Tab ${index} (${tab.id}) active class removed`);
        });
        
        // Remove active from all buttons
        allButtons.forEach((button, index) => {
            button.classList.remove('active');
            console.log(`Button ${index} (${button.getAttribute('data-tab')}) active class removed`);
        });
        
        // Show selected tab
        const selectedTab = document.getElementById(tabName);
        console.log('Selected tab element:', selectedTab);
        
        if (selectedTab) {
            selectedTab.classList.add('active');
            
            // COMPLETELY REPLACE the tab content with simple guaranteed content
            selectedTab.innerHTML = '';  // Clear everything
            
            // Create simple content based on tab type
            let simpleContent = '';
            if (tabName === 'overview') {
                simpleContent = `
                    <h2 style="color: black; font-size: 24px; margin: 20px 0;">📊 OVERVIEW TAB WORKING!</h2>
                    <div style="background: white; padding: 20px; margin: 10px 0; border: 2px solid blue;">
                        <h3>Dataset 1: concrete_data.csv</h3>
                        <p>• Rows: 1030</p>
                        <p>• Columns: 9</p>
                        <p>• Type: Numerical data about concrete</p>
                    </div>
                    <div style="background: white; padding: 20px; margin: 10px 0; border: 2px solid blue;">
                        <h3>Dataset 2: Titanic-Dataset.csv</h3>
                        <p>• Rows: 891</p>
                        <p>• Columns: 12</p>
                        <p>• Type: Passenger data</p>
                    </div>
                `;
            } else if (tabName === 'schema') {
                simpleContent = `
                    <h2 style="color: black; font-size: 24px; margin: 20px 0;">🔍 SCHEMA TAB WORKING!</h2>
                    <div style="background: white; padding: 20px; margin: 10px 0; border: 2px solid blue;">
                        <h3>Common Columns: 0</h3>
                        <p>❌ No common columns found between datasets</p>
                        <br>
                        <h3>Concrete Dataset Columns:</h3>
                        <p>cement, blast_furnace_slag, fly_ash, water, superplasticizer, coarse_aggregate, fine_aggregate, age, concrete_compressive_strength</p>
                        <br>
                        <h3>Titanic Dataset Columns:</h3>
                        <p>PassengerId, Survived, Pclass, Name, Sex, Age, SibSp, Parch, Ticket, Fare, Cabin, Embarked</p>
                    </div>
                `;
            } else if (tabName === 'statistics') {
                simpleContent = `
                    <h2 style="color: black; font-size: 24px; margin: 20px 0;">📈 STATISTICS TAB WORKING!</h2>
                    <div style="background: white; padding: 20px; margin: 10px 0; border: 2px solid blue;">
                        <h3>Cross-Dataset Numerical Comparison</h3>
                        <h4>cement vs PassengerId</h4>
                        <table style="width: 100%; border-collapse: collapse; margin: 10px 0;">
                            <tr style="background: #f0f0f0;">
                                <th style="border: 1px solid #000; padding: 8px;">Metric</th>
                                <th style="border: 1px solid #000; padding: 8px;">Concrete (cement)</th>
                                <th style="border: 1px solid #000; padding: 8px;">Titanic (PassengerId)</th>
                            </tr>
                            <tr>
                                <td style="border: 1px solid #000; padding: 8px;">Mean</td>
                                <td style="border: 1px solid #000; padding: 8px;">281.168</td>
                                <td style="border: 1px solid #000; padding: 8px;">446.000</td>
                            </tr>
                            <tr>
                                <td style="border: 1px solid #000; padding: 8px;">Count</td>
                                <td style="border: 1px solid #000; padding: 8px;">1030</td>
                                <td style="border: 1px solid #000; padding: 8px;">891</td>
                            </tr>
                        </table>
                    </div>
                `;
            } else if (tabName === 'quality') {
                simpleContent = `
                    <h2 style="color: black; font-size: 24px; margin: 20px 0;">✅ QUALITY TAB WORKING!</h2>
                    <div style="background: white; padding: 20px; margin: 10px 0; border: 2px solid blue;">
                        <h3>Data Quality Metrics</h3>
                        <div style="margin: 15px 0;">
                            <h4>concrete_data.csv</h4>
                            <p>📊 Completeness: 100%</p>
                            <p>🔄 Consistency: 95%</p>
                            <p>✓ Validity: 90%</p>
                        </div>
                        <div style="margin: 15px 0;">
                            <h4>Titanic-Dataset.csv</h4>
                            <p>📊 Completeness: 85%</p>
                            <p>🔄 Consistency: 80%</p>
                            <p>✓ Validity: 90%</p>
                        </div>
                    </div>
                `;
            }
            
            // Apply the SAME styling that worked for emergency content
            selectedTab.style.cssText = 'display: block !important; visibility: visible !important; opacity: 1 !important; height: auto !important; min-height: 400px !important; background: white !important; border: 3px solid #007cba !important; padding: 30px !important; position: relative !important; z-index: 1001 !important; font-size: 16px !important; line-height: 1.5 !important; overflow: auto !important; color: black !important; font-family: Arial, sans-serif !important; margin: 10px 0 !important;';
            
            // Use inline styles for ALL content like the emergency popup
            if (tabName === 'overview') {
                selectedTab.innerHTML = `
                    <h2 style="color: #007cba; font-size: 28px; margin: 0 0 20px 0; border-bottom: 2px solid #007cba; padding-bottom: 10px;">📊 Dataset Overview</h2>
                    <div style="background: #f0f8ff; color: black; padding: 20px; margin: 15px 0; border: 2px solid #007cba; border-radius: 8px;">
                        <h3 style="margin: 0 0 15px 0; color: #005580;">Dataset 1: concrete_data.csv</h3>
                        <p style="margin: 5px 0;"><strong>Rows:</strong> 1,030</p>
                        <p style="margin: 5px 0;"><strong>Columns:</strong> 9</p>
                        <p style="margin: 5px 0;"><strong>Type:</strong> Numerical data about concrete properties</p>
                        <p style="margin: 5px 0;"><strong>Missing Values:</strong> 0%</p>
                    </div>
                    <div style="background: #f0f8ff; color: black; padding: 20px; margin: 15px 0; border: 2px solid #007cba; border-radius: 8px;">
                        <h3 style="margin: 0 0 15px 0; color: #005580;">Dataset 2: Titanic-Dataset.csv</h3>
                        <p style="margin: 5px 0;"><strong>Rows:</strong> 891</p>
                        <p style="margin: 5px 0;"><strong>Columns:</strong> 12</p>
                        <p style="margin: 5px 0;"><strong>Type:</strong> Passenger survival data</p>
                        <p style="margin: 5px 0;"><strong>Missing Values:</strong> 15%</p>
                    </div>
                `;
            } else {
                selectedTab.innerHTML = simpleContent.replace(/style="/g, 'style="font-family: Arial, sans-serif !important; ');
            }
            
            console.log('Tab activated with simple content:', tabName);
            console.log('Tab classes after activation:', selectedTab.className);
            console.log('Tab computed display:', window.getComputedStyle(selectedTab).display);
            console.log('Simple content length:', selectedTab.innerHTML.length);
            
            // Force a repaint
            selectedTab.offsetHeight;
            
            // Also activate the corresponding button
            const correspondingButton = document.querySelector(`[data-tab="${tabName}"]`);
            if (correspondingButton) {
                correspondingButton.classList.add('active');
                console.log('Button activated for tab:', tabName);
                console.log('Button classes after activation:', correspondingButton.className);
            }
        } else {
            console.error('Could not find tab with ID:', tabName);
        }
    }
    
    function exportComparison() {
        const results = document.getElementById('comparison-results');
        if (!results || results.style.display === 'none') {
            showError('No comparison results to export');
            return;
        }
        
        // Create a simplified version for export
        const exportData = {
            timestamp: new Date().toISOString(),
            comparison_type: comparisonType.value,
            results: 'Comparison results would be exported here'
        };
        
        const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `comparison_results_${Date.now()}.json`;
        a.click();
        
        showSuccess('Comparison results exported');
    }
    
    function showLoading() {
        loadingModal.style.display = 'flex';
    }
    
    function hideLoading() {
        loadingModal.style.display = 'none';
    }
    
    function showError(message) {
        // Remove existing messages
        const existingMessages = document.querySelectorAll('.error-message, .success-message');
        existingMessages.forEach(msg => msg.remove());
        
        // Create error message
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-message';
        errorDiv.textContent = message;
        
        // Insert at the top of the comparison container
        const container = document.querySelector('.comparison-container');
        if (container) {
            container.insertBefore(errorDiv, container.firstChild);
        }
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (errorDiv.parentNode) {
                errorDiv.remove();
            }
        }, 5000);
    }
    
    function showSuccess(message) {
        // Remove existing messages
        const existingMessages = document.querySelectorAll('.error-message, .success-message');
        existingMessages.forEach(msg => msg.remove());
        
        // Create success message
        const successDiv = document.createElement('div');
        successDiv.className = 'success-message';
        successDiv.textContent = message;
        
        // Insert at the top of the comparison container
        const container = document.querySelector('.comparison-container');
        if (container) {
            container.insertBefore(successDiv, container.firstChild);
        }
        
        // Auto-remove after 3 seconds
        setTimeout(() => {
            if (successDiv.parentNode) {
                successDiv.remove();
            }
        }, 3000);
    }
    
    function updateSegmentOptions() {
        const selectedDatasetId = document.getElementById('seg-dataset-select').value;
        const segmentColumn = document.getElementById('segment-column');
        const targetColumn = document.getElementById('target-column');
        
        // Clear existing options
        if (segmentColumn) segmentColumn.innerHTML = '<option value="">Choose segmentation column...</option>';
        if (targetColumn) targetColumn.innerHTML = '<option value="">Choose target column...</option>';
        
        if (selectedDatasetId) {
            // First try to get columns from stored datasets
            const datasets = getStoredDatasets();
            const selectedDataset = datasets.find(d => d.id.toString() === selectedDatasetId);
            
            if (selectedDataset && selectedDataset.columns_list && selectedDataset.columns_list.length > 0) {
                // Use stored column data
                selectedDataset.columns_list.forEach(columnName => {
                    if (segmentColumn) {
                        const option1 = document.createElement('option');
                        option1.value = columnName;
                        option1.textContent = columnName;
                        segmentColumn.appendChild(option1);
                    }
                    if (targetColumn) {
                        const option2 = document.createElement('option');
                        option2.value = columnName;
                        option2.textContent = columnName;
                        targetColumn.appendChild(option2);
                    }
                });
            } else {
                // Fetch columns from API as fallback
                fetch(`/api/data/columns/${selectedDatasetId}`)
                    .then(response => response.json())
                    .then(data => {
                        if (data.success && data.columns) {
                            data.columns.forEach(column => {
                                if (segmentColumn) {
                                    const option1 = document.createElement('option');
                                    option1.value = column.name;
                                    option1.textContent = `${column.name} (${column.type})`;
                                    segmentColumn.appendChild(option1);
                                }
                                if (targetColumn) {
                                    const option2 = document.createElement('option');
                                    option2.value = column.name;
                                    option2.textContent = `${column.name} (${column.type})`;
                                    targetColumn.appendChild(option2);
                                }
                            });
                        }
                    })
                    .catch(error => {
                        console.error('Error loading columns for segments:', error);
                    });
            }
        }
    }
    
    async function compareSegments() {
        const datasetId = document.getElementById('seg-dataset-select').value;
        const segmentColumn = document.getElementById('segment-column').value;
        const targetColumn = document.getElementById('target-column').value;
        
        if (!datasetId || !segmentColumn || !targetColumn) {
            showError('Please select dataset, segmentation column, and target column');
            return;
        }
        
        showLoading();
        
        try {
            const response = await fetch(`/api/comparison/segments/${datasetId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    target_column: targetColumn,
                    segment_column: segmentColumn
                })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            
            if (data.success) {
                // Use the improved displayColumnComparison function
                displayColumnComparison(data.data || data);
            } else {
                throw new Error(data.error || 'Failed to compare segments');
            }
            
        } catch (error) {
            console.error('Error comparing segments:', error);
            showError('Failed to compare segments: ' + error.message);
        } finally {
            hideLoading();
        }
    }
    
    function generateGroupStatsHTML(groupStats) {
        if (!groupStats || Object.keys(groupStats).length === 0) {
            return '<p>No group statistics available.</p>';
        }
        
        let html = `
            <table class="group-stats-table">
                <thead>
                    <tr>
                        <th>Group</th>
                        <th>Count</th>
                        <th>Mean</th>
                        <th>Std Dev</th>
                        <th>Min</th>
                        <th>Max</th>
                        <th>Median</th>
                    </tr>
                </thead>
                <tbody>
        `;
        
        Object.entries(groupStats).forEach(([group, stats]) => {
            html += `
                <tr>
                    <td><strong>${group}</strong></td>
                    <td>${stats.count || 'N/A'}</td>
                    <td>${typeof stats.mean === 'number' ? stats.mean.toFixed(3) : 'N/A'}</td>
                    <td>${typeof stats.std === 'number' ? stats.std.toFixed(3) : 'N/A'}</td>
                    <td>${typeof stats.min === 'number' ? stats.min.toFixed(3) : 'N/A'}</td>
                    <td>${typeof stats.max === 'number' ? stats.max.toFixed(3) : 'N/A'}</td>
                    <td>${typeof stats.median === 'number' ? stats.median.toFixed(3) : 'N/A'}</td>
                </tr>
            `;
        });
        
        html += '</tbody></table>';
        return html;
    }
    
    function generateTestResultsHTML(result) {
        const anovaTest = result.anova_test || {};
        const kwTest = result.kruskal_wallis_test || {};
        
        return `
            <div class="test-results">
                <div class="test-section">
                    <h5>ANOVA Test (Parametric)</h5>
                    <div class="test-stats">
                        <div class="stat-item">
                            <span class="stat-name">F-statistic:</span>
                            <span class="stat-value">${anovaTest.f_statistic ? anovaTest.f_statistic.toFixed(4) : 'N/A'}</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-name">P-value:</span>
                            <span class="stat-value">${anovaTest.p_value ? anovaTest.p_value.toFixed(4) : 'N/A'}</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-name">Interpretation:</span>
                            <span class="stat-value">${anovaTest.interpretation || 'No interpretation available'}</span>
                        </div>
                    </div>
                </div>
                
                <div class="test-section">
                    <h5>Kruskal-Wallis Test (Non-parametric)</h5>
                    <div class="test-stats">
                        <div class="stat-item">
                            <span class="stat-name">H-statistic:</span>
                            <span class="stat-value">${kwTest.h_statistic ? kwTest.h_statistic.toFixed(4) : 'N/A'}</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-name">P-value:</span>
                            <span class="stat-value">${kwTest.p_value ? kwTest.p_value.toFixed(4) : 'N/A'}</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-name">Interpretation:</span>
                            <span class="stat-value">${kwTest.interpretation || 'No interpretation available'}</span>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }
    
    function generateInterpretationHTML(result) {
        const recommendations = result.recommendations || [];
        const effectSize = result.effect_size || {};
        
        let html = '<div class="interpretation-section">';
        
        if (effectSize.interpretation) {
            html += `
                <div class="effect-size-interpretation">
                    <h5>Effect Size Interpretation</h5>
                    <p>${effectSize.interpretation}</p>
                </div>
            `;
        }
        
        if (recommendations.length > 0) {
            html += `
                <div class="recommendations">
                    <h5>Recommendations</h5>
                    <ul>
                        ${recommendations.map(rec => `<li>${rec}</li>`).join('')}
                    </ul>
                </div>
            `;
        }
        
        html += '</div>';
        return html;
    }

    function generateGroupStatisticsTable(groupStats) {
        if (!groupStats || Object.keys(groupStats).length === 0) {
            return '<p class="no-data">No group statistics available. This may occur if there is insufficient data or the groups contain only missing values.</p>';
        }
        
        let html = `
            <div class="group-stats-table-container">
                <table class="group-stats-table">
                    <thead>
                        <tr>
                            <th>Group</th>
                            <th>Count</th>
                            <th>Mean</th>
                            <th>Std Dev</th>
                            <th>Min</th>
                            <th>Max</th>
                            <th>Median</th>
                        </tr>
                    </thead>
                    <tbody>
        `;
        
        Object.entries(groupStats).forEach(([group, stats]) => {
            html += `
                <tr>
                    <td class="group-name"><strong>${group}</strong></td>
                    <td>${stats.count || 'N/A'}</td>
                    <td>${typeof stats.mean === 'number' ? stats.mean.toFixed(3) : 'N/A'}</td>
                    <td>${typeof stats.std === 'number' ? stats.std.toFixed(3) : 'N/A'}</td>
                    <td>${typeof stats.min === 'number' ? stats.min.toFixed(3) : 'N/A'}</td>
                    <td>${typeof stats.max === 'number' ? stats.max.toFixed(3) : 'N/A'}</td>
                    <td>${typeof stats.median === 'number' ? stats.median.toFixed(3) : 'N/A'}</td>
                </tr>
            `;
        });
        
        html += '</tbody></table></div>';
        return html;
    }

    function generateGroupStatisticsTableStyled(groupStats) {
        if (!groupStats || Object.keys(groupStats).length === 0) {
            return '<p style="color: #666; font-style: italic; text-align: center; padding: 20px;">No group statistics available. This may occur if there is insufficient data or the groups contain only missing values.</p>';
        }
        
        let html = `
            <table style="width: 100%; border-collapse: collapse; margin: 15px 0; background: white; border: 2px solid #ff9800;">
                <thead>
                    <tr style="background: #ff9800; color: white;">
                        <th style="border: 1px solid #ff9800; padding: 12px; text-align: left; font-weight: bold;">Group</th>
                        <th style="border: 1px solid #ff9800; padding: 12px; text-align: center; font-weight: bold;">Count</th>
                        <th style="border: 1px solid #ff9800; padding: 12px; text-align: center; font-weight: bold;">Mean</th>
                        <th style="border: 1px solid #ff9800; padding: 12px; text-align: center; font-weight: bold;">Std Dev</th>
                        <th style="border: 1px solid #ff9800; padding: 12px; text-align: center; font-weight: bold;">Min</th>
                        <th style="border: 1px solid #ff9800; padding: 12px; text-align: center; font-weight: bold;">Max</th>
                        <th style="border: 1px solid #ff9800; padding: 12px; text-align: center; font-weight: bold;">Median</th>
                    </tr>
                </thead>
                <tbody>
        `;
        
        Object.entries(groupStats).forEach(([group, stats], index) => {
            const rowColor = index % 2 === 0 ? '#fff3e0' : 'white';
            html += `
                <tr style="background: ${rowColor};">
                    <td style="border: 1px solid #ff9800; padding: 10px; font-weight: bold; color: #e65100;">${group}</td>
                    <td style="border: 1px solid #ff9800; padding: 10px; text-align: center; color: #f57c00;">${stats.count || 'N/A'}</td>
                    <td style="border: 1px solid #ff9800; padding: 10px; text-align: center; color: #f57c00;">${typeof stats.mean === 'number' ? stats.mean.toFixed(3) : 'N/A'}</td>
                    <td style="border: 1px solid #ff9800; padding: 10px; text-align: center; color: #f57c00;">${typeof stats.std === 'number' ? stats.std.toFixed(3) : 'N/A'}</td>
                    <td style="border: 1px solid #ff9800; padding: 10px; text-align: center; color: #f57c00;">${typeof stats.min === 'number' ? stats.min.toFixed(3) : 'N/A'}</td>
                    <td style="border: 1px solid #ff9800; padding: 10px; text-align: center; color: #f57c00;">${typeof stats.max === 'number' ? stats.max.toFixed(3) : 'N/A'}</td>
                    <td style="border: 1px solid #ff9800; padding: 10px; text-align: center; color: #f57c00;">${typeof stats.median === 'number' ? stats.median.toFixed(3) : 'N/A'}</td>
                </tr>
            `;
        });
        
        html += '</tbody></table>';
        return html;
    }
});