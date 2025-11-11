console.log('IDS Frontend loaded');

// ========================================= UTILITY FUNCTIONS =============================================
/**
 * Fetch JSON from API (GET)
 */
async function fetchJSON(url) {
    try {
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        return await response.json();
    } catch (error) {
        console.error('fetchJSON error:', error);
        throw error;
    }
}

/**
 * POST JSON to API
 */
async function postJSON(url, data = {}) {
    try {
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        return await response.json();
    } catch (error) {
        console.error('postJSON error:', error);
        throw error;
    }
}

/**
 * DELETE request to API
 */
async function deleteJSON(url) {
    try {
        const response = await fetch(url, {
            method: 'DELETE'
        });
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        return await response.json();
    } catch (error) {
        console.error('deleteJSON error:', error);
        throw error;
    }
}

// ===== TOAST NOTIFICATIONS =====

/**
 * Show success toast notification
 */
function showSuccess(message) {
    showToast(message, 'success');
}

/**
 * Show error toast notification
 */
function showError(message) {
    showToast(message, 'danger');
}

/**
 * Show info toast notification
 */
function showInfo(message) {
    showToast(message, 'info');
}

/**
 * Generic toast function using Bootstrap toast
 */
function showToast(message, type = 'info') {
    // Create toast container if not exists
    let container = document.getElementById('toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        container.className = 'toast-container position-fixed top-0 end-0 p-3';
        container.style.zIndex = '9999';
        document.body.appendChild(container);
    }

    // Create toast element
    const toastId = 'toast-' + Date.now();
    const toastHTML = `
        <div id="${toastId}" class="toast align-items-center text-bg-${type} border-0" role="alert">
            <div class="d-flex">
                <div class="toast-body">
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        </div>
    `;

    container.insertAdjacentHTML('beforeend', toastHTML);

    // Show toast
    const toastElement = document.getElementById(toastId);
    const toast = new bootstrap.Toast(toastElement, {delay: 3000});
    toast.show();

    // Remove after hide
    toastElement.addEventListener('hidden.bs.toast', () => {
        toastElement.remove();
    });
}


// ========================================= WEBSOCKET CONNECTION =============================================

let ws = null;
let wsReconnectTimeout = null;

/**
 * Connect to WebSocket for real-time alerts
 */
function connectWebSocket() {
    // Close existing connection
    if (ws) {
        ws.close();
    }

    const wsUrl = `ws://${window.location.host}/ws/alerts`;
    console.log('Connecting to WebSocket:', wsUrl);

    ws = new WebSocket(wsUrl);

    ws.onopen = () => {
        console.log('WebSocket connected');
        updateWSStatus('connected');

        // Clear reconnect timeout
        if (wsReconnectTimeout) {
            clearTimeout(wsReconnectTimeout);
            wsReconnectTimeout = null;
        }

        // Send ping every 30s to keep connection alive
        setInterval(() => {
            if (ws && ws.readyState === WebSocket.OPEN) {
                ws.send('ping');
            }
        }, 30000);
    };

    ws.onmessage = (event) => {
        try {
            if (event.data === 'pong') {
                return;
            }

            const alert = JSON.parse(event.data);
            console.log('Received alert:', alert);

            // Show toast notification
            showAlertToast(alert);

            // Add to alerts feed
            addAlertToFeed(alert);

            // Trigger custom event for other pages
            window.dispatchEvent(new CustomEvent('newAlert', {detail: alert}));

        } catch (error) {
            console.error('Error parsing alert:', error);
        }
    };

    ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        updateWSStatus('error');
    };

    ws.onclose = () => {
        console.log('WebSocket disconnected');
        updateWSStatus('disconnected');

        // Auto-reconnect after 5s
        wsReconnectTimeout = setTimeout(() => {
            console.log('Attempting to reconnect WebSocket...');
            connectWebSocket();
        }, 5000);
    };
}

/**
 * Update WebSocket status badge
 */
function updateWSStatus(status) {
    const badge = document.getElementById('wsStatus');
    if (!badge) return;

    if (status === 'connected') {
        badge.textContent = 'Connected';
        badge.className = 'badge bg-success';
    } else if (status === 'disconnected') {
        badge.textContent = 'Disconnected';
        badge.className = 'badge bg-secondary';
    } else if (status === 'error') {
        badge.textContent = 'Error';
        badge.className = 'badge bg-danger';
    }
}

