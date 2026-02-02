// WebSocket connection
let ws = null;
let reconnectAttempts = 0;
const maxReconnectAttempts = 5;
let allData = [];
let currentFilter = 'all';
let autoRefreshEnabled = true;
let dateFromFilter = null;
let dateToFilter = null;
let recentAlerts = [];
const maxAlerts = 10;
let autoRefreshInterval = null;
let isWsConnected = false;

// DOM Elements with null checks
const connectionStatus = document.getElementById('connection-status');
const statusText = document.getElementById('status-text');
const dataTable = document.getElementById('data-table');
const tableBody = dataTable ? dataTable.querySelector('tbody') : null;
const emptyState = document.getElementById('empty-state');

// Stats elements
const totalDetections = document.getElementById('total-detections');
const totalViolations = document.getElementById('total-violations');
const totalSnapshots = document.getElementById('total-snapshots');
const alertClasses = document.getElementById('alert-classes');

// New feature elements
const filterBtns = document.querySelectorAll('.filter-btn');
const searchInput = document.getElementById('search-input');
const classFilter = document.getElementById('class-filter');
const refreshBtn = document.getElementById('refresh-btn');
const exportBtn = document.getElementById('export-btn');
const autoRefreshToggle = document.getElementById('auto-refresh');

// Date range picker elements
const dateFromInput = document.getElementById('date-from');
const dateToInput = document.getElementById('date-to');
const clearDatesBtn = document.getElementById('clear-dates-btn');

// Alerts panel elements
const alertsList = document.getElementById('alerts-list');
const alertCount = document.getElementById('alert-count');

// Tab elements
const tabButtons = document.querySelectorAll('.tab-button');
const tabPanes = document.querySelectorAll('.tab-pane');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    console.log('Dashboard initializing...');
    
    // Load initial data via HTTP API (works even without WebSocket)
    loadInitialData();
    
    // Setup WebSocket connection
    connectWebSocket();
    
    // Setup UI components
    updateSnapshotsCount();
    setupEventListeners();
    setupTabNavigation();
    
    // Start auto-refresh interval (10 seconds)
    startAutoRefresh();
    
    // Update summary stats periodically
    setInterval(updateSummaryStats, 5000);
});

// =============================================================================
// INITIAL DATA LOAD (HTTP FALLBACK)
// =============================================================================

async function loadInitialData() {
    try {
        console.log('Loading initial data via HTTP API...');
        
        // Fetch summary stats
        const summaryResponse = await fetch('/api/detections/summary');
        if (summaryResponse.ok) {
            const summary = await summaryResponse.json();
            updateStatsFromSummary(summary);
        }
        
        // Fetch recent detections
        const recentResponse = await fetch('/api/detections/recent?limit=100');
        if (recentResponse.ok) {
            const recent = await recentResponse.json();
            if (recent.data && recent.data.length > 0) {
                console.log('Loaded initial data:', recent.data.length, 'records');
                updateTable(recent.data);
            }
        }
        
        // Update today's stats
        updateTodayStats();
        
    } catch (error) {
        console.error('Error loading initial data:', error);
    }
}

async function updateTodayStats() {
    try {
        const response = await fetch('/api/detections/today');
        if (response.ok) {
            const stats = await response.json();
            
            const todayCountEl = document.getElementById('today-count');
            const weekCountEl = document.getElementById('week-count');
            const violationRateEl = document.getElementById('violation-rate');
            const avgConfidenceEl = document.getElementById('avg-confidence');
            
            if (todayCountEl) todayCountEl.textContent = stats.today_count || 0;
            if (weekCountEl) weekCountEl.textContent = stats.week_count || 0;
            if (violationRateEl) violationRateEl.textContent = (stats.violation_rate || 0) + '%';
            if (avgConfidenceEl) avgConfidenceEl.textContent = (stats.avg_confidence || 0) + '%';
        }
    } catch (error) {
        console.error('Error updating today stats:', error);
    }
}

// =============================================================================
// AUTO REFRESH FUNCTIONALITY
// =============================================================================

function startAutoRefresh() {
    if (autoRefreshInterval) {
        clearInterval(autoRefreshInterval);
    }
    
    autoRefreshInterval = setInterval(async () => {
        if (autoRefreshEnabled && !isWsConnected) {
            // Only use HTTP refresh if WebSocket is disconnected
            await refreshData();
        }
    }, 10000); // Refresh every 10 seconds when auto-refresh is on and WS is disconnected
    
    console.log('Auto-refresh started (10s interval, active when WS disconnected)');
}

async function refreshData() {
    console.log('Refreshing data...');
    
    try {
        // Show refresh animation
        if (refreshBtn) {
            const icon = refreshBtn.querySelector('i');
            if (icon) {
                icon.style.transition = 'transform 0.5s ease';
                icon.style.transform = 'rotate(360deg)';
                setTimeout(() => {
                    icon.style.transform = 'rotate(0deg)';
                }, 500);
            }
        }
        
        // Fetch fresh data from API
        const response = await fetch('/api/detections/recent?limit=100');
        
        if (response.ok) {
            const data = await response.json();
            if (data.data && data.data.length > 0) {
                console.log('Refreshed data:', data.data.length, 'records');
                updateTable(data.data);
                updateStats(data.data);
            }
        }
        
        // Also refresh summary stats
        const summaryResponse = await fetch('/api/detections/summary');
        if (summaryResponse.ok) {
            const summary = await summaryResponse.json();
            updateStatsFromSummary(summary);
        }
        
        // Update today's stats
        await updateTodayStats();
        
    } catch (error) {
        console.error('Error refreshing data:', error);
    }
}

function updateStatsFromSummary(summary) {
    if (!summary) return;
    
    if (totalDetections) totalDetections.textContent = summary.total_detections || 0;
    if (totalViolations) totalViolations.textContent = summary.total_violations || 0;
    if (alertClasses) alertClasses.textContent = summary.alert_classes || 0;
    
    // Update class filter dropdown
    if (classFilter && summary.unique_classes) {
        const currentValue = classFilter.value;
        classFilter.innerHTML = '<option value="">All Classes</option>';
        summary.unique_classes.forEach(cls => {
            const option = document.createElement('option');
            option.value = cls;
            option.textContent = cls;
            classFilter.appendChild(option);
        });
        classFilter.value = currentValue;
    }
}

// Setup tab navigation
function setupTabNavigation() {
    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            const tabName = button.dataset.tab;
            switchTab(tabName);
        });
    });
}

// Switch tab function
function switchTab(tabName) {
    // Remove active class from all buttons and panes
    tabButtons.forEach(btn => btn.classList.remove('active'));
    tabPanes.forEach(pane => pane.classList.remove('active'));
    
    // Add active class to selected button
    const activeButton = document.querySelector(`.tab-button[data-tab="${tabName}"]`);
    if (activeButton) {
        activeButton.classList.add('active');
    }
    
    // Add active class to selected pane
    const activePane = document.querySelector(`.tab-pane[data-tab="${tabName}"]`);
    if (activePane) {
        activePane.classList.add('active');
    }
    
    // Update analytics when export tab is opened
    if (tabName === 'export') {
        updateAnalyticsSummary();
    }
}

