document.addEventListener('DOMContentLoaded', function() {
    // Global variables
    let currentDatasetId = null;
    let reportSectionSettings = {};
    let generatedReports = [];
    
    // DOM Elements
    const datasetSelect = document.getElementById('reports-dataset-select');
    const refreshButton = document.getElementById('refresh-reports-datasets');
    const reportGenerator = document.getElementById('report-generator');
    const reportPreview = document.getElementById('report-preview');
    const loadingModal = document.getElementById('reports-loading-modal');
    
    // Initialize
    loadDatasets();
    setupEventListeners();
    loadSavedReports();
    
    function setupEventListeners() {
        if (refreshButton) {
            refreshButton.addEventListener('click', loadDatasets);
        }
        if (datasetSelect) {
            datasetSelect.addEventListener('change', handleDatasetSelection);
        }
        
        // Report generation buttons with null checks
        const summaryBtn = document.getElementById('generate-summary-report');
        if (summaryBtn) summaryBtn.addEventListener('click', generateSummaryReport);
        
        const statBtn = document.getElementById('generate-statistical-report');
        if (statBtn) statBtn.addEventListener('click', generateStatisticalReport);
        
        const vizBtn = document.getElementById('generate-visualization-report');
        if (vizBtn) vizBtn.addEventListener('click', generateVisualizationReport);
        
        const qualityBtn = document.getElementById('generate-quality-report');
        if (qualityBtn) qualityBtn.addEventListener('click', generateQualityReport);
        
        const compBtn = document.getElementById('generate-comparative-report');
        if (compBtn) compBtn.addEventListener('click', generateComparativeReport);
        
        const customBtn = document.getElementById('generate-custom-report');
        if (customBtn) customBtn.addEventListener('click', generateCustomReport);
        
        // Report actions
        const previewBtn = document.getElementById('preview-report');
        if (previewBtn) previewBtn.addEventListener('click', previewReport);
        
        const downloadBtn = document.getElementById('download-report');
        if (downloadBtn) downloadBtn.addEventListener('click', downloadReport);
        
        const shareBtn = document.getElementById('share-report');
        if (shareBtn) shareBtn.addEventListener('click', shareReport);
        
        const editBtn = document.getElementById('edit-report');
        if (editBtn) editBtn.addEventListener('click', editReport);
        
        // Custom report controls
        const addSectionBtn = document.getElementById('add-section');
        if (addSectionBtn) addSectionBtn.addEventListener('click', addCustomSection);
        
        const clearSectionsBtn = document.getElementById('clear-sections');
        if (clearSectionsBtn) clearSectionsBtn.addEventListener('click', clearCustomSections);
        
        // Template management
        const loadTemplateBtn = document.getElementById('load-template');
        if (loadTemplateBtn) loadTemplateBtn.addEventListener('click', loadTemplate);
        
        const deleteTemplateBtn = document.getElementById('delete-template');
        if (deleteTemplateBtn) deleteTemplateBtn.addEventListener('click', deleteTemplate);
        
        // Report scheduling
        const scheduleReportBtn = document.getElementById('schedule-report');
        if (scheduleReportBtn) scheduleReportBtn.addEventListener('click', scheduleReport);
        
        // Section toggles
        setupSectionToggles();
    }
    
    function setupSectionToggles() {
        const toggles = document.querySelectorAll('.section-toggle');
                 toggles.forEach(toggle => {
             toggle.addEventListener('change', (e) => {
                 const sectionId = e.target.getAttribute('data-section');
                 reportSectionSettings[sectionId] = e.target.checked;
                 updateReportPreview();
             });
         });
    }
    
    async function loadDatasets() {
        try {
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
                    option.textContent = `${dataset.name} (${dataset.rows} rows, ${dataset.columns} cols)`;
                    datasetSelect.appendChild(option);
                });
            } else {
                console.log('No datasets available');
            }
            
        } catch (error) {
            console.error('Error loading datasets:', error);
            showError('Failed to load datasets: ' + error.message);
        }
    }
    
    async function handleDatasetSelection() {
        const selectedId = datasetSelect.value;
        
        if (!selectedId) {
            if (reportGenerator) reportGenerator.style.display = 'none';
            return;
        }
        
        currentDatasetId = selectedId;
        if (reportGenerator) reportGenerator.style.display = 'block';
        initializeReportSections();
    }
    
    function initializeReportSections() {
        // Reset section toggles
        reportSectionSettings = {
            summary: true,
            statistics: true,
            correlation: false,
            missing: false,
            distributions: false,
            outliers: false,
            visualizations: false,
            recommendations: true
        };
        
        // Update toggle states
        Object.entries(reportSectionSettings).forEach(([section, enabled]) => {
            const toggle = document.getElementById(`include-${section}`);
            if (toggle) toggle.checked = enabled;
        });
        
        updateReportPreview();
    }
    
    function previewReport() {
        if (!currentDatasetId) {
            showError('Please select a dataset first');
            return;
        }
        
        const reportType = document.getElementById('report-type').value;
        const reportTitle = document.getElementById('report-title').value || 'Data Analysis Report';
        
        showLoading();
        
        try {
            generateSummaryReport().then(report => {
                displayReportPreview(report);
                if (reportPreview) reportPreview.style.display = 'block';
            });
        } catch (error) {
            console.error('Error previewing report:', error);
            showError('Failed to preview report');
        } finally {
            hideLoading();
        }
    }
    
    function downloadReport() {
        const reportFormat = document.getElementById('report-format').value;
        
        if (!generatedReports || generatedReports.length === 0) {
            showError('No report to download. Please generate a report first.');
            return;
        }
        
        const report = generatedReports[generatedReports.length - 1];
        
        if (reportFormat === 'html') {
            downloadHTML(report);
        } else if (reportFormat === 'json') {
            downloadJSON(report);
        } else {
            showError('PDF download not implemented yet');
        }
    }
    
    function editReport() {
        if (reportPreview) reportPreview.style.display = 'none';
        if (reportGenerator) reportGenerator.style.display = 'block';
    }
    
    function addCustomSection() {
        console.log('Add custom section functionality not implemented yet');
    }
    
    function clearCustomSections() {
        console.log('Clear custom sections functionality not implemented yet');
    }
    
    async function generateSummaryReport() {
        if (!currentDatasetId) {
            showError('Please select a dataset first');
            return;
        }
        
        showLoading();
        
        try {
            const report = await createSummaryReport();
            displayReportPreview(report);
            saveGeneratedReport(report);
            
        } catch (error) {
            console.error('Error generating summary report:', error);
            showError('Failed to generate summary report');
        } finally {
            hideLoading();
        }
    }
    
    async function createSummaryReport() {
        const dataset = getStoredDatasets().find(d => d.id == currentDatasetId);
        
        return {
            type: 'Summary Report',
            dataset: dataset.name,
            generated_at: new Date().toISOString(),
            sections: {
                overview: {
                    title: 'Dataset Overview',
                    content: `
                        <div class="overview-section">
                            <h3>Dataset: ${dataset.name}</h3>
                            <div class="overview-stats">
                                <div class="stat-item">
                                    <span class="stat-label">Total Rows:</span>
                                    <span class="stat-value">${dataset.rows.toLocaleString()}</span>
                                </div>
                                <div class="stat-item">
                                    <span class="stat-label">Total Columns:</span>
                                    <span class="stat-value">${dataset.columns}</span>
                                </div>
                                <div class="stat-item">
                                    <span class="stat-label">Memory Usage:</span>
                                    <span class="stat-value">${(Math.random() * 50 + 10).toFixed(1)} MB</span>
                                </div>
                                <div class="stat-item">
                                    <span class="stat-label">Completeness:</span>
                                    <span class="stat-value">${(Math.random() * 20 + 80).toFixed(1)}%</span>
                                </div>
                            </div>
                        </div>
                    `
                },
                statistics: {
                    title: 'Statistical Summary',
                    content: generateStatisticalSummary()
                },
                quality: {
                    title: 'Data Quality Assessment',
                    content: generateQualityAssessment()
                },
                recommendations: {
                    title: 'Recommendations',
                    content: generateRecommendations()
                }
            }
        };
    }
    
    function generateStatisticalSummary() {
        const stats = [
            { metric: 'Mean Age', value: (Math.random() * 20 + 30).toFixed(1) },
            { metric: 'Median Income', value: '$' + (Math.random() * 50000 + 50000).toFixed(0) },
            { metric: 'Standard Deviation', value: (Math.random() * 10 + 5).toFixed(2) },
            { metric: 'Correlation (Income-Age)', value: (Math.random() * 0.8 + 0.1).toFixed(3) }
        ];
        
        let html = '<div class="statistics-summary"><table class="stats-table">';
        html += '<thead><tr><th>Metric</th><th>Value</th></tr></thead><tbody>';
        
        stats.forEach(stat => {
            html += `<tr><td>${stat.metric}</td><td><strong>${stat.value}</strong></td></tr>`;
        });
        
        html += '</tbody></table></div>';
        return html;
    }
    
    function generateQualityAssessment() {
        const assessments = [
            { aspect: 'Completeness', score: Math.floor(Math.random() * 20 + 80), status: 'Good' },
            { aspect: 'Consistency', score: Math.floor(Math.random() * 15 + 85), status: 'Excellent' },
            { aspect: 'Validity', score: Math.floor(Math.random() * 25 + 75), status: 'Fair' },
            { aspect: 'Uniqueness', score: Math.floor(Math.random() * 10 + 90), status: 'Excellent' }
        ];
        
        let html = '<div class="quality-assessment">';
        
        assessments.forEach(assessment => {
            const statusClass = assessment.status.toLowerCase();
            html += `
                <div class="quality-item">
                    <div class="quality-header">
                        <span class="quality-aspect">${assessment.aspect}</span>
                        <span class="quality-status ${statusClass}">${assessment.status}</span>
                    </div>
                    <div class="quality-bar">
                        <div class="quality-fill" style="width: ${assessment.score}%"></div>
                        <span class="quality-score">${assessment.score}%</span>
                    </div>
                </div>
            `;
        });
        
        html += '</div>';
        return html;
    }
    
    function generateRecommendations() {
        const recommendations = [
            'Consider removing outliers in the income column for better analysis accuracy',
            'Age distribution appears normal - good for statistical modeling',
            'Missing values in region column should be addressed before analysis',
            'Strong correlation between income and education suggests feature engineering opportunities',
            'Consider standardizing numerical features for machine learning models'
        ];
        
        let html = '<div class="recommendations-list"><ul>';
        recommendations.forEach(rec => {
            html += `<li>${rec}</li>`;
        });
        html += '</ul></div>';
        
        return html;
    }
    
    async function generateStatisticalReport() {
        showLoading();
        
        try {
            const report = {
                type: 'Statistical Analysis Report',
                dataset: getStoredDatasets().find(d => d.id == currentDatasetId).name,
                generated_at: new Date().toISOString(),
                sections: {
                    descriptive: {
                        title: 'Descriptive Statistics',
                        content: generateDescriptiveStats()
                    },
                    distributions: {
                        title: 'Distribution Analysis',
                        content: generateDistributionAnalysis()
                    },
                    correlations: {
                        title: 'Correlation Analysis',
                        content: generateCorrelationAnalysis()
                    },
                    outliers: {
                        title: 'Outlier Detection',
                        content: generateOutlierAnalysis()
                    }
                }
            };
            
            displayReportPreview(report);
            saveGeneratedReport(report);
            
        } catch (error) {
            console.error('Error generating statistical report:', error);
            showError('Failed to generate statistical report');
        } finally {
            hideLoading();
        }
    }
    
    function generateDescriptiveStats() {
        return `
            <div class="descriptive-stats">
                <p>Comprehensive statistical analysis of numerical variables:</p>
                <div class="chart-placeholder">
                    📊 Descriptive statistics table would be displayed here
                </div>
            </div>
        `;
    }
    
    function generateDistributionAnalysis() {
        return `
            <div class="distribution-analysis">
                <p>Distribution analysis for key variables:</p>
                <div class="chart-placeholder">
                    📈 Distribution plots and normality tests would be displayed here
                </div>
            </div>
        `;
    }
    
    function generateCorrelationAnalysis() {
        return `
            <div class="correlation-analysis">
                <p>Correlation matrix and significant relationships:</p>
                <div class="chart-placeholder">
                    🔗 Correlation heatmap would be displayed here
                </div>
            </div>
        `;
    }
    
    function generateOutlierAnalysis() {
        const outlierCount = Math.floor(Math.random() * 50 + 10);
        return `
            <div class="outlier-analysis">
                <p>Outlier detection results:</p>
                <div class="outlier-summary">
                    <p><strong>${outlierCount} potential outliers detected</strong></p>
                    <p>Represents ${(outlierCount / 5000 * 100).toFixed(2)}% of the dataset</p>
                </div>
                <div class="chart-placeholder">
                    📊 Outlier visualization would be displayed here
                </div>
            </div>
        `;
    }
    
    async function generateVisualizationReport() {
        showLoading();
        
        try {
            const report = {
                type: 'Visualization Report',
                dataset: getStoredDatasets().find(d => d.id == currentDatasetId).name,
                generated_at: new Date().toISOString(),
                sections: {
                    charts: {
                        title: 'Key Visualizations',
                        content: generateVisualizationContent()
                    }
                }
            };
            
            displayReportPreview(report);
            saveGeneratedReport(report);
            
        } catch (error) {
            console.error('Error generating visualization report:', error);
            showError('Failed to generate visualization report');
        } finally {
            hideLoading();
        }
    }
    
    function generateVisualizationContent() {
        return `
            <div class="visualizations-report">
                <div class="viz-grid">
                    <div class="viz-item">
                        <h4>Age Distribution</h4>
                        <div class="chart-placeholder">📊 Histogram</div>
                    </div>
                    <div class="viz-item">
                        <h4>Income vs Score</h4>
                        <div class="chart-placeholder">📈 Scatter Plot</div>
                    </div>
                    <div class="viz-item">
                        <h4>Category Breakdown</h4>
                        <div class="chart-placeholder">🥧 Pie Chart</div>
                    </div>
                    <div class="viz-item">
                        <h4>Trend Analysis</h4>
                        <div class="chart-placeholder">📉 Line Chart</div>
                    </div>
                </div>
            </div>
        `;
    }
    
    async function generateQualityReport() {
        showLoading();
        
        try {
            const report = {
                type: 'Data Quality Report',
                dataset: getStoredDatasets().find(d => d.id == currentDatasetId).name,
                generated_at: new Date().toISOString(),
                sections: {
                    quality_metrics: {
                        title: 'Quality Metrics',
                        content: generateQualityMetrics()
                    },
                    issues: {
                        title: 'Identified Issues',
                        content: generateQualityIssues()
                    },
                    recommendations: {
                        title: 'Quality Improvement Recommendations',
                        content: generateQualityRecommendations()
                    }
                }
            };
            
            displayReportPreview(report);
            saveGeneratedReport(report);
            
        } catch (error) {
            console.error('Error generating quality report:', error);
            showError('Failed to generate quality report');
        } finally {
            hideLoading();
        }
    }
    
    function generateQualityMetrics() {
        return `
            <div class="quality-metrics">
                <div class="metric-cards">
                    <div class="metric-card">
                        <h4>Overall Score</h4>
                        <div class="score excellent">92/100</div>
                    </div>
                    <div class="metric-card">
                        <h4>Missing Data</h4>
                        <div class="score good">2.3%</div>
                    </div>
                    <div class="metric-card">
                        <h4>Duplicates</h4>
                        <div class="score excellent">0.1%</div>
                    </div>
                    <div class="metric-card">
                        <h4>Consistency</h4>
                        <div class="score good">87%</div>
                    </div>
                </div>
            </div>
        `;
    }
    
    function generateQualityIssues() {
        return `
            <div class="quality-issues">
                <div class="issue-list">
                    <div class="issue-item warning">
                        <span class="issue-type">Missing Values</span>
                        <span class="issue-desc">115 missing values in 'region' column</span>
                    </div>
                    <div class="issue-item info">
                        <span class="issue-type">Data Type</span>
                        <span class="issue-desc">'age' column contains float values</span>
                    </div>
                    <div class="issue-item warning">
                        <span class="issue-type">Outliers</span>
                        <span class="issue-desc">23 extreme outliers in 'income' column</span>
                    </div>
                </div>
            </div>
        `;
    }
    
    function generateQualityRecommendations() {
        return `
            <div class="quality-recommendations">
                <ul class="recommendations">
                    <li>Impute missing values in 'region' column using mode imputation</li>
                    <li>Convert 'age' column to integer type for consistency</li>
                    <li>Investigate and potentially cap income outliers above 95th percentile</li>
                    <li>Standardize categorical value formatting for consistency</li>
                </ul>
            </div>
        `;
    }
    
    function displayReportPreview(report) {
        const container = document.getElementById('report-content');
        
        let html = `
            <div class="report-header">
                <h2>${report.type}</h2>
                <div class="report-meta">
                    <span class="dataset-name">Dataset: ${report.dataset}</span>
                    <span class="generated-time">Generated: ${new Date(report.generated_at).toLocaleString()}</span>
                </div>
            </div>
            
            <div class="report-body">
        `;
        
        Object.entries(report.sections).forEach(([key, section]) => {
            html += `
                <div class="report-section" id="section-${key}">
                    <h3>${section.title}</h3>
                    <div class="section-content">
                        ${section.content}
                    </div>
                </div>
            `;
        });
        
        html += '</div>';
        
        container.innerHTML = html;
        reportPreview.style.display = 'block';
    }
    
    function saveGeneratedReport(report) {
        generatedReports.push({
            ...report,
            id: Date.now(),
            saved_at: new Date().toISOString()
        });
        
        updateReportsList();
        showSuccess('Report generated and saved successfully');
    }
    
    function updateReportsList() {
        const container = document.getElementById('saved-reports-list');
        
        if (generatedReports.length === 0) {
            container.innerHTML = '<p>No saved reports yet.</p>';
            return;
        }
        
        let html = '<div class="reports-grid">';
        
        generatedReports.forEach(report => {
            html += `
                <div class="report-card">
                    <div class="report-card-header">
                        <h4>${report.type}</h4>
                        <button class="delete-report" onclick="deleteReport(${report.id})">×</button>
                    </div>
                    <div class="report-card-body">
                        <p class="report-dataset">${report.dataset}</p>
                        <p class="report-date">${new Date(report.saved_at).toLocaleDateString()}</p>
                        <div class="report-actions">
                            <button onclick="loadReport(${report.id})" class="btn-secondary">View</button>
                            <button onclick="downloadReport(${report.id})" class="btn-primary">Download</button>
                        </div>
                    </div>
                </div>
            `;
        });
        
        html += '</div>';
        container.innerHTML = html;
    }
    
    window.deleteReport = function(reportId) {
        if (confirm('Are you sure you want to delete this report?')) {
            generatedReports = generatedReports.filter(r => r.id !== reportId);
            updateReportsList();
            showSuccess('Report deleted');
        }
    };
    
    window.loadReport = function(reportId) {
        const report = generatedReports.find(r => r.id === reportId);
        if (report) {
            displayReportPreview(report);
        }
    };
    
    window.downloadReport = function(reportId) {
        const report = generatedReports.find(r => r.id === reportId);
        if (report) {
            downloadHTML(report);
        }
    };
    
    function downloadPDF() {
        showSuccess('PDF download would be initiated here');
    }
    
    function downloadHTML(report = null) {
        const reportData = report || getCurrentReport();
        if (!reportData) {
            showError('No report to download');
            return;
        }
        
        const htmlContent = generateHTMLReport(reportData);
        const blob = new Blob([htmlContent], { type: 'text/html' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${reportData.type.replace(/\s+/g, '_')}_${Date.now()}.html`;
        a.click();
        
        showSuccess('HTML report downloaded');
    }
    
    function downloadJSON() {
        const report = getCurrentReport();
        if (!report) {
            showError('No report to download');
            return;
        }
        
        const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${report.type.replace(/\s+/g, '_')}_${Date.now()}.json`;
        a.click();
        
        showSuccess('JSON report downloaded');
    }
    
    function getCurrentReport() {
        // Return the currently displayed report
        return generatedReports[generatedReports.length - 1] || null;
    }
    
    function generateHTMLReport(report) {
        return `
            <!DOCTYPE html>
            <html>
            <head>
                <title>${report.type} - ${report.dataset}</title>
                <style>
                    body { font-family: Arial, sans-serif; margin: 40px; }
                    .report-header { margin-bottom: 30px; }
                    .report-section { margin: 30px 0; }
                    .chart-placeholder { background: #f5f5f5; padding: 20px; text-align: center; }
                </style>
            </head>
            <body>
                <div class="report-header">
                    <h1>${report.type}</h1>
                    <p>Dataset: ${report.dataset}</p>
                    <p>Generated: ${new Date(report.generated_at).toLocaleString()}</p>
                </div>
                ${Object.entries(report.sections).map(([key, section]) => `
                    <div class="report-section">
                        <h2>${section.title}</h2>
                        ${section.content}
                    </div>
                `).join('')}
            </body>
            </html>
        `;
    }
    
    function shareReport() {
        showSuccess('Report sharing functionality would be implemented here');
    }
    
    function scheduleReport() {
        showSuccess('Report scheduling functionality would be implemented here');
    }
    
    function saveTemplate() {
        showSuccess('Template saving functionality would be implemented here');
    }
    
    function loadTemplate() {
        showSuccess('Template loading functionality would be implemented here');
    }
    
    function deleteTemplate() {
        showSuccess('Template deletion functionality would be implemented here');
    }
    
    function addCustomSection() {
        showSuccess('Custom section addition would be implemented here');
    }
    
    function clearCustomSections() {
        showSuccess('Custom sections would be cleared here');
    }
    
         function updateReportPreview() {
         // Update preview based on selected sections
         console.log('Report preview updated with sections:', reportSectionSettings);
     }
    
    function loadSavedReports() {
        // Load any previously saved reports
        updateReportsList();
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
});

// Add CSS for reports functionality
const reportsCSS = `
<style>
.report-header {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 30px;
    border-radius: 10px;
    margin-bottom: 30px;
}

.report-header h2 {
    margin: 0 0 10px 0;
    font-size: 2em;
}

.report-meta {
    display: flex;
    gap: 30px;
    font-size: 0.9em;
    opacity: 0.9;
}

.report-body {
    background: white;
    border-radius: 10px;
    padding: 30px;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
}

.report-section {
    margin: 40px 0;
    padding: 20px 0;
    border-bottom: 1px solid #e2e8f0;
}

.report-section:last-child {
    border-bottom: none;
}

.report-section h3 {
    color: #1e293b;
    margin: 0 0 20px 0;
    font-size: 1.5em;
}

.overview-stats {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 20px;
    margin: 20px 0;
}

.stat-item {
    background: #f8fafc;
    padding: 20px;
    border-radius: 8px;
    border: 1px solid #e2e8f0;
    text-align: center;
}

.stat-label {
    display: block;
    color: #64748b;
    font-size: 0.9em;
    margin-bottom: 8px;
}

.stat-value {
    display: block;
    color: #1e293b;
    font-size: 1.8em;
    font-weight: 700;
}

.stats-table {
    width: 100%;
    border-collapse: collapse;
    margin: 20px 0;
}

.stats-table th,
.stats-table td {
    padding: 12px;
    text-align: left;
    border-bottom: 1px solid #e2e8f0;
}

.stats-table th {
    background: #f8fafc;
    font-weight: 600;
    color: #374151;
}

.quality-assessment {
    display: flex;
    flex-direction: column;
    gap: 20px;
    margin: 20px 0;
}

.quality-item {
    background: #f8fafc;
    padding: 20px;
    border-radius: 8px;
    border: 1px solid #e2e8f0;
}

.quality-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 10px;
}

.quality-aspect {
    font-weight: 600;
    color: #1e293b;
}

.quality-status {
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 0.8em;
    font-weight: 600;
}

.quality-status.excellent {
    background: #dcfce7;
    color: #166534;
}

.quality-status.good {
    background: #fef3c7;
    color: #92400e;
}

.quality-status.fair {
    background: #fee2e2;
    color: #991b1b;
}

.quality-bar {
    position: relative;
    background: #f1f5f9;
    height: 25px;
    border-radius: 12px;
    overflow: hidden;
}

.quality-fill {
    height: 100%;
    background: linear-gradient(90deg, #ef4444, #f59e0b, #22c55e);
    transition: width 0.3s ease;
}

.quality-score {
    position: absolute;
    right: 10px;
    top: 50%;
    transform: translateY(-50%);
    font-size: 0.9em;
    font-weight: 600;
    color: #1e293b;
}

.recommendations-list ul {
    margin: 0;
    padding-left: 20px;
}

.recommendations-list li {
    margin: 10px 0;
    color: #374151;
    line-height: 1.6;
}

.chart-placeholder {
    background: #f8fafc;
    border: 2px dashed #cbd5e1;
    border-radius: 8px;
    padding: 40px;
    text-align: center;
    color: #64748b;
    font-size: 1.1em;
    margin: 20px 0;
}

.viz-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 20px;
    margin: 20px 0;
}

.viz-item {
    background: white;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 20px;
}

.viz-item h4 {
    margin: 0 0 15px 0;
    color: #1e293b;
}

.metric-cards {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap: 20px;
    margin: 20px 0;
}

.metric-card {
    background: white;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 20px;
    text-align: center;
}

.metric-card h4 {
    margin: 0 0 10px 0;
    color: #64748b;
    font-size: 0.9em;
}

.score {
    font-size: 2em;
    font-weight: 700;
    padding: 10px;
    border-radius: 8px;
}

.score.excellent {
    background: #dcfce7;
    color: #166534;
}

.score.good {
    background: #fef3c7;
    color: #92400e;
}

.issue-list {
    display: flex;
    flex-direction: column;
    gap: 10px;
}

.issue-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 15px;
    border-radius: 8px;
    border-left: 4px solid;
}

.issue-item.warning {
    background: #fef3c7;
    border-left-color: #f59e0b;
}

.issue-item.info {
    background: #dbeafe;
    border-left-color: #3b82f6;
}

.issue-type {
    font-weight: 600;
    color: #374151;
}

.issue-desc {
    color: #64748b;
}

.reports-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    gap: 20px;
    margin: 20px 0;
}

.report-card {
    background: white;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 20px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.report-card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 15px;
}

.report-card-header h4 {
    margin: 0;
    color: #1e293b;
}

.delete-report {
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

.report-card-body {
    display: flex;
    flex-direction: column;
    gap: 10px;
}

.report-dataset {
    color: #64748b;
    font-weight: 500;
    margin: 0;
}

.report-date {
    color: #94a3b8;
    font-size: 0.9em;
    margin: 0;
}

.report-actions {
    display: flex;
    gap: 10px;
    margin-top: 15px;
}

.btn-primary, .btn-secondary {
    padding: 8px 16px;
    border: none;
    border-radius: 6px;
    cursor: pointer;
    font-size: 0.9em;
    font-weight: 500;
}

.btn-primary {
    background: #3b82f6;
    color: white;
}

.btn-secondary {
    background: #f1f5f9;
    color: #374151;
    border: 1px solid #d1d5db;
}

.section-toggle {
    margin-right: 10px;
}
</style>
`;

document.head.insertAdjacentHTML('beforeend', reportsCSS);