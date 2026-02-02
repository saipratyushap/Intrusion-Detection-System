document.addEventListener("DOMContentLoaded", function () {
    // Initialize Theme
    initTheme();
    
    // Theme Toggle Functionality
    const themeToggle = document.getElementById('themeToggle');
    if (themeToggle) {
        themeToggle.addEventListener('click', toggleTheme);
    }

    // Initialize Monitoring State
    initMonitoringState();
    
    // Initialize Keyboard Shortcuts
    initKeyboardShortcuts();

    var ws = new WebSocket("ws://localhost:8000/ws");

    // HTML Elements
    var totalDetections = document.getElementById("totalDetections");
    var totalViolations = document.getElementById("totalViolations");
    var mostFrequentClass = document.getElementById("mostFrequentClass");
    var dataTable = document.getElementById("dataTable");

    // Violation counts by time of day
    var violationCountsByTime = {
        morning: 0,
        afternoon: 0,
        night: 0
    };

    // Data Storage
    var detectionCounts = {}; // { "person": 5, "car": 3, ... }
    var confidenceData = {};  // { "person": [0.9, 0.8], "car": [0.7] }

    // Bar Chart Initialization
    var barCtx = document.getElementById("barChart").getContext("2d");
    var barChart = new Chart(barCtx, {
        type: "bar",
        data: {
            labels: [],
            datasets: [{
                label: "Average Confidence (%)",
                backgroundColor: [], // Colors will be assigned dynamically
                data: [],
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { display: false },
            }
        }
    });

    // Pie Chart Initialization
    var pieCtx = document.getElementById('violationPieChart').getContext('2d');
    var violationPieChart = new Chart(pieCtx, {
        type: 'pie',
        data: {
            labels: ['Morning (6 AM - 12 PM)', 'Afternoon (12 PM - 6 PM)', 'Night (6 PM - 12 AM)'],
            datasets: [{
                data: [0, 0, 0], // Initial values
                backgroundColor: ['#00f2ff', '#ff8c00', '#ff2d00'], 
                borderColor: '#121212',
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'top',
                    labels: {
                        color: '#fff',
                        font: { weight: 'bold' }
                    }
                }
            }
        }
    });

    ws.onmessage = function (event) {
        var data = JSON.parse(event.data);

        // Update summary cards
        totalDetections.innerHTML = data.summary.total_detections;
        totalViolations.innerHTML = data.summary.total_violations;
        mostFrequentClass.innerHTML = data.summary.most_frequent_class;

        // Process each detection
        data.timestamp.forEach(function(timestamp, index) {
            var detectedClass = data.class[index];
            var confidence = data.confidence[index];

            // Update detection counts and confidence data
            if (!detectionCounts[detectedClass]) {
                detectionCounts[detectedClass] = 0;
                confidenceData[detectedClass] = [];
            }
            detectionCounts[detectedClass] += 1;
            confidenceData[detectedClass].push(confidence);

            // Update violation count if violation occurred
            if (data.restricted_area_violation[index]) {
                updateViolationCounts(timestamp);
            }

            // Add new row to the table
            var newRow = `<tr>
                <td>${timestamp}</td>
                <td>${detectedClass}</td>
                <td>${(confidence).toFixed(2)}%</td>
                <td>${data.restricted_area_violation[index]}</td>
            </tr>`;
            dataTable.innerHTML = newRow + dataTable.innerHTML;
        });

        // Update the bar chart
        updateBarChart();
    };

    function updateBarChart() {
        barChart.data.labels = Object.keys(detectionCounts);
        
        barChart.data.datasets[0].data = Object.keys(confidenceData).map(cls => {
            let sum = confidenceData[cls].reduce((a, b) => a + b, 0);
            return (sum / confidenceData[cls].length);
        });

        // Assign different colors dynamically
        let colors = [
            "#FF5733", "#33FF57", "#3357FF", "#FF33A1", "#FFD700", "#00FFFF", 
            "#8A2BE2", "#DC143C", "#20B2AA", "#FF4500"
        ]; // More colors added for variety

        barChart.data.datasets[0].backgroundColor = barChart.data.labels.map((_, i) => colors[i % colors.length]);

        barChart.update();
    }

    function updateViolationCounts(timestamp) {
        var violationTime = new Date(timestamp).getHours(); 

        if (violationTime >= 6 && violationTime < 12) {
            violationCountsByTime.morning += 1;
        } else if (violationTime >= 12 && violationTime < 18) {
            violationCountsByTime.afternoon += 1;
        } else {
            violationCountsByTime.night += 1;
        }

        // Update Pie Chart
        violationPieChart.data.datasets[0].data = [
            violationCountsByTime.morning,
            violationCountsByTime.afternoon,
            violationCountsByTime.night
        ];
        violationPieChart.update();
    }

    // Simulated data for testing (REMOVE IN LIVE SYSTEM)
    // setInterval(() => {
    //     const fakeTimestamp = new Date().toISOString();
    //     updateViolationCounts(fakeTimestamp);
    // }, 5000);
});

// ============================================
// 🎨 Theme Management
// ============================================

function initTheme() {
    const savedTheme = localStorage.getItem('theme') || 
        (window.matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark');
    applyTheme(savedTheme);
}

function applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
    
    const themeToggle = document.getElementById('themeToggle');
    if (themeToggle) {
        const icon = theme === 'dark' ? 'fa-moon' : 'fa-sun';
        themeToggle.innerHTML = `<i class="fas ${icon}"></i>`;
    }
    
    // Update chart legend colors for light theme
    if (typeof violationPieChart !== 'undefined') {
        updateChartColors(theme);
    }
}

function toggleTheme() {
    const currentTheme = document.documentElement.getAttribute('data-theme') || 'dark';
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    applyTheme(newTheme);
}

function updateChartColors(theme) {
    const textColor = theme === 'dark' ? '#fff' : '#1e293b';
    if (typeof violationPieChart !== 'undefined' && violationPieChart.options.plugins.legend.labels) {
        violationPieChart.options.plugins.legend.labels.color = textColor;
        violationPieChart.update();
    }
}

// ============================================
// ⌨️ Keyboard Shortcuts
// ============================================

document.addEventListener('keydown', function(e) {
    // Don't trigger shortcuts when typing in inputs
    if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
        return;
    }
    
    switch(e.key) {
        case ' ':
            e.preventDefault();
            // Toggle monitoring (placeholder - implement based on your needs)
            console.log('Space pressed - Toggle monitoring');
            break;
        case 'm':
        case 'M':
            e.preventDefault();
            // Toggle mute (placeholder - implement based on your needs)
            console.log('M pressed - Toggle mute');
            break;
        case 'd':
        case 'D':
            if (e.ctrlKey || e.metaKey) {
                e.preventDefault();
                window.location.href = '/data';
            }
            break;
        case 's':
        case 'S':
            if (e.ctrlKey || e.metaKey) {
                e.preventDefault();
                window.location.href = '/snapshots';
            }
            break;
        case '?':
            showKeyboardShortcutsHelp();
            break;
        case '1':
            window.location.href = '/';
            break;
        case '2':
            window.location.href = '/data';
            break;
    }
});

