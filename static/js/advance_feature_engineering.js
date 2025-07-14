console.log('Advanced Feature Engineering JavaScript loaded!');

document.addEventListener('DOMContentLoaded', function() {
    // Global variables
    let currentDatasetId = null;
    let currentFeatures = [];
    let engineeredFeatures = [];
    
    // DOM Elements
    const datasetSelect = document.getElementById('adv-fe-dataset-select');
    const refreshButton = document.getElementById('refresh-adv-fe-datasets');
    const engineeringSections = document.getElementById('fe-workspace');
    const loadingModal = document.getElementById('adv-fe-loading-modal');
    
    // Initialize
    console.log('ADV: Initializing advanced feature engineering...');
    console.log('ADV: Dataset select element:', datasetSelect);
    console.log('ADV: Refresh button:', refreshButton);
    console.log('ADV: Engineering sections:', engineeringSections);
    
    loadDatasets();
    setupEventListeners();
    
    function setupEventListeners() {
        if (refreshButton) {
            refreshButton.addEventListener('click', loadDatasets);
        }
        if (datasetSelect) {
            datasetSelect.addEventListener('change', handleDatasetSelection);
        }
        
        // Engineering technique buttons with null checks
        const polyBtn = document.getElementById('apply-polynomial-features');
        if (polyBtn) polyBtn.addEventListener('click', applyPolynomialFeatures);
        
        const interactionBtn = document.getElementById('apply-interaction-features');
        if (interactionBtn) interactionBtn.addEventListener('click', applyInteractionFeatures);
        
        const selectionBtn = document.getElementById('apply-feature-selection');
        if (selectionBtn) selectionBtn.addEventListener('click', applyFeatureSelection);
        
        const reductionBtn = document.getElementById('apply-dimensionality-reduction');
        if (reductionBtn) reductionBtn.addEventListener('click', applyDimensionalityReduction);
        
        const timeBtn = document.getElementById('apply-time-features');
        if (timeBtn) timeBtn.addEventListener('click', applyTimeFeatures);
        
        const textBtn = document.getElementById('apply-text-features');
        if (textBtn) textBtn.addEventListener('click', applyTextFeatures);
        
        const clusterBtn = document.getElementById('apply-clustering-features');
        if (clusterBtn) clusterBtn.addEventListener('click', applyClusteringFeatures);
        
        const customBtn = document.getElementById('apply-custom-transformations');
        if (customBtn) customBtn.addEventListener('click', applyCustomTransformations);
        
        // Feature management buttons
        const saveBtn = document.getElementById('save-features');
        if (saveBtn) saveBtn.addEventListener('click', saveFeatures);
        
        const exportBtn = document.getElementById('export-features');
        if (exportBtn) exportBtn.addEventListener('click', exportFeatures);
        
        const resetBtn = document.getElementById('reset-features');
        if (resetBtn) resetBtn.addEventListener('click', resetFeatures);
        
        // Tab switching for sub-techniques
        const tabButtons = document.querySelectorAll('.subtab-button');
        tabButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                const parent = e.target.closest('[data-parent]');
                const parentId = parent.getAttribute('data-parent');
                const tabId = e.target.getAttribute('data-subtab');
                switchSubTab(parentId, tabId);
            });
        });
    }
    
    async function loadDatasets() {
        try {
            console.log('ADV: Loading datasets...');
            
            // Fetch real datasets from the API
            const response = await fetch('/api/data/datasets');
            console.log('ADV: Response status:', response.status);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            console.log('ADV: Received data:', data);
            
            datasetSelect.innerHTML = '<option value="">Choose a dataset...</option>';
            
            if (data.success && data.datasets) {
                console.log('ADV: Found datasets:', data.datasets.length);
                data.datasets.forEach(dataset => {
                    const option = document.createElement('option');
                    option.value = dataset.id;
                    option.textContent = `${dataset.name} (${dataset.rows} rows, ${dataset.columns} cols)`;
                    datasetSelect.appendChild(option);
                });
            } else {
                console.log('ADV: No datasets available or error:', data.error);
                showError('No datasets found. Please upload a dataset first.');
            }
            
        } catch (error) {
            console.error('ADV: Error loading datasets:', error);
            showError('Failed to load datasets: ' + error.message);
        }
    }
    
    async function handleDatasetSelection() {
        const selectedId = datasetSelect.value;
        
        if (!selectedId) {
            engineeringSections.style.display = 'none';
            return;
        }
        
        currentDatasetId = selectedId;
        await loadDatasetFeatures(selectedId);
        engineeringSections.style.display = 'block';
    }
    
    async function loadDatasetFeatures(datasetId) {
        showLoading();
        
        try {
            // Fetch real features from the API
            const response = await fetch(`/api/data/columns/${datasetId}`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            
            if (data.success && data.columns) {
                // Transform the column data into feature format
                const features = data.columns.map(col => ({
                    name: col.name,
                    type: col.is_numeric ? 'numeric' : 
                          col.is_datetime ? 'datetime' : 
                          col.dtype === 'object' ? 'text' : 'categorical',
                    dtype: col.dtype,
                    null_count: col.null_count,
                    unique_count: col.unique_count,
                    is_numeric: col.is_numeric,
                    is_categorical: col.is_categorical,
                    is_datetime: col.is_datetime
                }));
                
                currentFeatures = features;
                populateFeatureSelectors(features);
                updateFeaturesList();
            } else {
                throw new Error(data.error || 'Failed to load features');
            }
            
        } catch (error) {
            console.error('Error loading features:', error);
            showError('Failed to load dataset features: ' + error.message);
        } finally {
            hideLoading();
        }
    }
    
    function populateFeatureSelectors(features) {
        const numericFeatures = features.filter(f => f.type === 'numeric');
        const categoricalFeatures = features.filter(f => f.type === 'categorical');
        const textFeatures = features.filter(f => f.type === 'text');
        const datetimeFeatures = features.filter(f => f.type === 'datetime');
        
        // Populate various feature selectors
        populateSelect('polynomial-features-select', numericFeatures);
        populateSelect('interaction-features-select', numericFeatures);
        populateSelect('selection-features-target', numericFeatures);
        populateSelect('pca-features-select', numericFeatures);
        populateSelect('time-features-select', datetimeFeatures);
        populateSelect('text-features-select', textFeatures);
        populateSelect('clustering-features-select', numericFeatures);
        
        // Multi-select for various techniques
        populateMultiSelect('fs-features-list', features);
        populateMultiSelect('dr-features-list', numericFeatures);
        populateMultiSelect('cluster-features-list', numericFeatures);
    }
    
    function populateSelect(selectId, features) {
        const select = document.getElementById(selectId);
        if (!select) return;
        
        select.innerHTML = '<option value="">Select feature...</option>';
        features.forEach(feature => {
            const option = document.createElement('option');
            option.value = feature.name;
            option.textContent = feature.name;
            select.appendChild(option);
        });
    }
    
    function populateMultiSelect(containerId, features) {
        const container = document.getElementById(containerId);
        if (!container) return;
        
        container.innerHTML = '';
        features.forEach(feature => {
            const checkbox = document.createElement('div');
            checkbox.className = 'feature-checkbox';
            checkbox.innerHTML = `
                <input type="checkbox" id="feature_${feature.name}" value="${feature.name}">
                <label for="feature_${feature.name}">${feature.name} (${feature.type})</label>
            `;
            container.appendChild(checkbox);
        });
    }
    
    async function applyPolynomialFeatures() {
        const selectedFeature = document.getElementById('polynomial-features-select').value;
        const degree = document.getElementById('polynomial-degree').value || 2;
        
        if (!selectedFeature) {
            showError('Please select a feature for polynomial transformation');
            return;
        }
        
        showLoading();
        
        try {
            const response = await fetch(`/api/feature/polynomial/${currentDatasetId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    columns: [selectedFeature],
                    degree: degree
                })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const result = await response.json();
            
            if (result.success) {
                // Add new features to the list
                const newFeatures = result.new_columns || [];
                newFeatures.forEach(featureName => {
                    const newFeature = {
                        name: featureName,
                        type: 'numeric',
                        engineered: true,
                        source: `Polynomial degree ${degree} of ${selectedFeature}`
                    };
                    engineeredFeatures.push(newFeature);
                });
                
                updateFeaturesList();
                showSuccess(`Polynomial features of degree ${degree} created for ${selectedFeature}`);
            } else {
                throw new Error(result.error || 'Failed to create polynomial features');
            }
            
        } catch (error) {
            console.error('Error creating polynomial features:', error);
            showError('Failed to create polynomial features: ' + error.message);
        } finally {
            hideLoading();
        }
    }
    
    async function applyInteractionFeatures() {
        const selectedFeatures = getSelectedCheckboxes('interaction-features-list');
        
        if (selectedFeatures.length < 2) {
            showError('Please select at least 2 features for interaction');
            return;
        }
        
        showLoading();
        
        try {
            const response = await fetch(`/api/feature/interactions/${currentDatasetId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    columns: selectedFeatures
                })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const result = await response.json();
            
            if (result.success) {
                // Add new features to the list
                const newFeatures = result.new_columns || [];
                newFeatures.forEach(featureName => {
                    const newFeature = {
                        name: featureName,
                        type: 'numeric',
                        engineered: true,
                        source: `Interaction feature from ${selectedFeatures.length} features`
                    };
                    engineeredFeatures.push(newFeature);
                });
                
                updateFeaturesList();
                showSuccess(`Interaction features created for ${selectedFeatures.length} features`);
            } else {
                throw new Error(result.error || 'Failed to create interaction features');
            }
            
        } catch (error) {
            console.error('Error creating interaction features:', error);
            showError('Failed to create interaction features: ' + error.message);
        } finally {
            hideLoading();
        }
    }
    
    async function applyFeatureSelection() {
        const targetColumn = document.getElementById('selection-features-target').value;
        const method = document.getElementById('fs-method').value;
        const kValue = document.getElementById('fs-k-value').value || 5;
        
        if (!targetColumn) {
            showError('Please select a target column for feature selection');
            return;
        }
        
        showLoading();
        
        try {
            const response = await fetch(`/api/advance-feature/feature-selection/${currentDatasetId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    target_column: targetColumn,
                    method: method,
                    k: parseInt(kValue)
                })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const result = await response.json();
            
            if (result.success) {
                const results = result.results;
                
                document.getElementById('fs-results').innerHTML = `
                    <div class="selection-results">
                        <h5>Feature Selection Results (${method})</h5>
                        <p>Selected ${results.n_features_selected} features out of ${results.total_features}:</p>
                        <ul>
                            ${results.selected_features.map(feature => {
                                const score = results.feature_scores[feature] || 0;
                                return `<li>${feature} (Score: ${score.toFixed(3)})</li>`;
                            }).join('')}
                        </ul>
                        <p><strong>Target:</strong> ${results.target_column}</p>
                        <p><strong>Method:</strong> ${results.method}</p>
                    </div>
                `;
                
                showSuccess(`Feature selection completed using ${method}`);
            } else {
                throw new Error(result.error || 'Feature selection failed');
            }
            
        } catch (error) {
            console.error('Error in feature selection:', error);
            showError('Failed to perform feature selection: ' + error.message);
        } finally {
            hideLoading();
        }
    }
    
    async function applyDimensionalityReduction() {
        const selectedFeatures = getSelectedCheckboxes('dr-features-list');
        const method = document.getElementById('dr-method').value;
        const components = document.getElementById('dr-components').value || 2;
        
        if (selectedFeatures.length === 0) {
            showError('Please select features for dimensionality reduction');
            return;
        }
        
        showLoading();
        
        try {
            const response = await fetch(`/api/advance-feature/dimensionality-reduction/${currentDatasetId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    method: method,
                    n_components: parseInt(components),
                    columns: selectedFeatures
                })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const result = await response.json();
            
            if (result.success) {
                const results = result.results;
                
                // Add new features to the list
                results.component_names.forEach(componentName => {
                    const newFeature = {
                        name: componentName,
                        type: 'numeric',
                        engineered: true,
                        source: `${method} component from ${selectedFeatures.length} features`
                    };
                    engineeredFeatures.push(newFeature);
                });
                
                let explainedVarianceText = '';
                if (results.explained_variance) {
                    const totalVariance = results.cumulative_variance 
                        ? results.cumulative_variance[results.cumulative_variance.length - 1] 
                        : results.explained_variance.reduce((a, b) => a + b, 0);
                    explainedVarianceText = `<p>Explained variance: ${(totalVariance * 100).toFixed(1)}%</p>`;
                }
                
                document.getElementById('dr-results').innerHTML = `
                    <div class="reduction-results">
                        <h5>Dimensionality Reduction Results (${method.toUpperCase()})</h5>
                        <p>Reduced ${results.original_dimensions} features to ${results.n_components} components</p>
                        ${explainedVarianceText}
                        <p><strong>Components:</strong> ${results.component_names.join(', ')}</p>
                        <p><strong>Method:</strong> ${results.method}</p>
                    </div>
                `;
                
                updateFeaturesList();
                showSuccess(`Dimensionality reduction completed using ${method}`);
            } else {
                throw new Error(result.error || 'Dimensionality reduction failed');
            }
            
        } catch (error) {
            console.error('Error in dimensionality reduction:', error);
            showError('Failed to perform dimensionality reduction: ' + error.message);
        } finally {
            hideLoading();
        }
    }
    
    async function applyTimeFeatures() {
        const selectedFeature = document.getElementById('time-features-select').value;
        const timeFeatures = getSelectedCheckboxes('time-feature-types');
        
        if (!selectedFeature) {
            showError('Please select a datetime feature');
            return;
        }
        
        if (timeFeatures.length === 0) {
            showError('Please select time feature types to extract');
            return;
        }
        
        showLoading();
        
        try {
            const response = await fetch(`/api/advance-feature/time-features/${currentDatasetId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    column: selectedFeature,
                    features: timeFeatures
                })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const result = await response.json();
            
            if (result.success) {
                const results = result.results;
                
                // Add new features to the list
                results.feature_names.forEach(featureName => {
                    const newFeature = {
                        name: featureName,
                        type: 'numeric',
                        engineered: true,
                        source: `Time feature extracted from ${selectedFeature}`
                    };
                    engineeredFeatures.push(newFeature);
                });
                
                updateFeaturesList();
                showSuccess(`Extracted ${results.features_extracted} time features from ${selectedFeature}`);
            } else {
                throw new Error(result.error || 'Time feature extraction failed');
            }
            
        } catch (error) {
            console.error('Error in time feature extraction:', error);
            showError('Failed to extract time features: ' + error.message);
        } finally {
            hideLoading();
        }
    }
    
    async function applyTextFeatures() {
        const selectedFeature = document.getElementById('text-features-select').value;
        const textFeatures = getSelectedCheckboxes('text-feature-types');
        
        if (!selectedFeature) {
            showError('Please select a text feature');
            return;
        }
        
        if (textFeatures.length === 0) {
            showError('Please select text feature types to extract');
            return;
        }
        
        showLoading();
        
        try {
            const response = await fetch(`/api/advance-feature/text-features/${currentDatasetId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    column: selectedFeature,
                    features: textFeatures
                })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const result = await response.json();
            
            if (result.success) {
                const results = result.results;
                
                // Add new features to the list
                results.feature_names.forEach(featureName => {
                    const newFeature = {
                        name: featureName,
                        type: 'numeric',
                        engineered: true,
                        source: `Text feature extracted from ${selectedFeature}`
                    };
                    engineeredFeatures.push(newFeature);
                });
                
                updateFeaturesList();
                showSuccess(`Extracted ${results.features_extracted} text features from ${selectedFeature}`);
            } else {
                throw new Error(result.error || 'Text feature extraction failed');
            }
            
        } catch (error) {
            console.error('Error in text feature extraction:', error);
            showError('Failed to extract text features: ' + error.message);
        } finally {
            hideLoading();
        }
    }
    
    async function applyClusteringFeatures() {
        const selectedFeatures = getSelectedCheckboxes('cluster-features-list');
        const algorithm = document.getElementById('cluster-algorithm')?.value || 'kmeans';
        const kClusters = document.getElementById('cluster-k').value || 3;
        
        if (selectedFeatures.length === 0) {
            showError('Please select features for clustering');
            return;
        }
        
        showLoading();
        
        try {
            const response = await fetch(`/api/advance-feature/clustering/${currentDatasetId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    algorithm: algorithm,
                    n_clusters: parseInt(kClusters),
                    columns: selectedFeatures
                })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const result = await response.json();
            
            if (result.success) {
                const results = result.results;
                
                // Create cluster assignment feature
                const clusterFeatureName = `cluster_${algorithm}_${kClusters}`;
                
                const clusterFeature = {
                    name: clusterFeatureName,
                    type: 'categorical',
                    engineered: true,
                    source: `${algorithm} clustering (k=${kClusters}) on ${selectedFeatures.join(', ')}`
                };
                
                engineeredFeatures.push(clusterFeature);
                
                updateFeaturesList();
                showSuccess(`Clustering completed: ${results.n_clusters} clusters found using ${algorithm}`);
            } else {
                throw new Error(result.error || 'Clustering failed');
            }
            
        } catch (error) {
            console.error('Error in clustering:', error);
            showError('Failed to perform clustering: ' + error.message);
        } finally {
            hideLoading();
        }
    }
    
    async function applyCustomTransformations() {
        const transformationType = document.getElementById('custom-transformation').value;
        const targetFeature = document.getElementById('custom-target-feature').value;
        
        if (!targetFeature) {
            showError('Please select a target feature for transformation');
            return;
        }
        
        showLoading();
        
        try {
            let apiEndpoint;
            let requestBody;
            
            // Map transformation types to appropriate APIs
            if (transformationType === 'standardize') {
                apiEndpoint = `/api/feature/scale/${currentDatasetId}`;
                requestBody = { columns: [targetFeature], method: 'standard' };
            } else {
                apiEndpoint = `/api/feature/transform/${currentDatasetId}`;
                requestBody = { columns: [targetFeature], method: transformationType };
            }
            
            const response = await fetch(apiEndpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(requestBody)
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const result = await response.json();
            
            if (result.success) {
                const newFeatureName = `${transformationType}_${targetFeature}`;
                const newFeature = {
                    name: newFeatureName,
                    type: 'numeric',
                    engineered: true,
                    source: `${transformationType} transformation of ${targetFeature}`
                };
                
                engineeredFeatures.push(newFeature);
                updateFeaturesList();
                showSuccess(`${transformationType} transformation applied to ${targetFeature}`);
            } else {
                throw new Error(result.error || 'Failed to apply transformation');
            }
            
        } catch (error) {
            console.error('Error applying transformation:', error);
            showError('Failed to apply transformation: ' + error.message);
        } finally {
            hideLoading();
        }
    }
    
    function getSelectedCheckboxes(containerId) {
        const container = document.getElementById(containerId);
        if (!container) return [];
        
        const checkboxes = container.querySelectorAll('input[type="checkbox"]:checked');
        return Array.from(checkboxes).map(cb => cb.value);
    }
    
    function updateFeaturesList() {
        const container = document.getElementById('engineered-features-list');
        
        // Check if container exists before trying to update it
        if (!container) {
            console.warn('Features list container not found. The DOM element with id "engineered-features-list" does not exist.');
            return;
        }
        
        if (engineeredFeatures.length === 0) {
            container.innerHTML = '<p>No engineered features yet. Use the techniques above to create new features.</p>';
            return;
        }
        
        let html = '<div class="features-grid">';
        engineeredFeatures.forEach((feature, index) => {
            html += `
                <div class="feature-card">
                    <div class="feature-header">
                        <strong>${feature.name}</strong>
                        <button class="remove-feature" onclick="removeFeature(${index})">×</button>
                    </div>
                    <div class="feature-details">
                        <span class="feature-type">${feature.type}</span>
                        <span class="feature-source">${feature.source}</span>
                    </div>
                </div>
            `;
        });
        html += '</div>';
        
        container.innerHTML = html;
    }
    
    window.removeFeature = function(index) {
        engineeredFeatures.splice(index, 1);
        updateFeaturesList();
        showSuccess('Feature removed');
    };
    
    function switchSubTab(parentId, tabId) {
        const parent = document.getElementById(parentId);
        if (!parent) return;
        
        // Remove active class from all subtabs in this parent
        parent.querySelectorAll('.subtab-button').forEach(btn => btn.classList.remove('active'));
        parent.querySelectorAll('.subtab-content').forEach(content => content.classList.remove('active'));
        
        // Add active class to selected tab and content
        const activeButton = parent.querySelector(`[data-subtab="${tabId}"]`);
        const activeContent = parent.querySelector(`#${tabId}`);
        
        if (activeButton) activeButton.classList.add('active');
        if (activeContent) activeContent.classList.add('active');
    }
    
    function saveFeatures() {
        if (engineeredFeatures.length === 0) {
            showError('No engineered features to save');
            return;
        }
        
        // In a real app, this would save to the backend
        localStorage.setItem(`engineered_features_${currentDatasetId}`, JSON.stringify(engineeredFeatures));
        showSuccess(`${engineeredFeatures.length} engineered features saved`);
    }
    
    function exportFeatures() {
        if (engineeredFeatures.length === 0) {
            showError('No engineered features to export');
            return;
        }
        
        // Create CSV content
        const headers = ['feature_name', 'type', 'source', 'sample_values'];
        const rows = engineeredFeatures.map(feature => [
            feature.name,
            feature.type,
            feature.source,
            feature.values.slice(0, 5).join(';')
        ]);
        
        const csvContent = [headers, ...rows].map(row => row.join(',')).join('\n');
        
        // Download CSV
        const blob = new Blob([csvContent], { type: 'text/csv' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `engineered_features_${currentDatasetId}.csv`;
        a.click();
        
        showSuccess('Features exported to CSV');
    }
    
    function resetFeatures() {
        if (confirm('Are you sure you want to remove all engineered features?')) {
            engineeredFeatures = [];
            updateFeaturesList();
            showSuccess('All engineered features removed');
        }
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
    
    function showSuccess(message) {
        alert(message); // In a real app, use a proper notification system
    }
    
    // Download functionality
    function downloadDataset(format) {
        if (!currentDatasetId) {
            showError('No dataset selected');
            return;
        }
        
        showDownloadProgress();
        
        const url = `/api/advance-feature/download/${currentDatasetId}/${format}`;
        
        // Create a temporary link to trigger download
        const link = document.createElement('a');
        link.href = url;
        link.download = '';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
        // Show success message after a brief delay
        setTimeout(() => {
            hideDownloadProgress();
            showSuccess(`Dataset download started in ${format.toUpperCase()} format!`);
        }, 1000);
    }
    
    function showDownloadProgress() {
        const progressContainer = document.getElementById('download-progress');
        const progressFill = document.getElementById('progress-fill');
        const progressText = document.getElementById('progress-text');
        
        if (progressContainer && progressFill && progressText) {
            progressContainer.style.display = 'block';
            progressText.textContent = 'Preparing download...';
            
            // Simulate progress
            let progress = 0;
            const interval = setInterval(() => {
                progress += 10;
                progressFill.style.width = progress + '%';
                
                if (progress >= 100) {
                    clearInterval(interval);
                    progressText.textContent = 'Download ready!';
                }
            }, 100);
        }
    }
    
    function hideDownloadProgress() {
        const progressContainer = document.getElementById('download-progress');
        const progressFill = document.getElementById('progress-fill');
        
        if (progressContainer && progressFill) {
            progressContainer.style.display = 'none';
            progressFill.style.width = '0%';
        }
    }
    
    function showDownloadSection() {
        const downloadSection = document.getElementById('download-section');
        if (downloadSection) {
            downloadSection.style.display = 'block';
        }
    }
    
    // Show download section when any transformation is applied
    const originalShowSuccess = showSuccess;
    function showSuccess(message) {
        originalShowSuccess(message);
        if (currentDatasetId && engineeredFeatures.length > 0) {
            showDownloadSection();
        }
    }
    
    // Make download function global
    window.downloadDataset = downloadDataset;
});

// Add CSS for advanced feature engineering
const afeCSS = `
<style>
.features-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    gap: 15px;
    margin: 20px 0;
}

.feature-card {
    background: white;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 15px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.feature-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 10px;
}

.feature-header strong {
    color: #1e293b;
    font-size: 1.1em;
}

.remove-feature {
    background: #ef4444;
    color: white;
    border: none;
    border-radius: 50%;
    width: 24px;
    height: 24px;
    cursor: pointer;
    font-size: 16px;
    line-height: 1;
}

.feature-details {
    display: flex;
    flex-direction: column;
    gap: 5px;
}

.feature-type {
    background: #e0e7ff;
    color: #3730a3;
    padding: 2px 8px;
    border-radius: 12px;
    font-size: 0.8em;
    align-self: flex-start;
}

.feature-source {
    color: #64748b;
    font-size: 0.9em;
    font-style: italic;
}

.feature-checkbox {
    display: flex;
    align-items: center;
    gap: 8px;
    margin: 5px 0;
    padding: 8px;
    border-radius: 4px;
    transition: background-color 0.2s;
}

.feature-checkbox:hover {
    background: #f8fafc;
}

.feature-checkbox input[type="checkbox"] {
    margin: 0;
}

.feature-checkbox label {
    margin: 0;
    cursor: pointer;
    color: #374151;
}

.selection-results, .reduction-results {
    background: #f0f9ff;
    border: 1px solid #0ea5e9;
    border-radius: 8px;
    padding: 15px;
    margin: 15px 0;
}

.selection-results h5, .reduction-results h5 {
    color: #0c4a6e;
    margin: 0 0 10px 0;
}

.selection-results ul {
    margin: 10px 0 0 0;
    padding-left: 20px;
}

.subtab-button {
    background: #f1f5f9;
    border: 1px solid #cbd5e1;
    padding: 8px 16px;
    margin-right: 5px;
    border-radius: 6px 6px 0 0;
    cursor: pointer;
    transition: all 0.2s;
}

.subtab-button.active {
    background: white;
    border-bottom-color: white;
    font-weight: 600;
}

.subtab-content {
    display: none;
    background: white;
    border: 1px solid #cbd5e1;
    border-radius: 0 8px 8px 8px;
    padding: 20px;
}

.subtab-content.active {
    display: block;
}
</style>
`;

// CSS is now loaded from external file: feature_engineering.css
// document.head.insertAdjacentHTML('beforeend', afeCSS);