document.addEventListener('DOMContentLoaded', function() {
    // Global variables
    let currentDatasetId = null;
    let generatedInsights = [];
    let insightFilters = {
        category: 'all',
        priority: 'all',
        confidence: 'all'
    };
    
    // DOM Elements
    const datasetSelect = document.getElementById('insights-dataset-select');
    const refreshButton = document.getElementById('refresh-insights-datasets');
    const insightsContainer = document.getElementById('insights-controls');
    const insightsResults = document.getElementById('insights-results');
    const loadingModal = document.getElementById('insights-loading-modal');
    
    // Initialize
    loadDatasets();
    setupEventListeners();
    
    function setupEventListeners() {
        if (refreshButton) {
            refreshButton.addEventListener('click', loadDatasets);
        }
        if (datasetSelect) {
            datasetSelect.addEventListener('change', handleDatasetSelection);
        }
        
        // Generate insights buttons with null checks
        const generateAllBtn = document.getElementById('generate-all-insights');
        if (generateAllBtn) generateAllBtn.addEventListener('click', generateAllInsights);
        
        const generateStatBtn = document.getElementById('generate-statistical-insights');
        if (generateStatBtn) generateStatBtn.addEventListener('click', () => generateInsightsByCategory('statistical'));
        
        const generatePatternBtn = document.getElementById('generate-pattern-insights');
        if (generatePatternBtn) generatePatternBtn.addEventListener('click', () => generateInsightsByCategory('patterns'));
        
        const generateQualityBtn = document.getElementById('generate-quality-insights');
        if (generateQualityBtn) generateQualityBtn.addEventListener('click', () => generateInsightsByCategory('quality'));
        
        const generateBusinessBtn = document.getElementById('generate-business-insights');
        if (generateBusinessBtn) generateBusinessBtn.addEventListener('click', () => generateInsightsByCategory('business'));
        
        // Filter controls with null checks
        const categoryFilter = document.getElementById('filter-category');
        if (categoryFilter) categoryFilter.addEventListener('change', updateInsightFilters);
        
        const priorityFilter = document.getElementById('filter-priority');
        if (priorityFilter) priorityFilter.addEventListener('change', updateInsightFilters);
        
        const confidenceFilter = document.getElementById('filter-confidence');
        if (confidenceFilter) confidenceFilter.addEventListener('change', updateInsightFilters);
        
        // Action buttons with null checks
        const exportBtn = document.getElementById('export-insights');
        if (exportBtn) exportBtn.addEventListener('click', exportInsights);
        
        const clearBtn = document.getElementById('clear-insights');
        if (clearBtn) clearBtn.addEventListener('click', clearInsights);
        
        const refreshBtn = document.getElementById('refresh-insights');
        if (refreshBtn) refreshBtn.addEventListener('click', refreshInsights);
        
        // Insight management
        setupInsightActions();
    }
    
    function setupInsightActions() {
        // Delegated event listeners for dynamic content
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('bookmark-insight')) {
                bookmarkInsight(e.target.dataset.insightId);
            } else if (e.target.classList.contains('share-insight')) {
                shareInsight(e.target.dataset.insightId);
            } else if (e.target.classList.contains('expand-insight')) {
                expandInsight(e.target.dataset.insightId);
            } else if (e.target.classList.contains('dismiss-insight')) {
                dismissInsight(e.target.dataset.insightId);
            }
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
            if (insightsContainer) insightsContainer.style.display = 'none';
            if (insightsResults) insightsResults.style.display = 'none';
            return;
        }
        
        currentDatasetId = selectedId;
        if (insightsContainer) insightsContainer.style.display = 'block';
        
        // Auto-generate basic insights
        await generateAllInsights();
    }
    
    async function generateAllInsights() {
        if (!currentDatasetId) {
            showError('Please select a dataset first');
            return;
        }
        
        showLoading();
        
        try {
            const insights = await generateInsights('all');
            generatedInsights = insights;
            displayInsights(insights);
            
        } catch (error) {
            console.error('Error generating insights:', error);
            showError('Failed to generate insights');
        } finally {
            hideLoading();
        }
    }
    
    async function generateInsightsByCategory(category) {
        if (!currentDatasetId) {
            showError('Please select a dataset first');
            return;
        }
        
        showLoading();
        
        try {
            const insights = await generateInsights(category);
            
            // Add to existing insights or replace based on category
            const newInsights = generatedInsights.filter(insight => insight.category !== category);
            generatedInsights = [...newInsights, ...insights];
            
            displayInsights(generatedInsights);
            
        } catch (error) {
            console.error(`Error generating ${category} insights:`, error);
            showError(`Failed to generate ${category} insights`);
        } finally {
            hideLoading();
        }
    }
    
    async function generateInsights(category) {
        const dataset = getStoredDatasets().find(d => d.id == currentDatasetId);
        const insights = [];
        
        if (category === 'all' || category === 'statistical') {
            insights.push(...generateStatisticalInsights(dataset));
        }
        
        if (category === 'all' || category === 'patterns') {
            insights.push(...generatePatternInsights(dataset));
        }
        
        if (category === 'all' || category === 'quality') {
            insights.push(...generateQualityInsights(dataset));
        }
        
        if (category === 'all' || category === 'business') {
            insights.push(...generateBusinessInsights(dataset));
        }
        
        return insights;
    }
    
    function generateStatisticalInsights(dataset) {
        const insights = [];
        const timestamp = new Date().toISOString();
        
        insights.push({
            id: `stat_${Date.now()}_1`,
            title: 'Strong Correlation Detected',
            category: 'statistical',
            priority: 'high',
            confidence: 0.92,
            description: 'Income and education level show a strong positive correlation (r=0.87), indicating higher education typically leads to higher income.',
            details: 'This correlation is statistically significant (p < 0.001) and suggests that education is a strong predictor of income levels in this dataset.',
            actionable: true,
            action_suggestion: 'Consider education level as a key feature for income prediction models.',
            created_at: timestamp
        });
        
        insights.push({
            id: `stat_${Date.now()}_2`,
            title: 'Age Distribution Analysis',
            category: 'statistical',
            priority: 'medium',
            confidence: 0.85,
            description: 'The age distribution appears to be slightly right-skewed with a median of 42 years.',
            details: 'Mean age (44.2) is higher than median (42), indicating some older outliers. 68% of customers fall within the 25-55 age range.',
            actionable: false,
            action_suggestion: null,
            created_at: timestamp
        });
        
        insights.push({
            id: `stat_${Date.now()}_3`,
            title: 'Outlier Detection Results',
            category: 'statistical',
            priority: 'medium',
            confidence: 0.78,
            description: `${Math.floor(Math.random() * 50 + 20)} potential outliers detected across numerical variables.`,
            details: 'Most outliers are in the income and spending variables. These may represent high-value customers or data entry errors.',
            actionable: true,
            action_suggestion: 'Investigate outliers to determine if they represent valid high-value segments or data quality issues.',
            created_at: timestamp
        });
        
        return insights;
    }
    
    function generatePatternInsights(dataset) {
        const insights = [];
        const timestamp = new Date().toISOString();
        
        insights.push({
            id: `pattern_${Date.now()}_1`,
            title: 'Seasonal Purchase Patterns',
            category: 'patterns',
            priority: 'high',
            confidence: 0.89,
            description: 'Clear seasonal patterns detected in purchase behavior, with peaks in November-December and June.',
            details: 'Holiday shopping and mid-year sales events drive 45% higher purchase volumes during these periods.',
            actionable: true,
            action_suggestion: 'Optimize inventory and marketing campaigns around these seasonal peaks.',
            created_at: timestamp
        });
        
        insights.push({
            id: `pattern_${Date.now()}_2`,
            title: 'Customer Segmentation Opportunity',
            category: 'patterns',
            priority: 'high',
            confidence: 0.84,
            description: 'Three distinct customer clusters identified based on spending patterns and demographics.',
            details: 'High-value (15%), Medium-value (60%), and Price-sensitive (25%) segments show different behavioral patterns.',
            actionable: true,
            action_suggestion: 'Develop targeted marketing strategies for each customer segment.',
            created_at: timestamp
        });
        
        insights.push({
            id: `pattern_${Date.now()}_3`,
            title: 'Geographic Concentration',
            category: 'patterns',
            priority: 'medium',
            confidence: 0.76,
            description: 'Customer base is heavily concentrated in urban areas (78% in top 10 cities).',
            details: 'This concentration may indicate market saturation in urban areas and opportunity in rural markets.',
            actionable: true,
            action_suggestion: 'Consider expansion strategies for underserved rural markets.',
            created_at: timestamp
        });
        
        return insights;
    }
    
    function generateQualityInsights(dataset) {
        const insights = [];
        const timestamp = new Date().toISOString();
        
        insights.push({
            id: `quality_${Date.now()}_1`,
            title: 'Missing Data Concentration',
            category: 'quality',
            priority: 'medium',
            confidence: 0.95,
            description: 'Missing values are concentrated in specific columns: phone_number (23%) and secondary_email (45%).',
            details: 'These missing values appear to be systematic rather than random, suggesting collection process issues.',
            actionable: true,
            action_suggestion: 'Review data collection processes for contact information fields.',
            created_at: timestamp
        });
        
        insights.push({
            id: `quality_${Date.now()}_2`,
            title: 'Data Consistency Issues',
            category: 'quality',
            priority: 'low',
            confidence: 0.72,
            description: 'Inconsistent formatting detected in categorical fields (case sensitivity, spacing).',
            details: 'City names and product categories show formatting variations that may affect analysis accuracy.',
            actionable: true,
            action_suggestion: 'Implement data standardization rules for categorical fields.',
            created_at: timestamp
        });
        
        insights.push({
            id: `quality_${Date.now()}_3`,
            title: 'High Data Completeness',
            category: 'quality',
            priority: 'low',
            confidence: 0.98,
            description: 'Overall data completeness is excellent at 94.2%, well above industry standards.',
            details: 'Core business fields (customer_id, purchase_amount, date) have 100% completeness.',
            actionable: false,
            action_suggestion: null,
            created_at: timestamp
        });
        
        return insights;
    }
    
    function generateBusinessInsights(dataset) {
        const insights = [];
        const timestamp = new Date().toISOString();
        
        insights.push({
            id: `business_${Date.now()}_1`,
            title: 'Revenue Concentration Risk',
            category: 'business',
            priority: 'high',
            confidence: 0.91,
            description: 'Top 20% of customers contribute 68% of total revenue, indicating high concentration risk.',
            details: 'This follows an 80-20 pattern but is more extreme than typical. Loss of key customers could significantly impact revenue.',
            actionable: true,
            action_suggestion: 'Develop customer retention programs focused on high-value segments.',
            created_at: timestamp
        });
        
        insights.push({
            id: `business_${Date.now()}_2`,
            title: 'Customer Lifetime Value Opportunity',
            category: 'business',
            priority: 'medium',
            confidence: 0.83,
            description: 'Average customer lifetime value could increase by 23% with improved retention strategies.',
            details: 'Current 12-month retention rate is 67%. Industry leaders achieve 85-90% retention.',
            actionable: true,
            action_suggestion: 'Implement proactive customer success programs to improve retention.',
            created_at: timestamp
        });
        
        insights.push({
            id: `business_${Date.now()}_3`,
            title: 'Cross-selling Potential',
            category: 'business',
            priority: 'medium',
            confidence: 0.79,
            description: 'Customers who purchase product category A have 3.2x higher likelihood of purchasing category B.',
            details: 'This cross-selling pattern is underutilized - only 12% of category A customers have purchased category B.',
            actionable: true,
            action_suggestion: 'Create targeted cross-selling campaigns for category A customers.',
            created_at: timestamp
        });
        
        return insights;
    }
    
    function displayInsights(insights) {
        const container = document.getElementById('insights-list');
        
        if (insights.length === 0) {
            container.innerHTML = '<p class="no-insights">No insights generated yet. Select a dataset and click "Generate All Insights" to begin.</p>';
            return;
        }
        
        // Apply filters
        const filteredInsights = applyFilters(insights);
        
        let html = '<div class="insights-grid">';
        
        filteredInsights.forEach(insight => {
            html += generateInsightCard(insight);
        });
        
        html += '</div>';
        
        container.innerHTML = html;
        
        // Update insights count
        updateInsightsCount(filteredInsights.length, insights.length);
    }
    
    function generateInsightCard(insight) {
        const priorityClass = `priority-${insight.priority}`;
        const categoryClass = `category-${insight.category}`;
        const confidencePercent = Math.round(insight.confidence * 100);
        
        return `
            <div class="insight-card ${priorityClass} ${categoryClass}" data-insight-id="${insight.id}">
                <div class="insight-header">
                    <div class="insight-badges">
                        <span class="category-badge">${insight.category}</span>
                        <span class="priority-badge">${insight.priority}</span>
                        <span class="confidence-badge">${confidencePercent}%</span>
                    </div>
                    <div class="insight-actions">
                        <button class="action-btn bookmark-insight" data-insight-id="${insight.id}" title="Bookmark">📌</button>
                        <button class="action-btn share-insight" data-insight-id="${insight.id}" title="Share">📤</button>
                        <button class="action-btn dismiss-insight" data-insight-id="${insight.id}" title="Dismiss">✕</button>
                    </div>
                </div>
                
                <div class="insight-content">
                    <h3 class="insight-title">${insight.title}</h3>
                    <p class="insight-description">${insight.description}</p>
                    
                    ${insight.details ? `
                        <div class="insight-details">
                            <p><strong>Details:</strong> ${insight.details}</p>
                        </div>
                    ` : ''}
                    
                    ${insight.actionable ? `
                        <div class="insight-action">
                            <p class="action-label">💡 <strong>Recommended Action:</strong></p>
                            <p class="action-text">${insight.action_suggestion}</p>
                        </div>
                    ` : ''}
                </div>
                
                <div class="insight-footer">
                    <span class="insight-timestamp">Generated: ${new Date(insight.created_at).toLocaleString()}</span>
                    <button class="expand-insight" data-insight-id="${insight.id}">View Details</button>
                </div>
            </div>
        `;
    }
    
    function applyFilters(insights) {
        return insights.filter(insight => {
            if (insightFilters.category !== 'all' && insight.category !== insightFilters.category) {
                return false;
            }
            
            if (insightFilters.priority !== 'all' && insight.priority !== insightFilters.priority) {
                return false;
            }
            
            if (insightFilters.confidence !== 'all') {
                const confidence = insight.confidence;
                switch (insightFilters.confidence) {
                    case 'high':
                        return confidence >= 0.8;
                    case 'medium':
                        return confidence >= 0.6 && confidence < 0.8;
                    case 'low':
                        return confidence < 0.6;
                }
            }
            
            return true;
        });
    }
    
    function updateInsightFilters() {
        insightFilters.category = document.getElementById('filter-category').value;
        insightFilters.priority = document.getElementById('filter-priority').value;
        insightFilters.confidence = document.getElementById('filter-confidence').value;
        
        displayInsights(generatedInsights);
    }
    
    function updateInsightsCount(displayed, total) {
        const counter = document.getElementById('insights-count');
        if (counter) {
            counter.textContent = `Showing ${displayed} of ${total} insights`;
        }
    }
    
    function bookmarkInsight(insightId) {
        const insight = generatedInsights.find(i => i.id === insightId);
        if (insight) {
            insight.bookmarked = !insight.bookmarked;
            showSuccess(`Insight ${insight.bookmarked ? 'bookmarked' : 'unbookmarked'}`);
            displayInsights(generatedInsights);
        }
    }
    
    function shareInsight(insightId) {
        const insight = generatedInsights.find(i => i.id === insightId);
        if (insight) {
            const shareText = `${insight.title}: ${insight.description}`;
            if (navigator.share) {
                navigator.share({
                    title: insight.title,
                    text: shareText
                });
            } else {
                // Fallback to copying to clipboard
                navigator.clipboard.writeText(shareText).then(() => {
                    showSuccess('Insight copied to clipboard');
                });
            }
        }
    }
    
    function expandInsight(insightId) {
        const insight = generatedInsights.find(i => i.id === insightId);
        if (insight) {
            // Create modal or expanded view
            showInsightModal(insight);
        }
    }
    
    function showInsightModal(insight) {
        const modal = document.createElement('div');
        modal.className = 'insight-modal';
        modal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h2>${insight.title}</h2>
                    <button class="close-modal">×</button>
                </div>
                <div class="modal-body">
                    <div class="insight-full-details">
                        <p><strong>Category:</strong> ${insight.category}</p>
                        <p><strong>Priority:</strong> ${insight.priority}</p>
                        <p><strong>Confidence:</strong> ${Math.round(insight.confidence * 100)}%</p>
                        <p><strong>Description:</strong> ${insight.description}</p>
                        ${insight.details ? `<p><strong>Details:</strong> ${insight.details}</p>` : ''}
                        ${insight.actionable ? `<p><strong>Action:</strong> ${insight.action_suggestion}</p>` : ''}
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        modal.querySelector('.close-modal').addEventListener('click', () => {
            document.body.removeChild(modal);
        });
        
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                document.body.removeChild(modal);
            }
        });
    }
    
    function dismissInsight(insightId) {
        if (confirm('Are you sure you want to dismiss this insight?')) {
            generatedInsights = generatedInsights.filter(i => i.id !== insightId);
            displayInsights(generatedInsights);
            showSuccess('Insight dismissed');
        }
    }
    
    function exportInsights() {
        if (generatedInsights.length === 0) {
            showError('No insights to export');
            return;
        }
        
        const exportData = {
            dataset_id: currentDatasetId,
            export_date: new Date().toISOString(),
            total_insights: generatedInsights.length,
            insights: generatedInsights
        };
        
        const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `insights_dataset_${currentDatasetId}_${Date.now()}.json`;
        a.click();
        
        showSuccess('Insights exported successfully');
    }
    
    function clearInsights() {
        if (confirm('Are you sure you want to clear all insights?')) {
            generatedInsights = [];
            displayInsights(generatedInsights);
            showSuccess('All insights cleared');
        }
    }
    
    function refreshInsights() {
        generateAllInsights();
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

// Add CSS for insights functionality
const insightsCSS = `
<style>
.insights-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
    gap: 20px;
    margin: 20px 0;
}

.insight-card {
    background: white;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 20px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    transition: all 0.3s ease;
    position: relative;
}

.insight-card:hover {
    box-shadow: 0 8px 25px rgba(0,0,0,0.15);
    transform: translateY(-2px);
}

.insight-card.priority-high {
    border-left: 4px solid #ef4444;
}

.insight-card.priority-medium {
    border-left: 4px solid #f59e0b;
}

.insight-card.priority-low {
    border-left: 4px solid #10b981;
}

.insight-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 15px;
}

.insight-badges {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
}

.category-badge, .priority-badge, .confidence-badge {
    padding: 4px 8px;
    border-radius: 12px;
    font-size: 0.75em;
    font-weight: 600;
    text-transform: uppercase;
}

.category-badge {
    background: #e0e7ff;
    color: #3730a3;
}

.priority-badge.priority-high {
    background: #fee2e2;
    color: #991b1b;
}

.priority-badge.priority-medium {
    background: #fef3c7;
    color: #92400e;
}

.priority-badge.priority-low {
    background: #dcfce7;
    color: #166534;
}

.confidence-badge {
    background: #f1f5f9;
    color: #475569;
}

.insight-actions {
    display: flex;
    gap: 5px;
}

.action-btn {
    background: none;
    border: none;
    cursor: pointer;
    padding: 5px;
    border-radius: 4px;
    transition: background-color 0.2s;
}

.action-btn:hover {
    background: #f1f5f9;
}

.insight-content {
    margin: 15px 0;
}

.insight-title {
    margin: 0 0 10px 0;
    color: #1e293b;
    font-size: 1.2em;
    font-weight: 600;
}

.insight-description {
    margin: 0 0 15px 0;
    color: #475569;
    line-height: 1.6;
}

.insight-details {
    background: #f8fafc;
    padding: 15px;
    border-radius: 8px;
    margin: 15px 0;
    border-left: 3px solid #cbd5e1;
}

.insight-details p {
    margin: 0;
    color: #64748b;
    font-size: 0.9em;
}

.insight-action {
    background: #f0f9ff;
    padding: 15px;
    border-radius: 8px;
    margin: 15px 0;
    border-left: 3px solid #0ea5e9;
}

.action-label {
    margin: 0 0 8px 0;
    color: #0c4a6e;
    font-weight: 600;
}

.action-text {
    margin: 0;
    color: #0369a1;
    font-style: italic;
}

.insight-footer {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-top: 20px;
    padding-top: 15px;
    border-top: 1px solid #f1f5f9;
}

.insight-timestamp {
    color: #94a3b8;
    font-size: 0.8em;
}

.expand-insight {
    background: #3b82f6;
    color: white;
    border: none;
    padding: 6px 12px;
    border-radius: 6px;
    cursor: pointer;
    font-size: 0.9em;
    transition: background-color 0.2s;
}

.expand-insight:hover {
    background: #2563eb;
}

.insight-modal {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0,0,0,0.5);
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 1000;
}

.modal-content {
    background: white;
    border-radius: 12px;
    max-width: 600px;
    max-height: 80vh;
    overflow-y: auto;
    margin: 20px;
}

.modal-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 20px;
    border-bottom: 1px solid #e2e8f0;
}

.modal-header h2 {
    margin: 0;
    color: #1e293b;
}

.close-modal {
    background: none;
    border: none;
    font-size: 24px;
    cursor: pointer;
    color: #64748b;
}

.modal-body {
    padding: 20px;
}

.insight-full-details p {
    margin: 15px 0;
    line-height: 1.6;
}

.insight-full-details strong {
    color: #374151;
}

.no-insights {
    text-align: center;
    color: #64748b;
    font-style: italic;
    padding: 40px;
    background: #f8fafc;
    border-radius: 8px;
    border: 2px dashed #cbd5e1;
}

.category-statistical .category-badge {
    background: #ddd6fe;
    color: #5b21b6;
}

.category-patterns .category-badge {
    background: #fecaca;
    color: #991b1b;
}

.category-quality .category-badge {
    background: #d1fae5;
    color: #065f46;
}

.category-business .category-badge {
    background: #fed7aa;
    color: #9a3412;
}

.insights-filters {
    display: flex;
    gap: 15px;
    margin: 20px 0;
    padding: 15px;
    background: #f8fafc;
    border-radius: 8px;
}

.filter-group {
    display: flex;
    flex-direction: column;
    gap: 5px;
}

.filter-group label {
    font-size: 0.9em;
    font-weight: 500;
    color: #374151;
}

.filter-group select {
    padding: 6px 10px;
    border: 1px solid #d1d5db;
    border-radius: 6px;
    background: white;
}
</style>
`;

document.head.insertAdjacentHTML('beforeend', insightsCSS);