/**
 * Show alert as toast notification
 */
function showAlertToast(alert) {
    const type = alert.severity === 'critical' ? 'danger' : 'warning';
    const message = `🚨 ${alert.attack_type} detected from ${alert.source_ip}`;
    showToast(message, type);
}

/**
 * Add alert to feed list
 */
function addAlertToFeed(alert) {
    const feed = document.getElementById('alertsFeed');
    if (!feed) return;

    // Remove "no alerts" message
    if (feed.querySelector('.text-muted')) {
        feed.innerHTML = '';
    }

    // Create alert item
    const severityClass = alert.severity === 'critical' ? 'danger' : 'warning';
    const time = new Date(alert.timestamp).toLocaleTimeString();

    const alertHTML = `
        <div class="alert alert-${severityClass} alert-dismissible fade show mb-2" role="alert">
            <strong>${time}</strong> - ${alert.attack_type} 
            from <code>${alert.source_ip}</code> → <code>${alert.dest_ip}</code>
            <span class="badge bg-dark">${(alert.confidence * 100).toFixed(1)}%</span>
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;

    feed.insertAdjacentHTML('afterbegin', alertHTML);

    // Keep only last 20 alerts
    const alerts = feed.querySelectorAll('.alert');
    if (alerts.length > 20) {
        alerts[alerts.length - 1].remove();
    }
}

// ===== MONITOR PAGE FUNCTIONS =====

/**
 * Start monitoring
 */
async function startMonitoring() {
    const startBtn = document.getElementById('startBtn');
    const stopBtn = document.getElementById('stopBtn');
    const statusBadge = document.getElementById('statusBadge');

    try {
        startBtn.disabled = true;
        startBtn.innerHTML = '⏳ Starting...';

        const response = await postJSON('/api/monitor/start');

        console.log('Monitoring started:', response);
        showSuccess('Monitoring started successfully!');

        // Update UI
        startBtn.disabled = true;
        stopBtn.disabled = false;
        statusBadge.textContent = 'Active';
        statusBadge.className = 'badge bg-success fs-6';

        // Start stats update
        startStatsUpdate();

    } catch (error) {
        console.error('Failed to start monitoring:', error);
        showError('Failed to start monitoring: ' + error.message);

        // Reset button
        startBtn.disabled = false;
        startBtn.innerHTML = '▶ Start Monitoring';
    }
}

/**
 * Stop monitoring
 */
async function stopMonitoring() {
    const startBtn = document.getElementById('startBtn');
    const stopBtn = document.getElementById('stopBtn');
    const statusBadge = document.getElementById('statusBadge');

    try {
        stopBtn.disabled = true;
        stopBtn.innerHTML = '⏳ Stopping...';

        const response = await postJSON('/api/monitor/stop');

        console.log('Monitoring stopped:', response);
        showInfo('Monitoring stopped');

        // Update UI
        startBtn.disabled = false;
        stopBtn.disabled = true;
        stopBtn.innerHTML = '⏹ Stop Monitoring';
        statusBadge.textContent = 'Inactive';
        statusBadge.className = 'badge bg-secondary fs-6';

        // Stop stats update
        stopStatsUpdate();

    } catch (error) {
        console.error('Failed to stop monitoring:', error);
        showError('Failed to stop monitoring: ' + error.message);

        // Reset button
        stopBtn.disabled = false;
        stopBtn.innerHTML = '⏹ Stop Monitoring';
    }
}

let statsUpdateInterval = null;

/**
 * Start stats auto-update
 */
function startStatsUpdate() {
    // Update immediately
    updateStats();

    // Then update every 2 seconds
    statsUpdateInterval = setInterval(updateStats, 2000);
}

/**
 * Stop stats auto-update
 */
function stopStatsUpdate() {
    if (statsUpdateInterval) {
        clearInterval(statsUpdateInterval);
        statsUpdateInterval = null;
    }
}

/**
 * Update statistics from API
 */
async function updateStats() {
    try {
        const stats = await fetchJSON('/api/monitor/status');

        // Update capture stats
        document.getElementById('statsPackets').textContent =
            stats.capture.packets_captured.toLocaleString();  // ← ĐÚNG
        document.getElementById('statsFlows').textContent =
            stats.capture.active_flows.toLocaleString();
        document.getElementById('statsFeatures').textContent =
            stats.capture.features_extracted.toLocaleString();

        // Update detection stats
        document.getElementById('statsPredictions').textContent =
            stats.detection.total_predictions.toLocaleString();
        document.getElementById('statsAlerts').textContent =
            stats.detection.alerts_created.toLocaleString();

    } catch (error) {
        console.error('Failed to update stats:', error);
    }
}

// ============================= PAGE INITIALIZATION =============================

/**
 * Initialize monitor page
 */
function initMonitorPage() {
    const startBtn = document.getElementById('startBtn');
    const stopBtn = document.getElementById('stopBtn');

    if (!startBtn || !stopBtn) return; // Not on monitor page

    console.log('Initializing monitor page...');

    // Attach button handlers
    startBtn.addEventListener('click', startMonitoring);
    stopBtn.addEventListener('click', stopMonitoring);

    // Connect WebSocket
    connectWebSocket();

    // Check current status
    checkMonitoringStatus();
}

/**
 * Check current monitoring status on page load
 */
async function checkMonitoringStatus() {
    try {
        const stats = await fetchJSON('/api/monitor/status');

        const startBtn = document.getElementById('startBtn');
        const stopBtn = document.getElementById('stopBtn');
        const statusBadge = document.getElementById('statusBadge');

        if (stats.detection.is_running && stats.detection.detection_running) {
            // Already running
            startBtn.disabled = true;
            stopBtn.disabled = false;
            statusBadge.textContent = 'Active';
            statusBadge.className = 'badge bg-success fs-6';

            // Start stats update
            startStatsUpdate();
        }
    } catch (error) {
        console.error('Failed to check monitoring status:', error);
    }
}

// ================================== DASHBOARD PAGE FUNCTIONS ==================================
let pieChart = null;
let lineChart = null;
let dashboardRefreshInterval = null;

/**
 * Initialize dashboard page
 */
function initDashboard() {
    const totalAlertsEl = document.getElementById('totalAlerts');
    if (!totalAlertsEl) return; // Not on dashboard page

    console.log('Initializing dashboard...');

    // Load dashboard data
    loadDashboardData();

    // Auto-refresh every 5 seconds
    dashboardRefreshInterval = setInterval(loadDashboardData, 5000);

    // Listen for new alerts from WebSocket
    window.addEventListener('newAlert', () => {
        console.log('New alert received, refreshing dashboard...');
        loadDashboardData();
    });

    // Connect WebSocket for real-time updates
    connectWebSocket();
}

/**
 * Load all dashboard data
 */
async function loadDashboardData() {
    try {
        // Load stats, timeline, and recent alerts in parallel
        const [stats, timeline, recentAlerts] = await Promise.all([  // ← THÊM timeline
            fetchJSON('/api/stats'),
            fetchJSON('/api/stats/timeline?period=day'),  // ← THÊM DÒNG NÀY
            fetchJSON('/api/alerts/recent?n=5')
        ]);

        // Update stats cards
        updateStatsCards(stats);

        // Update pie chart
        updatePieChart(stats.attack_types);

        // Update timeline chart
        updateTimelineChart(timeline);  // ← Giờ timeline đã có

        // Update recent alerts table
        updateRecentAlertsTable(recentAlerts.alerts);

    } catch (error) {
        console.error('Failed to load dashboard data:', error);
    }
}

/**
 * Update stats cards
 */
function updateStatsCards(stats) {
    console.log('Stats received:', stats);  // ← Debug log

    // Total alerts
    const totalAlerts = stats.overview?.total_alerts || 0;
    document.getElementById('totalAlerts').textContent =
        totalAlerts.toLocaleString();

    // Critical alerts
    const criticalAlerts = stats.overview?.critical_alerts || 0;
    document.getElementById('criticalAlerts').textContent =
        criticalAlerts.toLocaleString();

    // Monitoring status
    const statusEl = document.getElementById('monitoringStatus');
    if (stats.overview?.monitoring_active) {
        statusEl.innerHTML = '<span class="badge bg-success">Active</span>';
    } else {
        statusEl.innerHTML = '<span class="badge bg-secondary">Inactive</span>';
    }
}

/**
 * Update pie chart with attack types distribution
 */
function updatePieChart(attackTypes) {
    const ctx = document.getElementById('attackTypesChart');
    if (!ctx) return;

    // Prepare data
    const labels = [];
    const data = [];
    const colors = {
        'DoS Hulk': '#dc3545',    // red
        'PortScan': '#fd7e14',     // orange
        'DDoS': '#6f42c1'          // purple
    };

    const backgroundColors = [];

    for (const [type, count] of Object.entries(attackTypes)) {
        labels.push(type);
        data.push(count);
        backgroundColors.push(colors[type] || '#6c757d');
    }

    // Check if no data
    if (data.every(v => v === 0)) {
        // Show "No data" message
        if (pieChart) {
            pieChart.destroy();
            pieChart = null;
        }
        ctx.getContext('2d').clearRect(0, 0, ctx.width, ctx.height);
        const context = ctx.getContext('2d');
        context.font = '16px Arial';
        context.fillStyle = '#6c757d';
        context.textAlign = 'center';
        context.fillText('No attack data yet', ctx.width / 2, ctx.height / 2);
        return;
    }

    // Create or update chart
    if (pieChart) {
        pieChart.data.labels = labels;
        pieChart.data.datasets[0].data = data;
        pieChart.data.datasets[0].backgroundColor = backgroundColors;
        pieChart.update();
    } else {
        pieChart = new Chart(ctx, {
            type: 'pie',
            data: {
                labels: labels,
                datasets: [{
                    data: data,
                    backgroundColor: backgroundColors
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });
    }
}

/**
 * Update timeline chart with last 24h alerts
 */
function updateTimelineChart(timelineData) {
    const ctx = document.getElementById('timelineChart');
    if (!ctx) return;

    // Prepare data
    const labels = [];
    const data = [];

    // Check if timeline has data
    if (!timelineData.timeline || timelineData.timeline.length === 0) {
        // Show "No data" message
        if (lineChart) {
            lineChart.destroy();
            lineChart = null;
        }
        ctx.getContext('2d').clearRect(0, 0, ctx.width, ctx.height);
        const context = ctx.getContext('2d');
        context.font = '16px Arial';
        context.fillStyle = '#6c757d';
        context.textAlign = 'center';
        context.fillText('No alerts in last 24 hours', ctx.width / 2, ctx.height / 2);
        return;
    }

    // Extract labels and data from timeline
    for (const entry of timelineData.timeline) {
        const time = new Date(entry.time);
        labels.push(time.toLocaleTimeString('en-US', {
            hour: '2-digit',
            minute: '2-digit'
        }));
        data.push(entry.total);
    }

    // Check if no data
    if (data.length === 0 || data.every(v => v === 0)) {
        // Show "No data" message
        if (lineChart) {
            lineChart.destroy();
            lineChart = null;
        }
        ctx.getContext('2d').clearRect(0, 0, ctx.width, ctx.height);
        const context = ctx.getContext('2d');
        context.font = '16px Arial';
        context.fillStyle = '#6c757d';
        context.textAlign = 'center';
        context.fillText('No alerts in last 24 hours', ctx.width / 2, ctx.height / 2);
        return;
    }

    // Create or update chart
    if (lineChart) {
        lineChart.data.labels = labels;
        lineChart.data.datasets[0].data = data;
        lineChart.update();
    } else {
        lineChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Alerts',
                    data: data,
                    borderColor: '#0d6efd',
                    backgroundColor: 'rgba(13, 110, 253, 0.1)',
                    tension: 0.4,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            stepSize: 1
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: false
                    }
                }
            }
        });
    }
}

/**
 * Update recent alerts table
 */
function updateRecentAlertsTable(alerts) {
    const tbody = document.querySelector('#recentAlertsTable tbody');
    if (!tbody) return;

    // Clear existing rows
    tbody.innerHTML = '';

    // Check if no alerts
    if (!alerts || alerts.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="5" class="text-center text-muted">No alerts yet</td>
            </tr>
        `;
        return;
    }

    // Add rows
    alerts.forEach(alert => {
        const time = new Date(alert.timestamp).toLocaleTimeString();
        const severityClass = alert.severity === 'critical' ? 'danger' : 'warning';
        const severityBadge = `<span class="badge bg-${severityClass}">${alert.severity}</span>`;

        const row = `
            <tr>
                <td>${time}</td>
                <td><strong>${alert.attack_type}</strong></td>
                <td><code>${alert.source_ip}</code></td>
                <td><code>${alert.dest_ip}</code></td>
                <td>${severityBadge}</td>
            </tr>
        `;
        tbody.insertAdjacentHTML('beforeend', row);
    });
}

