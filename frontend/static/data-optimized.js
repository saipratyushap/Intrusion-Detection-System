/**
 * Performance Optimized Data Manager
 * Prevents hanging by managing concurrent requests and throttling updates
 */

// Request management
const requestManager = {
    controllers: new Map(),
    
    createAbortController(key) {
        this.controllers.set(key, new AbortController());
        return this.controllers.get(key);
    },
    
    abort(key) {
        const controller = this.controllers.get(key);
        if (controller) {
            controller.abort();
            this.controllers.delete(key);
        }
    },
    
    abortAll() {
        this.controllers.forEach((controller, key) => {
            controller.abort();
        });
        this.controllers.clear();
    }
};

// Throttle function for limiting execution rate
function throttle(func, limit) {
    let inThrottle = false;
    return function(...args) {
        if (!inThrottle) {
            func.apply(this, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

// Debounce function for delaying execution
function debounce(func, wait) {
    let timeout;
    return function(...args) {
        clearTimeout(timeout);
        timeout = setTimeout(() => func.apply(this, args), wait);
    };
}

// Batch API calls to reduce simultaneous requests
const apiBatcher = {
    pending: new Map(),
    timer: null,
    batchDelay: 100, // Wait 100ms to batch requests
    
    queue(key, fetchFn) {
        return new Promise((resolve, reject) => {
            if (!this.pending.has(key)) {
                this.pending.set(key, []);
            }
            this.pending.get(key).push({ resolve, reject, fetchFn });
            
            if (!this.timer) {
                this.timer = setTimeout(() => this.processBatch(), this.batchDelay);
            }
        });
    },
    
    async processBatch() {
        const groups = new Map();
        
        // Group by endpoint
        this.pending.forEach((requests, key) => {
            const endpoint = key.split('?')[0];
            if (!groups.has(endpoint)) {
                groups.set(endpoint, []);
            }
            groups.get(endpoint).push(...requests);
        });
        
        // Process each group (limit concurrent to 3)
        const semaphore = new Semaphore(3);
        
        for (const [endpoint, requests] of groups) {
            await semaphore.acquire();
            this.executeBatch(endpoint, requests)
                .finally(() => semaphore.release());
        }
        
        this.pending.clear();
        this.timer = null;
    },
    
    async executeBatch(endpoint, requests) {
        // Execute first request normally, use its response as cache for others
        if (requests.length === 0) return;
        
        try {
            const first = requests[0];
            const response = await first.fetchFn();
            first.resolve(response);
            
            // Return cached response for other requests
            requests.slice(1).forEach(req => {
                req.resolve(response);
            });
        } catch (error) {
            requests.forEach(req => {
                req.reject(error);
            });
        }
    }
};

// Semaphore for limiting concurrent operations
class Semaphore {
    constructor(maxConcurrency) {
        this.maxConcurrency = maxConcurrency;
        this.currentCount = 0;
        this.waitQueue = [];
    }
    
    async acquire() {
        if (this.currentCount < this.maxConcurrency) {
            this.currentCount++;
            return;
        }
        
        return new Promise(resolve => {
            this.waitQueue.push(resolve);
        });
    }
    
    release() {
        this.currentCount--;
        if (this.waitQueue.length > 0) {
            this.currentCount++;
            const next = this.waitQueue.shift();
            next();
        }
    }
}

// Optimized DOM updates using DocumentFragment
function batchDOMUpdates(updates) {
    requestAnimationFrame(() => {
        const fragment = document.createDocumentFragment();
        updates.forEach(update => {
            const element = typeof update.selector === 'string' 
                ? document.querySelector(update.selector)
                : update.selector;
            if (element) {
                element.textContent = update.content;
            }
        });
    });
}

// Main optimized data loading
async function loadInitialDataOptimized() {
    const controller = requestManager.createAbortController('initialData');
    
    try {
        console.log('Loading initial data (optimized)...');
        
        // Use batched requests instead of Promise.all
        const summaryData = await apiBatcher.queue('summary', () => 
            fetch('/api/detections/summary', { signal: controller.signal })
                .then(res => res.json())
        );
        
        const recentData = await apiBatcher.queue('recent', () => 
            fetch('/api/detections/recent?limit=50', { signal: controller.signal })
                .then(res => res.json())
        );
        
        const todayData = apiBatcher.queue('today', () => 
            fetch('/api/detections/today', { signal: controller.signal })
                .then(res => res.json())
        );
        
        // Update UI with throttled function
        updateStatsThrottled(summaryData);
        updateTableOptimized(recentData.data || []);
        
    } catch (error) {
        if (error.name === 'AbortError') {
            console.log('Initial data loading cancelled');
        } else {
            console.error('Error loading initial data:', error);
        }
    }
}

// Throttled stats update (max once per 500ms)
const updateStatsThrottled = throttle((summary) => {
    if (!summary) return;
    
    const elements = {
        totalDetections: summary.total_detections || 0,
        totalViolations: summary.total_violations || 0,
        alertClasses: summary.alert_classes || 0
    };
    
    Object.entries(elements).forEach(([id, value]) => {
        const el = document.getElementById(id);
        if (el) el.textContent = value;
    });
}, 500);

// Optimized table update using DocumentFragment
function updateTableOptimized(data) {
    if (!Array.isArray(data) || data.length === 0) return;
    
    const tableBody = document.querySelector('#dataTable tbody, #data-table tbody');
    if (!tableBody) return;
    
    const fragment = document.createDocumentFragment();
    
    // Limit displayed rows to 50 for performance
    const displayData = data.slice(0, 50);
    
    displayData.forEach((item, index) => {
        const row = document.createElement('tr');
        row.style.animation = 'none';
        
        const confidence = parseFloat(item.Confidence || 0) * 100;
        const isViolation = item['Restricted Area Violation'] === 'Yes';
        
        row.innerHTML = `
            <td>${item.Timestamp || '-'}</td>
            <td><span class="class-badge">${item.Class || '-'}</span></td>
            <td>${confidence.toFixed(1)}%</td>
            <td><span class="violation-badge ${isViolation ? 'yes' : 'no'}">${isViolation ? 'Yes' : 'No'}</span></td>
        `;
        
        fragment.appendChild(row);
    });
    
    tableBody.innerHTML = '';
    tableBody.appendChild(fragment);
}

// Optimized auto-refresh with proper throttling
let refreshInProgress = false;
const refreshCooldown = 5000;

async function refreshDataOptimized() {
    if (refreshInProgress) {
        console.log('Refresh already in progress, skipping...');
        return;
    }
    
    refreshInProgress = true;
    const controller = requestManager.createAbortController('refresh');
    
    try {
        console.log('Refreshing data (optimized)...');
        
        const response = await fetch('/api/detections/recent?limit=50', {
            signal: controller.signal
        });
        
        if (!response.ok) throw new Error('Refresh failed');
        
        const data = await response.json();
        
        if (data.data && data.data.length > 0) {
            updateTableOptimized(data.data);
            updateStatsThrottled(data.summary || {});
        }
        
    } catch (error) {
        if (error.name !== 'AbortError') {
            console.error('Error refreshing data:', error);
        }
    } finally {
        refreshInProgress = false;
        setTimeout(() => {
            refreshInProgress = false;
        }, refreshCooldown);
    }
}

// WebSocket with exponential backoff
let wsConnectionAttempts = 0;
const MAX_WS_ATTEMPTS = 3;
const WS_BASE_DELAY = 1000;

function connectWebSocketOptimized() {
    if (wsConnectionAttempts >= MAX_WS_ATTEMPTS) {
        console.log('Max WebSocket attempts reached, falling back to HTTP polling');
        startOptimizedPolling();
        return;
    }
    
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/data`;
    
    console.log('Connecting to WebSocket (optimized):', wsUrl);
    
    const ws = new WebSocket(wsUrl);
    const connectionTimeout = setTimeout(() => {
        ws.close();
        wsConnectionAttempts++;
        console.log(`WebSocket timeout (attempt ${wsConnectionAttempts}/${MAX_WS_ATTEMPTS})`);
        connectWebSocketOptimized();
    }, 5000);
    
    ws.onopen = () => {
        console.log('WebSocket connected');
        clearTimeout(connectionTimeout);
        wsConnectionAttempts = 0;
        updateConnectionStatus(true);
        
        if (pollingInterval) {
            clearInterval(pollingInterval);
            pollingInterval = null;
        }
    };
    
    ws.onmessage = (event) => {
        try {
            const response = JSON.parse(event.data);
            
            if (response.data) {
                updateTableOptimized(response.data);
            }
        } catch (error) {
            console.error('Error parsing WebSocket message:', error);
        }
    };
    
    ws.onclose = () => {
        console.log('WebSocket disconnected');
        clearTimeout(connectionTimeout);
        updateConnectionStatus(false);
        startOptimizedPolling();
    };
    
    ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        ws.close();
    };
}

// Optimized polling
let pollingInterval = null;
let pollingAttempts = 0;
const MAX_POLLING_ATTEMPTS = 5;

function startOptimizedPolling() {
    if (pollingInterval) return;
    
    const pollWithBackoff = async () => {
        if (pollingAttempts >= MAX_POLLING_ATTEMPTS) {
            console.log('Max polling attempts reached, slowing down');
            pollingInterval = setInterval(pollWithBackoff, 30000);
            return;
        }
        
        try {
            await refreshDataOptimized();
            pollingAttempts = 0;
        } catch (error) {
            pollingAttempts++;
            console.log(`Polling attempt ${pollingAttempts}/${MAX_POLLING_ATTEMPTS}`);
        }
    };
    
    pollingInterval = setInterval(pollWithBackoff, 10000);
    console.log('Optimized polling started (10s interval)');
}

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    requestManager.abortAll();
    if (pollingInterval) {
        clearInterval(pollingInterval);
    }
});

// Export the optimized functions
window.dataOptimizations = {
    loadInitialData: loadInitialDataOptimized,
    refreshData: refreshDataOptimized,
    connectWebSocket: connectWebSocketOptimized,
    cleanup: () => requestManager.abortAll()
};

