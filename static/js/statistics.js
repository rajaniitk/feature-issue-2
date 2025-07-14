document.addEventListener('DOMContentLoaded', function() {
    // Global variables
    let currentDatasetId = null;
    let currentColumns = [];
    
    // DOM Elements
    const datasetSelect = document.getElementById('stats-dataset-select');
    const refreshButton = document.getElementById('refresh-stats-datasets');
    const statsSections = document.getElementById('stats-sections');
    const loadingModal = document.getElementById('stats-loading-modal');
    
    // Initialize
    loadDatasets();
    setupEventListeners();
    
    // Utility function to safely format numbers
    function safeFormat(value, decimals = 4) {
        if (value === null || value === undefined || isNaN(value)) {
            return 'N/A';
        }
        return typeof value === 'number' ? value.toFixed(decimals) : value;
    }
    
    // Event listeners
    function setupEventListeners() {
        refreshButton.addEventListener('click', loadDatasets);
        datasetSelect.addEventListener('change', handleDatasetSelection);
        
        // Descriptive statistics
        document.getElementById('generate-descriptive').addEventListener('click', generateDescriptiveStats);
        
        // Normality tests
        document.getElementById('run-normality').addEventListener('click', runNormalityTest);
        
        // Correlation tests
        document.getElementById('run-correlation').addEventListener('click', runCorrelationTest);
        
        // T-tests
        document.getElementById('ttest-type').addEventListener('change', handleTTestTypeChange);
        document.getElementById('run-ttest').addEventListener('click', runTTest);
        
        // ANOVA
        document.getElementById('anova-type').addEventListener('change', handleANOVATypeChange);
        document.getElementById('run-anova').addEventListener('click', runANOVA);
        
        // Chi-square tests
        document.getElementById('chi-test-type').addEventListener('change', handleChiTestTypeChange);
        document.getElementById('run-chi-square').addEventListener('click', runChiSquareTest);
        
        // Non-parametric tests
        document.getElementById('nonparam-test-type').addEventListener('change', handleNonParametricTypeChange);
        document.getElementById('run-nonparametric').addEventListener('click', runNonParametricTest);
        
        // Variance tests
        document.getElementById('run-variance-test').addEventListener('click', runVarianceTest);
        
        // McNemar test
        document.getElementById('run-mcnemar').addEventListener('click', runMcNemarTest);
        
        // Multiple comparisons
        document.getElementById('run-multiple-comparison').addEventListener('click', runMultipleComparison);
    }
    
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
            statsSections.style.display = 'none';
            return;
        }
        
        currentDatasetId = selectedId;
        await loadDatasetColumns(selectedId);
        statsSections.style.display = 'block';
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
        // Get all select elements that need column population
        const selects = [
            'desc-columns', 'normality-column', 'corr-column1', 'corr-column2',
            'ttest-column', 'ttest-data-column', 'ttest-group-column', 'ttest-before', 'ttest-after',
            'anova-dependent', 'anova-independent', 'anova-independent2', 'chi-var1', 'chi-var2', 'chi-observed',
            'mw-data-column', 'mw-group-column', 'wilcoxon-col1', 'wilcoxon-col2',
            'kw-dependent', 'kw-independent', 'friedman-columns', 'variance-columns',
            'mcnemar-col1', 'mcnemar-col2', 'mc-dependent', 'mc-independent'
        ];
        
        selects.forEach(selectId => {
            const select = document.getElementById(selectId);
            if (select) {
                const isMultiple = select.hasAttribute('multiple');
                const placeholder = selectId.includes('desc') ? 'Select columns...' : 'Choose column...';
                
                if (!isMultiple) {
                    select.innerHTML = `<option value="">${placeholder}</option>`;
                } else {
                    select.innerHTML = '';
                }
                
                columns.forEach(column => {
                    // Filter columns based on select type
                    let shouldInclude = true;
                    
                    if (selectId.includes('normality') || selectId.includes('corr') || 
                        selectId.includes('ttest') || selectId.includes('anova-dependent') ||
                        selectId.includes('mw-data') || selectId.includes('wilcoxon') ||
                        selectId.includes('kw-dependent') || selectId.includes('friedman') ||
                        selectId.includes('variance') || selectId.includes('mc-dependent')) {
                        shouldInclude = column.is_numeric;
                    }
                    
                    if (selectId.includes('group') || selectId.includes('anova-independent') ||
                        selectId.includes('kw-independent') || selectId.includes('mc-independent') ||
                        selectId.includes('chi') || selectId.includes('mcnemar')) {
                        shouldInclude = !column.is_numeric; // Categorical columns
                    }
                    
                    if (shouldInclude) {
                        const option = document.createElement('option');
                        option.value = column.name;
                        option.textContent = `${column.name} (${column.dtype})`;
                        select.appendChild(option);
                    }
                });
            }
        });
    }
    
    async function generateDescriptiveStats() {
        const selectedColumns = Array.from(document.getElementById('desc-columns').selectedOptions)
            .map(option => option.value);
        
        if (selectedColumns.length === 0) {
            showError('Please select at least one column');
            return;
        }
        
        showLoading('Generating descriptive statistics...');
        
        try {
            // Fetch real descriptive statistics from API
            const response = await fetch('/api/statistical/descriptive', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    dataset_id: currentDatasetId,
                    columns: selectedColumns
                })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            
            if (data.success && data.statistics) {
                displayDescriptiveStats(data.statistics);
            } else {
                throw new Error(data.error || 'Failed to generate descriptive statistics');
            }
            
        } catch (error) {
            console.error('Error generating descriptive statistics:', error);
            showError('Failed to generate descriptive statistics: ' + error.message);
        } finally {
            hideLoading();
        }
    }
    
    function displayDescriptiveStats(stats) {
        const container = document.getElementById('descriptive-results');
        
        let html = '<div class="stats-table-container">';
        
        // Handle both numeric and categorical statistics
        if (stats.numeric) {
            html += '<h4>Numeric Variables</h4>';
            html += '<table class="stats-table">';
            html += '<thead><tr><th>Statistic</th>';
            
            Object.keys(stats.numeric).forEach(column => {
                html += `<th>${column}</th>`;
            });
            
            html += '</tr></thead><tbody>';
            
            const statNames = ['count', 'mean', 'std', 'min', '25%', '50%', '75%', 'max'];
            
            statNames.forEach(stat => {
                html += `<tr><td><strong>${stat}</strong></td>`;
                Object.values(stats.numeric).forEach(columnStats => {
                    const value = columnStats[stat];
                    if (value !== undefined && value !== null && !isNaN(value)) {
                        const displayValue = stat === 'count' ? value : parseFloat(value).toFixed(3);
                        html += `<td>${displayValue}</td>`;
                    } else {
                        html += `<td>N/A</td>`;
                    }
                });
                html += '</tr>';
            });
            
            html += '</tbody></table>';
        }
        
        if (stats.categorical) {
            html += '<h4>Categorical Variables</h4>';
            html += '<table class="stats-table">';
            html += '<thead><tr><th>Statistic</th>';
            
            Object.keys(stats.categorical).forEach(column => {
                html += `<th>${column}</th>`;
            });
            
            html += '</tr></thead><tbody>';
            
            const catStatNames = ['count', 'unique', 'top', 'freq'];
            
            catStatNames.forEach(stat => {
                html += `<tr><td><strong>${stat}</strong></td>`;
                Object.values(stats.categorical).forEach(columnStats => {
                    const value = columnStats[stat];
                    if (value !== undefined && value !== null) {
                        html += `<td>${value}</td>`;
                    } else {
                        html += `<td>N/A</td>`;
                    }
                });
                html += '</tr>';
            });
            
            html += '</tbody></table>';
        }
        
        html += '</div>';
        container.innerHTML = html;
    }
    
    async function runNormalityTest() {
        const column = document.getElementById('normality-column').value;
        const testType = document.getElementById('normality-test').value;
        
        if (!column) {
            showError('Please select a column');
            return;
        }
        
        showLoading('Running normality test...');
        
        try {
            // Run real normality test via API
            const response = await fetch('/api/statistical/normality', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    dataset_id: currentDatasetId,
                    column: column,
                    test_type: testType
                })
            });
            
            const data = await response.json();
            
            if (data.success && data.result) {
                displayNormalityResult(data.result, column, testType);
            } else {
                // Show the actual backend error message instead of generic one
                const errorMessage = data.error || 'Failed to run normality test';
                displayNormalityError(errorMessage, column, testType);
            }
            
        } catch (error) {
            console.error('Error running normality test:', error);
            // Handle network errors
            if (error.message.includes('HTTP error!')) {
                displayNormalityError('Server error occurred. Please check your data and try again.', column, testType);
            } else {
                displayNormalityError('Network error: ' + error.message, column, testType);
            }
        } finally {
            hideLoading();
        }
    }
    
    function displayNormalityError(errorMessage, column, testType) {
        const container = document.getElementById('normality-results');
        container.innerHTML = `
            <div class="test-result error">
                <h4>Normality Test Error</h4>
                <p><strong>Test:</strong> ${testType.replace('_', ' ').toUpperCase()}</p>
                <p><strong>Column:</strong> "${column}"</p>
                <p><strong>Error:</strong> ${errorMessage}</p>
                <div class="error-help">
                    <p><strong>Common solutions:</strong></p>
                    <ul>
                        <li>Ensure the column contains numeric data</li>
                        <li>Check for sufficient data points (minimum varies by test)</li>
                        <li>Remove or handle missing values</li>
                        <li>Try a different normality test if sample size is an issue</li>
                    </ul>
                    <p><strong>Test requirements:</strong></p>
                    <ul>
                        <li><strong>Shapiro-Wilk:</strong> 3-5000 data points</li>
                        <li><strong>Anderson-Darling:</strong> 5+ data points</li>
                        <li><strong>Kolmogorov-Smirnov:</strong> 5+ data points</li>
                        <li><strong>Jarque-Bera:</strong> 20+ data points</li>
                    </ul>
                </div>
            </div>
        `;
    }

    function displayNormalityResult(result, column, testType) {
        const container = document.getElementById('normality-results');
        
        // Handle Anderson-Darling specific results
        let isNormal = false;
        let hasValidResult = false;
        
        if (testType === 'anderson_darling' && result.is_normal_5_percent !== undefined) {
            isNormal = result.is_normal_5_percent;
            hasValidResult = true;
        } else if (result && typeof result.p_value !== 'undefined' && result.p_value !== null) {
            isNormal = result.p_value >= 0.05;
            hasValidResult = true;
        }
        
        if (!hasValidResult) {
            displayNormalityError('Invalid test results - no valid statistical results available', column, testType);
            return;
        }
        
        const testName = testType.replace('_', ' ').toUpperCase() + ' Normality Test';
        
        // Build comprehensive normality test result display
        let html = `
            <div style="background: white; border: 3px solid #007cba; border-radius: 15px; padding: 0; margin: 20px 0; overflow: hidden; box-shadow: 0 8px 25px rgba(0,124,186,0.15);">
                
                <!-- Header Section -->
                <div style="background: linear-gradient(135deg, #007cba 0%, #005580 50%, #003d5c 100%); padding: 25px 30px; color: white; position: relative; overflow: hidden;">
                    <div style="position: absolute; top: -20px; right: -20px; width: 100px; height: 100px; background: rgba(255,255,255,0.1); border-radius: 50%; transform: rotate(45deg);"></div>
                    <div style="position: relative; z-index: 2;">
                        <h3 style="margin: 0 0 10px 0; font-size: 24px; font-weight: bold; text-shadow: 1px 1px 2px rgba(0,0,0,0.3);">
                            📊 ${testName} Results
                        </h3>
                        <div style="background: rgba(255,255,255,0.2); border: 2px solid rgba(255,255,255,0.3); border-radius: 20px; padding: 8px 16px; display: inline-block;">
                            <span style="font-size: 14px; font-weight: bold;">${isNormal ? '✅ NORMAL' : '❌ NOT NORMAL'}</span>
                        </div>
                    </div>
                </div>

                <!-- Main Content -->
                <div style="padding: 25px;">
                    
                    <!-- Test Information -->
                    <div style="background: #f0f8ff; border: 2px solid #007cba; border-radius: 10px; padding: 20px; margin-bottom: 20px;">
                        <h4 style="color: #005580; margin: 0 0 15px 0; font-size: 18px;">📋 Test Information</h4>
                        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px;">
                            <div style="background: white; padding: 12px; border-radius: 8px; border-left: 4px solid #007cba;">
                                <strong style="color: #005580;">Variable:</strong><br>
                                <span style="font-size: 16px; color: #333;">${column}</span>
                            </div>
                            <div style="background: white; padding: 12px; border-radius: 8px; border-left: 4px solid #ff9800;">
                                <strong style="color: #e65100;">Test Type:</strong><br>
                                <span style="font-size: 16px; color: #333;">${testName}</span>
                            </div>
                            <div style="background: white; padding: 12px; border-radius: 8px; border-left: 4px solid #4caf50;">
                                <strong style="color: #2e7d32;">Sample Size:</strong><br>
                                <span style="font-size: 16px; color: #333;">${result.sample_size || 'N/A'}</span>
                            </div>
                        </div>
                    </div>

                    <!-- Test Statistics -->
                    <div style="background: ${isNormal ? '#e8f5e8' : '#fff3e0'}; border: 2px solid ${isNormal ? '#4caf50' : '#ff9800'}; border-radius: 10px; padding: 20px; margin-bottom: 20px;">
                        <h4 style="color: ${isNormal ? '#2e7d32' : '#f57c00'}; margin: 0 0 15px 0; font-size: 18px;">📊 Test Statistics</h4>
                        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px;">
                            <div style="background: white; padding: 15px; border-radius: 8px; text-align: center; border-left: 4px solid #2196f3;">
                                <div style="font-size: 28px; font-weight: bold; color: #1976d2;">${safeFormat(result.test_statistic)}</div>
                                <div style="color: #666; font-size: 14px;">Test Statistic</div>
                            </div>
        `;

        // Add appropriate statistical display based on test type
        if (testType === 'anderson_darling') {
            html += `
                            <div style="background: white; padding: 15px; border-radius: 8px; text-align: center; border-left: 4px solid #ff5722;">
                                <div style="font-size: 18px; font-weight: bold; color: #d84315;">${result.critical_values ? result.critical_values.map(v => v.toFixed(3)).join(', ') : 'N/A'}</div>
                                <div style="color: #666; font-size: 14px;">Critical Values</div>
                            </div>
                            <div style="background: white; padding: 15px; border-radius: 8px; text-align: center; border-left: 4px solid #9c27b0;">
                                <div style="font-size: 16px; font-weight: bold; color: #7b1fa2;">${result.significance_levels ? result.significance_levels.join('%, ') + '%' : 'N/A'}</div>
                                <div style="color: #666; font-size: 14px;">Significance Levels</div>
                            </div>
                            <div style="background: white; padding: 15px; border-radius: 8px; text-align: center; border-left: 4px solid #607d8b;">
                                <div style="font-size: 24px; font-weight: bold; color: #455a64;">${isNormal ? 'YES' : 'NO'}</div>
                                <div style="color: #666; font-size: 14px;">Normal at 5%</div>
                            </div>
            `;
        } else {
            html += `
                            <div style="background: white; padding: 15px; border-radius: 8px; text-align: center; border-left: 4px solid #ff5722;">
                                <div style="font-size: 28px; font-weight: bold; color: #d84315;">${safeFormat(result.p_value)}</div>
                                <div style="color: #666; font-size: 14px;">P-value</div>
                            </div>
                            <div style="background: white; padding: 15px; border-radius: 8px; text-align: center; border-left: 4px solid #9c27b0;">
                                <div style="font-size: 28px; font-weight: bold; color: #7b1fa2;">0.05</div>
                                <div style="color: #666; font-size: 14px;">Significance Level (α)</div>
                            </div>
            `;
        }

        html += `
                        </div>
                    </div>
        `;

        // Descriptive Statistics
        if (result.descriptive_stats) {
            const stats = result.descriptive_stats;
            html += `
                    <!-- Descriptive Statistics -->
                    <div style="background: #e0f2f1; border: 2px solid #4caf50; border-radius: 10px; padding: 20px; margin-bottom: 20px;">
                        <h4 style="color: #2e7d32; margin: 0 0 15px 0; font-size: 18px;">📈 Descriptive Statistics</h4>
                        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 15px;">
                            <div style="background: white; padding: 12px; border-radius: 8px; text-align: center; border-left: 4px solid #4caf50;">
                                <div style="font-size: 20px; font-weight: bold; color: #2e7d32;">${safeFormat(stats.mean)}</div>
                                <div style="color: #666; font-size: 12px;">Mean</div>
                            </div>
                            <div style="background: white; padding: 12px; border-radius: 8px; text-align: center; border-left: 4px solid #ff9800;">
                                <div style="font-size: 20px; font-weight: bold; color: #f57c00;">${safeFormat(stats.median)}</div>
                                <div style="color: #666; font-size: 12px;">Median</div>
                            </div>
                            <div style="background: white; padding: 12px; border-radius: 8px; text-align: center; border-left: 4px solid #9c27b0;">
                                <div style="font-size: 20px; font-weight: bold; color: #7b1fa2;">${safeFormat(stats.std)}</div>
                                <div style="color: #666; font-size: 12px;">Std Dev</div>
                            </div>
                            <div style="background: white; padding: 12px; border-radius: 8px; text-align: center; border-left: 4px solid #3f51b5;">
                                <div style="font-size: 20px; font-weight: bold; color: #303f9f;">${safeFormat(stats.skewness)}</div>
                                <div style="color: #666; font-size: 12px;">Skewness</div>
                            </div>
                            <div style="background: white; padding: 12px; border-radius: 8px; text-align: center; border-left: 4px solid #607d8b;">
                                <div style="font-size: 20px; font-weight: bold; color: #455a64;">${safeFormat(stats.kurtosis)}</div>
                                <div style="color: #666; font-size: 12px;">Kurtosis</div>
                            </div>
                        </div>
                    </div>
            `;
        }

        // Comprehensive Conclusion
        const skewness = result.descriptive_stats ? result.descriptive_stats.skewness : null;
        const kurtosis = result.descriptive_stats ? result.descriptive_stats.kurtosis : null;
        
        let interpretation = result.interpretation || (isNormal ? 'The data appears to be normally distributed.' : 'The data does not appear to be normally distributed.');
        
        let detailedConclusion = '';
        if (isNormal) {
            detailedConclusion = `
                <strong>✅ Data is Normally Distributed:</strong>
                <p>The ${testName} indicates that the data follows a normal distribution. This means:</p>
                <ul>
                    <li>✅ Parametric tests (t-tests, ANOVA) are appropriate</li>
                    <li>✅ Mean and standard deviation are reliable measures</li>
                    <li>✅ The data follows the bell curve pattern</li>
                    <li>✅ Statistical inference assumptions are met</li>
                    <li>📊 Confidence intervals and hypothesis tests are valid</li>
                </ul>
            `;
        } else {
            detailedConclusion = `
                <strong>❌ Data is NOT Normally Distributed:</strong>
                <p>The ${testName} indicates significant deviation from normality. Consider:</p>
                <ul>
                    <li>⚠️ Use non-parametric tests instead of parametric tests</li>
                    <li>⚠️ Median may be more appropriate than mean</li>
                    <li>⚠️ Data transformation (log, square root) may help</li>
                    <li>⚠️ Bootstrap methods for confidence intervals</li>
                    <li>📊 Consider larger sample sizes</li>
                </ul>
            `;
            
            if (skewness !== null) {
                if (Math.abs(skewness) > 2) {
                    detailedConclusion += `<p><strong>Skewness Issue:</strong> Highly ${skewness > 0 ? 'right' : 'left'}-skewed distribution (${safeFormat(skewness)}) - consider log transformation.</p>`;
                } else if (Math.abs(skewness) > 0.5) {
                    detailedConclusion += `<p><strong>Skewness Issue:</strong> Moderately ${skewness > 0 ? 'right' : 'left'}-skewed distribution (${safeFormat(skewness)}).</p>`;
                }
            }
            
            if (kurtosis !== null) {
                if (kurtosis > 2) {
                    detailedConclusion += `<p><strong>Kurtosis Issue:</strong> Heavy-tailed distribution (${safeFormat(kurtosis)}) - more extreme values than normal.</p>`;
                } else if (kurtosis < -2) {
                    detailedConclusion += `<p><strong>Kurtosis Issue:</strong> Light-tailed distribution (${safeFormat(kurtosis)}) - fewer extreme values than normal.</p>`;
                }
            }
        }

        html += `
                    <!-- Conclusion Section -->
                    <div style="background: ${isNormal ? '#e8f5e8' : '#fff3e0'}; border: 2px solid ${isNormal ? '#4caf50' : '#ff9800'}; border-radius: 10px; padding: 20px; margin-bottom: 20px;">
                        <h4 style="color: ${isNormal ? '#2e7d32' : '#f57c00'}; margin: 0 0 15px 0; font-size: 18px;">🎯 Conclusion & Recommendations</h4>
                        <div style="background: white; padding: 15px; border-radius: 8px; border-left: 4px solid ${isNormal ? '#4caf50' : '#ff9800'};">
                            <div style="font-size: 16px; line-height: 1.6; color: #333;">
                                ${detailedConclusion}
                            </div>
                        </div>
                    </div>

                    <!-- Statistical Decision -->
                    <div style="background: #e3f2fd; border: 2px solid #2196f3; border-radius: 10px; padding: 20px; margin-bottom: 20px;">
                        <h4 style="color: #1976d2; margin: 0 0 15px 0; font-size: 18px;">⚖️ Statistical Decision</h4>
                        <div style="background: white; padding: 15px; border-radius: 8px; border-left: 4px solid #2196f3;">
                            <p style="margin: 0; font-size: 16px; line-height: 1.5; color: #333;">
                                <strong>${interpretation}</strong>
                            </p>
                            <div style="margin-top: 15px; padding: 10px; background: #f5f5f5; border-radius: 8px;">
                                <p style="margin: 0; font-size: 14px; color: #666;">
                                    <strong>Decision Rule:</strong> 
                                    ${testType === 'anderson_darling' ? 
                                        `Test statistic (${safeFormat(result.test_statistic)}) ${isNormal ? '< critical value' : '≥ critical value'} → ${isNormal ? 'Normal' : 'Not Normal'}` :
                                        `${isNormal ? 
                                            `p-value (${safeFormat(result.p_value)}) ≥ 0.05 → Fail to reject H₀ (Normal)` : 
                                            `p-value (${safeFormat(result.p_value)}) < 0.05 → Reject H₀ (Not Normal)`}`}
                                </p>
                            </div>
                        </div>
                    </div>

                    <!-- Hypotheses Section -->
                    <div style="background: #e3f2fd; border: 2px solid #2196f3; border-radius: 10px; padding: 20px;">
                        <h4 style="color: #1976d2; margin: 0 0 15px 0; font-size: 18px;">📝 Hypotheses</h4>
                        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
                            <div style="background: white; padding: 15px; border-radius: 8px; border-left: 4px solid #2196f3;">
                                <div style="font-weight: bold; color: #1976d2; margin-bottom: 8px;">Null Hypothesis (H₀):</div>
                                <div style="color: #333; font-size: 14px;">The data follows a normal distribution</div>
                            </div>
                            <div style="background: white; padding: 15px; border-radius: 8px; border-left: 4px solid #ff5722;">
                                <div style="font-weight: bold; color: #d84315; margin-bottom: 8px;">Alternative Hypothesis (H₁):</div>
                                <div style="color: #333; font-size: 14px;">The data does not follow a normal distribution</div>
                            </div>
                        </div>
                    </div>

                </div>
            </div>
        `;
        
        container.innerHTML = html;
    }
    
    async function runCorrelationTest() {
        const column1 = document.getElementById('corr-column1').value;
        const column2 = document.getElementById('corr-column2').value;
        const method = document.getElementById('correlation-method').value;
        
        if (!column1 || !column2) {
            showError('Please select both columns');
            return;
        }
        
        if (column1 === column2) {
            showError('Please select different columns');
            return;
        }
        
        showLoading('Running correlation test...');
        
        try {
            // Run real correlation test via API
            const response = await fetch('/api/statistical/correlation', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    dataset_id: currentDatasetId,
                    column1: column1,
                    column2: column2,
                    method: method
                })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            
            if (data.success && data.result) {
                displayCorrelationResult(data.result, column1, column2, method);
            } else {
                throw new Error(data.error || 'Failed to run correlation test');
            }
            
        } catch (error) {
            console.error('Error running correlation test:', error);
            showError('Failed to run correlation test: ' + error.message);
        } finally {
            hideLoading();
        }
    }
    
    function displayCorrelationResult(result, column1, column2, method) {
        const container = document.getElementById('correlation-results');
        
        // Safely handle undefined or null result
        if (!result || typeof result.correlation === 'undefined' || result.correlation === null) {
            container.innerHTML = `
                <div class="test-result error">
                    <h4>Correlation Test Error</h4>
                    <p>Unable to calculate correlation between "${column1}" and "${column2}". This may be due to:</p>
                    <ul>
                        <li>Non-numeric data in selected columns</li>
                        <li>Insufficient data points</li>
                        <li>Missing or invalid values</li>
                    </ul>
                </div>
            `;
            return;
        }
        
        const correlation = result.correlation_coefficient || result.correlation;
        const strength = Math.abs(correlation);
        let strengthText = 'weak';
        let strengthColor = '#ff9800';
        if (strength > 0.7) {
            strengthText = 'strong';
            strengthColor = '#4caf50';
        } else if (strength > 0.3) {
            strengthText = 'moderate';
            strengthColor = '#2196f3';
        }
        
        const direction = correlation > 0 ? 'positive' : 'negative';
        const isSignificant = result.p_value && result.p_value < 0.05;
        
        // Build comprehensive correlation result display
        let html = `
            <div style="background: white; border: 3px solid #007cba; border-radius: 15px; padding: 0; margin: 20px 0; overflow: hidden; box-shadow: 0 8px 25px rgba(0,124,186,0.15);">
                
                <!-- Header Section -->
                <div style="background: linear-gradient(135deg, #007cba 0%, #005580 50%, #003d5c 100%); padding: 25px 30px; color: white; position: relative; overflow: hidden;">
                    <div style="position: absolute; top: -20px; right: -20px; width: 100px; height: 100px; background: rgba(255,255,255,0.1); border-radius: 50%; transform: rotate(45deg);"></div>
                    <div style="position: relative; z-index: 2;">
                        <h3 style="margin: 0 0 10px 0; font-size: 24px; font-weight: bold; text-shadow: 1px 1px 2px rgba(0,0,0,0.3);">
                            📈 ${method.toUpperCase()} Correlation Analysis
                        </h3>
                        <div style="background: rgba(255,255,255,0.2); border: 2px solid rgba(255,255,255,0.3); border-radius: 20px; padding: 8px 16px; display: inline-block;">
                            <span style="font-size: 14px; font-weight: bold;">${isSignificant ? '✅ SIGNIFICANT' : '❌ NOT SIGNIFICANT'}</span>
                        </div>
                    </div>
                </div>

                <!-- Main Content -->
                <div style="padding: 25px;">
                    
                    <!-- Variables Section -->
                    <div style="background: #f0f8ff; border: 2px solid #007cba; border-radius: 10px; padding: 20px; margin-bottom: 20px;">
                        <h4 style="color: #005580; margin: 0 0 15px 0; font-size: 18px;">📋 Variables</h4>
                        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px;">
                            <div style="background: white; padding: 12px; border-radius: 8px; border-left: 4px solid #007cba;">
                                <strong style="color: #005580;">Variable 1:</strong><br>
                                <span style="font-size: 16px; color: #333;">${column1}</span>
                            </div>
                            <div style="background: white; padding: 12px; border-radius: 8px; border-left: 4px solid #ff9800;">
                                <strong style="color: #e65100;">Variable 2:</strong><br>
                                <span style="font-size: 16px; color: #333;">${column2}</span>
                            </div>
                            <div style="background: white; padding: 12px; border-radius: 8px; border-left: 4px solid #4caf50;">
                                <strong style="color: #2e7d32;">Method:</strong><br>
                                <span style="font-size: 16px; color: #333;">${method.toUpperCase()}</span>
                            </div>
                            <div style="background: white; padding: 12px; border-radius: 8px; border-left: 4px solid #9c27b0;">
                                <strong style="color: #7b1fa2;">Sample Size:</strong><br>
                                <span style="font-size: 16px; color: #333;">${result.sample_size || 'N/A'}</span>
                            </div>
                        </div>
                    </div>

                    <!-- Correlation Statistics -->
                    <div style="background: ${isSignificant ? '#e8f5e8' : '#fff3e0'}; border: 2px solid ${isSignificant ? '#4caf50' : '#ff9800'}; border-radius: 10px; padding: 20px; margin-bottom: 20px;">
                        <h4 style="color: ${isSignificant ? '#2e7d32' : '#f57c00'}; margin: 0 0 15px 0; font-size: 18px;">📊 Correlation Statistics</h4>
                        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px;">
                            <div style="background: white; padding: 15px; border-radius: 8px; text-align: center; border-left: 4px solid ${strengthColor};">
                                <div style="font-size: 36px; font-weight: bold; color: ${strengthColor};">${safeFormat(correlation, 4)}</div>
                                <div style="color: #666; font-size: 14px;">Correlation Coefficient</div>
                                <div style="color: ${strengthColor}; font-size: 12px; font-weight: bold; margin-top: 5px;">${strengthText.toUpperCase()}</div>
                            </div>
                            <div style="background: white; padding: 15px; border-radius: 8px; text-align: center; border-left: 4px solid #ff5722;">
                                <div style="font-size: 28px; font-weight: bold; color: #d84315;">${safeFormat(result.p_value)}</div>
                                <div style="color: #666; font-size: 14px;">P-value</div>
                            </div>
                            ${result.confidence_interval_95 ? `
                            <div style="background: white; padding: 15px; border-radius: 8px; text-align: center; border-left: 4px solid #2196f3;">
                                <div style="font-size: 18px; font-weight: bold; color: #1976d2;">[${safeFormat(result.confidence_interval_95[0], 3)}, ${safeFormat(result.confidence_interval_95[1], 3)}]</div>
                                <div style="color: #666; font-size: 14px;">95% Confidence Interval</div>
                            </div>
                            ` : ''}
                        </div>
                    </div>

                    <!-- Interpretation Section -->
                    <div style="background: #e3f2fd; border: 2px solid #2196f3; border-radius: 10px; padding: 20px; margin-bottom: 20px;">
                        <h4 style="color: #1976d2; margin: 0 0 15px 0; font-size: 18px;">📝 Interpretation</h4>
                        <div style="background: white; padding: 15px; border-radius: 8px; border-left: 4px solid #2196f3;">
                            <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 10px;">
                                <div style="background: ${strengthColor}; color: white; padding: 8px 12px; border-radius: 15px; font-weight: bold; font-size: 14px;">
                                    ${strengthText.toUpperCase()} ${direction.toUpperCase()}
                                </div>
                                <div style="background: ${isSignificant ? '#4caf50' : '#ff9800'}; color: white; padding: 8px 12px; border-radius: 15px; font-weight: bold; font-size: 14px;">
                                    ${isSignificant ? 'SIGNIFICANT' : 'NOT SIGNIFICANT'}
                                </div>
                            </div>
                            <p style="margin: 10px 0; color: #333; font-size: 16px; line-height: 1.5;">
                                <strong>There is a ${strengthText} ${direction} correlation between "${column1}" and "${column2}"</strong> 
                                (r = ${safeFormat(correlation, 4)}, p = ${safeFormat(result.p_value)}).
                            </p>
                            <div style="background: #f5f5f5; padding: 10px; border-radius: 8px; margin-top: 10px;">
                                <p style="margin: 0; color: #666; font-size: 14px;">
                                    <strong>Practical Meaning:</strong> 
                                    ${strength > 0.7 ? 'Strong relationship - changes in one variable are closely associated with changes in the other.' :
                                      strength > 0.3 ? 'Moderate relationship - there is a noticeable association between the variables.' :
                                      'Weak relationship - the variables have little linear association.'}
                                </p>
                            </div>
                        </div>
                    </div>

                    <!-- Statistical Decision -->
                    <div style="background: ${isSignificant ? '#e8f5e8' : '#fff3e0'}; border: 2px solid ${isSignificant ? '#4caf50' : '#ff9800'}; border-radius: 10px; padding: 20px;">
                        <h4 style="color: ${isSignificant ? '#2e7d32' : '#f57c00'}; margin: 0 0 15px 0; font-size: 18px;">🎯 Statistical Decision</h4>
                        <div style="background: white; padding: 15px; border-radius: 8px; border-left: 4px solid ${isSignificant ? '#4caf50' : '#ff9800'};">
                            <p style="margin: 0; font-size: 16px; line-height: 1.5; color: #333;">
                                <strong>${isSignificant ? 
                                    'The correlation is statistically significant.' : 
                                    'The correlation is not statistically significant.'}</strong>
                            </p>
                            <div style="margin-top: 15px; padding: 10px; background: ${isSignificant ? '#e8f5e8' : '#fff3e0'}; border-radius: 8px;">
                                <p style="margin: 0; font-size: 14px; color: #666;">
                                    <strong>Decision:</strong> 
                                    ${isSignificant ? 
                                        `p-value (${safeFormat(result.p_value)}) < 0.05 → Reject H₀ (no correlation)` : 
                                        `p-value (${safeFormat(result.p_value)}) ≥ 0.05 → Fail to reject H₀ (no correlation)`}
                                </p>
                            </div>
                        </div>
                    </div>

                </div>
            </div>
        `;
        
        container.innerHTML = html;
    }
    
    function handleTTestTypeChange() {
        const testType = document.getElementById('ttest-type').value;
        
        // Hide all config sections
        document.querySelectorAll('.ttest-config').forEach(section => {
            section.style.display = 'none';
        });
        
        // Show relevant section
        const sectionMap = {
            'one_sample': 'ttest-one-sample',
            'two_sample': 'ttest-two-sample', 
            'paired': 'ttest-paired'
        };
        
        const sectionId = sectionMap[testType];
        if (sectionId) {
            document.getElementById(sectionId).style.display = 'block';
        }
    }

    function handleANOVATypeChange() {
        const anovaType = document.getElementById('anova-type').value;
        const twoWayControls = document.getElementById('two-way-controls');
        
        if (anovaType === 'two_way') {
            twoWayControls.classList.add('active');
        } else {
            twoWayControls.classList.remove('active');
        }
    }
    
    async function runTTest() {
        const testType = document.getElementById('ttest-type').value;
        const alpha = parseFloat(document.getElementById('alpha-level').value);
        
        // Get test-specific parameters
        let requestData = {
            dataset_id: currentDatasetId,
            test_type: testType,
            alpha: alpha
        };
        
        if (testType === 'one_sample') {
            requestData.column = document.getElementById('ttest-column').value;
            requestData.mu = parseFloat(document.getElementById('test-value').value);
        } else if (testType === 'two_sample') {
            requestData.column = document.getElementById('ttest-data-column').value;
            requestData.group_column = document.getElementById('ttest-group-column').value;
        } else if (testType === 'paired') {
            requestData.column1 = document.getElementById('ttest-before').value;
            requestData.column2 = document.getElementById('ttest-after').value;
        }
        
        showLoading('Running T-test...');
        
        try {
            // Run real T-test via API
            const response = await fetch('/api/statistical/ttest', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(requestData)
            });
            
            const data = await response.json();
            
            if (data.success && data.result) {
                displayTTestResult(data.result, testType, alpha);
            } else {
                // Show the actual backend error message instead of generic one
                const errorMessage = data.error || 'Failed to run T-test';
                displayTTestError(errorMessage, testType, requestData);
            }
            
        } catch (error) {
            console.error('Error running t-test:', error);
            // Handle network errors
            if (error.message.includes('HTTP error!')) {
                displayTTestError('Server error occurred. Please check your data and parameters.', testType, requestData);
            } else {
                displayTTestError('Network error: ' + error.message, testType, requestData);
            }
        } finally {
            hideLoading();
        }
    }
    
    function displayTTestError(errorMessage, testType, requestData) {
        const container = document.getElementById('ttest-results');
        
        let parameterInfo = '';
        if (testType === 'one_sample') {
            parameterInfo = `<p><strong>Column:</strong> "${requestData.column || 'Not selected'}"</p>
                           <p><strong>Test Value (μ):</strong> ${requestData.mu || 'Not specified'}</p>`;
        } else if (testType === 'two_sample') {
            parameterInfo = `<p><strong>Data Column:</strong> "${requestData.column || 'Not selected'}"</p>
                           <p><strong>Group Column:</strong> "${requestData.group_column || 'Not selected'}"</p>`;
        } else if (testType === 'paired') {
            parameterInfo = `<p><strong>Before Column:</strong> "${requestData.column1 || 'Not selected'}"</p>
                           <p><strong>After Column:</strong> "${requestData.column2 || 'Not selected'}"</p>`;
        }
        
        container.innerHTML = `
            <div class="test-result error">
                <h4>T-Test Error</h4>
                <p><strong>Test Type:</strong> ${testType.replace('_', ' ').toUpperCase()}</p>
                ${parameterInfo}
                <p><strong>Error:</strong> ${errorMessage}</p>
                <div class="error-help">
                    <p><strong>Common solutions:</strong></p>
                    <ul>
                        <li>Ensure all required columns are selected</li>
                        <li>Check that data columns contain numeric data</li>
                        <li>Verify group columns have exactly 2 groups (for two-sample test)</li>
                        <li>Ensure sufficient data points in each group (minimum 2-3 per group)</li>
                        <li>Check for missing or invalid values</li>
                    </ul>
                    <p><strong>Test requirements:</strong></p>
                    <ul>
                        <li><strong>One-sample:</strong> Column with 3+ numeric values</li>
                        <li><strong>Two-sample:</strong> Data column + group column with exactly 2 groups, 2+ values per group</li>
                        <li><strong>Paired:</strong> Two numeric columns with 3+ paired observations</li>
                    </ul>
                </div>
            </div>
        `;
    }
    
    function displayTTestResult(result, testType, alpha) {
        const container = document.getElementById('ttest-results');
        
        // Safely handle undefined or null result
        if (!result || typeof result.statistic === 'undefined' || typeof result.p_value === 'undefined') {
            container.innerHTML = `
                <div class="test-result error">
                    <h4>T-Test Error</h4>
                    <p>Unable to perform T-test. Please check that the selected columns contain valid numeric data.</p>
                </div>
            `;
            return;
        }
        
        const isSignificant = result.p_value < alpha;
        const testName = testType.replace('_', ' ').toUpperCase() + ' T-Test';
        
        // Build comprehensive T-test result display
        let html = `
            <div style="background: white; border: 3px solid #007cba; border-radius: 15px; padding: 0; margin: 20px 0; overflow: hidden; box-shadow: 0 8px 25px rgba(0,124,186,0.15);">
                
                <!-- Header Section -->
                <div style="background: linear-gradient(135deg, #007cba 0%, #005580 50%, #003d5c 100%); padding: 25px 30px; color: white; position: relative; overflow: hidden;">
                    <div style="position: absolute; top: -20px; right: -20px; width: 100px; height: 100px; background: rgba(255,255,255,0.1); border-radius: 50%; transform: rotate(45deg);"></div>
                    <div style="position: relative; z-index: 2;">
                        <h3 style="margin: 0 0 10px 0; font-size: 24px; font-weight: bold; text-shadow: 1px 1px 2px rgba(0,0,0,0.3);">
                            🧪 ${testName} Results
                        </h3>
                        <div style="background: rgba(255,255,255,0.2); border: 2px solid rgba(255,255,255,0.3); border-radius: 20px; padding: 8px 16px; display: inline-block;">
                            <span style="font-size: 14px; font-weight: bold;">${isSignificant ? '✅ SIGNIFICANT' : '❌ NOT SIGNIFICANT'}</span>
                        </div>
                    </div>
                </div>

                <!-- Main Content -->
                <div style="padding: 25px;">
                    
                    <!-- Test Information -->
                    <div style="background: #f0f8ff; border: 2px solid #007cba; border-radius: 10px; padding: 20px; margin-bottom: 20px;">
                        <h4 style="color: #005580; margin: 0 0 15px 0; font-size: 18px;">📋 Test Information</h4>
                        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px;">
                            <div style="background: white; padding: 12px; border-radius: 8px; border-left: 4px solid #007cba;">
                                <strong style="color: #005580;">Test Type:</strong><br>
                                <span style="font-size: 16px; color: #333;">${testName}</span>
                            </div>
                            <div style="background: white; padding: 12px; border-radius: 8px; border-left: 4px solid #ff9800;">
                                <strong style="color: #e65100;">Significance Level:</strong><br>
                                <span style="font-size: 16px; color: #333;">α = ${alpha}</span>
                            </div>
                            <div style="background: white; padding: 12px; border-radius: 8px; border-left: 4px solid #4caf50;">
                                <strong style="color: #2e7d32;">Sample Size:</strong><br>
                                <span style="font-size: 16px; color: #333;">${result.sample_size || 'N/A'}</span>
                            </div>
                        </div>
                    </div>

                    <!-- Test Statistics -->
                    <div style="background: ${isSignificant ? '#e8f5e8' : '#fff3e0'}; border: 2px solid ${isSignificant ? '#4caf50' : '#ff9800'}; border-radius: 10px; padding: 20px; margin-bottom: 20px;">
                        <h4 style="color: ${isSignificant ? '#2e7d32' : '#f57c00'}; margin: 0 0 15px 0; font-size: 18px;">📊 Test Statistics</h4>
                        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 15px;">
                            <div style="background: white; padding: 15px; border-radius: 8px; text-align: center; border-left: 4px solid #2196f3;">
                                <div style="font-size: 28px; font-weight: bold; color: #1976d2;">${safeFormat(result.test_statistic || result.statistic)}</div>
                                <div style="color: #666; font-size: 14px;">T-statistic</div>
                            </div>
                            <div style="background: white; padding: 15px; border-radius: 8px; text-align: center; border-left: 4px solid #ff5722;">
                                <div style="font-size: 28px; font-weight: bold; color: #d84315;">${safeFormat(result.p_value)}</div>
                                <div style="color: #666; font-size: 14px;">P-value</div>
                            </div>
                            <div style="background: white; padding: 15px; border-radius: 8px; text-align: center; border-left: 4px solid #9c27b0;">
                                <div style="font-size: 28px; font-weight: bold; color: #7b1fa2;">${result.degrees_of_freedom || 'N/A'}</div>
                                <div style="color: #666; font-size: 14px;">Degrees of Freedom</div>
                            </div>
                            ${result.effect_size && typeof result.effect_size === 'number' ? `
                            <div style="background: white; padding: 15px; border-radius: 8px; text-align: center; border-left: 4px solid #607d8b;">
                                <div style="font-size: 28px; font-weight: bold; color: #455a64;">${safeFormat(result.effect_size, 3)}</div>
                                <div style="color: #666; font-size: 14px;">Effect Size</div>
                            </div>
                            ` : ''}
                        </div>
                    </div>
        `;

        // Group/Sample Information for specific test types
        if (testType === 'two_sample') {
            html += `
                    <!-- Group Statistics -->
                    <div style="background: #e0f2f1; border: 2px solid #4caf50; border-radius: 10px; padding: 20px; margin-bottom: 20px;">
                        <h4 style="color: #2e7d32; margin: 0 0 15px 0; font-size: 18px;">👥 Group Statistics</h4>
                        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 15px;">
                            ${result.group1_name ? `
                            <div style="background: white; padding: 15px; border-radius: 8px; border-left: 4px solid #4caf50;">
                                <div style="font-weight: bold; color: #2e7d32; margin-bottom: 10px; font-size: 16px;">${result.group1_name}</div>
                                <div style="margin: 5px 0;"><strong>Mean:</strong> ${safeFormat(result.group1_mean)}</div>
                                <div style="margin: 5px 0;"><strong>Sample Size:</strong> ${result.group1_size || 'N/A'}</div>
                            </div>
                            ` : ''}
                            ${result.group2_name ? `
                            <div style="background: white; padding: 15px; border-radius: 8px; border-left: 4px solid #ff9800;">
                                <div style="font-weight: bold; color: #f57c00; margin-bottom: 10px; font-size: 16px;">${result.group2_name}</div>
                                <div style="margin: 5px 0;"><strong>Mean:</strong> ${safeFormat(result.group2_mean)}</div>
                                <div style="margin: 5px 0;"><strong>Sample Size:</strong> ${result.group2_size || 'N/A'}</div>
                            </div>
                            ` : ''}
                        </div>
                        ${result.equal_variance_assumed !== undefined ? `
                        <div style="margin-top: 15px; text-align: center; background: rgba(0,124,186,0.1); padding: 10px; border-radius: 8px;">
                            <strong style="color: #005580;">Equal Variances Assumed: ${result.equal_variance_assumed ? 'Yes' : 'No'}</strong>
                            ${result.levene_test_p_value ? ` (Levene's test p-value: ${safeFormat(result.levene_test_p_value)})` : ''}
                        </div>
                        ` : ''}
                    </div>
            `;
        } else if (testType === 'paired') {
            html += `
                    <!-- Paired Sample Information -->
                    <div style="background: #e0f2f1; border: 2px solid #4caf50; border-radius: 10px; padding: 20px; margin-bottom: 20px;">
                        <h4 style="color: #2e7d32; margin: 0 0 15px 0; font-size: 18px;">🔗 Paired Sample Statistics</h4>
                        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px;">
                            <div style="background: white; padding: 15px; border-radius: 8px; text-align: center; border-left: 4px solid #4caf50;">
                                <div style="font-size: 24px; font-weight: bold; color: #2e7d32;">${safeFormat(result.mean_difference)}</div>
                                <div style="color: #666; font-size: 14px;">Mean Difference</div>
                            </div>
                            <div style="background: white; padding: 15px; border-radius: 8px; text-align: center; border-left: 4px solid #ff9800;">
                                <div style="font-size: 24px; font-weight: bold; color: #f57c00;">${result.sample_size || 'N/A'}</div>
                                <div style="color: #666; font-size: 14px;">Paired Observations</div>
                            </div>
                        </div>
                    </div>
            `;
        } else if (testType === 'one_sample') {
            html += `
                    <!-- One Sample Information -->
                    <div style="background: #e0f2f1; border: 2px solid #4caf50; border-radius: 10px; padding: 20px; margin-bottom: 20px;">
                        <h4 style="color: #2e7d32; margin: 0 0 15px 0; font-size: 18px;">📊 Sample Statistics</h4>
                        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px;">
                            <div style="background: white; padding: 15px; border-radius: 8px; text-align: center; border-left: 4px solid #4caf50;">
                                <div style="font-size: 24px; font-weight: bold; color: #2e7d32;">${safeFormat(result.sample_mean)}</div>
                                <div style="color: #666; font-size: 14px;">Sample Mean</div>
                            </div>
                            <div style="background: white; padding: 15px; border-radius: 8px; text-align: center; border-left: 4px solid #ff9800;">
                                <div style="font-size: 24px; font-weight: bold; color: #f57c00;">${safeFormat(result.test_value || result.mu)}</div>
                                <div style="color: #666; font-size: 14px;">Test Value (μ₀)</div>
                            </div>
                        </div>
                    </div>
            `;
        }

        // Conclusion Section
        html += `
                    <!-- Conclusion Section -->
                    <div style="background: ${isSignificant ? '#e8f5e8' : '#fff3e0'}; border: 2px solid ${isSignificant ? '#4caf50' : '#ff9800'}; border-radius: 10px; padding: 20px; margin-bottom: 20px;">
                        <h4 style="color: ${isSignificant ? '#2e7d32' : '#f57c00'}; margin: 0 0 15px 0; font-size: 18px;">🎯 Conclusion</h4>
                        <div style="background: white; padding: 15px; border-radius: 8px; border-left: 4px solid ${isSignificant ? '#4caf50' : '#ff9800'};">
                            <p style="margin: 0; font-size: 16px; line-height: 1.5; color: #333;">
                                <strong>${result.interpretation || (isSignificant ? 
                                    'The test is statistically significant. We reject the null hypothesis.' : 
                                    'The test is not statistically significant. We fail to reject the null hypothesis.')}</strong>
                            </p>
                            <div style="margin-top: 15px; padding: 10px; background: ${isSignificant ? '#e8f5e8' : '#fff3e0'}; border-radius: 8px;">
                                <p style="margin: 0; font-size: 14px; color: #666;">
                                    <strong>Statistical Decision:</strong> 
                                    ${isSignificant ? 
                                        `p-value (${safeFormat(result.p_value)}) < α (${alpha}) → Reject H₀` : 
                                        `p-value (${safeFormat(result.p_value)}) ≥ α (${alpha}) → Fail to reject H₀`}
                                </p>
                            </div>
                        </div>
                    </div>

                    <!-- Hypotheses Section -->
                    <div style="background: #e3f2fd; border: 2px solid #2196f3; border-radius: 10px; padding: 20px;">
                        <h4 style="color: #1976d2; margin: 0 0 15px 0; font-size: 18px;">📝 Hypotheses</h4>
                        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
                            <div style="background: white; padding: 15px; border-radius: 8px; border-left: 4px solid #2196f3;">
                                <div style="font-weight: bold; color: #1976d2; margin-bottom: 8px;">Null Hypothesis (H₀):</div>
                                <div style="color: #333; font-size: 14px;">${result.null_hypothesis || 'No significant difference exists'}</div>
                            </div>
                            <div style="background: white; padding: 15px; border-radius: 8px; border-left: 4px solid #ff5722;">
                                <div style="font-weight: bold; color: #d84315; margin-bottom: 8px;">Alternative Hypothesis (H₁):</div>
                                <div style="color: #333; font-size: 14px;">${result.alternative_hypothesis || 'A significant difference exists'}</div>
                            </div>
                        </div>
                    </div>

                </div>
            </div>
        `;
        
        container.innerHTML = html;
    }
    
    function handleChiTestTypeChange() {
        const testType = document.getElementById('chi-test-type').value;
        
        document.getElementById('chi-independence').style.display = 
            testType === 'independence' ? 'block' : 'none';
        document.getElementById('chi-goodness').style.display = 
            testType === 'goodness_of_fit' ? 'block' : 'none';
    }
    
    async function runANOVA() {
        const dependent = document.getElementById('anova-dependent').value;
        const independent = document.getElementById('anova-independent').value;
        const anovaType = document.getElementById('anova-type').value;
        
        if (!dependent || !independent) {
            showError('Please select dependent and independent variables');
            return;
        }
        
        // For two-way ANOVA, check if second independent variable is selected
        let independent2 = null;
        if (anovaType === 'two_way') {
            independent2 = document.getElementById('anova-independent2').value;
            if (!independent2) {
                showError('Please select the second independent variable for two-way ANOVA');
                return;
            }
        }
        
        showLoading('Running ANOVA...');
        
        try {
            // Build request body
            const requestBody = {
                dataset_id: currentDatasetId,
                dependent: dependent,
                anova_type: anovaType
            };
            
            // Add independent variables based on ANOVA type
            if (anovaType === 'one_way') {
                requestBody.independent = [independent];
            } else if (anovaType === 'two_way') {
                requestBody.independent = [independent, independent2];
            }
            
            // Run real ANOVA via API
            const response = await fetch('/api/statistical/anova', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(requestBody)
            });
            
            const data = await response.json();
            
            if (data.success && data.result) {
                displayANOVAResult(data.result, dependent, independent, anovaType, independent2);
            } else {
                // Show the actual backend error message instead of generic one
                const errorMessage = data.error || 'Failed to run ANOVA';
                displayANOVAError(errorMessage, dependent, independent, anovaType, independent2);
            }
            
        } catch (error) {
            console.error('Error running ANOVA:', error);
            // Handle network errors
            if (error.message.includes('HTTP error!')) {
                displayANOVAError('Server error occurred. Please check your data and parameters.', dependent, independent, anovaType, independent2);
            } else {
                displayANOVAError('Network error: ' + error.message, dependent, independent, anovaType, independent2);
            }
        } finally {
            hideLoading();
        }
    }
    
    function displayANOVAError(errorMessage, dependent, independent, anovaType, independent2) {
        const container = document.getElementById('anova-results');
        
        let independentInfo = `<p><strong>Independent Variable:</strong> "${independent || 'Not selected'}"</p>`;
        if (anovaType === 'two_way') {
            independentInfo += `<p><strong>Second Independent Variable:</strong> "${independent2 || 'Not selected'}"</p>`;
        }
        
        container.innerHTML = `
            <div class="test-result error">
                <h4>ANOVA Error</h4>
                <p><strong>Test Type:</strong> ${anovaType.replace('_', ' ').toUpperCase()}</p>
                <p><strong>Dependent Variable:</strong> "${dependent || 'Not selected'}"</p>
                ${independentInfo}
                <p><strong>Error:</strong> ${errorMessage}</p>
                <div class="error-help">
                    <p><strong>Common solutions:</strong></p>
                    <ul>
                        <li>Ensure all required variables are selected</li>
                        <li>Check that dependent variable contains numeric data</li>
                        <li>Verify independent variables have 2+ groups with sufficient data</li>
                        <li>For two-way ANOVA: select exactly 2 independent variables</li>
                        <li>Ensure at least 5 total observations for the test</li>
                        <li>Check for missing or invalid values</li>
                    </ul>
                    <p><strong>ANOVA requirements:</strong></p>
                    <ul>
                        <li><strong>One-way:</strong> Numeric dependent variable + 1 categorical independent variable with 2+ groups</li>
                        <li><strong>Two-way:</strong> Numeric dependent variable + 2 categorical independent variables</li>
                        <li><strong>Data:</strong> Minimum 5 observations total, at least 2 per group</li>
                    </ul>
                </div>
            </div>
        `;
    }
    
    function displayANOVAResult(result, dependent, independent, anovaType, independent2) {
        const container = document.getElementById('anova-results');
        
        // Safely handle undefined or null result
        if (!result || (anovaType === 'one_way' && (typeof result.f_statistic === 'undefined' || typeof result.p_value === 'undefined'))) {
            container.innerHTML = `
                <div class="test-result error">
                    <h4>ANOVA Error</h4>
                    <p>Unable to perform ANOVA test. Please check that the selected variables contain valid data.</p>
                </div>
            `;
            return;
        }

        // Determine significance based on test type
        let isSignificant = false;
        if (anovaType === 'two_way' && result.anova_table && result.anova_table.p_values) {
            isSignificant = result.anova_table.p_values.some(p => p !== null && p < 0.05);
        } else if (result.p_value !== undefined) {
            isSignificant = result.p_value < 0.05;
        }
        
        // Build the comprehensive result display
        let html = `
            <div style="background: white; border: 3px solid #007cba; border-radius: 15px; padding: 0; margin: 20px 0; overflow: hidden; box-shadow: 0 8px 25px rgba(0,124,186,0.15);">
                
                <!-- Header Section -->
                <div style="background: linear-gradient(135deg, #007cba 0%, #005580 50%, #003d5c 100%); padding: 25px 30px; color: white; position: relative; overflow: hidden;">
                    <div style="position: absolute; top: -20px; right: -20px; width: 100px; height: 100px; background: rgba(255,255,255,0.1); border-radius: 50%; transform: rotate(45deg);"></div>
                    <div style="position: relative; z-index: 2;">
                        <h3 style="margin: 0 0 10px 0; font-size: 24px; font-weight: bold; text-shadow: 1px 1px 2px rgba(0,0,0,0.3);">
                            📊 ${anovaType.replace('_', '-').toUpperCase()} ANOVA Results
                        </h3>
                        <div style="background: rgba(255,255,255,0.2); border: 2px solid rgba(255,255,255,0.3); border-radius: 20px; padding: 8px 16px; display: inline-block;">
                            <span style="font-size: 14px; font-weight: bold;">${isSignificant ? '✅ SIGNIFICANT' : '❌ NOT SIGNIFICANT'}</span>
                        </div>
                    </div>
                </div>

                <!-- Main Content -->
                <div style="padding: 25px;">
                    
                    <!-- Variables Section -->
                    <div style="background: #f0f8ff; border: 2px solid #007cba; border-radius: 10px; padding: 20px; margin-bottom: 20px;">
                        <h4 style="color: #005580; margin: 0 0 15px 0; font-size: 18px;">📋 Analysis Variables</h4>
                        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 15px;">
                            <div style="background: white; padding: 12px; border-radius: 8px; border-left: 4px solid #007cba;">
                                <strong style="color: #005580;">Dependent Variable:</strong><br>
                                <span style="font-size: 16px; color: #333;">${dependent}</span>
                            </div>
                            <div style="background: white; padding: 12px; border-radius: 8px; border-left: 4px solid #ff9800;">
                                <strong style="color: #e65100;">Independent Variable 1:</strong><br>
                                <span style="font-size: 16px; color: #333;">${independent}</span>
                            </div>
                            ${anovaType === 'two_way' && independent2 ? `
                            <div style="background: white; padding: 12px; border-radius: 8px; border-left: 4px solid #4caf50;">
                                <strong style="color: #2e7d32;">Independent Variable 2:</strong><br>
                                <span style="font-size: 16px; color: #333;">${independent2}</span>
                            </div>
                            ` : ''}
                        </div>
                        ${result.sample_size ? `
                        <div style="margin-top: 15px; text-align: center; background: rgba(0,124,186,0.1); padding: 10px; border-radius: 8px;">
                            <strong style="color: #005580;">Sample Size: ${result.sample_size}</strong>
                            ${result.groups_factor1 ? ` | Factor 1 Groups: ${result.groups_factor1}` : ''}
                            ${result.groups_factor2 ? ` | Factor 2 Groups: ${result.groups_factor2}` : ''}
                            ${result.min_cell_count ? ` | Min Cell Count: ${result.min_cell_count}` : ''}
                        </div>
                        ` : ''}
                    </div>
        `;

        // Statistics Section
        if (anovaType === 'two_way' && result.anova_table) {
            // Two-way ANOVA with detailed table
            html += `
                    <!-- ANOVA Table Section -->
                    <div style="background: #fff9e6; border: 2px solid #ff9800; border-radius: 10px; padding: 20px; margin-bottom: 20px;">
                        <h4 style="color: #e65100; margin: 0 0 15px 0; font-size: 18px;">📊 ANOVA Table</h4>
                        <div style="overflow-x: auto;">
                            <table style="width: 100%; border-collapse: collapse; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                                <thead>
                                    <tr style="background: linear-gradient(135deg, #ff9800, #f57c00); color: white;">
                                        <th style="padding: 15px; text-align: left; font-weight: bold;">Source of Variation</th>
                                        <th style="padding: 15px; text-align: center; font-weight: bold;">df</th>
                                        <th style="padding: 15px; text-align: center; font-weight: bold;">Sum of Squares</th>
                                        <th style="padding: 15px; text-align: center; font-weight: bold;">Mean Square</th>
                                        <th style="padding: 15px; text-align: center; font-weight: bold;">F-statistic</th>
                                        <th style="padding: 15px; text-align: center; font-weight: bold;">P-value</th>
                                        <th style="padding: 15px; text-align: center; font-weight: bold;">Significance</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    ${result.anova_table.sources.map((source, index) => {
                                        const pVal = result.anova_table.p_values[index];
                                        const isRowSignificant = pVal !== null && pVal < 0.05;
                                        const rowClass = isRowSignificant ? 'background: #e8f5e8;' : '';
                                        const significanceIcon = isRowSignificant ? '✅' : '❌';
                                        const significanceText = isRowSignificant ? 'Significant' : 'Not Significant';
                                        
                                        return `
                                        <tr style="${rowClass}">
                                            <td style="padding: 12px; border-bottom: 1px solid #e0e0e0; font-weight: bold; color: #333;">${source}</td>
                                            <td style="padding: 12px; border-bottom: 1px solid #e0e0e0; text-align: center;">${result.anova_table.degrees_of_freedom[index] || 'N/A'}</td>
                                            <td style="padding: 12px; border-bottom: 1px solid #e0e0e0; text-align: center;">${safeFormat(result.anova_table.sum_squares ? result.anova_table.sum_squares[index] : null)}</td>
                                            <td style="padding: 12px; border-bottom: 1px solid #e0e0e0; text-align: center;">${safeFormat(result.anova_table.mean_squares ? result.anova_table.mean_squares[index] : null)}</td>
                                            <td style="padding: 12px; border-bottom: 1px solid #e0e0e0; text-align: center; font-weight: bold;">${safeFormat(result.anova_table.f_statistics[index])}</td>
                                            <td style="padding: 12px; border-bottom: 1px solid #e0e0e0; text-align: center; font-weight: bold;">${safeFormat(pVal)}</td>
                                            <td style="padding: 12px; border-bottom: 1px solid #e0e0e0; text-align: center;">
                                                <span style="background: ${isRowSignificant ? '#4caf50' : '#ff9800'}; color: white; padding: 4px 8px; border-radius: 12px; font-size: 12px; font-weight: bold;">
                                                    ${significanceIcon} ${significanceText}
                                                </span>
                                            </td>
                                        </tr>
                                        `;
                                    }).join('')}
                                </tbody>
                            </table>
                        </div>
                    </div>
            `;

            // Model Statistics for Two-way ANOVA
            if (result.model_r_squared !== undefined) {
                html += `
                    <!-- Model Statistics Section -->
                    <div style="background: #f3e5f5; border: 2px solid #9c27b0; border-radius: 10px; padding: 20px; margin-bottom: 20px;">
                        <h4 style="color: #7b1fa2; margin: 0 0 15px 0; font-size: 18px;">📈 Model Statistics</h4>
                        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px;">
                            <div style="background: white; padding: 15px; border-radius: 8px; text-align: center; border-left: 4px solid #9c27b0;">
                                <div style="font-size: 24px; font-weight: bold; color: #7b1fa2;">${safeFormat(result.model_r_squared, 3)}</div>
                                <div style="color: #666; font-size: 14px;">R-squared</div>
                            </div>
                            <div style="background: white; padding: 15px; border-radius: 8px; text-align: center; border-left: 4px solid #673ab7;">
                                <div style="font-size: 24px; font-weight: bold; color: #512da8;">${safeFormat(result.model_adj_r_squared, 3)}</div>
                                <div style="color: #666; font-size: 14px;">Adjusted R-squared</div>
                            </div>
                            <div style="background: white; padding: 15px; border-radius: 8px; text-align: center; border-left: 4px solid #3f51b5;">
                                <div style="font-size: 24px; font-weight: bold; color: #303f9f;">${safeFormat(result.model_f_statistic)}</div>
                                <div style="color: #666; font-size: 14px;">Model F-statistic</div>
                            </div>
                            <div style="background: white; padding: 15px; border-radius: 8px; text-align: center; border-left: 4px solid #2196f3;">
                                <div style="font-size: 24px; font-weight: bold; color: #1976d2;">${safeFormat(result.model_f_pvalue)}</div>
                                <div style="color: #666; font-size: 14px;">Model P-value</div>
                            </div>
                        </div>
                    </div>
                `;
            }

        } else {
            // One-way ANOVA statistics
            html += `
                    <!-- Statistics Section -->
                    <div style="background: #e8f5e8; border: 2px solid #4caf50; border-radius: 10px; padding: 20px; margin-bottom: 20px;">
                        <h4 style="color: #2e7d32; margin: 0 0 15px 0; font-size: 18px;">📊 Test Statistics</h4>
                        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px;">
                            <div style="background: white; padding: 15px; border-radius: 8px; text-align: center; border-left: 4px solid #4caf50;">
                                <div style="font-size: 28px; font-weight: bold; color: #2e7d32;">${safeFormat(result.f_statistic)}</div>
                                <div style="color: #666; font-size: 14px;">F-statistic</div>
                            </div>
                            <div style="background: white; padding: 15px; border-radius: 8px; text-align: center; border-left: 4px solid #ff9800;">
                                <div style="font-size: 28px; font-weight: bold; color: #f57c00;">${safeFormat(result.p_value)}</div>
                                <div style="color: #666; font-size: 14px;">P-value</div>
                            </div>
                            <div style="background: white; padding: 15px; border-radius: 8px; text-align: center; border-left: 4px solid #9c27b0;">
                                <div style="font-size: 28px; font-weight: bold; color: #7b1fa2;">${result.degrees_of_freedom_between || 'N/A'}, ${result.degrees_of_freedom_within || 'N/A'}</div>
                                <div style="color: #666; font-size: 14px;">Degrees of Freedom</div>
                            </div>
                            ${result.eta_squared ? `
                            <div style="background: white; padding: 15px; border-radius: 8px; text-align: center; border-left: 4px solid #607d8b;">
                                <div style="font-size: 28px; font-weight: bold; color: #455a64;">${safeFormat(result.eta_squared, 3)}</div>
                                <div style="color: #666; font-size: 14px;">Effect Size (η²)</div>
                            </div>
                            ` : ''}
                        </div>
                    </div>
            `;
        }

        // Group Statistics (if available)
        if (result.group_statistics && Object.keys(result.group_statistics).length > 0) {
            html += `
                    <!-- Group Statistics Section -->
                    <div style="background: #e0f2f1; border: 2px solid #4caf50; border-radius: 10px; padding: 20px; margin-bottom: 20px;">
                        <h4 style="color: #2e7d32; margin: 0 0 15px 0; font-size: 18px;">👥 Group Statistics</h4>
                        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 15px;">
                            ${Object.entries(result.group_statistics).map(([group, stats]) => `
                                <div style="background: white; padding: 15px; border-radius: 8px; border-left: 4px solid #4caf50;">
                                    <div style="font-weight: bold; color: #2e7d32; margin-bottom: 10px; font-size: 16px;">${group}</div>
                                    <div style="margin: 5px 0;"><strong>Mean:</strong> ${safeFormat(stats.mean)}</div>
                                    <div style="margin: 5px 0;"><strong>Std Dev:</strong> ${safeFormat(stats.std || stats.standard_deviation)}</div>
                                    <div style="margin: 5px 0;"><strong>Count:</strong> ${stats.count || stats.size}</div>
                                </div>
                            `).join('')}
                        </div>
                    </div>
            `;
        }

        // Conclusion Section
        html += `
                    <!-- Conclusion Section -->
                    <div style="background: ${isSignificant ? '#e8f5e8' : '#fff3e0'}; border: 2px solid ${isSignificant ? '#4caf50' : '#ff9800'}; border-radius: 10px; padding: 20px; margin-bottom: 20px;">
                        <h4 style="color: ${isSignificant ? '#2e7d32' : '#f57c00'}; margin: 0 0 15px 0; font-size: 18px;">🎯 Conclusion</h4>
                        <div style="background: white; padding: 15px; border-radius: 8px; border-left: 4px solid ${isSignificant ? '#4caf50' : '#ff9800'};">
                            <p style="margin: 0; font-size: 16px; line-height: 1.5; color: #333;">
                                <strong>${result.interpretation || (isSignificant ? 
                                    'There is a statistically significant difference between groups.' : 
                                    'There is no statistically significant difference between groups.')}</strong>
                            </p>
                            ${result.significant_effects && result.significant_effects.length > 0 ? `
                            <div style="margin-top: 15px; padding: 10px; background: ${isSignificant ? '#e8f5e8' : '#fff3e0'}; border-radius: 8px;">
                                <strong>Significant Effects:</strong>
                                <ul style="margin: 10px 0; padding-left: 20px;">
                                    ${result.significant_effects.map(effect => `<li>${effect}</li>`).join('')}
                                </ul>
                            </div>
                            ` : ''}
                        </div>
                    </div>
        `;

        // Post-hoc Analysis (if available)
        if (result.post_hoc) {
            html += `
                    <!-- Post-hoc Analysis Section -->
                    <div style="background: #e3f2fd; border: 2px solid #2196f3; border-radius: 10px; padding: 20px;">
                        <h4 style="color: #1976d2; margin: 0 0 15px 0; font-size: 18px;">🔍 Post-hoc Analysis</h4>
                        <div style="background: white; padding: 15px; border-radius: 8px; border-left: 4px solid #2196f3;">
                            <p style="margin: 0; font-size: 16px; color: #333;">
                                <strong>${result.post_hoc.test}:</strong> ${result.post_hoc.summary || 'Multiple comparisons performed'}
                            </p>
                        </div>
                    </div>
            `;
        }

        html += `
                </div>
            </div>
        `;
        
        container.innerHTML = html;
    }
    
    async function runChiSquareTest() {
        const testType = document.getElementById('chi-test-type').value;
        
        showLoading('Running chi-square test...');
        
        try {
            // Prepare request data based on test type
            let requestData = {
                dataset_id: currentDatasetId,
                test_type: testType
            };
            
            if (testType === 'independence') {
                requestData.var1 = document.getElementById('chi-var1').value;
                requestData.var2 = document.getElementById('chi-var2').value;
            } else if (testType === 'goodness_of_fit') {
                requestData.var1 = document.getElementById('chi-observed').value;
                requestData.var2 = null; // Not needed for goodness of fit
            }
            
            // Run real chi-square test via API
            const response = await fetch('/api/statistical/chi_square', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(requestData)
            });
            
            const data = await response.json();
            
            if (data.success && data.result) {
                displayChiSquareResult(data.result, testType);
            } else {
                // Show the actual backend error message instead of generic one
                const errorMessage = data.error || 'Failed to run chi-square test';
                displayChiSquareError(errorMessage, testType);
            }
            
        } catch (error) {
            console.error('Error running chi-square test:', error);
            displayChiSquareError('Network error: ' + error.message, testType);
        } finally {
            hideLoading();
        }
    }
    
    function displayChiSquareError(errorMessage, testType) {
        const container = document.getElementById('chi-square-results');
        
        container.innerHTML = `
            <div class="test-result error">
                <h4>Chi-Square Test Error</h4>
                <p><strong>Test Type:</strong> ${testType.replace('_', ' ').toUpperCase()}</p>
                <p><strong>Error:</strong> ${errorMessage}</p>
                <div class="error-help">
                    <p><strong>Common solutions:</strong></p>
                    <ul>
                        <li>Ensure variables are selected for the test type</li>
                        <li>Check that variables contain categorical data</li>
                        <li>Verify sufficient observations in each category</li>
                        <li>For independence test: select two categorical variables</li>
                        <li>For goodness of fit: select one categorical variable</li>
                    </ul>
                </div>
            </div>
        `;
    }

    function displayChiSquareResult(result, testType) {
        const container = document.getElementById('chi-square-results');
        
        // Safely handle undefined or null result
        if (!result || typeof result.chi2_statistic === 'undefined' || typeof result.p_value === 'undefined') {
            container.innerHTML = `
                <div class="test-result error">
                    <h4>Chi-Square Test Error</h4>
                    <p>Unable to perform Chi-square test. Please check that the selected variables contain valid categorical data.</p>
                </div>
            `;
            return;
        }
        
        const isSignificant = result.p_value < 0.05;
        const testName = `Chi-Square Test of ${testType.charAt(0).toUpperCase() + testType.slice(1)}`;
        
        // Build comprehensive Chi-square result display
        let html = `
            <div style="background: white; border: 3px solid #007cba; border-radius: 15px; padding: 0; margin: 20px 0; overflow: hidden; box-shadow: 0 8px 25px rgba(0,124,186,0.15);">
                
                <!-- Header Section -->
                <div style="background: linear-gradient(135deg, #007cba 0%, #005580 50%, #003d5c 100%); padding: 25px 30px; color: white; position: relative; overflow: hidden;">
                    <div style="position: absolute; top: -20px; right: -20px; width: 100px; height: 100px; background: rgba(255,255,255,0.1); border-radius: 50%; transform: rotate(45deg);"></div>
                    <div style="position: relative; z-index: 2;">
                        <h3 style="margin: 0 0 10px 0; font-size: 24px; font-weight: bold; text-shadow: 1px 1px 2px rgba(0,0,0,0.3);">
                            🎲 ${testName} Results
                        </h3>
                        <div style="background: rgba(255,255,255,0.2); border: 2px solid rgba(255,255,255,0.3); border-radius: 20px; padding: 8px 16px; display: inline-block;">
                            <span style="font-size: 14px; font-weight: bold;">${isSignificant ? '✅ SIGNIFICANT' : '❌ NOT SIGNIFICANT'}</span>
                        </div>
                    </div>
                </div>

                <!-- Main Content -->
                <div style="padding: 25px;">
                    
                    <!-- Test Information -->
                    <div style="background: #f0f8ff; border: 2px solid #007cba; border-radius: 10px; padding: 20px; margin-bottom: 20px;">
                        <h4 style="color: #005580; margin: 0 0 15px 0; font-size: 18px;">📋 Test Information</h4>
                        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px;">
                            <div style="background: white; padding: 12px; border-radius: 8px; border-left: 4px solid #007cba;">
                                <strong style="color: #005580;">Test Type:</strong><br>
                                <span style="font-size: 16px; color: #333;">${testName}</span>
                            </div>
                            <div style="background: white; padding: 12px; border-radius: 8px; border-left: 4px solid #ff9800;">
                                <strong style="color: #e65100;">Variables:</strong><br>
                                <span style="font-size: 16px; color: #333;">${result.column1}${result.column2 ? ' × ' + result.column2 : ''}</span>
                            </div>
                            <div style="background: white; padding: 12px; border-radius: 8px; border-left: 4px solid #4caf50;">
                                <strong style="color: #2e7d32;">Significance Level:</strong><br>
                                <span style="font-size: 16px; color: #333;">α = 0.05</span>
                            </div>
                        </div>
                    </div>

                    <!-- Test Statistics -->
                    <div style="background: ${isSignificant ? '#e8f5e8' : '#fff3e0'}; border: 2px solid ${isSignificant ? '#4caf50' : '#ff9800'}; border-radius: 10px; padding: 20px; margin-bottom: 20px;">
                        <h4 style="color: ${isSignificant ? '#2e7d32' : '#f57c00'}; margin: 0 0 15px 0; font-size: 18px;">📊 Test Statistics</h4>
                        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 15px;">
                            <div style="background: white; padding: 15px; border-radius: 8px; text-align: center; border-left: 4px solid #2196f3;">
                                <div style="font-size: 28px; font-weight: bold; color: #1976d2;">${safeFormat(result.chi2_statistic)}</div>
                                <div style="color: #666; font-size: 14px;">Chi-Square (χ²)</div>
                            </div>
                            <div style="background: white; padding: 15px; border-radius: 8px; text-align: center; border-left: 4px solid #ff5722;">
                                <div style="font-size: 28px; font-weight: bold; color: #d84315;">${safeFormat(result.p_value)}</div>
                                <div style="color: #666; font-size: 14px;">P-value</div>
                            </div>
                            <div style="background: white; padding: 15px; border-radius: 8px; text-align: center; border-left: 4px solid #9c27b0;">
                                <div style="font-size: 28px; font-weight: bold; color: #7b1fa2;">${result.degrees_of_freedom || 'N/A'}</div>
                                <div style="color: #666; font-size: 14px;">Degrees of Freedom</div>
                            </div>
                            ${result.cramers_v ? `
                            <div style="background: white; padding: 15px; border-radius: 8px; text-align: center; border-left: 4px solid #607d8b;">
                                <div style="font-size: 28px; font-weight: bold; color: #455a64;">${safeFormat(result.cramers_v, 3)}</div>
                                <div style="color: #666; font-size: 14px;">Cramér's V (Effect Size)</div>
                            </div>
                            ` : ''}
                        </div>
                    </div>
        `;

        // Contingency Table (if available)
        if (result.contingency_table) {
            html += `
                    <!-- Contingency Table -->
                    <div style="background: #e0f2f1; border: 2px solid #4caf50; border-radius: 10px; padding: 20px; margin-bottom: 20px;">
                        <h4 style="color: #2e7d32; margin: 0 0 15px 0; font-size: 18px;">📊 Contingency Table</h4>
                        <div style="overflow-x: auto;">
                            <table style="width: 100%; border-collapse: collapse; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                                <thead>
                                    <tr style="background: linear-gradient(135deg, #4caf50, #2e7d32); color: white;">
                                        <th style="padding: 12px; font-weight: bold; text-align: left;">Row / Column</th>
                                        ${Object.keys(result.contingency_table).length > 0 ? 
                                            Object.keys(Object.values(result.contingency_table)[0]).map(col => 
                                                `<th style="padding: 12px; font-weight: bold; text-align: center;">${col}</th>`
                                            ).join('') : ''}
                                    </tr>
                                </thead>
                                <tbody>
                                    ${Object.entries(result.contingency_table).map(([row, cols]) => `
                                        <tr style="border-bottom: 1px solid #e0e0e0;">
                                            <td style="padding: 12px; font-weight: bold; background: #f5f5f5;">${row}</td>
                                            ${Object.values(cols).map(val => 
                                                `<td style="padding: 12px; text-align: center;">${val}</td>`
                                            ).join('')}
                                        </tr>
                                    `).join('')}
                                </tbody>
                            </table>
                        </div>
                    </div>
            `;
        }

        // Assumption Check
        if (result.assumption_met !== undefined) {
            const assumptionColor = result.assumption_met ? '#4caf50' : '#ff9800';
            const assumptionBg = result.assumption_met ? '#e8f5e8' : '#fff3e0';
            
            html += `
                    <!-- Assumption Check -->
                    <div style="background: ${assumptionBg}; border: 2px solid ${assumptionColor}; border-radius: 10px; padding: 20px; margin-bottom: 20px;">
                        <h4 style="color: ${assumptionColor}; margin: 0 0 15px 0; font-size: 18px;">⚠️ Assumption Check</h4>
                        <div style="background: white; padding: 15px; border-radius: 8px; border-left: 4px solid ${assumptionColor};">
                            <div style="display: flex; align-items: center; gap: 10px;">
                                <div style="font-size: 24px;">${result.assumption_met ? '✅' : '⚠️'}</div>
                                <div>
                                    <strong style="color: ${assumptionColor};">
                                        ${result.assumption_met ? 'Assumptions Met' : 'Assumptions May Be Violated'}
                                    </strong>
                                    <p style="margin: 8px 0 0 0; color: #666; font-size: 14px;">
                                        ${result.assumption_met ? 
                                            'All expected frequencies ≥ 5. Chi-square test is appropriate.' : 
                                            'Some expected frequencies < 5. Results may be less reliable. Consider Fisher\'s exact test.'}
                                    </p>
                                    ${result.min_expected_frequency ? `
                                    <p style="margin: 8px 0 0 0; color: #666; font-size: 14px;">
                                        <strong>Minimum Expected Frequency:</strong> ${safeFormat(result.min_expected_frequency)}
                                    </p>
                                    ` : ''}
                                </div>
                            </div>
                        </div>
                    </div>
            `;
        }

        // Conclusion Section
        html += `
                    <!-- Conclusion Section -->
                    <div style="background: ${isSignificant ? '#e8f5e8' : '#fff3e0'}; border: 2px solid ${isSignificant ? '#4caf50' : '#ff9800'}; border-radius: 10px; padding: 20px; margin-bottom: 20px;">
                        <h4 style="color: ${isSignificant ? '#2e7d32' : '#f57c00'}; margin: 0 0 15px 0; font-size: 18px;">🎯 Conclusion</h4>
                        <div style="background: white; padding: 15px; border-radius: 8px; border-left: 4px solid ${isSignificant ? '#4caf50' : '#ff9800'};">
                            <p style="margin: 0; font-size: 16px; line-height: 1.5; color: #333;">
                                <strong>${result.interpretation || (isSignificant ? 
                                    'There is a statistically significant association between the variables.' : 
                                    'There is no statistically significant association between the variables.')}</strong>
                            </p>
                            <div style="margin-top: 15px; padding: 10px; background: ${isSignificant ? '#e8f5e8' : '#fff3e0'}; border-radius: 8px;">
                                <p style="margin: 0; font-size: 14px; color: #666;">
                                    <strong>Statistical Decision:</strong> 
                                    ${isSignificant ? 
                                        `χ² = ${safeFormat(result.chi2_statistic)}, p = ${safeFormat(result.p_value)} < 0.05 → Reject H₀` : 
                                        `χ² = ${safeFormat(result.chi2_statistic)}, p = ${safeFormat(result.p_value)} ≥ 0.05 → Fail to reject H₀`}
                                </p>
                            </div>
                        </div>
                    </div>

                    <!-- Hypotheses Section -->
                    <div style="background: #e3f2fd; border: 2px solid #2196f3; border-radius: 10px; padding: 20px;">
                        <h4 style="color: #1976d2; margin: 0 0 15px 0; font-size: 18px;">📝 Hypotheses</h4>
                        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
                            <div style="background: white; padding: 15px; border-radius: 8px; border-left: 4px solid #2196f3;">
                                <div style="font-weight: bold; color: #1976d2; margin-bottom: 8px;">Null Hypothesis (H₀):</div>
                                <div style="color: #333; font-size: 14px;">${result.null_hypothesis || 'Variables are independent'}</div>
                            </div>
                            <div style="background: white; padding: 15px; border-radius: 8px; border-left: 4px solid #ff5722;">
                                <div style="font-weight: bold; color: #d84315; margin-bottom: 8px;">Alternative Hypothesis (H₁):</div>
                                <div style="color: #333; font-size: 14px;">${result.alternative_hypothesis || 'Variables are not independent'}</div>
                            </div>
                        </div>
                    </div>

                </div>
            </div>
        `;
        
        container.innerHTML = html;
    }
    
    // Non-parametric test handlers
    function handleNonParametricTypeChange() {
        const testType = document.getElementById('nonparam-test-type').value;
        
        // Hide all config sections
        document.querySelectorAll('.nonparam-config').forEach(section => {
            section.style.display = 'none';
        });
        
        // Show relevant section
        const sectionMap = {
            'mann_whitney': 'mann-whitney-config',
            'wilcoxon': 'wilcoxon-config',
            'kruskal_wallis': 'kruskal-config',
            'friedman': 'friedman-config'
        };
        
        const sectionId = sectionMap[testType];
        if (sectionId) {
            document.getElementById(sectionId).style.display = 'block';
        }
    }

    async function runNonParametricTest() {
        const testType = document.getElementById('nonparam-test-type').value;
        
        let endpoint = '/api/statistical/';
        let requestData = { dataset_id: currentDatasetId };
        
        // Get test-specific parameters and set endpoint
        if (testType === 'mann_whitney') {
            endpoint += 'mann_whitney';
            requestData.column = document.getElementById('mw-data-column').value;
            requestData.group_column = document.getElementById('mw-group-column').value;
        } else if (testType === 'wilcoxon') {
            endpoint += 'wilcoxon';
            requestData.column1 = document.getElementById('wilcoxon-col1').value;
            requestData.column2 = document.getElementById('wilcoxon-col2').value;
        } else if (testType === 'kruskal_wallis') {
            endpoint += 'kruskal_wallis';
            requestData.dependent_var = document.getElementById('kw-dependent').value;
            requestData.independent_var = document.getElementById('kw-independent').value;
        } else if (testType === 'friedman') {
            endpoint += 'friedman';
            const selectedColumns = Array.from(document.getElementById('friedman-columns').selectedOptions)
                .map(option => option.value);
            requestData.columns = selectedColumns;
        }
        
        showLoading('Running non-parametric test...');
        
        try {
            const response = await fetch(endpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(requestData)
            });
            
            const data = await response.json();
            
            if (data.success && data.results) {
                displayNonParametricResult(data.results, testType);
            } else {
                // Show the actual backend error message instead of generic one
                const errorMessage = data.error || 'Failed to run non-parametric test';
                displayNonParametricError(errorMessage, testType, requestData);
            }
            
        } catch (error) {
            console.error('Error running non-parametric test:', error);
            // Handle network errors
            if (error.message.includes('HTTP error!')) {
                displayNonParametricError('Server error occurred. Please check your data and parameters.', testType, requestData);
            } else {
                displayNonParametricError('Network error: ' + error.message, testType, requestData);
            }
        } finally {
            hideLoading();
        }
    }

    function displayNonParametricError(errorMessage, testType, requestData) {
        const container = document.getElementById('nonparametric-results');
        
        let parameterInfo = '';
        if (testType === 'mann_whitney') {
            parameterInfo = `<p><strong>Data Column:</strong> "${requestData.column || 'Not selected'}"</p>
                           <p><strong>Group Column:</strong> "${requestData.group_column || 'Not selected'}"</p>`;
        } else if (testType === 'wilcoxon') {
            parameterInfo = `<p><strong>Column 1:</strong> "${requestData.column1 || 'Not selected'}"</p>
                           <p><strong>Column 2:</strong> "${requestData.column2 || 'Not selected'}"</p>`;
        } else if (testType === 'kruskal_wallis') {
            parameterInfo = `<p><strong>Dependent Variable:</strong> "${requestData.dependent_var || 'Not selected'}"</p>
                           <p><strong>Independent Variable:</strong> "${requestData.independent_var || 'Not selected'}"</p>`;
        } else if (testType === 'friedman') {
            parameterInfo = `<p><strong>Columns:</strong> ${requestData.columns ? requestData.columns.join(', ') : 'Not selected'}</p>`;
        }
        
        container.innerHTML = `
            <div class="test-result error">
                <h4>Non-Parametric Test Error</h4>
                <p><strong>Test Type:</strong> ${testType.replace('_', ' ').toUpperCase()}</p>
                ${parameterInfo}
                <p><strong>Error:</strong> ${errorMessage}</p>
                <div class="error-help">
                    <p><strong>Common solutions:</strong></p>
                    <ul>
                        <li>Ensure all required columns are selected</li>
                        <li>Check that data columns contain numeric data</li>
                        <li>Verify group columns have the correct number of groups</li>
                        <li>Ensure sufficient data points per group</li>
                        <li>Check for missing or invalid values</li>
                    </ul>
                    <p><strong>Test requirements:</strong></p>
                    <ul>
                        <li><strong>Mann-Whitney:</strong> Data column + group column with exactly 2 groups, 3+ values per group</li>
                        <li><strong>Wilcoxon:</strong> Two numeric columns with 6+ paired observations</li>
                        <li><strong>Kruskal-Wallis:</strong> Numeric dependent + categorical independent with 2+ groups</li>
                        <li><strong>Friedman:</strong> 3+ numeric columns with 6+ complete observations</li>
                    </ul>
                </div>
            </div>
        `;
    }

    function displayNonParametricResult(result, testType) {
        const container = document.getElementById('nonparametric-results');
        
        const isSignificant = result.p_value < 0.05;
        const testName = testType.replace('_', ' ').toUpperCase() + ' Test';
        
        // Get the appropriate test statistic
        const testStatistic = result.test_statistic || result.statistic || result.h_statistic || result.u_statistic || result.chi2_statistic;
        
        // Build comprehensive non-parametric test result display
        let html = `
            <div style="background: white; border: 3px solid #007cba; border-radius: 15px; padding: 0; margin: 20px 0; overflow: hidden; box-shadow: 0 8px 25px rgba(0,124,186,0.15);">
                
                <!-- Header Section -->
                <div style="background: linear-gradient(135deg, #007cba 0%, #005580 50%, #003d5c 100%); padding: 25px 30px; color: white; position: relative; overflow: hidden;">
                    <div style="position: absolute; top: -20px; right: -20px; width: 100px; height: 100px; background: rgba(255,255,255,0.1); border-radius: 50%; transform: rotate(45deg);"></div>
                    <div style="position: relative; z-index: 2;">
                        <h3 style="margin: 0 0 10px 0; font-size: 24px; font-weight: bold; text-shadow: 1px 1px 2px rgba(0,0,0,0.3);">
                            📊 ${testName} Results
                        </h3>
                        <div style="background: rgba(255,255,255,0.2); border: 2px solid rgba(255,255,255,0.3); border-radius: 20px; padding: 8px 16px; display: inline-block;">
                            <span style="font-size: 14px; font-weight: bold;">${isSignificant ? '✅ SIGNIFICANT' : '❌ NOT SIGNIFICANT'}</span>
                        </div>
                    </div>
                </div>

                <!-- Main Content -->
                <div style="padding: 25px;">
                    
                    <!-- Test Information -->
                    <div style="background: #f0f8ff; border: 2px solid #007cba; border-radius: 10px; padding: 20px; margin-bottom: 20px;">
                        <h4 style="color: #005580; margin: 0 0 15px 0; font-size: 18px;">📋 Test Information</h4>
                        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px;">
                            <div style="background: white; padding: 12px; border-radius: 8px; border-left: 4px solid #007cba;">
                                <strong style="color: #005580;">Test Type:</strong><br>
                                <span style="font-size: 16px; color: #333;">${testName}</span>
                            </div>
                            <div style="background: white; padding: 12px; border-radius: 8px; border-left: 4px solid #ff9800;">
                                <strong style="color: #e65100;">Method:</strong><br>
                                <span style="font-size: 16px; color: #333;">Non-parametric</span>
                            </div>
                            <div style="background: white; padding: 12px; border-radius: 8px; border-left: 4px solid #4caf50;">
                                <strong style="color: #2e7d32;">Sample Size:</strong><br>
                                <span style="font-size: 16px; color: #333;">${result.sample_size || (result.group1_size && result.group2_size ? result.group1_size + result.group2_size : 'N/A')}</span>
                            </div>
                        </div>
                    </div>

                    <!-- Test Statistics -->
                    <div style="background: ${isSignificant ? '#e8f5e8' : '#fff3e0'}; border: 2px solid ${isSignificant ? '#4caf50' : '#ff9800'}; border-radius: 10px; padding: 20px; margin-bottom: 20px;">
                        <h4 style="color: ${isSignificant ? '#2e7d32' : '#f57c00'}; margin: 0 0 15px 0; font-size: 18px;">📊 Test Statistics</h4>
                        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 15px;">
                            <div style="background: white; padding: 15px; border-radius: 8px; text-align: center; border-left: 4px solid #2196f3;">
                                <div style="font-size: 28px; font-weight: bold; color: #1976d2;">${safeFormat(testStatistic)}</div>
                                <div style="color: #666; font-size: 14px;">${testType === 'mann_whitney' ? 'U-statistic' : 
                                    testType === 'wilcoxon' ? 'W-statistic' :
                                    testType === 'kruskal_wallis' ? 'H-statistic' :
                                    testType === 'friedman' ? 'χ²-statistic' : 'Test Statistic'}</div>
                            </div>
                            <div style="background: white; padding: 15px; border-radius: 8px; text-align: center; border-left: 4px solid #ff5722;">
                                <div style="font-size: 28px; font-weight: bold; color: #d84315;">${safeFormat(result.p_value)}</div>
                                <div style="color: #666; font-size: 14px;">P-value</div>
                            </div>
                            ${result.effect_size ? `
                            <div style="background: white; padding: 15px; border-radius: 8px; text-align: center; border-left: 4px solid #607d8b;">
                                <div style="font-size: 28px; font-weight: bold; color: #455a64;">${safeFormat(result.effect_size, 3)}</div>
                                <div style="color: #666; font-size: 14px;">Effect Size</div>
                            </div>
                            ` : ''}
                        </div>
                    </div>
        `;

        // Group Statistics (if available)
        if (result.group_statistics && Object.keys(result.group_statistics).length > 0) {
            html += `
                    <!-- Group Statistics -->
                    <div style="background: #e0f2f1; border: 2px solid #4caf50; border-radius: 10px; padding: 20px; margin-bottom: 20px;">
                        <h4 style="color: #2e7d32; margin: 0 0 15px 0; font-size: 18px;">👥 Group Statistics</h4>
                        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 15px;">
                            ${Object.entries(result.group_statistics).map(([group, stats]) => `
                                <div style="background: white; padding: 15px; border-radius: 8px; border-left: 4px solid #4caf50;">
                                    <div style="font-weight: bold; color: #2e7d32; margin-bottom: 10px; font-size: 16px;">${group}</div>
                                    <div style="margin: 5px 0;"><strong>Median:</strong> ${safeFormat(stats.median)}</div>
                                    ${stats.mean_rank ? `<div style="margin: 5px 0;"><strong>Mean Rank:</strong> ${safeFormat(stats.mean_rank)}</div>` : ''}
                                    <div style="margin: 5px 0;"><strong>Size:</strong> ${stats.size}</div>
                                </div>
                            `).join('')}
                        </div>
                    </div>
            `;
        }

        // Post-hoc Analysis (if available)
        if (result.post_hoc && result.post_hoc.length > 0) {
            html += `
                    <!-- Post-hoc Analysis -->
                    <div style="background: #e3f2fd; border: 2px solid #2196f3; border-radius: 10px; padding: 20px; margin-bottom: 20px;">
                        <h4 style="color: #1976d2; margin: 0 0 15px 0; font-size: 18px;">🔍 Post-hoc Pairwise Comparisons</h4>
                        <div style="overflow-x: auto;">
                            <table style="width: 100%; border-collapse: collapse; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                                <thead>
                                    <tr style="background: linear-gradient(135deg, #2196f3, #1976d2); color: white;">
                                        <th style="padding: 12px; font-weight: bold; text-align: left;">Group 1</th>
                                        <th style="padding: 12px; font-weight: bold; text-align: left;">Group 2</th>
                                        <th style="padding: 12px; font-weight: bold; text-align: center;">U-statistic</th>
                                        <th style="padding: 12px; font-weight: bold; text-align: center;">P-value</th>
                                        <th style="padding: 12px; font-weight: bold; text-align: center;">Significant</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    ${result.post_hoc.map(comparison => `
                                        <tr style="border-bottom: 1px solid #e0e0e0;">
                                            <td style="padding: 12px; font-weight: bold;">${comparison.group1}</td>
                                            <td style="padding: 12px; font-weight: bold;">${comparison.group2}</td>
                                            <td style="padding: 12px; text-align: center;">${safeFormat(comparison.u_statistic)}</td>
                                            <td style="padding: 12px; text-align: center;">${safeFormat(comparison.p_value)}</td>
                                            <td style="padding: 12px; text-align: center;">
                                                <span style="background: ${comparison.significant ? '#4caf50' : '#ff9800'}; color: white; padding: 4px 8px; border-radius: 12px; font-size: 12px; font-weight: bold;">
                                                    ${comparison.significant ? '✅ Yes' : '❌ No'}
                                                </span>
                                            </td>
                                        </tr>
                                    `).join('')}
                                </tbody>
                            </table>
                        </div>
                    </div>
            `;
        }

        // Comprehensive Conclusion
        let detailedConclusion = '';
        if (isSignificant) {
            detailedConclusion = `
                <strong>✅ Statistically Significant Result:</strong>
                <p>The ${testName} indicates a statistically significant difference (p = ${safeFormat(result.p_value)} < 0.05). This means:</p>
                <ul>
                    <li>✅ The null hypothesis is rejected</li>
                    <li>✅ There is evidence of a true difference between groups/conditions</li>
                    <li>✅ The effect is unlikely due to random chance</li>
                    <li>📊 Non-parametric approach was appropriate for this data</li>
                </ul>
            `;
        } else {
            detailedConclusion = `
                <strong>❌ Not Statistically Significant:</strong>
                <p>The ${testName} does not show a statistically significant difference (p = ${safeFormat(result.p_value)} ≥ 0.05). This means:</p>
                <ul>
                    <li>❌ We fail to reject the null hypothesis</li>
                    <li>❌ Insufficient evidence of a true difference</li>
                    <li>❌ The observed difference could be due to random chance</li>
                    <li>📊 Consider larger sample sizes or different approaches</li>
                </ul>
            `;
        }

        html += `
                    <!-- Conclusion Section -->
                    <div style="background: ${isSignificant ? '#e8f5e8' : '#fff3e0'}; border: 2px solid ${isSignificant ? '#4caf50' : '#ff9800'}; border-radius: 10px; padding: 20px; margin-bottom: 20px;">
                        <h4 style="color: ${isSignificant ? '#2e7d32' : '#f57c00'}; margin: 0 0 15px 0; font-size: 18px;">🎯 Conclusion & Interpretation</h4>
                        <div style="background: white; padding: 15px; border-radius: 8px; border-left: 4px solid ${isSignificant ? '#4caf50' : '#ff9800'};">
                            <div style="font-size: 16px; line-height: 1.6; color: #333;">
                                ${detailedConclusion}
                            </div>
                        </div>
                    </div>

                    <!-- Hypotheses Section -->
                    <div style="background: #e3f2fd; border: 2px solid #2196f3; border-radius: 10px; padding: 20px;">
                        <h4 style="color: #1976d2; margin: 0 0 15px 0; font-size: 18px;">📝 Statistical Hypotheses</h4>
                        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
                            <div style="background: white; padding: 15px; border-radius: 8px; border-left: 4px solid #2196f3;">
                                <div style="font-weight: bold; color: #1976d2; margin-bottom: 8px;">Null Hypothesis (H₀):</div>
                                <div style="color: #333; font-size: 14px;">${result.null_hypothesis || 'No difference between groups/conditions'}</div>
                            </div>
                            <div style="background: white; padding: 15px; border-radius: 8px; border-left: 4px solid #ff5722;">
                                <div style="font-weight: bold; color: #d84315; margin-bottom: 8px;">Alternative Hypothesis (H₁):</div>
                                <div style="color: #333; font-size: 14px;">${result.alternative_hypothesis || 'There is a difference between groups/conditions'}</div>
                            </div>
                        </div>
                    </div>

                </div>
            </div>
        `;
        
        container.innerHTML = html;
    }

    async function runVarianceTest() {
        const testType = document.getElementById('variance-test-type').value;
        const selectedColumns = Array.from(document.getElementById('variance-columns').selectedOptions)
            .map(option => option.value);
        
        if (selectedColumns.length < 2) {
            showError('Please select at least 2 columns');
            return;
        }
        
        showLoading('Running variance test...');
        
        try {
            const response = await fetch('/api/statistical/variance', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    dataset_id: currentDatasetId,
                    columns: selectedColumns,
                    test_type: testType
                })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            
            if (data.success && data.results) {
                displayVarianceResult(data.results, testType);
            } else {
                throw new Error(data.error || 'Failed to run variance test');
            }
            
        } catch (error) {
            console.error('Error running variance test:', error);
            showError('Failed to run variance test: ' + error.message);
        } finally {
            hideLoading();
        }
    }

    function displayVarianceResult(result, testType) {
        const container = document.getElementById('variance-results');
        
        const isSignificant = result.p_value < 0.05;
        const testName = testType.toUpperCase() + ' Variance Test';
        
        // Build comprehensive variance test result display
        let html = `
            <div style="background: white; border: 3px solid #007cba; border-radius: 15px; padding: 0; margin: 20px 0; overflow: hidden; box-shadow: 0 8px 25px rgba(0,124,186,0.15);">
                
                <!-- Header Section -->
                <div style="background: linear-gradient(135deg, #007cba 0%, #005580 50%, #003d5c 100%); padding: 25px 30px; color: white; position: relative; overflow: hidden;">
                    <div style="position: absolute; top: -20px; right: -20px; width: 100px; height: 100px; background: rgba(255,255,255,0.1); border-radius: 50%; transform: rotate(45deg);"></div>
                    <div style="position: relative; z-index: 2;">
                        <h3 style="margin: 0 0 10px 0; font-size: 24px; font-weight: bold; text-shadow: 1px 1px 2px rgba(0,0,0,0.3);">
                            📊 ${testName} Results
                        </h3>
                        <div style="background: rgba(255,255,255,0.2); border: 2px solid rgba(255,255,255,0.3); border-radius: 20px; padding: 8px 16px; display: inline-block;">
                            <span style="font-size: 14px; font-weight: bold;">${isSignificant ? '✅ UNEQUAL VARIANCES' : '❌ EQUAL VARIANCES'}</span>
                        </div>
                    </div>
                </div>

                <!-- Main Content -->
                <div style="padding: 25px;">
                    
                    <!-- Test Information -->
                    <div style="background: #f0f8ff; border: 2px solid #007cba; border-radius: 10px; padding: 20px; margin-bottom: 20px;">
                        <h4 style="color: #005580; margin: 0 0 15px 0; font-size: 18px;">📋 Test Information</h4>
                        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px;">
                            <div style="background: white; padding: 12px; border-radius: 8px; border-left: 4px solid #007cba;">
                                <strong style="color: #005580;">Test Type:</strong><br>
                                <span style="font-size: 16px; color: #333;">${testName}</span>
                            </div>
                            <div style="background: white; padding: 12px; border-radius: 8px; border-left: 4px solid #ff9800;">
                                <strong style="color: #e65100;">Purpose:</strong><br>
                                <span style="font-size: 16px; color: #333;">Test for Equal Variances</span>
                            </div>
                            <div style="background: white; padding: 12px; border-radius: 8px; border-left: 4px solid #4caf50;">
                                <strong style="color: #2e7d32;">Groups:</strong><br>
                                <span style="font-size: 16px; color: #333;">${result.columns ? result.columns.length : 'N/A'} variables</span>
                            </div>
                        </div>
                    </div>

                    <!-- Test Statistics -->
                    <div style="background: ${isSignificant ? '#fff3e0' : '#e8f5e8'}; border: 2px solid ${isSignificant ? '#ff9800' : '#4caf50'}; border-radius: 10px; padding: 20px; margin-bottom: 20px;">
                        <h4 style="color: ${isSignificant ? '#f57c00' : '#2e7d32'}; margin: 0 0 15px 0; font-size: 18px;">📊 Test Statistics</h4>
                        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 15px;">
                            <div style="background: white; padding: 15px; border-radius: 8px; text-align: center; border-left: 4px solid #2196f3;">
                                <div style="font-size: 28px; font-weight: bold; color: #1976d2;">${safeFormat(result.test_statistic)}</div>
                                <div style="color: #666; font-size: 14px;">Test Statistic</div>
                            </div>
                            <div style="background: white; padding: 15px; border-radius: 8px; text-align: center; border-left: 4px solid #ff5722;">
                                <div style="font-size: 28px; font-weight: bold; color: #d84315;">${safeFormat(result.p_value)}</div>
                                <div style="color: #666; font-size: 14px;">P-value</div>
                            </div>
                            <div style="background: white; padding: 15px; border-radius: 8px; text-align: center; border-left: 4px solid #9c27b0;">
                                <div style="font-size: 28px; font-weight: bold; color: #7b1fa2;">${result.degrees_of_freedom || 'N/A'}</div>
                                <div style="color: #666; font-size: 14px;">Degrees of Freedom</div>
                            </div>
                        </div>
                    </div>

                    <!-- Group Statistics -->
                    ${result.group_statistics ? `
                    <div style="background: #e0f2f1; border: 2px solid #4caf50; border-radius: 10px; padding: 20px; margin-bottom: 20px;">
                        <h4 style="color: #2e7d32; margin: 0 0 15px 0; font-size: 18px;">📈 Group Statistics</h4>
                        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px;">
                            ${Object.entries(result.group_statistics).map(([group, stats]) => `
                                <div style="background: white; padding: 15px; border-radius: 8px; border-left: 4px solid #4caf50;">
                                    <div style="font-weight: bold; color: #2e7d32; margin-bottom: 10px; font-size: 16px;">${group}</div>
                                    <div style="margin: 5px 0;"><strong>Variance:</strong> ${safeFormat(stats.variance)}</div>
                                    <div style="margin: 5px 0;"><strong>Std Dev:</strong> ${safeFormat(stats.std)}</div>
                                    <div style="margin: 5px 0;"><strong>Mean:</strong> ${safeFormat(stats.mean)}</div>
                                    <div style="margin: 5px 0;"><strong>Size:</strong> ${stats.size}</div>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                    ` : ''}

                    <!-- Conclusion Section -->
                    <div style="background: ${isSignificant ? '#fff3e0' : '#e8f5e8'}; border: 2px solid ${isSignificant ? '#ff9800' : '#4caf50'}; border-radius: 10px; padding: 20px; margin-bottom: 20px;">
                        <h4 style="color: ${isSignificant ? '#f57c00' : '#2e7d32'}; margin: 0 0 15px 0; font-size: 18px;">🎯 Conclusion</h4>
                        <div style="background: white; padding: 15px; border-radius: 8px; border-left: 4px solid ${isSignificant ? '#ff9800' : '#4caf50'};">
                            <p style="margin: 0; font-size: 16px; line-height: 1.5; color: #333;">
                                <strong>${result.interpretation || 
                                    (isSignificant ? 
                                        'The variances are significantly different between groups.' : 
                                        'The variances are not significantly different between groups.')}</strong>
                            </p>
                            <div style="margin-top: 15px; padding: 10px; background: ${isSignificant ? '#fff3e0' : '#e8f5e8'}; border-radius: 8px;">
                                <p style="margin: 0; font-size: 14px; color: #666;">
                                    <strong>Implication:</strong> 
                                    ${isSignificant ? 
                                        'Equal variance assumptions for parametric tests may be violated. Consider using robust methods or data transformation.' : 
                                        'Equal variance assumptions are met. Parametric tests requiring equal variances are appropriate.'}
                                </p>
                            </div>
                        </div>
                    </div>

                    <!-- Hypotheses Section -->
                    <div style="background: #e3f2fd; border: 2px solid #2196f3; border-radius: 10px; padding: 20px;">
                        <h4 style="color: #1976d2; margin: 0 0 15px 0; font-size: 18px;">📝 Hypotheses</h4>
                        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
                            <div style="background: white; padding: 15px; border-radius: 8px; border-left: 4px solid #2196f3;">
                                <div style="font-weight: bold; color: #1976d2; margin-bottom: 8px;">Null Hypothesis (H₀):</div>
                                <div style="color: #333; font-size: 14px;">All groups have equal variances</div>
                            </div>
                            <div style="background: white; padding: 15px; border-radius: 8px; border-left: 4px solid #ff5722;">
                                <div style="font-weight: bold; color: #d84315; margin-bottom: 8px;">Alternative Hypothesis (H₁):</div>
                                <div style="color: #333; font-size: 14px;">At least one group has different variance</div>
                            </div>
                        </div>
                    </div>

                </div>
            </div>
        `;
        
        container.innerHTML = html;
    }

    async function runMcNemarTest() {
        const column1 = document.getElementById('mcnemar-col1').value;
        const column2 = document.getElementById('mcnemar-col2').value;
        
        if (!column1 || !column2) {
            showError('Please select both columns');
            return;
        }
        
        showLoading('Running McNemar test...');
        
        try {
            const response = await fetch('/api/statistical/mcnemar', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    dataset_id: currentDatasetId,
                    column1: column1,
                    column2: column2
                })
            });
            
            const data = await response.json();
            
            if (data.success && data.results) {
                displayMcNemarResult(data.results, column1, column2);
            } else {
                // Show the actual backend error message instead of generic one
                const errorMessage = data.error || 'Failed to run McNemar test';
                displayMcNemarError(errorMessage, column1, column2);
            }
            
        } catch (error) {
            console.error('Error running McNemar test:', error);
            displayMcNemarError('Network error: ' + error.message, column1, column2);
        } finally {
            hideLoading();
        }
    }

    function displayMcNemarError(errorMessage, column1, column2) {
        const container = document.getElementById('mcnemar-results');
        
        container.innerHTML = `
            <div class="test-result error">
                <h4>McNemar Test Error</h4>
                <p><strong>Column 1:</strong> "${column1 || 'Not selected'}"</p>
                <p><strong>Column 2:</strong> "${column2 || 'Not selected'}"</p>
                <p><strong>Error:</strong> ${errorMessage}</p>
                <div class="error-help">
                    <p><strong>Common solutions:</strong></p>
                    <ul>
                        <li>Ensure both columns are selected</li>
                        <li>Check that both columns contain binary/categorical data</li>
                        <li>Verify the data forms a 2x2 contingency table</li>
                        <li>McNemar test requires paired observations</li>
                    </ul>
                </div>
            </div>
        `;
    }

    function displayMcNemarResult(result, column1, column2) {
        const container = document.getElementById('mcnemar-results');
        
        const isSignificant = result.p_value < 0.05;
        
        const html = `
            <div class="test-result ${isSignificant ? 'significant' : 'not-significant'}">
                <h4>McNemar Test Results: "${column1}" vs "${column2}"</h4>
                <div class="result-stats">
                    <div class="stat-item">
                        <strong>Test Statistic:</strong> ${safeFormat(result.test_statistic)}
                    </div>
                    <div class="stat-item">
                        <strong>P-value:</strong> ${safeFormat(result.p_value)}
                    </div>
                    <div class="stat-item">
                        <strong>Test Type:</strong> ${result.test_type}
                    </div>
                </div>
                <div class="conclusion">
                    <strong>Conclusion:</strong> ${result.interpretation || 
                        (isSignificant ? 
                            'Marginal probabilities are significantly different' : 
                            'Marginal probabilities are not significantly different')}
                </div>
            </div>
        `;
        
        container.innerHTML = html;
    }

    async function runMultipleComparison() {
        const dependent = document.getElementById('mc-dependent').value;
        const independent = document.getElementById('mc-independent').value;
        const method = document.getElementById('mc-method').value;
        
        if (!dependent || !independent) {
            showError('Please select both dependent and independent variables');
            return;
        }
        
        showLoading('Running multiple comparison...');
        
        try {
            const response = await fetch('/api/statistical/multiple_comparison', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    dataset_id: currentDatasetId,
                    dependent: dependent,
                    independent: independent,
                    method: method
                })
            });
            
            const data = await response.json();
            
            if (data.success && data.results) {
                displayMultipleComparisonResult(data.results, dependent, independent, method);
            } else {
                // Show the actual backend error message instead of generic one
                const errorMessage = data.error || 'Failed to run multiple comparison';
                displayMultipleComparisonError(errorMessage, dependent, independent, method);
            }
            
        } catch (error) {
            console.error('Error running multiple comparison:', error);
            displayMultipleComparisonError('Network error: ' + error.message, dependent, independent, method);
        } finally {
            hideLoading();
        }
    }

    function displayMultipleComparisonError(errorMessage, dependent, independent, method) {
        const container = document.getElementById('multiple-comparison-results');
        
        container.innerHTML = `
            <div class="test-result error">
                <h4>Multiple Comparison Error</h4>
                <p><strong>Method:</strong> ${method.replace('_', ' ').toUpperCase()}</p>
                <p><strong>Dependent Variable:</strong> "${dependent || 'Not selected'}"</p>
                <p><strong>Independent Variable:</strong> "${independent || 'Not selected'}"</p>
                <p><strong>Error:</strong> ${errorMessage}</p>
                <div class="error-help">
                    <p><strong>Common solutions:</strong></p>
                    <ul>
                        <li>Ensure both dependent and independent variables are selected</li>
                        <li>Check that dependent variable contains numeric data</li>
                        <li>Verify independent variable has 2+ groups with sufficient data</li>
                        <li>Ensure at least 10 total observations for reliable results</li>
                        <li>Check for missing or invalid values</li>
                    </ul>
                    <p><strong>Supported methods:</strong> Tukey, Bonferroni, Holm</p>
                </div>
            </div>
        `;
    }

    function displayMultipleComparisonResult(result, dependent, independent, method) {
        const container = document.getElementById('multiple-comparison-results');
        
        const testName = method.toUpperCase() + ' Multiple Comparisons';
        
        let html = `
            <div class="test-result">
                <h4>${testName}: "${dependent}" by "${independent}"</h4>
        `;
        
        if (result.group_comparisons) {
            html += `
                <div class="comparisons-table">
                    <table class="stats-table">
                        <thead>
                            <tr>
                                <th>Group 1</th>
                                <th>Group 2</th>
                                <th>Mean Diff</th>
                                <th>P-value</th>
                                <th>Significant</th>
                            </tr>
                        </thead>
                        <tbody>
            `;
            
            result.group_comparisons.forEach(comp => {
                html += `
                    <tr>
                        <td>${comp.group1}</td>
                        <td>${comp.group2}</td>
                        <td>${safeFormat(comp.mean_diff)}</td>
                        <td>${safeFormat(comp.p_value)}</td>
                        <td>${comp.reject ? 'Yes' : 'No'}</td>
                    </tr>
                `;
            });
            
            html += `
                        </tbody>
                    </table>
                </div>
            `;
        }
        
        html += `</div>`;
        container.innerHTML = html;
    }

    function showLoading(message = 'Loading...') {
        loadingModal.querySelector('.modal-content').textContent = message;
        loadingModal.style.display = 'flex';
    }
    
    function hideLoading() {
        loadingModal.style.display = 'none';
    }
    
    function showError(message) {
        alert(message); // In a real app, use a proper notification system
    }
    
    // Initialize t-test and chi-square sections
    handleTTestTypeChange();
    handleChiTestTypeChange();
    handleNonParametricTypeChange();
});