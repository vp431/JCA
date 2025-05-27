// Custom JavaScript for JoSAA Choice Filling App

document.addEventListener('DOMContentLoaded', function() {
    // Set active nav item based on current URL
    setActiveNavItem();
    
    // Initialize tooltips
    initializeTooltips();
    
    // Auto-dismiss alerts after 5 seconds
    autoDismissAlerts();
    
    // Add event listeners for any college branch buttons
    setupBranchButtons();
});

// Set the active navigation item based on current URL
function setActiveNavItem() {
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.navbar-nav .nav-link');
    
    navLinks.forEach(link => {
        const href = link.getAttribute('href');
        if (currentPath === href || (href !== '/' && currentPath.startsWith(href))) {
            link.classList.add('active');
        }
    });
}

// Initialize Bootstrap tooltips
function initializeTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

// Auto-dismiss alerts after 5 seconds
function autoDismissAlerts() {
    setTimeout(function() {
        const alerts = document.querySelectorAll('.alert');
        alerts.forEach(alert => {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);
}

// Setup branch selection buttons
function setupBranchButtons() {
    const branchButtons = document.querySelectorAll('.branch-btn');
    if (branchButtons.length > 0) {
        branchButtons.forEach(btn => {
            btn.addEventListener('click', function() {
                const branchName = this.textContent.trim();
                document.getElementById('branch_name').value = branchName;
            });
        });
    }
}

// Dynamically load college branches when college is selected
function loadBranches(collegeId) {
    if (!collegeId) return;
    
    fetch(`/api/colleges/${collegeId}/branches`)
        .then(response => response.json())
        .then(data => {
            const branchSelect = document.getElementById('branch_id');
            branchSelect.innerHTML = '<option value="" selected disabled>-- Select Branch --</option>';
            
            data.forEach(branch => {
                const option = document.createElement('option');
                option.value = branch.id;
                option.textContent = branch.name;
                branchSelect.appendChild(option);
            });
        })
        .catch(error => console.error('Error loading branches:', error));
}

// Confirm deletion
function confirmDelete(message) {
    return confirm(message || 'Are you sure you want to delete this item?');
} 