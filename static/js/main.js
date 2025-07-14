document.addEventListener('DOMContentLoaded', () => {
    const sidebarToggleBtn = document.getElementById('sidebar-toggle-btn');
    const sidebar = document.getElementById('sidebar');
    const sidebarCloseBtn = document.getElementById('sidebar-close-btn');
    const mainContent = document.getElementById('main-content');

    // Function to toggle sidebar visibility and update main content padding
    function toggleSidebar() {
        const isHidden = sidebar.classList.contains('hidden');

        sidebar.classList.toggle('hidden');
        mainContent.classList.toggle('sidebar-hidden');

        // Optional: Update hamburger icon appearance if needed
        // if (isHidden) {
        //     sidebarToggleBtn.innerHTML = '&#10799;'; // Example: 'X' or another icon
        // } else {
        //     sidebarToggleBtn.innerHTML = '&#9776;'; // Hamburger icon
        // }
    }

    // Event listener for the hamburger button (always on)
    if (sidebarToggleBtn) {
        sidebarToggleBtn.addEventListener('click', (event) => {
            event.stopPropagation(); // Prevent document click from closing immediately
            toggleSidebar();
        });
    }

    // Event listener for the close button inside the sidebar
    if (sidebarCloseBtn) {
        sidebarCloseBtn.addEventListener('click', () => {
            sidebar.classList.add('hidden');
            mainContent.classList.add('sidebar-hidden');
        });
    }

    // Close sidebar when clicking outside of it
    document.addEventListener('click', (event) => {
        // Only proceed if the sidebar is currently NOT hidden
        if (!sidebar.classList.contains('hidden')) {
            // Check if the click was outside the sidebar AND outside the toggle button
            if (!sidebar.contains(event.target) && !sidebarToggleBtn.contains(event.target)) {
                sidebar.classList.add('hidden');
                mainContent.classList.add('sidebar-hidden');
            }
        }
    });

    // Highlight the active link in the sidebar
    const currentPath = window.location.pathname.replace(/\/$/, ''); // Remove trailing slash for comparison
    const sidebarLinks = document.querySelectorAll('.sidebar-menu a');
    sidebarLinks.forEach(link => {
        const linkHref = link.getAttribute('href').replace(/\/$/, '');

        if (currentPath === '' && linkHref === '') { // Matches root path '/'
             link.classList.add('active');
        } else if (currentPath !== '' && linkHref === currentPath) { // Matches other paths
             link.classList.add('active');
        }
    });

    // Initial setup: Ensure correct state on page load for mobile (sidebar starts hidden)
    const mobileMediaQuery = window.matchMedia('(max-width: 768px)');
    if (mobileMediaQuery.matches) {
        // On mobile, ensure sidebar starts hidden and content has no padding
        sidebar.classList.add('hidden');
        mainContent.classList.add('sidebar-hidden');
    }

    // Add listener for window resize to adjust sidebar state if needed
    mobileMediaQuery.addEventListener('change', (event) => {
        if (event.matches) { // Matches means screen is now SMALLER than 768px
            // Ensure sidebar is hidden and content has no padding
            if (!sidebar.classList.contains('hidden')) {
                sidebar.classList.add('hidden');
                mainContent.classList.add('sidebar-hidden');
            }
        } else { // Does not match means screen is now LARGER than 768px
            // Ensure sidebar is visible and content has padding
            if (sidebar.classList.contains('hidden')) {
                sidebar.classList.remove('hidden');
                mainContent.classList.remove('sidebar-hidden');
            }
        }
    });
});

// Global utility functions that can be used across all modules
window.getStoredDatasets = function() {
    const stored = localStorage.getItem('datasets');
    return stored ? JSON.parse(stored) : [];
};

window.storeDatasets = function(datasets) {
    localStorage.setItem('datasets', JSON.stringify(datasets));
};

window.refreshStoredDatasets = async function() {
    try {
        const response = await fetch('/api/data/datasets');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        if (data.success && data.datasets) {
            storeDatasets(data.datasets);
            return data.datasets;
        }
        return [];
    } catch (error) {
        console.error('Error refreshing datasets:', error);
        return getStoredDatasets(); // Return cached data on error
    }
};

// Global loading and notification functions
window.showGlobalLoading = function() {
    let loadingModal = document.getElementById('global-loading-modal');
    if (!loadingModal) {
        loadingModal = document.createElement('div');
        loadingModal.id = 'global-loading-modal';
        loadingModal.innerHTML = `
            <div class="loading-backdrop">
                <div class="loading-content">
                    <div class="loading-spinner"></div>
                    <p>Loading...</p>
                </div>
            </div>
        `;
        loadingModal.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.5);
            display: none;
            justify-content: center;
            align-items: center;
            z-index: 9999;
        `;
        document.body.appendChild(loadingModal);
    }
    loadingModal.style.display = 'flex';
};

window.hideGlobalLoading = function() {
    const loadingModal = document.getElementById('global-loading-modal');
    if (loadingModal) {
        loadingModal.style.display = 'none';
    }
};

window.showGlobalError = function(message) {
    // Create a simple error notification
    const errorDiv = document.createElement('div');
    errorDiv.className = 'global-error-notification';
    errorDiv.innerHTML = `
        <div class="error-content">
            <span class="error-icon">⚠️</span>
            <span class="error-message">${message}</span>
            <button onclick="this.parentElement.parentElement.remove()">×</button>
        </div>
    `;
    errorDiv.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: #fee2e2;
        border: 1px solid #fecaca;
        border-radius: 8px;
        padding: 16px;
        max-width: 400px;
        z-index: 10000;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    `;
    document.body.appendChild(errorDiv);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        if (errorDiv.parentElement) {
            errorDiv.remove();
        }
    }, 5000);
};

window.showGlobalSuccess = function(message) {
    // Create a simple success notification
    const successDiv = document.createElement('div');
    successDiv.className = 'global-success-notification';
    successDiv.innerHTML = `
        <div class="success-content">
            <span class="success-icon">✅</span>
            <span class="success-message">${message}</span>
            <button onclick="this.parentElement.parentElement.remove()">×</button>
        </div>
    `;
    successDiv.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: #d1fae5;
        border: 1px solid #a7f3d0;
        border-radius: 8px;
        padding: 16px;
        max-width: 400px;
        z-index: 10000;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    `;
    document.body.appendChild(successDiv);
    
    // Auto remove after 3 seconds
    setTimeout(() => {
        if (successDiv.parentElement) {
            successDiv.remove();
        }
    }, 3000);
};