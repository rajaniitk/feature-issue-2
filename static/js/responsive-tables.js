/**
 * Responsive Tables and Content Utility
 * Handles automatic table wrapping and responsive content layout
 */

// Utility functions for responsive content handling
const ResponsiveContent = {
    
    /**
     * Automatically wrap tables in responsive containers
     */
    wrapTables: function(container = document) {
        const tables = container.querySelectorAll('table:not(.wrapped)');
        
        tables.forEach(table => {
            // Skip if already wrapped
            if (table.closest('.table-container') || table.closest('.table-wrapper')) {
                return;
            }
            
            // Create wrapper
            const wrapper = document.createElement('div');
            wrapper.className = 'table-container';
            
            // Insert wrapper and move table
            table.parentNode.insertBefore(wrapper, table);
            wrapper.appendChild(table);
            
            // Mark as wrapped
            table.classList.add('wrapped');
            
            // Add scroll indicators if needed
            this.addScrollIndicators(wrapper);
        });
    },
    
    /**
     * Add scroll indicators to show if content is scrollable
     */
    addScrollIndicators: function(container) {
        const table = container.querySelector('table');
        if (!table) return;
        
        // Check if content is wider than container
        const checkScroll = () => {
            const hasHorizontalScroll = container.scrollWidth > container.clientWidth;
            const hasVerticalScroll = container.scrollHeight > container.clientHeight;
            
            container.classList.toggle('has-horizontal-scroll', hasHorizontalScroll);
            container.classList.toggle('has-vertical-scroll', hasVerticalScroll);
        };
        
        // Check on load and resize
        checkScroll();
        window.addEventListener('resize', checkScroll);
        
        // Add scroll event listeners for visual feedback
        container.addEventListener('scroll', () => {
            const isScrolledLeft = container.scrollLeft === 0;
            const isScrolledRight = container.scrollLeft >= (container.scrollWidth - container.clientWidth);
            const isScrolledTop = container.scrollTop === 0;
            const isScrolledBottom = container.scrollTop >= (container.scrollHeight - container.clientHeight);
            
            container.classList.toggle('scrolled-left', !isScrolledLeft);
            container.classList.toggle('scrolled-right', !isScrolledRight);
            container.classList.toggle('scrolled-top', !isScrolledTop);
            container.classList.toggle('scrolled-bottom', !isScrolledBottom);
        });
    },
    
    /**
     * Create a responsive correlation matrix
     */
    createCorrelationMatrix: function(data, container) {
        if (!data || !container) return;
        
        // Create matrix container
        const matrixContainer = document.createElement('div');
        matrixContainer.className = 'correlation-matrix-container';
        
        // Create table
        const table = document.createElement('table');
        table.className = 'correlation-matrix';
        
        // Create header row
        const headerRow = document.createElement('tr');
        headerRow.innerHTML = '<th class="first-column header">Variable</th>';
        
        if (data.columns) {
            data.columns.forEach(col => {
                const th = document.createElement('th');
                th.textContent = col;
                th.title = col; // Tooltip for long names
                headerRow.appendChild(th);
            });
        }
        
        table.appendChild(headerRow);
        
        // Create data rows
        if (data.values) {
            data.values.forEach((row, i) => {
                const tr = document.createElement('tr');
                
                // First column (row header)
                const firstTd = document.createElement('td');
                firstTd.className = 'first-column';
                firstTd.textContent = data.columns[i] || `Row ${i + 1}`;
                firstTd.title = data.columns[i] || `Row ${i + 1}`;
                tr.appendChild(firstTd);
                
                // Data cells
                row.forEach((value, j) => {
                    const td = document.createElement('td');
                    const numValue = parseFloat(value);
                    
                    if (!isNaN(numValue)) {
                        td.textContent = numValue.toFixed(3);
                        
                        // Add correlation strength classes
                        const absValue = Math.abs(numValue);
                        let className = 'corr-value ';
                        
                        if (absValue >= 0.8) {
                            className += numValue > 0 ? 'strong-positive' : 'strong-negative';
                        } else if (absValue >= 0.6) {
                            className += numValue > 0 ? 'moderate-positive' : 'moderate-negative';
                        } else if (absValue >= 0.3) {
                            className += numValue > 0 ? 'weak-positive' : 'weak-negative';
                        } else {
                            className += 'neutral';
                        }
                        
                        td.className = className;
                        td.title = `Correlation: ${numValue.toFixed(4)}`;
                    } else {
                        td.textContent = value;
                        td.className = 'corr-value neutral';
                    }
                    
                    tr.appendChild(td);
                });
                
                table.appendChild(tr);
            });
        }
        
        matrixContainer.appendChild(table);
        container.innerHTML = '';
        container.appendChild(matrixContainer);
        
        // Add scroll indicators
        this.addScrollIndicators(matrixContainer);
    },
    
    /**
     * Create responsive statistics summary
     */
    createStatsSummary: function(data, container) {
        if (!data || !container) return;
        
        const summaryDiv = document.createElement('div');
        summaryDiv.className = 'stats-summary';
        
        Object.entries(data).forEach(([key, value]) => {
            const card = document.createElement('div');
            card.className = 'stat-card';
            
            const title = document.createElement('h4');
            title.textContent = key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
            
            const valueSpan = document.createElement('span');
            valueSpan.className = 'value';
            
            // Format value based on type
            if (typeof value === 'number') {
                if (value % 1 === 0) {
                    valueSpan.textContent = value.toLocaleString();
                } else {
                    valueSpan.textContent = value.toFixed(4);
                }
            } else {
                valueSpan.textContent = value;
            }
            
            card.appendChild(title);
            card.appendChild(valueSpan);
            summaryDiv.appendChild(card);
        });
        
        container.innerHTML = '';
        container.appendChild(summaryDiv);
    },
    
    /**
     * Create missing values display
     */
    createMissingValuesDisplay: function(data, container) {
        if (!data || !container) return;
        
        const missingDiv = document.createElement('div');
        missingDiv.className = 'missing-values-display';
        
        Object.entries(data).forEach(([column, info]) => {
            const item = document.createElement('div');
            item.className = 'missing-item';
            
            const columnName = document.createElement('div');
            columnName.className = 'column-name';
            columnName.textContent = column;
            
            const missingCount = document.createElement('div');
            missingCount.className = 'missing-count';
            missingCount.textContent = info.count || info;
            
            const missingPercentage = document.createElement('div');
            missingPercentage.className = 'missing-percentage';
            if (info.percentage !== undefined) {
                missingPercentage.textContent = `${info.percentage.toFixed(1)}%`;
            }
            
            item.appendChild(columnName);
            item.appendChild(missingCount);
            if (info.percentage !== undefined) {
                item.appendChild(missingPercentage);
            }
            
            missingDiv.appendChild(item);
        });
        
        container.innerHTML = '';
        container.appendChild(missingDiv);
    },
    
    /**
     * Create data types display
     */
    createDataTypesDisplay: function(data, container) {
        if (!data || !container) return;
        
        const typesDiv = document.createElement('div');
        typesDiv.className = 'data-types-display';
        
        Object.entries(data).forEach(([column, type]) => {
            const item = document.createElement('div');
            item.className = 'type-item';
            
            // Add type-specific class
            const typeClass = type.toLowerCase().includes('int') || type.toLowerCase().includes('float') ? 'numeric' :
                            type.toLowerCase().includes('object') || type.toLowerCase().includes('category') ? 'categorical' :
                            type.toLowerCase().includes('datetime') ? 'datetime' :
                            type.toLowerCase().includes('bool') ? 'boolean' : 'other';
            
            item.classList.add(typeClass);
            
            const columnName = document.createElement('div');
            columnName.className = 'column-name';
            columnName.textContent = column;
            
            const dataType = document.createElement('div');
            dataType.className = 'data-type';
            dataType.textContent = type;
            
            item.appendChild(columnName);
            item.appendChild(dataType);
            typesDiv.appendChild(item);
        });
        
        container.innerHTML = '';
        container.appendChild(typesDiv);
    },
    
    /**
     * Make content responsive
     */
    makeResponsive: function(container = document) {
        // Wrap tables
        this.wrapTables(container);
        
        // Add responsive classes to content areas
        const contentAreas = container.querySelectorAll('.content-area');
        contentAreas.forEach(area => {
            area.classList.add('full-width');
            
            // Check if contains tables
            if (area.querySelector('table')) {
                area.classList.add('data-display');
            }
        });
        
        // Handle wide content
        const wideElements = container.querySelectorAll('pre, code, .wide-content');
        wideElements.forEach(element => {
            if (!element.closest('.scrollable-content')) {
                const wrapper = document.createElement('div');
                wrapper.className = 'scrollable-content';
                element.parentNode.insertBefore(wrapper, element);
                wrapper.appendChild(element);
            }
        });
    },
    
    /**
     * Initialize responsive behavior
     */
    init: function() {
        // Make existing content responsive
        this.makeResponsive();
        
        // Watch for new content
        const observer = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                if (mutation.type === 'childList') {
                    mutation.addedNodes.forEach((node) => {
                        if (node.nodeType === Node.ELEMENT_NODE) {
                            this.makeResponsive(node);
                        }
                    });
                }
            });
        });
        
        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
        
        // Handle window resize
        let resizeTimeout;
        window.addEventListener('resize', () => {
            clearTimeout(resizeTimeout);
            resizeTimeout = setTimeout(() => {
                this.makeResponsive();
            }, 250);
        });
        
        console.log('Responsive content system initialized');
    }
};

// Auto-initialize when DOM is loaded
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => ResponsiveContent.init());
} else {
    ResponsiveContent.init();
}

// Export for use in other scripts
window.ResponsiveContent = ResponsiveContent;