// ================================== UPDATE PAGE INITIALIZATION ==================================

// Update the existing DOMContentLoaded listener
document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM loaded');

    initMonitorPage();

    // Initialize dashboard if on dashboard page
    initDashboard();
});


// ================================== ALERTS PAGE FUNCTIONS ==================================

let currentPage = 1;
let currentFilters = {};
let deleteAlertId = null;

/**
 * Initialize alerts page
 */
function initAlertsPage() {
    const alertsTable = document.getElementById('alertsTable');
    if (!alertsTable) return; // Not on alerts page

    console.log('Initializing alerts page...');

    // Load alerts
    loadAlerts();

    // Setup filter form
    const filterForm = document.getElementById('filterForm');
    if (filterForm) {
        filterForm.addEventListener('submit', applyFilters);
    }

    // Setup delete modal
    const confirmDeleteBtn = document.getElementById('confirmDeleteBtn');
    if (confirmDeleteBtn) {
        confirmDeleteBtn.addEventListener('click', confirmDelete);
    }

    // Listen for new alerts from WebSocket
    window.addEventListener('newAlert', () => {
        console.log('New alert received, refreshing alerts page...');
        loadAlerts();
    });

    // Connect WebSocket for real-time updates
    connectWebSocket();
}

/**
 * Load alerts from API
 */