// ============================================
// 🎛️ Monitoring State Management
// ============================================

// Global monitoring state
let monitoringState = {
    isMonitoring: true,
    isMuted: false,
    currentCamera: 1,
    totalCameras: 4
};

// Initialize monitoring state from localStorage
function initMonitoringState() {
    // Load saved state
    const savedState = localStorage.getItem('monitoringState');
    if (savedState) {
        try {
            monitoringState = { ...monitoringState, ...JSON.parse(savedState) };
        } catch (e) {
            console.error('Error parsing monitoring state:', e);
        }
    }
    
    // Apply saved state to UI
    updateMonitoringUI();
    updateMuteUI();
    updateCameraUI();
    
    // Check for monitoring support
    if (monitoringState.currentCamera < 1 || monitoringState.currentCamera > monitoringState.totalCameras) {
        monitoringState.currentCamera = 1;
    }
}

// Save monitoring state to localStorage
function saveMonitoringState() {
    localStorage.setItem('monitoringState', JSON.stringify(monitoringState));
}

// Toggle monitoring (Start/Stop)
function toggleMonitoring() {
    monitoringState.isMonitoring = !monitoringState.isMonitoring;
    saveMonitoringState();
    updateMonitoringUI();
    
    // Show toast notification
    showToast(
        monitoringState.isMonitoring ? 'Monitoring started' : 'Monitoring stopped',
        monitoringState.isMonitoring ? 'success' : 'warning'
    );
    
    // Trigger event for other components
    window.dispatchEvent(new CustomEvent('monitoringToggle', { 
        detail: { isMonitoring: monitoringState.isMonitoring } 
    }));
    
    return monitoringState.isMonitoring;
}

