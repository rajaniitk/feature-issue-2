document.addEventListener('DOMContentLoaded', () => {
    const fileInput = document.getElementById('file-upload');
    const fileNameDisplay = document.getElementById('file-name');
    const uploadForm = document.getElementById('upload-form');
    const uploadStatus = document.getElementById('upload-status');
    const filePreviewSection = document.getElementById('file-preview');

    if (fileInput) {
        fileInput.addEventListener('change', function() {
            if (this.files.length > 0) {
                fileNameDisplay.textContent = this.files[0].name;
                fileNameDisplay.style.color = '#333';
            } else {
                fileNameDisplay.textContent = 'No file chosen';
                fileNameDisplay.style.color = '#999';
            }
        });
    }

    if (uploadForm) {
        uploadForm.addEventListener('submit', async function(event) {
            event.preventDefault(); // Prevent default browser form submission

            const formData = new FormData(this);
            const file = fileInput.files[0];

            // Clear previous status and preview
            uploadStatus.textContent = '';
            uploadStatus.style.color = '';
            if (filePreviewSection) filePreviewSection.innerHTML = '';

            if (!file) {
                uploadStatus.textContent = 'Please select a file to upload.';
                uploadStatus.style.color = 'red';
                return;
            }

            // Disable button and show loading state
            const submitButton = uploadForm.querySelector('button[type="submit"]');
            submitButton.disabled = true;
            uploadStatus.textContent = 'Uploading...';
            uploadStatus.style.color = '#888';

            try {
                // Use the correct API route for upload
                const uploadUrl = '/api/data/upload';

                // POST the form data to the upload endpoint
                const response = await fetch(uploadUrl, {
                    method: 'POST',
                    body: formData
                    // 'Content-Type' is automatically set by FormData for multipart/form-data
                });

                // IMPORTANT: Check if the response is OK (status code 2xx)
                // If it's not OK (e.g., 404, 500), response.json() might fail if the response is HTML.
                if (!response.ok) {
                    // Try to get error message from Flask's JSON response if available
                    let errorMsg = `HTTP error! Status: ${response.status}`;
                    try {
                        const errorResult = await response.json();
                        errorMsg = errorResult.error || errorMsg;
                    } catch (jsonError) {
                        // If response is not JSON (e.g., HTML error page), use status text
                        console.error("Failed to parse error response as JSON:", jsonError);
                    }
                    throw new Error(errorMsg); // Throw an error to be caught by the catch block
                }

                const result = await response.json(); // Parse the JSON response from Flask

                if (result.success) { // Check if Flask reported success
                    uploadStatus.textContent = result.message || 'File uploaded successfully!';
                    uploadStatus.style.color = 'green';

                    if (result.dataset_id) {
                        // Optionally, store dataset_id locally if needed
                        // localStorage.setItem('currentDatasetId', result.dataset_id);
                    }
                    if (result.preview) {
                        displayFilePreview(result.preview);
                    }
                    // Clear file input and reset UI
                    fileInput.value = '';
                    fileNameDisplay.textContent = 'No file chosen';
                    fileNameDisplay.style.color = '#999';
                    
                } else {
                    // Handle errors reported by Flask (result.success is false)
                    uploadStatus.textContent = result.error || 'Upload failed.';
                    uploadStatus.style.color = 'red';
                }
            } catch (error) {
                console.error('Fetch operation failed:', error);
                // This catch block now handles both network errors and errors thrown from !response.ok
                uploadStatus.textContent = error.message || 'An unexpected error occurred during fetch.';
                uploadStatus.style.color = 'red';
            } finally {
                // Re-enable the button
                submitButton.disabled = false;
            }
        });
    }

    // Function to display the file preview table
    function displayFilePreview(previewData) {
        if (!filePreviewSection || !previewData) {
            return;
        }
        const { head, tail, columns, dtypes } = previewData; // Removed shape as it's not used in table creation
        let previewHTML = '';

        if (head && head.length > 0) {
            previewHTML += '<h3>File Preview (First 10 Rows)</h3>';
            previewHTML += createTable(head, columns, dtypes, 'preview-table-head');
        }
        if (tail && tail.length > 0) {
            previewHTML += '<h3>File Preview (Last 10 Rows)</h3>';
            previewHTML += createTable(tail, columns, dtypes, 'preview-table-tail');
        }
        
        if (!previewHTML) {
            previewHTML = '<p>No preview data available.</p>';
        }
        filePreviewSection.innerHTML = previewHTML;
    }

    // Helper function to create an HTML table
    function createTable(data, columns, dtypes, tableClass) {
        let tableHTML = '<div class="preview-table-container">';
        tableHTML += `<table class="preview-table ${tableClass}">`;
        
        // Table header
        tableHTML += '<thead><tr>';
        columns.forEach(col => {
            const colType = dtypes[col] || 'unknown';
            const safeCol = col.replace(/</g, "&lt;").replace(/>/g, "&gt;");
            tableHTML += `<th title="${safeCol} (${colType})">${safeCol}</th>`;
        });
        tableHTML += '</tr></thead>';

        // Table body
        tableHTML += '<tbody>';
        data.forEach(row => {
            tableHTML += '<tr>';
            columns.forEach(col => {
                const cellValue = row[col];
                const safeCell = cellValue !== null && cellValue !== undefined
                    ? String(cellValue).replace(/</g, "&lt;").replace(/>/g, "&gt;")
                    : '';
                tableHTML += `<td>${safeCell}</td>`;
            });
            tableHTML += '</tr>';
        });
        tableHTML += '</tbody>';
        tableHTML += '</table></div>';
        return tableHTML;
    }
});