async function loadAlerts() {
    try {
        // Build query params
        const params = new URLSearchParams({
            page: currentPage,
            limit: 50
        });

        // Add filters
        if (currentFilters.attack_type) {
            params.append('attack_type', currentFilters.attack_type);
        }
        if (currentFilters.severity) {
            params.append('severity', currentFilters.severity);
        }
        if (currentFilters.source_ip) {
            params.append('source_ip', currentFilters.source_ip);
        }

        // Fetch alerts
        const response = await fetchJSON(`/api/alerts?${params.toString()}`);

        // Render table
        renderAlertsTable(response.alerts);

        // Update pagination
        updatePagination(response);

    } catch (error) {
        console.error('Failed to load alerts:', error);
        showError('Failed to load alerts: ' + error.message);
    }
}

/**
 * Render alerts table
 */
function renderMetricsTable(metrics) {
    const tbody = document.querySelector('#metricsTable tbody');
    if (!tbody) return;

    // Clear existing rows
    tbody.innerHTML = '';

    // Get class names
    const classes = ['BENIGN', 'DoS Hulk', 'PortScan', 'DDoS'];

    // Check if metrics has test.classification_report data
    if (!metrics.test || !metrics.test.classification_report) {
        tbody.innerHTML = `
            <tr>
                <td colspan="5" class="text-center text-muted">No per-class metrics available</td>
            </tr>
        `;
        return;
    }

    // Add rows for each class
    classes.forEach(className => {
        const classMetrics = metrics.test.classification_report[className];

        if (!classMetrics) return;

        const precision = (classMetrics.precision * 100).toFixed(2);
        const recall = (classMetrics.recall * 100).toFixed(2);
        const f1 = (classMetrics['f1-score'] * 100).toFixed(2);
        const support = classMetrics.support.toLocaleString();

        const row = `
            <tr>
                <td><strong>${className}</strong></td>
                <td>${precision}%</td>
                <td>${recall}%</td>
                <td>${f1}%</td>
                <td>${support}</td>
            </tr>
        `;
        tbody.insertAdjacentHTML('beforeend', row);
    });
}