// Toggle mute (Mute/Unmute alerts)
function toggleMute() {
    monitoringState.isMuted = !monitoringState.isMuted;
    saveMonitoringState();
    updateMuteUI();
    
    // Show toast notification
    showToast(
        monitoringState.isMuted ? 'Alerts muted' : 'Alerts unmuted',
        monitoringState.isMuted ? 'warning' : 'info'
    );
    
    // Trigger event for other components
    window.dispatchEvent(new CustomEvent('muteToggle', { 
        detail: { isMuted: monitoringState.isMuted } 
    }));
    
    return monitoringState.isMuted;
}

// Switch camera (1-4)
function switchCamera(cameraId) {
    if (cameraId < 1 || cameraId > monitoringState.totalCameras) {
        console.log(`Camera ${cameraId} not available`);
        return false;
    }
    
    monitoringState.currentCamera = cameraId;
    saveMonitoringState();
    updateCameraUI();
    
    // Show toast notification
    showToast(`Switched to Camera ${cameraId}`, 'info');
    
    // Trigger event for other components
    window.dispatchEvent(new CustomEvent('cameraSwitch', { 
        detail: { cameraId: monitoringState.currentCamera } 
    }));
    
    return true;
}

// Update monitoring UI indicators
function updateMonitoringUI() {
    const indicator = document.getElementById('monitoringIndicator');
    const toggleBtn = document.getElementById('monitoringToggleBtn');
    const toggleText = document.getElementById('monitoringToggleText');
    
    if (indicator) {
        if (monitoringState.isMonitoring) {
            indicator.innerHTML = '<i class="fas fa-circle" style="color: #22c55e;"></i> Live';
            indicator.classList.remove('stopped');
            indicator.classList.add('active');
        } else {
            indicator.innerHTML = '<i class="fas fa-pause" style="color: #fbbf24;"></i> Paused';
            indicator.classList.remove('active');
            indicator.classList.add('stopped');
        }
    }
    
    // Update toggle button
    if (toggleBtn && toggleText) {
        if (monitoringState.isMonitoring) {
            toggleBtn.innerHTML = '<i class="fas fa-stop"></i> <span id="monitoringToggleText">Stop</span>';
            toggleBtn.classList.remove('btn-warning');
            toggleBtn.classList.add('btn-primary');
        } else {
            toggleBtn.innerHTML = '<i class="fas fa-play"></i> <span id="monitoringToggleText">Start</span>';
            toggleBtn.classList.remove('btn-primary');
            toggleBtn.classList.add('btn-warning');
        }
    }
    
    // Update page title with monitoring status
    document.title = monitoringState.isMonitoring ? '● Live Monitoring' : '○ Monitoring Paused';
}

// Update mute UI indicators
function updateMuteUI() {
    const muteBtn = document.getElementById('muteToggleBtn');
    if (muteBtn) {
        if (monitoringState.isMuted) {
            muteBtn.innerHTML = '<i class="fas fa-volume-mute"></i>';
            muteBtn.classList.add('muted');
        } else {
            muteBtn.innerHTML = '<i class="fas fa-volume-up"></i>';
            muteBtn.classList.remove('muted');
        }
    }
}

// Update camera UI
function updateCameraUI() {
    // Update camera indicator
    const cameraIndicator = document.getElementById('cameraIndicator');
    if (cameraIndicator) {
        cameraIndicator.textContent = `Camera ${monitoringState.currentCamera}`;
    }
    
    // Update camera buttons
    document.querySelectorAll('.camera-btn').forEach((btn, index) => {
        const btnCamera = index + 1;
        if (btnCamera === monitoringState.currentCamera) {
            btn.classList.add('active');
        } else {
            btn.classList.remove('active');
        }
    });
}

// ============================================
// ⌨️ Enhanced Keyboard Shortcuts
// ============================================