// Update analytics summary
function updateAnalyticsSummary() {
    if (!allData || allData.length === 0) {
        document.getElementById('analytics-total').textContent = '0';
        document.getElementById('analytics-violations').textContent = '0';
        document.getElementById('analytics-safe').textContent = '0';
        document.getElementById('analytics-percent').textContent = '0%';
        return;
    }
    
    const total = allData.length;
    const violations = allData.filter(item => item['Restricted Area Violation'] === 'Yes').length;
    const safe = total - violations;
    const percent = total > 0 ? Math.round((violations / total) * 100) : 0;
    
    document.getElementById('analytics-total').textContent = total;
    document.getElementById('analytics-violations').textContent = violations;
    document.getElementById('analytics-safe').textContent = safe;
    document.getElementById('analytics-percent').textContent = percent + '%';
}

// Setup event listeners for new features
function setupEventListeners() {
    filterBtns.forEach(btn => {
        btn.addEventListener('click', (e) => {
            filterBtns.forEach(b => b.classList.remove('active'));
            e.target.closest('.filter-btn').classList.add('active');
            currentFilter = e.target.closest('.filter-btn').dataset.filter;
            filterAndDisplayData();
        });
    });
    
    searchInput.addEventListener('input', filterAndDisplayData);
    classFilter.addEventListener('change', filterAndDisplayData);
    
    // Date range picker events
    dateFromInput.addEventListener('change', () => {
        dateFromFilter = dateFromInput.value ? new Date(dateFromInput.value) : null;
        filterAndDisplayData();
    });
    
    dateToInput.addEventListener('change', () => {
        dateToFilter = dateToInput.value ? new Date(dateToInput.value + 'T23:59:59') : null;
        filterAndDisplayData();
    });
    
    clearDatesBtn.addEventListener('click', () => {
        dateFromInput.value = '';
        dateToInput.value = '';
        dateFromFilter = null;
        dateToFilter = null;
        filterAndDisplayData();
    });
    
    refreshBtn.addEventListener('click', async () => {
        const icon = refreshBtn.querySelector('i');
        if (icon) {
            icon.style.transition = 'transform 0.5s ease';
            icon.style.transform = 'rotate(360deg)';
            setTimeout(() => {
                icon.style.transform = 'rotate(0deg)';
            }, 500);
        }
        // Actually refresh the data
        await refreshData();
    });
    exportBtn.addEventListener('click', exportToCSV);
    
    // Quick export buttons
    const quickExportButtons = document.querySelectorAll('.btn-quick-export');
    quickExportButtons.forEach(btn => {
        btn.addEventListener('click', (e) => {
            const exportType = e.target.closest('.btn-quick-export').dataset.export;
            quickExportData(exportType);
        });
    });
    
    autoRefreshToggle.addEventListener('change', (e) => {
        autoRefreshEnabled = e.target.checked;
    });
}