/**
 * Update pagination controls
 */
function updatePagination(response) {
    // Update total count
    const totalCountEl = document.getElementById('totalCount');
    if (totalCountEl) {
        totalCountEl.textContent = response.total.toLocaleString();
    }

    // Update page info
    document.getElementById('currentPage').textContent = response.page;
    document.getElementById('totalPages').textContent = response.pages;

    // Update Previous button
    const prevPage = document.getElementById('prevPage');
    if (prevPage) {
        if (response.has_prev) {
            prevPage.classList.remove('disabled');
        } else {
            prevPage.classList.add('disabled');
        }
    }

    // Update Next button
    const nextPage = document.getElementById('nextPage');
    if (nextPage) {
        if (response.has_next) {
            nextPage.classList.remove('disabled');
        } else {
            nextPage.classList.add('disabled');
        }
    }
}

/**
 * Apply filters
 */
function applyFilters(event) {
    event.preventDefault();

    // Get filter values
    currentFilters = {
        attack_type: document.getElementById('filterAttackType').value,
        severity: document.getElementById('filterSeverity').value,
        source_ip: document.getElementById('filterSourceIP').value.trim()
    };

    // Reset to page 1
    currentPage = 1;

    // Reload alerts
    loadAlerts();

    console.log('Filters applied:', currentFilters);
}

