// Olivian Group - Dashboard JavaScript

const Dashboard = {
    // Initialize dashboard functionality
    init: function() {
        this.initSidebar();
        this.initCharts();
        this.initDataTables();
        this.initModals();
    },

    // Initialize sidebar functionality
    initSidebar: function() {
        const sidebarToggle = document.querySelector('#sidebar-toggle');
        const sidebar = document.querySelector('.sidebar');
        const mainContent = document.querySelector('.main-content');

        if (sidebarToggle && sidebar) {
            sidebarToggle.addEventListener('click', function() {
                sidebar.classList.toggle('show');
                if (window.innerWidth <= 768) {
                    mainContent.style.marginLeft = sidebar.classList.contains('show') ? '280px' : '0';
                }
            });
        }

        // Auto-collapse sidebar on mobile
        if (window.innerWidth <= 768) {
            const menuLinks = document.querySelectorAll('.sidebar .nav-link');
            menuLinks.forEach(link => {
                link.addEventListener('click', () => {
                    sidebar.classList.remove('show');
                    mainContent.style.marginLeft = '0';
                });
            });
        }
    },

    // Initialize charts (placeholder for Chart.js integration)
    initCharts: function() {
        // This will be expanded when Chart.js is integrated
        const chartElements = document.querySelectorAll('[data-chart]');
        chartElements.forEach(element => {
            // Placeholder for chart initialization
            element.innerHTML = '<p class="text-muted">Chart will be rendered here</p>';
        });
    },

    // Initialize DataTables (placeholder)
    initDataTables: function() {
        const tables = document.querySelectorAll('.data-table');
        tables.forEach(table => {
            // Add basic table enhancements
            table.classList.add('table-hover');
            
            // Add search functionality if not present
            if (!table.parentElement.querySelector('.table-search')) {
                const searchDiv = document.createElement('div');
                searchDiv.className = 'table-search mb-3';
                searchDiv.innerHTML = `
                    <input type="text" class="form-control" placeholder="Search table..." onkeyup="Dashboard.filterTable(this, '${table.id}')">
                `;
                table.parentElement.insertBefore(searchDiv, table);
            }
        });
    },

    // Simple table filter function
    filterTable: function(input, tableId) {
        const filter = input.value.toUpperCase();
        const table = document.getElementById(tableId);
        const rows = table.getElementsByTagName('tr');

        for (let i = 1; i < rows.length; i++) {
            const row = rows[i];
            const cells = row.getElementsByTagName('td');
            let found = false;

            for (let j = 0; j < cells.length; j++) {
                const cell = cells[j];
                if (cell.textContent.toUpperCase().indexOf(filter) > -1) {
                    found = true;
                    break;
                }
            }

            row.style.display = found ? '' : 'none';
        }
    },

    // Initialize modals
    initModals: function() {
        // Add loading states to modal forms
        const modalForms = document.querySelectorAll('.modal form');
        modalForms.forEach(form => {
            form.addEventListener('submit', function() {
                const submitBtn = form.querySelector('button[type="submit"]');
                if (submitBtn) {
                    OlivianSolar.showLoading(submitBtn);
                }
            });
        });
    },

    // Update dashboard stats (for AJAX updates)
    updateStats: function(stats) {
        Object.keys(stats).forEach(key => {
            const element = document.querySelector(`[data-stat="${key}"]`);
            if (element) {
                element.textContent = stats[key];
            }
        });
    },

    // Show notification
    showNotification: function(message, type = 'info') {
        const alertHtml = `
            <div class="alert alert-${type} alert-dismissible fade show" role="alert" data-auto-dismiss="5000">
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;
        
        const container = document.querySelector('.notifications-container') || document.body;
        container.insertAdjacentHTML('afterbegin', alertHtml);
        
        // Re-initialize alerts for auto-dismiss
        OlivianSolar.initAlerts();
    }
};

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    Dashboard.init();
});

// Export for global use
window.Dashboard = Dashboard;