// Connect to WebSocket with auto-reconnect
function connectWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/data`;
    
    console.log('Attempting to connect to WebSocket:', wsUrl);
    ws = new WebSocket(wsUrl);
    
    const connectionTimeout = setTimeout(() => {
        if (ws.readyState !== WebSocket.OPEN) {
            console.log('Connection timeout, reconnecting...');
            ws.close();
            scheduleReconnect();
        }
    }, 5000);
    
    ws.onopen = () => {
        console.log('✅ WebSocket connected successfully');
        clearTimeout(connectionTimeout);
        updateConnectionStatus(true);
        reconnectAttempts = 0;
    };
    
    ws.onmessage = (event) => {
        try {
            const response = JSON.parse(event.data);
            // Only log if data length changes to avoid console spam
            if (response.data && (!allData || response.data.length !== allData.length)) {
                console.log('WebSocket update received. Records:', response.data.length);
            }
            
            if (Array.isArray(response.data)) {
                updateTable(response.data);
                updateStats(response.data);
            } else {
                console.warn('Invalid data format in WebSocket message:', response);
            }
        } catch (error) {
            console.error('Error parsing WebSocket message:', error);
        }
    };
    
    ws.onclose = (event) => {
        console.log('WebSocket disconnected', event.code, event.reason);
        clearTimeout(connectionTimeout);
        updateConnectionStatus(false);
        scheduleReconnect();
    };
    
    ws.onerror = (error) => {
        console.error('WebSocket error:', error);
    };
}

function scheduleReconnect() {
    if (reconnectAttempts < maxReconnectAttempts) {
        reconnectAttempts++;
        const delay = Math.min(1000 * Math.pow(2, reconnectAttempts), 30000);
        console.log(`Reconnecting in ${delay}ms... (attempt ${reconnectAttempts}/${maxReconnectAttempts})`);
        setTimeout(connectWebSocket, delay);
    }
}

// Update connection status
function updateConnectionStatus(connected) {
    if (connected) {
        connectionStatus.classList.add('connected');
        connectionStatus.classList.remove('disconnected');
        statusText.textContent = '● LIVE';
    } else {
        connectionStatus.classList.add('disconnected');
        connectionStatus.classList.remove('connected');
        statusText.textContent = '○ Disconnected';
    }
}

// Update WebSocket data and store for filtering
function updateTable(data) {
    // Ensure data is an array
    if (!Array.isArray(data)) {
        console.error('updateTable received invalid data:', data);
        return;
    }

    allData = data;
    
    if (!tableBody) {
        console.warn('Table body element not found');
        return;
    }
    
    if (data.length === 0) {
        tableBody.innerHTML = '';
        if (emptyState) emptyState.classList.add('show');
        if (dataTable) dataTable.style.display = 'none';
        updateAlertsPanel(data);
        // Update filter summary even if empty
        updateFilterSummary(0);
        return;
    }
    
    // Update class filter dropdown
    if (classFilter) {
        const currentValue = classFilter.value; // Save current selection
        const classes = new Set(data.map(item => item.Class).filter(c => c));
        console.log('Available classes:', Array.from(classes));
        
        classFilter.innerHTML = '<option value="">All Classes</option>';
        classes.forEach(cls => {
            const option = document.createElement('option');
            option.value = cls.trim(); // Trim whitespace from class names
            option.textContent = cls;
            classFilter.appendChild(option);
        });
        
        // Restore previous selection if it still exists
        if (currentValue && Array.from(classes).some(c => c.trim() === currentValue)) {
            classFilter.value = currentValue;
            console.log('Restored class filter to:', currentValue);
        }
    }
    
    // Update alerts panel
    updateAlertsPanel(data);
    
    if (emptyState) emptyState.classList.remove('show');
    if (dataTable) dataTable.style.display = 'table';
    filterAndDisplayData();
}

// Update statistics
function updateStats(data) {
    if (!data || data.length === 0) return;
    
    // Total detections
    if (totalDetections) totalDetections.textContent = data.length;
    
    // Total violations
    const violations = data.filter(item => item['Restricted Area Violation'] === 'Yes');
    if (totalViolations) totalViolations.textContent = violations.length;
    
    // Alert classes count (unique classes with violations)
    const alertClassesSet = new Set(violations.map(v => v.Class));
    if (alertClasses) alertClasses.textContent = alertClassesSet.size;
    
    // Snapshots count
    updateSnapshotsCount();
}

// Update snapshots count
async function updateSnapshotsCount() {
    try {
        const response = await fetch('/api/snapshots-count');
        const data = await response.json();
        totalSnapshots.textContent = data.count || 0;
    } catch (error) {
        console.error('Error updating snapshots count:', error);
    }
}

// Quick export with filters
function quickExportData(exportType) {
    let filteredData = allData;
    let filename = `detection-log`;
    
    switch(exportType) {
        case 'violations':
            filteredData = allData.filter(item => item['Restricted Area Violation'] === 'Yes');
            filename += `-violations`;
            break;
        case 'today':
            const today = new Date();
            today.setHours(0, 0, 0, 0);
            filteredData = allData.filter(item => {
                const itemDate = new Date(item.Timestamp);
                itemDate.setHours(0, 0, 0, 0);
                return itemDate.getTime() === today.getTime();
            });
            filename += `-today`;
            break;
        case 'week':
            const weekAgo = new Date();
            weekAgo.setDate(weekAgo.getDate() - 7);
            filteredData = allData.filter(item => new Date(item.Timestamp) >= weekAgo);
            filename += `-week`;
            break;
        case 'all':
            filename += `-all`;
            break;
    }
    
    if (!filteredData || filteredData.length === 0) {
        alert(`No data found for ${exportType} filter`);
        return;
    }
    
    // Create CSV content
    const headers = ['Timestamp', 'Class', 'Confidence', 'Violation'];
    const csvContent = [
        headers.join(','),
        ...filteredData.map(item => [
            `"${item.Timestamp}"`,
            item.Class,
            (parseFloat(item.Confidence || 0) * 100).toFixed(1),
            item['Restricted Area Violation']
        ].join(','))
    ].join('\n');
    
    // Generate filename
    filename += `-${new Date().toISOString().split('T')[0]}.csv`;
    
    // Create blob and download
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    window.URL.revokeObjectURL(url);
}

// =============================================================================
// NEW FEATURES: ACTIVITY FEED, SYSTEM HEALTH, CAMERAS, USER ACTIVITY
// =============================================================================

// Activity Feed Functions
async function loadActivityFeed() {
    const container = document.getElementById('activity-feed');
    if (!container) return;
    
    container.innerHTML = '<div class="loading-spinner"><i class="fas fa-spinner fa-spin"></i> Loading activity data...</div>';
    
    try {
        const response = await fetch('/api/activity/feed?limit=50');
        if (!response.ok) throw new Error('Failed to load activity feed');
        
        const data = await response.json();
        const activities = data.events || [];
        
        if (activities.length === 0) {
            container.innerHTML = '<div class="empty-state show"><div class="empty-icon">📋</div><h3>No Activity Yet</h3><p>System activity will appear here</p></div>';
            return;
        }
        
        container.innerHTML = activities.map(item => `
            <div class="activity-item">
                <div class="activity-icon">${getActivityIcon(item.type)}</div>
                <div class="activity-content">
                    <div class="activity-title">${item.title || item.type}</div>
                    <div class="activity-details">${item.description || ''}</div>
                    <div class="activity-time">${formatTimeAgo(item.timestamp)}</div>
                </div>
            </div>
        `).join('');
        
    } catch (error) {
        console.error('Error loading activity feed:', error);
        container.innerHTML = '<div class="empty-state show"><div class="empty-icon">⚠️</div><h3>Error Loading Data</h3><p>Could not load activity feed</p></div>';
    }
}

function getActivityIcon(type) {
    const icons = {
        'detection': '🎯',
        'violation': '🚨',
        'email': '📧',
        'recording': '🎬',
        'camera': '📹',
        'user': '👤',
        'system': '⚙️',
        'alert': '🔔'
    };
    return icons[type] || '📌';
}

function formatTimeAgo(timestamp) {
    // Handle null, undefined, or invalid dates
    if (!timestamp || timestamp === 'null' || timestamp === 'undefined') {
        return new Date().toLocaleDateString(); // Show today's date for unknown timestamps
    }
    
    const now = new Date();
    const time = new Date(timestamp);
    
    // Check if the date is valid
    if (isNaN(time.getTime())) {
        return new Date().toLocaleDateString(); // Show today's date for invalid timestamps
    }
    
    const diff = Math.floor((now - time) / 1000);
    
    if (diff < 0) return 'Just now'; // Handle future dates
    if (diff < 60) return 'Just now';
    if (diff < 3600) return `${Math.floor(diff / 60)} minutes ago`;
    if (diff < 86400) return `${Math.floor(diff / 3600)} hours ago`;
    return time.toLocaleDateString();
}

// System Health Functions
async function loadSystemHealth() {
    const container = document.getElementById('system-health');
    if (!container) return;
    
    container.innerHTML = '<div class="loading-spinner"><i class="fas fa-spinner fa-spin"></i> Loading health data...</div>';
    
    try {
        const response = await fetch('/api/health/detailed');
        if (!response.ok) throw new Error('Failed to load system health');
        
        const health = await response.json();
        
        console.log('Health API response:', health); // Debug log
        
        // Handle the actual nested API response structure
        // The API returns: { cpu: {percent}, memory: {percent}, disk: {percent}, ... }
        // Or flat structure: { cpu_percent, memory_percent, disk_percent, ... }
        
        const cpuPercent = health.cpu?.percent ?? health.cpu_percent ?? 0;
        const memoryPercent = health.memory?.percent ?? health.memory_percent ?? 0;
        const diskPercent = health.disk?.percent ?? health.disk_percent ?? 0;
        
        // Handle uptime - could be uptime_formatted or just "uptime"
        const uptime = health.uptime_formatted ?? health.uptime ?? 'N/A';
        
        // Network connected - determine based on network data
        const networkConnected = health.network_connected ?? 
                                  (health.network?.bytes_sent_mb !== undefined || health.network?.bytes_recv_mb !== undefined);
        
        // Process info
        const activeThreads = health.active_threads ?? health.process?.active_threads ?? health.process?.threads ?? 0;
        const openFiles = health.open_files ?? health.process?.open_files ?? 0;
        const pythonVersion = health.python_version ?? 'N/A';
        
        container.innerHTML = `
            <div class="health-card">
                <div class="health-card-header">
                    <div class="health-card-icon">🖥️</div>
                    <div class="health-card-title">CPU & Memory</div>
                </div>
                <div class="health-metric">
                    <span class="health-metric-label">CPU Usage</span>
                    <span class="health-metric-value">${cpuPercent}%</span>
                </div>
                <div class="health-progress">
                    <div class="health-progress-fill ${getProgressClass(cpuPercent)}" style="width: ${cpuPercent}%"></div>
                </div>
                <div class="health-metric">
                    <span class="health-metric-label">Memory Usage</span>
                    <span class="health-metric-value">${memoryPercent}%</span>
                </div>
                <div class="health-progress">
                    <div class="health-progress-fill ${getProgressClass(memoryPercent)}" style="width: ${memoryPercent}%"></div>
                </div>
            </div>
            
            <div class="health-card">
                <div class="health-card-header">
                    <div class="health-card-icon">💾</div>
                    <div class="health-card-title">Disk & Network</div>
                </div>
                <div class="health-metric">
                    <span class="health-metric-label">Disk Usage</span>
                    <span class="health-metric-value">${diskPercent}%</span>
                </div>
                <div class="health-metric">
                    <span class="health-metric-label">Network Status</span>
                    <span class="health-metric-value">${networkConnected ? 'Connected' : 'Disconnected'}</span>
                </div>
                <div class="health-metric">
                    <span class="health-metric-label">Uptime</span>
                    <span class="health-metric-value">${uptime}</span>
                </div>
            </div>
            
            <div class="health-card">
                <div class="health-card-header">
                    <div class="health-card-icon">📊</div>
                    <div class="health-card-title">Process Info</div>
                </div>
                <div class="health-metric">
                    <span class="health-metric-label">Active Threads</span>
                    <span class="health-metric-value">${activeThreads}</span>
                </div>
                <div class="health-metric">
                    <span class="health-metric-label">Open Files</span>
                    <span class="health-metric-value">${openFiles}</span>
                </div>
                <div class="health-metric">
                    <span class="health-metric-label">Python Version</span>
                    <span class="health-metric-value">${pythonVersion}</span>
                </div>
            </div>
        `;
        
    } catch (error) {
        console.error('Error loading system health:', error);
        container.innerHTML = '<div class="empty-state show"><div class="empty-icon">⚠️</div><h3>Error Loading Data</h3><p>Could not load system health data</p></div>';
    }
}

function getProgressClass(value) {
    if (value > 80) return 'low';
    if (value > 50) return 'medium';
    return 'high';
}

// Cameras Management Functions
async function loadCameras() {
    const container = document.getElementById('cameras-list');
    if (!container) return;
    
    container.innerHTML = '<div class="loading-spinner"><i class="fas fa-spinner fa-spin"></i> Loading cameras...</div>';
    
    try {
        const response = await fetch('/api/cameras');
        if (!response.ok) throw new Error('Failed to load cameras');
        
        const data = await response.json();
        const cameras = data.cameras || [];
        
        if (cameras.length === 0) {
            container.innerHTML = '<div class="empty-state show"><div class="empty-icon">📹</div><h3>No Cameras Configured</h3><p>Add cameras to start monitoring</p></div>';
            return;
        }
        
        container.innerHTML = cameras.map(camera => `
            <div class="camera-card">
                <div class="camera-header">
                    <div class="camera-status ${camera.status === 'online' ? 'online' : 'offline'}"></div>
                    <div class="camera-name">${camera.name}</div>
                </div>
                <div class="camera-details">
                    <div class="camera-detail">
                        <span class="camera-detail-label">ID</span>
                        <span class="camera-detail-value">${camera.id}</span>
                    </div>
                    <div class="camera-detail">
                        <span class="camera-detail-label">Status</span>
                        <span class="camera-detail-value">${camera.status}</span>
                    </div>
                    <div class="camera-detail">
                        <span class="camera-detail-label">Type</span>
                        <span class="camera-detail-value">${camera.type || 'IP Camera'}</span>
                    </div>
                    <div class="camera-detail">
                        <span class="camera-detail-label">Last Check</span>
                        <span class="camera-detail-value">${formatTimeAgo(camera.last_check)}</span>
                    </div>
                </div>
            </div>
        `).join('');
        
    } catch (error) {
        console.error('Error loading cameras:', error);
        container.innerHTML = '<div class="empty-state show"><div class="empty-icon">⚠️</div><h3>Error Loading Data</h3><p>Could not load camera data</p></div>';
    }
}

// User Activity Functions
async function loadUserActivity() {
    const container = document.getElementById('user-activity');
    const statsContainer = document.getElementById('user-stats');
    if (!container) return;
    
    container.innerHTML = '<div class="loading-spinner"><i class="fas fa-spinner fa-spin"></i> Loading user activity...</div>';
    
    try {
        // First, get the stats from the new dedicated stats endpoint
        let stats = { total_users: 0, total_actions: 0, active_today: 0, unique_ips: 0 };
        try {
            const statsResponse = await fetch('/api/users/stats');
            if (statsResponse.ok) {
                const statsData = await statsResponse.json();
                stats = {
                    total_users: statsData.total_users || 0,
                    total_actions: statsData.total_actions || 0,
                    active_today: statsData.active_today || 0,
                    unique_ips: statsData.unique_ips || 0
                };
            }
        } catch (statsError) {
            console.warn('Could not load user stats:', statsError);
        }
        
        // Update stats display
        if (statsContainer) {
            statsContainer.innerHTML = `
                <div class="user-stat-card">
                    <div class="user-stat-value">${stats.total_users}</div>
                    <div class="user-stat-label">Total Users</div>
                </div>
                <div class="user-stat-card">
                    <div class="user-stat-value">${stats.total_actions}</div>
                    <div class="user-stat-label">Total Actions</div>
                </div>
                <div class="user-stat-card">
                    <div class="user-stat-value">${stats.active_today}</div>
                    <div class="user-stat-label">Active Today</div>
                </div>
                <div class="user-stat-card">
                    <div class="user-stat-value">${stats.unique_ips}</div>
                    <div class="user-stat-label">Unique IPs</div>
                </div>
            `;
        }
        
        // Now get the activity feed
        const response = await fetch('/api/users/activity?limit=50');
        if (!response.ok) throw new Error('Failed to load user activity');
        
        const data = await response.json();
        const activities = data.activities || data.events || [];  // Handle both API response formats
        
        if (activities.length === 0) {
            container.innerHTML = '<div class="empty-state show"><div class="empty-icon">👥</div><h3>No User Activity</h3><p>User activity will appear here</p></div>';
            return;
        }
        
        container.innerHTML = activities.map(item => `
            <div class="user-activity-item">
                <div class="user-avatar">${getUserAvatar(item.user || 'Anonymous')}</div>
                <div class="user-info">
                    <div class="user-name">${item.user || 'Anonymous'}</div>
                    <div class="user-action">${item.action}</div>
                    <div class="user-time">${formatTimeAgo(item.timestamp)}</div>
                </div>
            </div>
        `).join('');
        
    } catch (error) {
        console.error('Error loading user activity:', error);
        container.innerHTML = '<div class="empty-state show"><div class="empty-icon">⚠️</div><h3>Error Loading Data</h3><p>Could not load user activity</p></div>';
    }
}

function getUserAvatar(username) {
    const colors = ['#00d4ff', '#7c3aed', '#22c55e', '#f59e0b', '#ef4444'];
    const index = username.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0) % colors.length;
    const initial = username.charAt(0).toUpperCase();
    return `<span style="color: ${colors[index]}; font-weight: bold;">${initial}</span>`;
}

// Setup event listeners for new tabs
function setupNewTabListeners() {
    // Activity Feed refresh
    const activityRefresh = document.getElementById('refresh-activity');
    if (activityRefresh) {
        activityRefresh.addEventListener('click', loadActivityFeed);
    }
    
    // System Health refresh
    const healthRefresh = document.getElementById('refresh-health');
    if (healthRefresh) {
        healthRefresh.addEventListener('click', loadSystemHealth);
    }
    
    // Cameras refresh
    const camerasRefresh = document.getElementById('refresh-cameras');
    if (camerasRefresh) {
        camerasRefresh.addEventListener('click', loadCameras);
    }
    
    // User Activity refresh
    const usersRefresh = document.getElementById('refresh-users');
    if (usersRefresh) {
        usersRefresh.addEventListener('click', loadUserActivity);
    }
}

// Load new tab content when tabs are clicked
const originalSwitchTab = switchTab;
switchTab = function(tabName) {
    // Call original function
    originalSwitchTab(tabName);
    
    // Load tab-specific content
    switch(tabName) {
        case 'activity':
            loadActivityFeed();
            break;
        case 'health':
            loadSystemHealth();
            break;
        case 'cameras':
            loadCameras();
            break;
        case 'users':
            loadUserActivity();
            break;
        case 'analytics':
            if (!charts.mainChart) {
                initializeCharts();
            }
            loadAllChartData();
            break;
    }
};

// Initialize new tab listeners on DOM load
document.addEventListener('DOMContentLoaded', () => {
    setupNewTabListeners();
});

// =============================================================================
// ANALYTICS CHARTS FUNCTIONALITY
// =============================================================================

// Chart instances
let charts = {
    mainChart: null,
    classPieChart: null,
    violationLineChart: null,
    confidenceBarChart: null,
    statusDoughnutChart: null
};

// Chart color palette
const chartColors = {
    primary: ['#00d4ff', '#7c3aed', '#ec4899', '#22c55e', '#f59e0b', '#ef4444', '#06b6d4', '#8b5cf6', '#14b8a6', '#f97316'],
    gradient1: ['#00d4ff', '#7c3aed'],
    violations: '#ef4444',
    safe: '#22c55e'
};

// Chart.js default configuration
Chart.defaults.color = '#94a3b8';
Chart.defaults.borderColor = 'rgba(255, 255, 255, 0.1)';
Chart.defaults.font.family = "'Inter', 'Segoe UI', sans-serif";

// Initialize charts when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    initializeCharts();
    setupChartEventListeners();
});

// Initialize all chart instances
function initializeCharts() {
    console.log('Initializing analytics charts...');
    
    // Destroy existing charts if they exist
    Object.values(charts).forEach(chart => {
        if (chart) chart.destroy();
    });
    
    // Get canvas contexts
    const mainCanvas = document.getElementById('mainChart');
    const classPieCanvas = document.getElementById('classPieChart');
    const violationLineCanvas = document.getElementById('violationLineChart');
    const confidenceBarCanvas = document.getElementById('confidenceBarChart');
    const statusDoughnutCanvas = document.getElementById('statusDoughnutChart');
    
    // Check if canvas elements exist
    if (!mainCanvas || !classPieCanvas || !violationLineCanvas || !confidenceBarCanvas || !statusDoughnutCanvas) {
        console.warn('Chart canvas elements not found in DOM');
        return;
    }
    
    const mainCtx = mainCanvas.getContext('2d');
    const classPieCtx = classPieCanvas.getContext('2d');
    const violationLineCtx = violationLineCanvas.getContext('2d');
    const confidenceBarCtx = confidenceBarCanvas.getContext('2d');
    const statusDoughnutCtx = statusDoughnutCanvas.getContext('2d');
    
    // Create gradient for main chart
    const mainGradient = mainCtx.createLinearGradient(0, 0, mainCanvas.width, 0);
    mainGradient.addColorStop(0, '#00d4ff');
    mainGradient.addColorStop(1, '#7c3aed');
    
    // Initialize Main Chart (Class Distribution Pie)
    charts.mainChart = new Chart(mainCtx, {
        type: 'pie',
        data: {
            labels: [],
            datasets: [{
                data: [],
                backgroundColor: chartColors.primary,
                borderColor: 'rgba(255, 255, 255, 0.2)',
                borderWidth: 2,
                hoverOffset: 10
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        padding: 20,
                        usePointStyle: true,
                        pointStyle: 'circle'
                    }
                },
                tooltip: {
                    backgroundColor: 'rgba(15, 23, 42, 0.9)',
                    titleColor: '#f1f5f9',
                    bodyColor: '#cbd5e1',
                    borderColor: 'rgba(0, 212, 255, 0.3)',
                    borderWidth: 1,
                    cornerRadius: 8,
                    padding: 12
                }
            },
            animation: {
                animateRotate: true,
                animateScale: true,
                duration: 1000,
                easing: 'easeOutQuart'
            }
        }
    });
    
    // Initialize Class Distribution Pie Chart
    charts.classPieChart = new Chart(classPieCtx, {
        type: 'doughnut',
        data: {
            labels: [],
            datasets: [{
                data: [],
                backgroundColor: chartColors.primary,
                borderColor: 'rgba(255, 255, 255, 0.2)',
                borderWidth: 2,
                hoverOffset: 10
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '60%',
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        padding: 15,
                        usePointStyle: true,
                        pointStyle: 'circle'
                    }
                },
                tooltip: {
                    backgroundColor: 'rgba(15, 23, 42, 0.9)',
                    titleColor: '#f1f5f9',
                    bodyColor: '#cbd5e1',
                    borderColor: 'rgba(0, 212, 255, 0.3)',
                    borderWidth: 1,
                    cornerRadius: 8,
                    padding: 12
                }
            },
            animation: {
                animateRotate: true,
                animateScale: true,
                duration: 1000,
                easing: 'easeOutQuart'
            }
        }
    });
    
    // Initialize Violation Trend Line Chart
    charts.violationLineChart = new Chart(violationLineCtx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [
                {
                    label: 'Violations',
                    data: [],
                    borderColor: chartColors.violations,
                    backgroundColor: 'rgba(239, 68, 68, 0.1)',
                    borderWidth: 3,
                    fill: true,
                    tension: 0.4,
                    pointRadius: 4,
                    pointBackgroundColor: chartColors.violations,
                    pointBorderColor: '#fff',
                    pointBorderWidth: 2,
                    pointHoverRadius: 6
                },
                {
                    label: 'Detections',
                    data: [],
                    borderColor: chartColors.primary[0],
                    backgroundColor: 'rgba(0, 212, 255, 0.1)',
                    borderWidth: 3,
                    fill: true,
                    tension: 0.4,
                    pointRadius: 4,
                    pointBackgroundColor: chartColors.primary[0],
                    pointBorderColor: '#fff',
                    pointBorderWidth: 2,
                    pointHoverRadius: 6
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index',
                intersect: false
            },
            scales: {
                x: {
                    grid: {
                        color: 'rgba(255, 255, 255, 0.05)'
                    }
                },
                y: {
                    beginAtZero: true,
                    grid: {
                        color: 'rgba(255, 255, 255, 0.05)'
                    }
                }
            },
            plugins: {
                legend: {
                    position: 'top',
                    labels: {
                        padding: 20,
                        usePointStyle: true,
                        pointStyle: 'circle'
                    }
                },
                tooltip: {
                    backgroundColor: 'rgba(15, 23, 42, 0.9)',
                    titleColor: '#f1f5f9',
                    bodyColor: '#cbd5e1',
                    borderColor: 'rgba(0, 212, 255, 0.3)',
                    borderWidth: 1,
                    cornerRadius: 8,
                    padding: 12
                }
            },
            animation: {
                duration: 1000,
                easing: 'easeOutQuart'
            }
        }
    });
    
    // Initialize Confidence Bar Chart
    charts.confidenceBarChart = new Chart(confidenceBarCtx, {
        type: 'bar',
        data: {
            labels: [],
            datasets: [{
                label: 'Avg Confidence %',
                data: [],
                backgroundColor: chartColors.primary.map((color, index) => 
                    index < 4 ? `rgba(0, 212, 255, 0.8)` : 
                    index < 8 ? `rgba(124, 58, 237, 0.8)` : 
                    `rgba(236, 72, 153, 0.8)`
                ),
                borderColor: chartColors.primary.slice(0, 4),
                borderWidth: 2,
                borderRadius: 8,
                borderSkipped: false
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            indexAxis: 'y',
            scales: {
                x: {
                    beginAtZero: true,
                    max: 100,
                    grid: {
                        color: 'rgba(255, 255, 255, 0.05)'
                    }
                },
                y: {
                    grid: {
                        display: false
                    }
                }
            },
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    backgroundColor: 'rgba(15, 23, 42, 0.9)',
                    titleColor: '#f1f5f9',
                    bodyColor: '#cbd5e1',
                    borderColor: 'rgba(0, 212, 255, 0.3)',
                    borderWidth: 1,
                    cornerRadius: 8,
                    padding: 12
                }
            },
            animation: {
                duration: 1000,
                easing: 'easeOutQuart'
            }
        }
    });
    
    // Initialize Status Doughnut Chart
    charts.statusDoughnutChart = new Chart(statusDoughnutCtx, {
        type: 'doughnut',
        data: {
            labels: ['Violations', 'Safe'],
            datasets: [{
                data: [0, 0],
                backgroundColor: [chartColors.violations, chartColors.safe],
                borderColor: 'rgba(255, 255, 255, 0.2)',
                borderWidth: 2,
                hoverOffset: 10
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '65%',
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        padding: 20,
                        usePointStyle: true,
                        pointStyle: 'circle'
                    }
                },
                tooltip: {
                    backgroundColor: 'rgba(15, 23, 42, 0.9)',
                    titleColor: '#f1f5f9',
                    bodyColor: '#cbd5e1',
                    borderColor: 'rgba(0, 212, 255, 0.3)',
                    borderWidth: 1,
                    cornerRadius: 8,
                    padding: 12
                }
            },
            animation: {
                animateRotate: true,
                animateScale: true,
                duration: 1000,
                easing: 'easeOutQuart'
            }
        }
    });
    
    console.log('Charts initialized successfully');
}

// Setup event listeners for chart controls
function setupChartEventListeners() {
    const chartTypeSelect = document.getElementById('chart-type');
    const refreshChartsBtn = document.getElementById('refresh-charts');
    
    if (chartTypeSelect) {
        chartTypeSelect.addEventListener('change', (e) => {
            changeMainChartType(e.target.value);
        });
    }
    
    if (refreshChartsBtn) {
        refreshChartsBtn.addEventListener('click', async () => {
            await refreshAllCharts();
        });
    }
}

// Change main chart type based on selection
function changeMainChartType(chartType) {
    if (!charts.mainChart) return;
    
    const ctx = charts.mainChart.ctx;
    const canvas = charts.mainChart.canvas;
    
    // Create new gradient
    const gradient = ctx.createLinearGradient(0, 0, canvas.width, 0);
    gradient.addColorStop(0, '#00d4ff');
    gradient.addColorStop(1, '#7c3aed');
    
    let newType = 'pie';
    let newData = charts.mainChart.data;
    
    switch(chartType) {
        case 'classDistribution':
            newType = 'pie';
            break;
        case 'violationTrend':
            newType = 'line';
            break;
        case 'confidenceByClass':
            newType = 'bar';
            break;
        case 'hourlyActivity':
            newType = 'bar';
            break;
        case 'violationPie':
            newType = 'doughnut';
            break;
    }
    
    // Destroy and recreate chart with new type
    charts.mainChart.destroy();
    
    charts.mainChart = new Chart(ctx, {
        type: newType,
        data: newData,
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        padding: 20,
                        usePointStyle: true,
                        pointStyle: 'circle'
                    }
                },
                tooltip: {
                    backgroundColor: 'rgba(15, 23, 42, 0.9)',
                    titleColor: '#f1f5f9',
                    bodyColor: '#cbd5e1',
                    borderColor: 'rgba(0, 212, 255, 0.3)',
                    borderWidth: 1,
                    cornerRadius: 8,
                    padding: 12
                }
            },
            animation: {
                duration: 1000,
                easing: 'easeOutQuart'
            }
        }
    });
}

// Fetch and load all chart data
async function loadAllChartData() {
    console.log('Loading chart data...');
    
    try {
        // Fetch data from all API endpoints
        await Promise.all([
            loadClassDistributionChart(),
            loadViolationTrendChart(),
            loadConfidenceByClassChart(),
            loadHourlyActivityChart(),
            loadViolationStatusChart(),
            loadAnalyticsStats()
        ]);
        
        console.log('All chart data loaded successfully');
    } catch (error) {
        console.error('Error loading chart data:', error);
    }
}

// Load Class Distribution Chart
async function loadClassDistributionChart() {
    try {
        const response = await fetch('/api/analytics/charts/class-distribution');
        if (!response.ok) throw new Error('Failed to fetch class distribution');
        
        const data = await response.json();
        
        if (charts.mainChart) {
            charts.mainChart.data.labels = data.labels || [];
            charts.mainChart.data.datasets[0].data = data.data || [];
            charts.mainChart.data.datasets[0].backgroundColor = data.colors || chartColors.primary;
            charts.mainChart.update();
        }
        
        if (charts.classPieChart) {
            charts.classPieChart.data.labels = data.labels || [];
            charts.classPieChart.data.datasets[0].data = data.data || [];
            charts.classPieChart.data.datasets[0].backgroundColor = data.colors || chartColors.primary;
            charts.classPieChart.update();
        }
        
        return data;
    } catch (error) {
        console.error('Error loading class distribution chart:', error);
        return null;
    }
}

// Load Violation Trend Chart
async function loadViolationTrendChart(days = 7) {
    try {
        const response = await fetch(`/api/analytics/charts/violation-trend?days=${days}`);
        if (!response.ok) throw new Error('Failed to fetch violation trend');
        
        const data = await response.json();
        
        if (charts.violationLineChart) {
            charts.violationLineChart.data.labels = data.labels || [];
            charts.violationLineChart.data.datasets[0].data = data.violations || [];
            charts.violationLineChart.data.datasets[1].data = data.detections || [];
            charts.violationLineChart.update();
        }
        
        return data;
    } catch (error) {
        console.error('Error loading violation trend chart:', error);
        return null;
    }
}

// Load Confidence by Class Chart
async function loadConfidenceByClassChart() {
    try {
        const response = await fetch('/api/analytics/charts/confidence-by-class');
        if (!response.ok) throw new Error('Failed to fetch confidence by class');
        
        const data = await response.json();
        
        if (charts.confidenceBarChart) {
            charts.confidenceBarChart.data.labels = data.labels || [];
            charts.confidenceBarChart.data.datasets[0].data = data.data || [];
            charts.confidenceBarChart.update();
        }
        
        return data;
    } catch (error) {
        console.error('Error loading confidence by class chart:', error);
        return null;
    }
}

// Load Hourly Activity Chart
async function loadHourlyActivityChart() {
    try {
        const response = await fetch('/api/analytics/charts/hourly-activity');
        if (!response.ok) throw new Error('Failed to fetch hourly activity');
        
        const data = await response.json();
        
        // This data can be used for additional charts if needed
        return data;
    } catch (error) {
        console.error('Error loading hourly activity chart:', error);
        return null;
    }
}

// Load Violation Status Chart
async function loadViolationStatusChart() {
    try {
        const response = await fetch('/api/analytics/charts/violation-status');
        if (!response.ok) throw new Error('Failed to fetch violation status');
        
        const data = await response.json();
        
        if (charts.statusDoughnutChart) {
            charts.statusDoughnutChart.data.labels = data.labels || [];
            charts.statusDoughnutChart.data.datasets[0].data = data.data || [];
            charts.statusDoughnutChart.data.datasets[0].backgroundColor = data.colors || [chartColors.violations, chartColors.safe];
            charts.statusDoughnutChart.update();
        }
        
        return data;
    } catch (error) {
        console.error('Error loading violation status chart:', error);
        return null;
    }
}

// Load Analytics Stats
async function loadAnalyticsStats() {
    try {
        const response = await fetch('/api/analytics/stats');
        if (!response.ok) throw new Error('Failed to fetch analytics stats');
        
        const stats = await response.json();
        
        // Update stats summary elements
        const statElements = {
            'stat-total': stats.total_detections || 0,
            'stat-violations': stats.total_violations || 0,
            'stat-safe': stats.total_safe || 0,
            'stat-rate': (stats.violation_rate || 0) + '%',
            'stat-confidence': (stats.avg_confidence || 0) + '%',
            'stat-top-class': stats.top_class || '-'
        };
        
        Object.entries(statElements).forEach(([id, value]) => {
            const element = document.getElementById(id);
            if (element) element.textContent = value;
        });
        
        return stats;
    } catch (error) {
        console.error('Error loading analytics stats:', error);
        return null;
    }
}

// Refresh all charts
async function refreshAllCharts() {
    console.log('Refreshing all charts...');
    
    // Show loading animation on refresh button
    const refreshBtn = document.getElementById('refresh-charts');
    if (refreshBtn) {
        const icon = refreshBtn.querySelector('i');
        if (icon) {
            icon.style.transition = 'transform 0.5s ease';
            icon.style.transform = 'rotate(360deg)';
            setTimeout(() => {
                icon.style.transform = 'rotate(0deg)';
            }, 500);
        }
    }
    
    // Reload all chart data
    await loadAllChartData();
    
    console.log('All charts refreshed');
}


// Update real-time alerts panel
function updateAlertsPanel(data) {
    if (!alertsList || !alertCount) {
        return;
    }
    
    if (!data || data.length === 0) {
        alertCount.textContent = '0';
        alertsList.innerHTML = '<div class="no-alerts"><i class="fas fa-check-circle"></i><p>No active alerts</p></div>';
        return;
    }
    
    // Get all violations from the data (show all historical violations)
    const allViolations = data.filter(item => {
        return item['Restricted Area Violation'] === 'Yes';
    }).sort((a, b) => new Date(b.Timestamp) - new Date(a.Timestamp));
    
    // Update alert count
    alertCount.textContent = allViolations.length;
    
    if (allViolations.length === 0) {
        alertsList.innerHTML = '<div class="no-alerts"><i class="fas fa-check-circle"></i><p>No active alerts</p></div>';
        return;
    }
    
    // Display alerts (limit to 10)
    const displayAlerts = allViolations.slice(0, maxAlerts);
    alertsList.innerHTML = displayAlerts.map((item, index) => {
        const alertTime = new Date(item.Timestamp);
        const timeStr = alertTime.toLocaleString();
        const confidence = (parseFloat(item.Confidence || 0) * 100).toFixed(1);
        
        return `
            <div class="alert-item">
                <div class="alert-item-content">
                    <div class="alert-item-time">${timeStr}</div>
                    <div class="alert-item-text">
                        <span>🚨 Violation Detected</span>
                        <span class="alert-item-badge">${item.Class}</span>
                    </div>
                </div>
                <div style="font-size: 0.9rem; color: #94a3b8; font-weight: 600;">${confidence}%</div>
            </div>
        `;
    }).join('');
}

// Throttle function for smooth updates
function throttle(func, limit) {
    let inThrottle;
    return function(...args) {
        if (!inThrottle) {
            func.apply(this, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

// Filter and display data based on current filters
function filterAndDisplayData() {
    if (!tableBody) {
        console.warn('Table body element not found');
        return;
    }
    
    let filteredData = allData;
    
    console.log('Starting filter with', filteredData.length, 'total records');
    console.log('Current filter:', currentFilter);
    console.log('Class filter value:', classFilter ? classFilter.value : 'N/A');
    
    // Apply violation filter
    if (currentFilter === 'violations') {
        filteredData = filteredData.filter(item => item['Restricted Area Violation'] === 'Yes');
        console.log('After violation filter:', filteredData.length, 'records');
    } else if (currentFilter === 'safe') {
        filteredData = filteredData.filter(item => item['Restricted Area Violation'] === 'No');
        console.log('After safe filter:', filteredData.length, 'records');
    }
    
    // Apply class filter - case-insensitive comparison
    if (classFilter && classFilter.value) {
        const selectedClass = classFilter.value.trim().toLowerCase();
        console.log('Filtering by class:', selectedClass);
        filteredData = filteredData.filter(item => {
            const itemClass = (item.Class || '').trim().toLowerCase();
            return itemClass === selectedClass;
        });
        console.log('After class filter:', filteredData.length, 'records');
    }
    
    // Apply date range filter
    if (dateFromFilter || dateToFilter) {
        filteredData = filteredData.filter(item => {
            const itemDate = new Date(item.Timestamp);
            if (dateFromFilter && itemDate < dateFromFilter) return false;
            if (dateToFilter && itemDate > dateToFilter) return false;
            return true;
        });
    }
    
    // Apply search filter
    const searchTerm = searchInput ? searchInput.value.toLowerCase() : '';
    if (searchTerm) {
        filteredData = filteredData.filter(item => 
            item.Timestamp.toLowerCase().includes(searchTerm) ||
            item.Class.toLowerCase().includes(searchTerm)
        );
    }
    
    // Sort by timestamp descending (most recent first)
    const sortedData = [...filteredData].sort((a, b) => {
        return new Date(b.Timestamp) - new Date(a.Timestamp);
    });
    
    // Display filtered data in dashboard tab
    const displayData = sortedData.slice(0, 50);
    
    tableBody.innerHTML = displayData.map(item => {
        const confidence = parseFloat(item.Confidence || 0) * 100;
        const isViolation = item['Restricted Area Violation'] === 'Yes';
        
        return `
            <tr>
                <td class="timestamp-cell">${item.Timestamp || '-'}</td>
                <td>
                    <span class="class-badge">${item.Class || '-'}</span>
                </td>
                <td>
                    <div class="confidence-bar">
                        <span class="confidence-value">${confidence.toFixed(1)}%</span>
                        <div class="confidence-track">
                            <div class="confidence-fill" style="width: ${confidence}%"></div>
                        </div>
                    </div>
                </td>
                <td>
                    <span class="violation-badge ${isViolation ? 'yes' : 'no'}">
                        ${isViolation ? '🚨 Yes' : '✓ No'}
                    </span>
                </td>
            </tr>
        `;
    }).join('');
    
    if (displayData.length === 0 && searchTerm) {
        tableBody.innerHTML = '<tr><td colspan="4" style="text-align: center; padding: 2rem; color: #94a3b8;">No results found</td></tr>';
    }
    
    // Also update the filters tab results table
    updateFilteredResultsTable(displayData, sortedData.length);
    
    // Update filter summary
    updateFilterSummary(filteredData.length);
}

// Update filtered results table in filters tab
function updateFilteredResultsTable(displayData, totalCount) {
    const filteredTable = document.getElementById('filtered-data-table');
    const filteredEmptyState = document.getElementById('filtered-empty-state');
    
    if (!filteredTable) return;
    
    const filteredTableBody = filteredTable.querySelector('tbody');
    
    if (!filteredTableBody) return;
    
    if (displayData.length === 0) {
        filteredTable.style.display = 'none';
        if (filteredEmptyState) filteredEmptyState.style.display = 'block';
        return;
    }
    
    filteredTable.style.display = 'table';
    if (filteredEmptyState) filteredEmptyState.style.display = 'none';
    
    filteredTableBody.innerHTML = displayData.map(item => {
        const confidence = parseFloat(item.Confidence || 0) * 100;
        const isViolation = item['Restricted Area Violation'] === 'Yes';
        
        return `
            <tr>
                <td class="timestamp-cell">${item.Timestamp || '-'}</td>
                <td>
                    <span class="class-badge">${item.Class || '-'}</span>
                </td>
                <td>
                    <div class="confidence-bar">
                        <span class="confidence-value">${confidence.toFixed(1)}%</span>
                        <div class="confidence-track">
                            <div class="confidence-fill" style="width: ${confidence}%"></div>
                        </div>
                    </div>
                </td>
                <td>
                    <span class="violation-badge ${isViolation ? 'yes' : 'no'}">
                        ${isViolation ? '🚨 Yes' : '✓ No'}
                    </span>
                </td>
            </tr>
        `;
    }).join('');
}

// Update filter summary display
function updateFilterSummary(resultCount) {
    const summaryText = document.getElementById('filter-summary-text');
    if (!summaryText) return;
    
    const filters = [];
    
    if (currentFilter !== 'all') {
        filters.push(currentFilter === 'violations' ? 'Violations Only' : 'Safe Only');
    }
    
    if (classFilter && classFilter.value) {
        filters.push(`Class: ${classFilter.value}`);
    }
    
    if (dateFromFilter && dateToFilter) {
        filters.push(`Dates: ${dateFromInput.value} to ${dateToInput.value}`);
    } else if (dateFromFilter) {
        filters.push(`From: ${dateFromInput.value}`);
    } else if (dateToFilter) {
        filters.push(`To: ${dateToInput.value}`);
    }
    
    const searchTerm = searchInput ? searchInput.value.trim() : '';
    if (searchTerm) {
        filters.push(`Search: "${searchTerm}"`);
    }
    
    if (filters.length === 0) {
        summaryText.textContent = 'None';
        summaryText.style.color = '#94a3b8';
    } else {
        summaryText.innerHTML = filters.map(f => `<span style="display: inline-block; background: rgba(0, 212, 255, 0.15); padding: 0.3rem 0.7rem; border-radius: 4px; margin-right: 0.5rem; font-size: 0.9rem;">${f}</span>`).join('');
    }
}

// Update summary statistics
function updateSummaryStats() {
    if (!allData || allData.length === 0) return;
    
    const now = new Date();
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    const weekAgo = new Date(today.getTime() - 7 * 24 * 60 * 60 * 1000);
    
    // Count detections today
    const todayCount = allData.filter(item => {
        const itemDate = new Date(item.Timestamp);
        return itemDate >= today;
    }).length;
    
    // Count detections this week
    const weekCount = allData.filter(item => {
        const itemDate = new Date(item.Timestamp);
        return itemDate >= weekAgo;
    }).length;
    
    // Calculate violation rate
    const violations = allData.filter(item => item['Restricted Area Violation'] === 'Yes').length;
    const violationRate = allData.length > 0 ? Math.round((violations / allData.length) * 100) : 0;
    
    // Calculate average confidence
    const avgConfidence = allData.length > 0 
        ? Math.round((allData.reduce((sum, item) => sum + parseFloat(item.Confidence || 0), 0) / allData.length) * 100)
        : 0;
    
    // Update UI with null checks
    const todayCountEl = document.getElementById('today-count');
    const weekCountEl = document.getElementById('week-count');
    const violationRateEl = document.getElementById('violation-rate');
    const avgConfidenceEl = document.getElementById('avg-confidence');
    
    if (todayCountEl) todayCountEl.textContent = todayCount;
    if (weekCountEl) weekCountEl.textContent = weekCount;
    if (violationRateEl) violationRateEl.textContent = violationRate + '%';
    if (avgConfidenceEl) avgConfidenceEl.textContent = avgConfidence + '%';
}

// Export filtered data to CSV
function exportToCSV() {
    // Get filtered data based on current filters
    let filteredData = allData;
    
    // Apply all active filters
    if (currentFilter === 'violations') {
        filteredData = filteredData.filter(item => item['Restricted Area Violation'] === 'Yes');
    } else if (currentFilter === 'safe') {
        filteredData = filteredData.filter(item => item['Restricted Area Violation'] === 'No');
    }
    
    if (classFilter.value) {
        filteredData = filteredData.filter(item => item.Class === classFilter.value);
    }
    
    if (dateFromFilter || dateToFilter) {
        filteredData = filteredData.filter(item => {
            const itemDate = new Date(item.Timestamp);
            if (dateFromFilter && itemDate < dateFromFilter) return false;
            if (dateToFilter && itemDate > dateToFilter) return false;
            return true;
        });
    }
    
    const searchTerm = searchInput.value.toLowerCase();
    if (searchTerm) {
        filteredData = filteredData.filter(item => 
            item.Timestamp.toLowerCase().includes(searchTerm) ||
            item.Class.toLowerCase().includes(searchTerm)
        );
    }
    
    if (!filteredData || filteredData.length === 0) {
        alert('No data to export');
        return;
    }
    
    // Create CSV content
    const headers = ['Timestamp', 'Class', 'Confidence', 'Violation'];
    const csvContent = [
        headers.join(','),
        ...filteredData.map(item => [
            `"${item.Timestamp}"`,
            item.Class,
            (parseFloat(item.Confidence || 0) * 100).toFixed(1),
            item['Restricted Area Violation']
        ].join(','))
    ].join('\n');
    
    // Generate filename with date range if filters applied
    let filename = 'detection-log';
    if (dateFromFilter || dateToFilter) {
        const from = dateFromFilter ? dateFromFilter.toISOString().split('T')[0] : 'start';
        const to = dateToFilter ? dateToFilter.toISOString().split('T')[0] : 'end';
        filename += `-${from}_to_${to}`;
    }
    filename += `-${new Date().toISOString().split('T')[0]}.csv`;
    
    // Create blob and download
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    window.URL.revokeObjectURL(url);
}