/**
 * Go to previous page
 */
function goToPreviousPage(event) {
    event.preventDefault();

    if (currentPage > 1) {
        currentPage--;
        loadAlerts();
    }
}

/**
 * Go to next page
 */
function goToNextPage(event) {
    event.preventDefault();

    currentPage++;
    loadAlerts();
}

/**
 * Show delete confirmation modal
 */
function showDeleteModal(alertId) {
    deleteAlertId = alertId;
    const modal = new bootstrap.Modal(document.getElementById('deleteModal'));
    modal.show();
}

/**
 * Confirm delete alert
 */
async function confirmDelete() {
    if (!deleteAlertId) return;

    try {
        // Delete alert
        await deleteJSON(`/api/alerts/${deleteAlertId}`);

        // Hide modal
        const modal = bootstrap.Modal.getInstance(document.getElementById('deleteModal'));
        modal.hide();

        // Show success
        showSuccess('Alert deleted successfully');

        // Reload alerts
        loadAlerts();

        // Reset
        deleteAlertId = null;

    } catch (error) {
        console.error('Failed to delete alert:', error);
        showError('Failed to delete alert: ' + error.message);
    }
}

// ================================== UPDATE PAGE INITIALIZATION ==================================

// Update the existing DOMContentLoaded listener
document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM loaded');

    // Initialize monitor page if on monitor page
    initMonitorPage();

    // Initialize dashboard if on dashboard page
    initDashboard();

    // Initialize alerts page if on alerts page
    initAlertsPage();
});


// ================================== SETTINGS PAGE FUNCTIONS ==================================

let deleteIPId = null;
let deleteIPType = null; // 'whitelist' or 'blacklist'

/**
 * Initialize settings page
 */
function initSettingsPage() {
    const whitelistTable = document.getElementById('whitelistTable');
    if (!whitelistTable) return; // Not on settings page

    console.log('Initializing settings page...');

    // Load whitelist and blacklist
    loadWhitelist();
    loadBlacklist();

    // Setup form handlers
    const whitelistForm = document.getElementById('addWhitelistForm');
    if (whitelistForm) {
        whitelistForm.addEventListener('submit', addToWhitelist);
    }

    const blacklistForm = document.getElementById('addBlacklistForm');
    if (blacklistForm) {
        blacklistForm.addEventListener('submit', addToBlacklist);
    }

    // Setup delete modal
    const confirmDeleteIPBtn = document.getElementById('confirmDeleteIPBtn');
    if (confirmDeleteIPBtn) {
        confirmDeleteIPBtn.addEventListener('click', confirmDeleteIP);
    }
}

/**
 * Validate IP address format
 */