function initKeyboardShortcuts() {
    document.addEventListener('keydown', function(e) {
        // Don't trigger shortcuts when typing in inputs
        if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA' || e.target.contentEditable === 'true') {
            return;
        }
        
        // Handle keyboard shortcuts
        switch(e.key) {
            case ' ':
                // Space: Start/Stop monitoring
                e.preventDefault();
                toggleMonitoring();
                break;
                
            case 'm':
            case 'M':
                // M: Mute/unmute alerts
                e.preventDefault();
                toggleMute();
                break;
                
            case 'Escape':
                // Esc: Return to home/dashboard
                e.preventDefault();
                window.location.href = '/';
                break;
                
            case '1':
            case '2':
            case '3':
            case '4':
                // 1-4: Switch cameras
                e.preventDefault();
                const cameraId = parseInt(e.key);
                switchCamera(cameraId);
                break;
                
            case '?':
                // ?: Show help
                e.preventDefault();
                showKeyboardShortcutsHelp();
                break;
                
            case 'd':
            case 'D':
                if (e.ctrlKey || e.metaKey) {
                    // Ctrl+D: Go to data/dashboard
                    e.preventDefault();
                    window.location.href = '/data';
                }
                break;
                
            case 's':
            case 'S':
                if (e.ctrlKey || e.metaKey) {
                    // Ctrl+S: Go to snapshots
                    e.preventDefault();
                    window.location.href = '/snapshots';
                }
                break;
                
            case 'h':
            case 'H':
                // H: Go to home
                e.preventDefault();
                window.location.href = '/';
                break;
        }
    });
    
    // Add keyboard shortcut hints to UI
    updateShortcutHints();
}

// Show keyboard shortcuts help
function showKeyboardShortcutsHelp() {
    // Create modal if it doesn't exist
    let modal = document.getElementById('shortcutsModal');
    if (!modal) {
        modal = document.createElement('div');
        modal.id = 'shortcutsModal';
        modal.className = 'shortcuts-modal';
        modal.innerHTML = `
            <div class="shortcuts-modal-content">
                <div class="shortcuts-modal-header">
                    <h3><i class="fas fa-keyboard"></i> Keyboard Shortcuts</h3>
                    <button class="shortcuts-modal-close" onclick="hideKeyboardShortcutsHelp()">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                <div class="shortcuts-modal-body">
                    <div class="shortcut-group">
                        <h4>Monitoring</h4>
                        <div class="shortcut-item">
                            <kbd>Space</kbd>
                            <span>Start/Stop Monitoring</span>
                        </div>
                        <div class="shortcut-item">
                            <kbd>M</kbd>
                            <span>Mute/Unmute Alerts</span>
                        </div>
                    </div>
                    <div class="shortcut-group">
                        <h4>Camera Navigation</h4>
                        <div class="shortcut-item">
                            <kbd>1</kbd><kbd>2</kbd><kbd>3</kbd><kbd>4</kbd>
                            <span>Switch Camera (1-4)</span>
                        </div>
                    </div>
                    <div class="shortcut-group">
                        <h4>Navigation</h4>
                        <div class="shortcut-item">
                            <kbd>Esc</kbd>
                            <span>Return to Home</span>
                        </div>
                        <div class="shortcut-item">
                            <kbd>H</kbd>
                            <span>Go to Dashboard</span>
                        </div>
                        <div class="shortcut-item">
                            <kbd>Ctrl + D</kbd>
                            <span>Go to Data Page</span>
                        </div>
                        <div class="shortcut-item">
                            <kbd>Ctrl + S</kbd>
                            <span>Go to Snapshots</span>
                        </div>
                    </div>
                    <div class="shortcut-group">
                        <h4>Help</h4>
                        <div class="shortcut-item">
                            <kbd>?</kbd>
                            <span>Show This Help</span>
                        </div>
                    </div>
                </div>
            </div>
        `;
        document.body.appendChild(modal);
        
        // Add click outside to close
        modal.addEventListener('click', function(e) {
            if (e.target === modal) {
                hideKeyboardShortcutsHelp();
            }
        });
    }
    
    // Show modal
    modal.classList.add('show');
    document.body.style.overflow = 'hidden';
}

