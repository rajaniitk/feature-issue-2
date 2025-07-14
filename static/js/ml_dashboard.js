document.addEventListener('DOMContentLoaded', function() {
    // Global variables
    let currentDatasetId = null;
    let currentFeatures = [];
    let trainedModel = null;
    
    // DOM Elements
    const datasetSelect = document.getElementById('ml-dataset-select');
    const refreshButton = document.getElementById('refresh-ml-datasets');
    const mlWorkflow = document.getElementById('ml-workflow');
    const availableFeatures = document.getElementById('available-features');
    const targetColumn = document.getElementById('target-column');
    const problemType = document.getElementById('problem-type');
    const algorithm = document.getElementById('algorithm');
    const testSize = document.getElementById('test-size');
    const trainModelBtn = document.getElementById('train-model');
    const crossValidateBtn = document.getElementById('cross-validate');
    const hyperparameterTuneBtn = document.getElementById('hyperparameter-tune');
    const saveModelBtn = document.getElementById('save-model');
    const loadingModal = document.getElementById('ml-loading-modal');
    
    // Initialize
    loadDatasets();
    
    // Event listeners
    refreshButton.addEventListener('click', loadDatasets);
    datasetSelect.addEventListener('change', handleDatasetSelection);
    problemType.addEventListener('change', updateAlgorithmOptions);
    algorithm.addEventListener('change', updateHyperparameters);
    trainModelBtn.addEventListener('click', trainModel);
    crossValidateBtn.addEventListener('click', crossValidateModel);
    hyperparameterTuneBtn.addEventListener('click', tuneHyperparameters);
    saveModelBtn.addEventListener('click', saveModel);
    
    // Feature selection buttons
    document.getElementById('select-all-features').addEventListener('click', selectAllFeatures);
    document.getElementById('clear-features').addEventListener('click', clearFeatures);
    document.getElementById('auto-select-features').addEventListener('click', autoSelectFeatures);
    
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
            mlWorkflow.style.display = 'none';
            return;
        }
        
        currentDatasetId = selectedId;
        await loadDatasetFeatures(selectedId);
        mlWorkflow.style.display = 'block';
    }
    
    async function loadDatasetFeatures(datasetId) {
        showLoading('Loading dataset features...');
        
        try {
            // Fetch real features from the API
            const response = await fetch(`/api/data/columns/${datasetId}`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            
            if (data.success && data.columns) {
                currentFeatures = data.columns;
                displayFeatures(data.columns);
                populateTargetColumn(data.columns);
            } else {
                throw new Error(data.error || 'Failed to load features');
            }
            
        } catch (error) {
            console.error('Error loading features:', error);
            showError('Failed to load dataset features');
        } finally {
            hideLoading();
        }
    }
    
    function displayFeatures(features) {
        let html = '';
        
        features.forEach(feature => {
            const typeClass = feature.is_numeric ? 'numeric' : 'categorical';
            html += `
                <div class="feature-item ${typeClass}">
                    <label class="feature-checkbox">
                        <input type="checkbox" value="${feature.name}" class="feature-select">
                        <span class="checkmark"></span>
                        <div class="feature-info">
                            <strong>${feature.name}</strong>
                            <small>${feature.dtype} (${feature.is_numeric ? 'Numeric' : 'Categorical'}) - Missing: ${feature.null_count}</small>
                        </div>
                    </label>
                </div>
            `;
        });
        
        availableFeatures.innerHTML = html;
    }
    
    function populateTargetColumn(features) {
        targetColumn.innerHTML = '<option value="">Select target column...</option>';
        
        features.forEach(feature => {
            const option = document.createElement('option');
            option.value = feature.name;
            option.textContent = `${feature.name} (${feature.dtype})`;
            targetColumn.appendChild(option);
        });
    }
    
    function updateAlgorithmOptions() {
        const type = problemType.value;
        algorithm.innerHTML = '';
        
        let algorithms = [];
        
        switch (type) {
            case 'classification':
                algorithms = [
                    { value: 'random_forest', text: 'Random Forest' },
                    { value: 'logistic_regression', text: 'Logistic Regression' },
                    { value: 'svm', text: 'Support Vector Machine' },
                    { value: 'gradient_boosting', text: 'Gradient Boosting' },
                    { value: 'neural_network', text: 'Neural Network' }
                ];
                break;
            case 'regression':
                algorithms = [
                    { value: 'random_forest', text: 'Random Forest Regressor' },
                    { value: 'linear_regression', text: 'Linear Regression' },
                    { value: 'svm', text: 'Support Vector Regression' },
                    { value: 'gradient_boosting', text: 'Gradient Boosting Regressor' },
                    { value: 'neural_network', text: 'Neural Network' }
                ];
                break;
            case 'clustering':
                algorithms = [
                    { value: 'kmeans', text: 'K-Means' },
                    { value: 'dbscan', text: 'DBSCAN' },
                    { value: 'hierarchical', text: 'Hierarchical Clustering' },
                    { value: 'gaussian_mixture', text: 'Gaussian Mixture' }
                ];
                break;
        }
        
        algorithms.forEach(alg => {
            const option = document.createElement('option');
            option.value = alg.value;
            option.textContent = alg.text;
            algorithm.appendChild(option);
        });
        
        if (algorithms.length > 0) {
            algorithm.value = algorithms[0].value;
            updateHyperparameters();
        }
    }
    
    function updateHyperparameters() {
        const alg = algorithm.value;
        const container = document.getElementById('hyperparameter-controls');
        
        let html = '';
        
        switch (alg) {
            case 'random_forest':
                html = `
                    <div class="form-group">
                        <label>Number of Trees:</label>
                        <input type="number" id="n_estimators" value="100" min="10" max="1000">
                    </div>
                    <div class="form-group">
                        <label>Max Depth:</label>
                        <input type="number" id="max_depth" value="10" min="3" max="50">
                    </div>
                `;
                break;
            case 'logistic_regression':
            case 'linear_regression':
                html = `
                    <div class="form-group">
                        <label>Regularization (C):</label>
                        <input type="number" id="C" value="1.0" min="0.001" max="100" step="0.1">
                    </div>
                `;
                break;
            case 'svm':
                html = `
                    <div class="form-group">
                        <label>C Parameter:</label>
                        <input type="number" id="C" value="1.0" min="0.001" max="100" step="0.1">
                    </div>
                    <div class="form-group">
                        <label>Kernel:</label>
                        <select id="kernel">
                            <option value="rbf">RBF</option>
                            <option value="linear">Linear</option>
                            <option value="poly">Polynomial</option>
                        </select>
                    </div>
                `;
                break;
            case 'kmeans':
                html = `
                    <div class="form-group">
                        <label>Number of Clusters:</label>
                        <input type="number" id="n_clusters" value="3" min="2" max="20">
                    </div>
                `;
                break;
        }
        
        container.innerHTML = html;
    }
    
    function selectAllFeatures() {
        const checkboxes = document.querySelectorAll('.feature-select');
        checkboxes.forEach(cb => cb.checked = true);
    }
    
    function clearFeatures() {
        const checkboxes = document.querySelectorAll('.feature-select');
        checkboxes.forEach(cb => cb.checked = false);
    }
    
    function autoSelectFeatures() {
        // Auto-select numeric features for demonstration
        const checkboxes = document.querySelectorAll('.feature-select');
        checkboxes.forEach(cb => {
            const featureName = cb.value;
            const feature = currentFeatures.find(f => f.name === featureName);
            cb.checked = feature && feature.is_numeric;
        });
    }
    
    async function trainModel() {
        if (!validateModelConfiguration()) return;
        
        showLoading('Training your model with real data...');
        
        try {
            const selectedFeatures = getSelectedFeatures();
            const target = targetColumn.value;
            const hyperparams = getHyperparameters();
            
            const requestData = {
                dataset_id: currentDatasetId,
                features: selectedFeatures,
                target: target,
                algorithm: algorithm.value,
                problem_type: problemType.value,
                test_size: parseFloat(testSize.value) || 0.2,
                hyperparameters: hyperparams
            };
            
            const response = await fetch('/api/ml/train', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(requestData)
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const results = await response.json();
            
            if (results.success) {
                displayTrainingResults(results);
                trainedModel = results;
                saveModelBtn.disabled = false;
                showSuccess('Model trained successfully with real data!');
            } else {
                throw new Error(results.error || 'Training failed');
            }
            
        } catch (error) {
            console.error('Error training model:', error);
            showError('Failed to train model: ' + error.message);
        } finally {
            hideLoading();
        }
    }
    
    function getHyperparameters() {
        const hyperparams = {};
        const container = document.getElementById('hyperparameter-controls');
        const inputs = container.querySelectorAll('input, select');
        
        inputs.forEach(input => {
            if (input.value) {
                hyperparams[input.id] = input.type === 'number' ? parseFloat(input.value) : input.value;
            }
        });
        
        return hyperparams;
    }
    
    function validateModelConfiguration() {
        const selectedFeatures = getSelectedFeatures();
        const target = targetColumn.value;
        
        if (selectedFeatures.length === 0) {
            showError('Please select at least one feature');
            return false;
        }
        
        if (!target) {
            showError('Please select a target column');
            return false;
        }
        
        if (selectedFeatures.includes(target)) {
            showError('Target column cannot be in the feature list');
            return false;
        }
        
        return true;
    }
    
    function getSelectedFeatures() {
        const checkboxes = document.querySelectorAll('.feature-select:checked');
        return Array.from(checkboxes).map(cb => cb.value);
    }
    
    function displayTrainingResults(results) {
        // Update score cards with real results
        if (results.training_score !== undefined) {
            document.getElementById('training-score').textContent = (results.training_score * 100).toFixed(1) + '%';
        }
        if (results.validation_score !== undefined) {
            document.getElementById('validation-score').textContent = (results.validation_score * 100).toFixed(1) + '%';
        }
        if (results.test_score !== undefined) {
            document.getElementById('test-score').textContent = (results.test_score * 100).toFixed(1) + '%';
        }
        
        // Display detailed metrics
        const metricsContainer = document.getElementById('detailed-metrics-content');
        let html = '<div class="metrics-grid">';
        
        if (results.metrics) {
            for (const [metric, value] of Object.entries(results.metrics)) {
                const displayValue = metric.includes('score') || metric === 'accuracy' || metric === 'precision' || metric === 'recall' || metric === 'f1_score' ? 
                    (value * 100).toFixed(2) + '%' : value.toFixed(4);
                html += `
                    <div class="metric-item">
                        <strong>${metric.replace('_', ' ').toUpperCase()}</strong>
                        <span>${displayValue}</span>
                    </div>
                `;
            }
        }
        
        html += '</div>';
        metricsContainer.innerHTML = html;
        
        // Show results section
        document.getElementById('training-results').style.display = 'block';
        
        // Show feature importance if available
        if (results.feature_importance) {
            displayFeatureImportance(results.feature_importance);
        }
    }
    
    function displayFeatureImportance(importances) {
        const container = document.getElementById('importance-chart');
        
        // Sort importances by value
        const sortedImportances = Object.entries(importances)
            .map(([feature, importance]) => ({ feature, importance }))
            .sort((a, b) => b.importance - a.importance);
        
        let html = '<div class="importance-bars">';
        
        sortedImportances.forEach(item => {
            const percentage = (item.importance * 100).toFixed(1);
            html += `
                <div class="importance-item">
                    <div class="importance-label">${item.feature}</div>
                    <div class="importance-bar-container">
                        <div class="importance-bar" style="width: ${percentage}%"></div>
                        <span class="importance-value">${percentage}%</span>
                    </div>
                </div>
            `;
        });
        
        html += '</div>';
        container.innerHTML = html;
        
        document.getElementById('feature-importance').style.display = 'block';
    }
    
    async function crossValidateModel() {
        if (!validateModelConfiguration()) return;
        
        showLoading('Performing cross-validation with real data...');
        
        try {
            const requestData = {
                dataset_id: currentDatasetId,
                features: getSelectedFeatures(),
                target: targetColumn.value,
                algorithm: algorithm.value,
                problem_type: problemType.value,
                cv_folds: 5,
                hyperparameters: getHyperparameters()
            };
            
            const response = await fetch('/api/ml/cross-validate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(requestData)
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const results = await response.json();
            
            if (results.success) {
                showSuccess(`Cross-validation completed! Mean score: ${(results.mean_score * 100).toFixed(1)}% (±${(results.std_score * 100).toFixed(1)}%)`);
            } else {
                throw new Error(results.error || 'Cross-validation failed');
            }
            
        } catch (error) {
            console.error('Error in cross-validation:', error);
            showError('Failed to perform cross-validation: ' + error.message);
        } finally {
            hideLoading();
        }
    }
    
    async function tuneHyperparameters() {
        if (!validateModelConfiguration()) return;
        
        showLoading('Tuning hyperparameters with real data...');
        
        try {
            const requestData = {
                dataset_id: currentDatasetId,
                features: getSelectedFeatures(),
                target: targetColumn.value,
                algorithm: algorithm.value,
                problem_type: problemType.value
            };
            
            const response = await fetch('/api/ml/tune-hyperparameters', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(requestData)
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const results = await response.json();
            
            if (results.success) {
                showSuccess('Hyperparameter tuning completed! Best parameters have been applied.');
                
                // Update hyperparameter values with the best found parameters
                if (results.best_params) {
                    updateHyperparameterValues(results.best_params);
                }
            } else {
                throw new Error(results.error || 'Hyperparameter tuning failed');
            }
            
        } catch (error) {
            console.error('Error in hyperparameter tuning:', error);
            showError('Failed to tune hyperparameters: ' + error.message);
        } finally {
            hideLoading();
        }
    }
    
    function updateHyperparameterValues(bestParams) {
        const container = document.getElementById('hyperparameter-controls');
        const inputs = container.querySelectorAll('input, select');
        
        inputs.forEach(input => {
            if (bestParams[input.id] !== undefined) {
                input.value = bestParams[input.id];
            }
        });
    }
    
    function saveModel() {
        if (!trainedModel) {
            showError('No trained model to save');
            return;
        }
        
        const modelName = document.getElementById('model-name').value || 'Untitled Model';
        
        const modelData = {
            id: Date.now(),
            name: modelName,
            algorithm: trainedModel.algorithm,
            problem_type: trainedModel.problem_type,
            features: trainedModel.features,
            target: trainedModel.target,
            test_score: trainedModel.test_score,
            metrics: trainedModel.metrics,
            created: new Date().toISOString(),
            dataset: currentDatasetId
        };
        
        // Save to localStorage (in real app, save to backend)
        const savedModels = JSON.parse(localStorage.getItem('savedModels') || '[]');
        savedModels.push(modelData);
        localStorage.setItem('savedModels', JSON.stringify(savedModels));
        
        showSuccess('Model saved successfully!');
        updateSavedModelsDisplay();
    }
    
    function updateSavedModelsDisplay() {
        const modelsList = document.getElementById('models-list');
        const savedModels = JSON.parse(localStorage.getItem('savedModels') || '[]');
        
        if (savedModels.length === 0) {
            modelsList.innerHTML = '<p>No saved models yet.</p>';
            return;
        }
        
        let html = '';
        savedModels.forEach(model => {
            html += `
                <div class="model-card">
                    <h4>${model.name}</h4>
                    <p><strong>Algorithm:</strong> ${model.algorithm}</p>
                    <p><strong>Type:</strong> ${model.problem_type}</p>
                    <p><strong>Score:</strong> ${(model.test_score * 100).toFixed(1)}%</p>
                    <p><strong>Features:</strong> ${model.features.length}</p>
                    <p><strong>Created:</strong> ${new Date(model.created).toLocaleDateString()}</p>
                    <div class="model-actions">
                        <button class="btn btn-secondary" onclick="loadModel(${model.id})">Load</button>
                        <button class="btn btn-secondary" onclick="deleteModel(${model.id})">Delete</button>
                    </div>
                </div>
            `;
        });
        
        modelsList.innerHTML = html;
    }
    
    function showLoading(message = 'Training your model...') {
        document.getElementById('loading-message').textContent = message;
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
    
    // Initialize algorithm options
    updateAlgorithmOptions();
    
    // Initialize saved models display
    updateSavedModelsDisplay();
});

// Global functions for model management
function loadModel(modelId) {
    const savedModels = JSON.parse(localStorage.getItem('savedModels') || '[]');
    const model = savedModels.find(m => m.id === modelId);
    
    if (model) {
        // Load model configuration
        document.getElementById('ml-dataset-select').value = model.dataset;
        document.getElementById('problem-type').value = model.problem_type;
        document.getElementById('target-column').value = model.target;
        document.getElementById('model-name').value = model.name;
        
        // Trigger dataset selection
        document.getElementById('ml-dataset-select').dispatchEvent(new Event('change'));
        
        setTimeout(() => {
            // Select features
            model.features.forEach(feature => {
                const checkbox = document.querySelector(`input[value="${feature}"]`);
                if (checkbox) checkbox.checked = true;
            });
            
            // Update algorithm
            document.getElementById('algorithm').value = model.algorithm;
        }, 500);
        
        alert('Model configuration loaded successfully!');
    }
}

function deleteModel(modelId) {
    if (confirm('Are you sure you want to delete this model?')) {
        const savedModels = JSON.parse(localStorage.getItem('savedModels') || '[]');
        const filteredModels = savedModels.filter(m => m.id !== modelId);
        localStorage.setItem('savedModels', JSON.stringify(filteredModels));
        
        // Update display
        const event = new Event('DOMContentLoaded');
        document.dispatchEvent(event);
    }
}