function validateIP(ip) {
    const ipRegex = /^(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/;
    return ipRegex.test(ip);
}

/**
 * Load whitelist from API
 */
async function loadWhitelist() {
    try {
        const response = await fetchJSON('/api/whitelist');
        renderIPTable(response.whitelist, 'whitelistTable', 'whitelist');
    } catch (error) {
        console.error('Failed to load whitelist:', error);
        showError('Failed to load whitelist: ' + error.message);
    }
}

/**
 * Load blacklist from API
 */
async function loadBlacklist() {
    try {
        const response = await fetchJSON('/api/blacklist');
        renderIPTable(response.blacklist, 'blacklistTable', 'blacklist');
    } catch (error) {
        console.error('Failed to load blacklist:', error);
        showError('Failed to load blacklist: ' + error.message);
    }
}

/**
 * Render IP table (whitelist or blacklist)
 */
function renderIPTable(ipList, tableId, type) {
    const tbody = document.querySelector(`#${tableId} tbody`);
    if (!tbody) return;

    // Clear existing rows
    tbody.innerHTML = '';

    // Check if empty
    if (!ipList || ipList.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="5" class="text-center text-muted">No IPs in ${type}</td>
            </tr>
        `;
        return;
    }

    // Add rows
    ipList.forEach(item => {
        const addedAt = new Date(item.added_at).toLocaleString();

        const row = `
            <tr>
                <td>${item.id}</td>
                <td><code>${item.ip_address}</code></td>
                <td>${item.description || '-'}</td>
                <td>${addedAt}</td>
                <td>
                    <button class="btn btn-sm btn-danger" 
                            onclick="showDeleteIPModal(${item.id}, '${item.ip_address}', '${type}')">
                        Delete
                    </button>
                </td>
            </tr>
        `;
        tbody.insertAdjacentHTML('beforeend', row);
    });
}

/**
 * Add IP to whitelist
 */
async function addToWhitelist(event) {
    event.preventDefault();

    const ipInput = document.getElementById('whitelistIP');
    const descInput = document.getElementById('whitelistDesc');

    const ip = ipInput.value.trim();
    const description = descInput.value.trim();

    // Validate IP
    if (!validateIP(ip)) {
        ipInput.classList.add('is-invalid');
        showError('Invalid IP address format');
        return;
    }

    ipInput.classList.remove('is-invalid');

    try {
        const payload = {
            ip_address: ip,
            description: description
        };
        console.log('Sending payload:', payload);  // ← THÊM LOG

        // Add to whitelist
        await postJSON('/api/whitelist', payload);

        // Show success
        showSuccess(`IP ${ip} added to whitelist`);

        // Clear form
        ipInput.value = '';
        descInput.value = '';

        // Reload whitelist
        loadWhitelist();

    } catch (error) {
        console.error('Failed to add to whitelist:', error);
        showError('Failed to add to whitelist: ' + error.message);
    }
}

/**
 * Add IP to blacklist
 */
async function addToBlacklist(event) {
    event.preventDefault();

    const ipInput = document.getElementById('blacklistIP');
    const descInput = document.getElementById('blacklistDesc');

    const ip = ipInput.value.trim();
    const description = descInput.value.trim();

    // Validate IP
    if (!validateIP(ip)) {
        ipInput.classList.add('is-invalid');
        showError('Invalid IP address format');
        return;
    }

    ipInput.classList.remove('is-invalid');

    try {
        // Add to blacklist
        await postJSON('/api/blacklist', {
            ip_address: ip,
            description: description
        });

        // Show success
        showSuccess(`IP ${ip} added to blacklist`);

        // Clear form
        ipInput.value = '';
        descInput.value = '';

        // Reload blacklist
        loadBlacklist();

    } catch (error) {
        console.error('Failed to add to blacklist:', error);
        showError('Failed to add to blacklist: ' + error.message);
    }
}

/**
 * Show delete IP confirmation modal
 */
function showDeleteIPModal(id, ipAddress, type) {
    deleteIPId = id;
    deleteIPType = type;

    // Update modal text
    document.getElementById('deleteIPAddress').textContent = ipAddress;

    // Show modal
    const modal = new bootstrap.Modal(document.getElementById('deleteIPModal'));
    modal.show();
}

/**
 * Confirm delete IP
 */
async function confirmDeleteIP() {
    if (!deleteIPId || !deleteIPType) return;

    try {
        // Delete IP
        const endpoint = deleteIPType === 'whitelist' ?
            `/api/whitelist/${deleteIPId}` :
            `/api/blacklist/${deleteIPId}`;

        await deleteJSON(endpoint);

        // Hide modal
        const modal = bootstrap.Modal.getInstance(document.getElementById('deleteIPModal'));
        modal.hide();

        // Show success
        showSuccess('IP deleted successfully');

        // Reload appropriate list
        if (deleteIPType === 'whitelist') {
            loadWhitelist();
        } else {
            loadBlacklist();
        }

        // Reset
        deleteIPId = null;
        deleteIPType = null;

    } catch (error) {
        console.error('Failed to delete IP:', error);
        showError('Failed to delete IP: ' + error.message);
    }
}

// ================================== UPDATE PAGE INITIALIZATION ==================================

// Update the existing DOMContentLoaded listener
document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM loaded');

    // Initialize monitor page if on monitor page
    initMonitorPage();

    // Initialize dashboard if on dashboard page
    initDashboard();

    // Initialize alerts page if on alerts page
    initAlertsPage();

    // Initialize settings page if on settings page
    initSettingsPage();
});


// ================================== MODEL PAGE FUNCTIONS ==================================

/**
 * Initialize model page
 */
function initModelPage() {
    const modelAlgorithm = document.getElementById('modelAlgorithm');
    if (!modelAlgorithm) return; // Not on model page

    console.log('Initializing model page...');

    // Load model data
    loadModelInfo();
    loadModelMetrics();
}

/**
 * Load model information from API
 */
async function loadModelInfo() {
    try {
        const info = await fetchJSON('/api/model/info');

        // Model Overview
        document.getElementById('modelAlgorithm').textContent = info.model.algorithm || 'XGBoost';
        document.getElementById('modelVersion').textContent = info.model.version || 'v1.0';
        document.getElementById('featuresCount').textContent = info.model.features_count || '25';
        document.getElementById('classesCount').textContent = info.model.classes_count || '4';

        // Attack Classes
        const classes = info.model.classes || ['BENIGN', 'DoS Hulk', 'PortScan', 'DDoS'];
        document.getElementById('attackClasses').textContent = classes.join(', ');

        // Overall Accuracy
        const accuracy = (info.performance.accuracy * 100).toFixed(2);
        document.getElementById('overallAccuracy').textContent = accuracy + '%';
        document.getElementById('accuracyBar').style.width = accuracy + '%';
        document.getElementById('accuracyBar').textContent = accuracy + '%';
        document.getElementById('accuracyBar').setAttribute('aria-valuenow', accuracy);

        // Training Info
        const trainingDate = info.training.date ?
            new Date(info.training.date).toLocaleDateString() :
            'November 8, 2025';  // ← Fallback to timestamp from metrics file
        document.getElementById('trainingDate').textContent = trainingDate;
        document.getElementById('datasetName').textContent = info.training.dataset || 'CICIDS2017';
        document.getElementById('trainingSamples').textContent =
            (info.training.samples || 2791127).toLocaleString();

        // Configuration
        document.getElementById('alertThreshold').textContent =
            (info.configuration.alert_threshold || 0.95);
        document.getElementById('dedupWindow').textContent =
            (info.configuration.deduplication_window || 60) + ' seconds';

    } catch (error) {
        console.error('Failed to load model info:', error);
        showError('Failed to load model information');
    }
}

/**
 * Load model metrics from API
 */
async function loadModelMetrics() {
    try {
        const metrics = await fetchJSON('/api/model/metrics');

        // Render per-class metrics table
        renderMetricsTable(metrics);

    } catch (error) {
        console.error('Failed to load model metrics:', error);
        // Show fallback message if metrics file not found
        const tbody = document.querySelector('#metricsTable tbody');
        if (tbody) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="5" class="text-center text-muted">
                        Metrics data not available
                    </td>
                </tr>
            `;
        }
    }
}


// ================================== UPDATE PAGE INITIALIZATION ==================================

// Update the existing DOMContentLoaded listener
document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM loaded');

    // Initialize monitor page if on monitor page
    initMonitorPage();

    // Initialize dashboard if on dashboard page
    initDashboard();

    // Initialize alerts page if on alerts page
    initAlertsPage();

    // Initialize settings page if on settings page
    initSettingsPage();

    // Initialize model page if on model page
    initModelPage();
});