// Hide keyboard shortcuts help
function hideKeyboardShortcutsHelp() {
    const modal = document.getElementById('shortcutsModal');
    if (modal) {
        modal.classList.remove('show');
        document.body.style.overflow = '';
    }
}

// Update shortcut hints in UI
function updateShortcutHints() {
    const hintsContainer = document.getElementById('shortcutsHint');
    if (hintsContainer) {
        hintsContainer.innerHTML = `
            <span class="shortcut-hint-item"><kbd>Space</kbd> Start/Stop</span>
            <span class="shortcut-hint-item"><kbd>M</kbd> Mute</span>
            <span class="shortcut-hint-item"><kbd>1-4</kbd> Camera</span>
            <span class="shortcut-hint-item"><kbd>?</kbd> Help</span>
        `;
    }
}

// ============================================
// 🍞 Toast Notifications
// ============================================

function showToast(message, type = 'info') {
    // Create toast container if it doesn't exist
    let toastContainer = document.getElementById('toastContainer');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.id = 'toastContainer';
        toastContainer.className = 'toast-container';
        document.body.appendChild(toastContainer);
    }
    
    // Create toast element
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `
        <div class="toast-icon">
            <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'warning' ? 'exclamation-triangle' : 'info-circle'}"></i>
        </div>
        <div class="toast-message">${message}</div>
        <button class="toast-close" onclick="this.parentElement.remove()">
            <i class="fas fa-times"></i>
        </button>
    `;
    
    toastContainer.appendChild(toast);
    
    // Auto remove after 3 seconds
    setTimeout(() => {
        toast.classList.add('fade-out');
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// ============================================
// 🎯 Monitoring Controls (API Integration)
// ============================================

// Start monitoring via API
async function startMonitoring() {
    try {
        const response = await fetch('/api/monitoring/start', { method: 'POST' });
        if (response.ok) {
            monitoringState.isMonitoring = true;
            saveMonitoringState();
            updateMonitoringUI();
            return true;
        }
    } catch (error) {
        console.error('Error starting monitoring:', error);
    }
    return false;
}

// Stop monitoring via API
async function stopMonitoring() {
    try {
        const response = await fetch('/api/monitoring/stop', { method: 'POST' });
        if (response.ok) {
            monitoringState.isMonitoring = false;
            saveMonitoringState();
            updateMonitoringUI();
            return true;
        }
    } catch (error) {
        console.error('Error stopping monitoring:', error);
    }
    return false;
}

// Mute alerts via API
async function muteAlerts() {
    try {
        const response = await fetch('/api/alerts/mute', { method: 'POST' });
        if (response.ok) {
            monitoringState.isMuted = true;
            saveMonitoringState();
            updateMuteUI();
            return true;
        }
    } catch (error) {
        console.error('Error muting alerts:', error);
    }
    return false;
}

// Unmute alerts via API
async function unmuteAlerts() {
    try {
        const response = await fetch('/api/alerts/unmute', { method: 'POST' });
        if (response.ok) {
            monitoringState.isMuted = false;
            saveMonitoringState();
            updateMuteUI();
            return true;
        }
    } catch (error) {
        console.error('Error unmuting alerts:', error);
    }
    return false;
}

// Switch camera via API
async function switchCameraAPI(cameraId) {
    try {
        const response = await fetch(`/api/camera/${cameraId}/switch`, { 
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        if (response.ok) {
            monitoringState.currentCamera = cameraId;
            saveMonitoringState();
            updateCameraUI();
            return true;
        }
    } catch (error) {
        console.error('Error switching camera:', error);
    }
    return false;
}

// ============================================
// 🧪 Demo Mode Functions (for testing without backend)
// ============================================

// Simulate monitoring toggle (for demo purposes)
function simulateMonitoringToggle() {
    console.log('Demo mode: Simulating monitoring toggle');
    toggleMonitoring();
}

// Simulate mute toggle (for demo purposes)
function simulateMuteToggle() {
    console.log('Demo mode: Simulating mute toggle');
    toggleMute();
}

// Simulate camera switch (for demo purposes)
function simulateCameraSwitch(cameraId) {
    console.log(`Demo mode: Simulating camera switch to ${cameraId}`);
    switchCamera(cameraId);
}
