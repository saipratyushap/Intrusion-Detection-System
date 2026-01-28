// ============================================
// 📸 Snapshot Gallery JavaScript
// Restricted Area Monitoring System
// ============================================

// Global State
let snapshots = [];
let filteredSnapshots = [];
let selectedSnapshots = new Set();
let currentPage = 1;
const ITEMS_PER_PAGE = 12;
let currentLightboxIndex = 0;

// DOM Elements
const snapshotGrid = document.getElementById('snapshotGrid');
const loadingState = document.getElementById('loadingState');
const emptyState = document.getElementById('emptyState');
const searchInput = document.getElementById('searchInput');
const filterSelect = document.getElementById('filterSelect');
const sortSelect = document.getElementById('sortSelect');
const totalSnapshotsEl = document.getElementById('totalSnapshots');
const violationSnapshotsEl = document.getElementById('violationSnapshots');
const safeSnapshotsEl = document.getElementById('safeSnapshots');
const selectedCountEl = document.getElementById('selectedCount');
const selectAllBtn = document.getElementById('selectAllBtn');
const deselectAllBtn = document.getElementById('deselectAllBtn');
const downloadSelectedBtn = document.getElementById('downloadSelectedBtn');
const deleteSelectedBtn = document.getElementById('deleteSelectedBtn');
const gridViewBtn = document.getElementById('gridViewBtn');
const listViewBtn = document.getElementById('listViewBtn');
const lightbox = document.getElementById('lightbox');
const lightboxImage = document.getElementById('lightboxImage');
const lightboxTitle = document.getElementById('lightboxTitle');
const lightboxDetails = document.getElementById('lightboxDetails');
const themeToggle = document.getElementById('themeToggle');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    initTheme();
    loadSnapshots();
    setupEventListeners();
    setupKeyboardShortcuts();
});

// Theme Management
function initTheme() {
    const savedTheme = localStorage.getItem('theme') || 
        (window.matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark');
    applyTheme(savedTheme);
}

function applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
    const icon = theme === 'dark' ? 'fa-moon' : 'fa-sun';
    if (themeToggle) {
        themeToggle.innerHTML = `<i class="fas ${icon}"></i>`;
    }
}

if (themeToggle) {
    themeToggle.addEventListener('click', () => {
        const currentTheme = document.documentElement.getAttribute('data-theme') || 'dark';
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        applyTheme(newTheme);
    });
}

// Event Listeners
function setupEventListeners() {
    searchInput.addEventListener('input', debounce(filterAndSortSnapshots, 300));
    filterSelect.addEventListener('change', filterAndSortSnapshots);
    sortSelect.addEventListener('change', filterAndSortSnapshots);
    
    selectAllBtn.addEventListener('click', selectAllSnapshots);
    deselectAllBtn.addEventListener('click', deselectAllSnapshots);
    downloadSelectedBtn.addEventListener('click', downloadSelected);
    deleteSelectedBtn.addEventListener('click', deleteSelected);
    
    gridViewBtn.addEventListener('click', () => setView('grid'));
    listViewBtn.addEventListener('click', () => setView('list'));
    
    // Lightbox navigation
    document.getElementById('lightboxClose').addEventListener('click', closeLightbox);
    document.getElementById('lightboxPrev').addEventListener('click', () => navigateLightbox(-1));
    document.getElementById('lightboxNext').addEventListener('click', () => navigateLightbox(1));
    document.getElementById('lightboxDownload').addEventListener('click', downloadCurrentSnapshot);
    document.getElementById('lightboxDelete').addEventListener('click', deleteCurrentSnapshot);
    
    // Close lightbox on escape
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && lightbox.classList.contains('active')) {
            closeLightbox();
        }
    });
    
    // Close lightbox on backdrop click
    lightbox.addEventListener('click', (e) => {
        if (e.target === lightbox) {
            closeLightbox();
        }
    });
}

// Keyboard Shortcuts
function setupKeyboardShortcuts() {
    document.addEventListener('keydown', (e) => {
        // Don't trigger shortcuts when typing in inputs
        if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
            return;
        }
        
        switch (e.key) {
            case ' ':
                e.preventDefault();
                toggleSelectionOnHovered();
                break;
            case 'a':
                if (e.ctrlKey || e.metaKey) {
                    e.preventDefault();
                    selectAllSnapshots();
                }
                break;
            case 'd':
                if (e.ctrlKey || e.metaKey) {
                    e.preventDefault();
                    deselectAllSnapshots();
                }
                break;
            case 'Delete':
            case 'Backspace':
                if (selectedSnapshots.size > 0) {
                    deleteSelected();
                }
                break;
            case 'ArrowLeft':
                if (lightbox.classList.contains('active')) {
                    navigateLightbox(-1);
                }
                break;
            case 'ArrowRight':
                if (lightbox.classList.contains('active')) {
                    navigateLightbox(1);
                }
                break;
            case '?':
                showHelp();
                break;
        }
    });
}

// Load Snapshots
async function loadSnapshots() {
    try {
        loadingState.style.display = 'block';
        snapshotGrid.style.display = 'none';
        emptyState.style.display = 'none';
        
        // Fetch snapshots from API
        const response = await fetch('/api/snapshots');
        const data = await response.json();
        
        if (data.snapshots && data.snapshots.length > 0) {
            snapshots = data.snapshots.map(s => ({
                id: s.id || s.filename,
                filename: s.filename,
                timestamp: s.timestamp,
                class: s.class,
                confidence: s.confidence,
                violation: s.violation || s.is_violation,
                path: s.path || `/data/frames/${s.filename}`
            }));
            
            // Update stats
            updateStats();
            filterAndSortSnapshots();
            
            loadingState.style.display = 'none';
            snapshotGrid.style.display = 'grid';
        } else {
            // Use demo data for demonstration
            snapshots = generateDemoSnapshots();
            updateStats();
            filterAndSortSnapshots();
            
            loadingState.style.display = 'none';
            snapshotGrid.style.display = 'grid';
        }
    } catch (error) {
        console.error('Error loading snapshots:', error);
        // Fallback to demo data
        snapshots = generateDemoSnapshots();
        updateStats();
        filterAndSortSnapshots();
        loadingState.style.display = 'none';
        snapshotGrid.style.display = 'grid';
    }
}

// Generate Demo Snapshots (for demonstration)
function generateDemoSnapshots() {
    const classes = ['Person', 'Car', 'Truck', 'Motorcycle', 'Bicycle'];
    const demoSnapshots = [];
    
    for (let i = 0; i < 24; i++) {
        const isViolation = Math.random() > 0.5;
        const timestamp = new Date(Date.now() - i * 3600000).toISOString();
        const cls = classes[Math.floor(Math.random() * classes.length)];
        
        demoSnapshots.push({
            id: `demo_${i}`,
            filename: `frame_demo_${i}.jpg`,
            timestamp: timestamp,
            class: cls,
            confidence: 0.7 + Math.random() * 0.29,
            violation: isViolation,
            path: `/data/frames/frame_20260127_133418_091154.jpg` // Use existing image
        });
    }
    
    return demoSnapshots;
}

// Update Statistics
function updateStats() {
    totalSnapshotsEl.textContent = snapshots.length;
    const violations = snapshots.filter(s => s.violation);
    violationSnapshotsEl.textContent = violations.length;
    safeSnapshotsEl.textContent = snapshots.length - violations.length;
    updateSelectedCount();
}

// Filter and Sort Snapshots
function filterAndSortSnapshots() {
    const searchTerm = searchInput.value.toLowerCase();
    const filter = filterSelect.value;
    const sort = sortSelect.value;
    
    filteredSnapshots = snapshots.filter(snapshot => {
        // Search filter
        const matchesSearch = snapshot.class.toLowerCase().includes(searchTerm) ||
            snapshot.timestamp.toLowerCase().includes(searchTerm);
        
        // Type filter
        if (filter === 'violation' && !snapshot.violation) return false;
        if (filter === 'safe' && snapshot.violation) return false;
        
        return matchesSearch;
    });
    
    // Sort
    filteredSnapshots.sort((a, b) => {
        const timeA = new Date(a.timestamp).getTime();
        const timeB = new Date(b.timestamp).getTime();
        return sort === 'newest' ? timeB - timeA : timeA - timeB;
    });
    
    currentPage = 1;
    renderSnapshots();
}

// Render Snapshots
function renderSnapshots() {
    const startIndex = (currentPage - 1) * ITEMS_PER_PAGE;
    const endIndex = startIndex + ITEMS_PER_PAGE;
    const pageSnapshots = filteredSnapshots.slice(startIndex, endIndex);
    
    if (filteredSnapshots.length === 0) {
        snapshotGrid.innerHTML = '';
        emptyState.style.display = 'block';
        document.getElementById('pagination').style.display = 'none';
        return;
    }
    
    emptyState.style.display = 'none';
    document.getElementById('pagination').style.display = 'block';
    
    snapshotGrid.innerHTML = pageSnapshots.map((snapshot, index) => {
        const globalIndex = startIndex + index;
        const isSelected = selectedSnapshots.has(snapshot.id);
        const violationClass = snapshot.violation ? 'yes' : 'no';
        const confidencePercent = (snapshot.confidence * 100).toFixed(1);
        
        return `
            <div class="snapshot-card ${isSelected ? 'selected' : ''}" 
                 data-id="${snapshot.id}" 
                 data-index="${globalIndex}"
                 onclick="handleCardClick(event, ${globalIndex})">
                <div class="snapshot-overlay">
                    <div class="checkbox-wrapper ${isSelected ? 'checked' : ''}" 
                         onclick="event.stopPropagation(); toggleSelection('${snapshot.id}')">
                        <i class="fas fa-check"></i>
                    </div>
                    <span class="violation-badge ${violationClass}">
                        ${snapshot.violation ? '🚨 Violation' : '✓ Safe'}
                    </span>
                </div>
                <img class="snapshot-image" src="${snapshot.path}" alt="${snapshot.class}" 
                     onerror="this.src='data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 width=%22280%22 height=%22200%22><rect fill=%22%231a1a2e%22 width=%22100%%22 height=%22100%%22/><text fill=%22%2394a3b8%22 x=%2250%%22 y=%2250%%22 text-anchor=%22middle%22>No Image</text></svg>'">
                <div class="snapshot-info">
                    <div class="snapshot-class">${snapshot.class}</div>
                    <div class="snapshot-meta">
                        <span class="snapshot-time">${formatDate(snapshot.timestamp)}</span>
                        <span class="snapshot-confidence">${confidencePercent}%</span>
                    </div>
                </div>
            </div>
        `;
    }).join('');
    
    updatePagination();
}

// Handle Card Click
function handleCardClick(event, index) {
    if (event.shiftKey) {
        // Shift+Click for range selection
        toggleRangeSelection(index);
    } else {
        // Regular click opens lightbox
        openLightbox(index);
    }
}

// Toggle Selection
function toggleSelection(id) {
    if (selectedSnapshots.has(id)) {
        selectedSnapshots.delete(id);
    } else {
        selectedSnapshots.add(id);
    }
    updateSelectionUI();
}

function selectAllSnapshots() {
    filteredSnapshots.forEach(s => selectedSnapshots.add(s.id));
    updateSelectionUI();
}

function deselectAllSnapshots() {
    selectedSnapshots.clear();
    updateSelectionUI();
}

function toggleSelectionOnHovered() {
    // Toggle selection of first visible snapshot
    if (filteredSnapshots.length > 0) {
        const firstSnapshot = filteredSnapshots[0];
        toggleSelection(firstSnapshot.id);
    }
}

function toggleRangeSelection(endIndex) {
    if (selectedSnapshots.size === 0) {
        toggleSelection(filteredSnapshots[endIndex].id);
        return;
    }
    
    // Find first selected
    const selectedIds = Array.from(selectedSnapshots);
    const firstSelectedIndex = filteredSnapshots.findIndex(s => s.id === selectedIds[0]);
    
    // Select range
    const start = Math.min(firstSelectedIndex, endIndex);
    const end = Math.max(firstSelectedIndex, endIndex);
    
    for (let i = start; i <= end; i++) {
        selectedSnapshots.add(filteredSnapshots[i].id);
    }
    updateSelectionUI();
}

function updateSelectionUI() {
    // Update card visuals
    document.querySelectorAll('.snapshot-card').forEach(card => {
        const id = card.dataset.id;
        const checkbox = card.querySelector('.checkbox-wrapper');
        if (selectedSnapshots.has(id)) {
            card.classList.add('selected');
            checkbox.classList.add('checked');
        } else {
            card.classList.remove('selected');
            checkbox.classList.remove('checked');
        }
    });
    
    updateSelectedCount();
    downloadSelectedBtn.disabled = selectedSnapshots.size === 0;
    deleteSelectedBtn.disabled = selectedSnapshots.size === 0;
}

function updateSelectedCount() {
    selectedCountEl.textContent = selectedSnapshots.size;
}

// Set View Mode
function setView(view) {
    if (view === 'grid') {
        snapshotGrid.classList.remove('list-view');
        gridViewBtn.classList.add('active');
        listViewBtn.classList.remove('active');
    } else {
        snapshotGrid.classList.add('list-view');
        listViewBtn.classList.add('active');
        gridViewBtn.classList.remove('active');
    }
}

// Lightbox Functions
function openLightbox(index) {
    currentLightboxIndex = index;
    const snapshot = filteredSnapshots[index];
    
    lightboxImage.src = snapshot.path;
    lightboxTitle.textContent = `${snapshot.class} - ${snapshot.violation ? 'Violation' : 'Safe'}`;
    lightboxDetails.innerHTML = `
        <p><strong>Time:</strong> ${formatDateTime(snapshot.timestamp)}</p>
        <p><strong>Confidence:</strong> ${(snapshot.confidence * 100).toFixed(1)}%</p>
        <p><strong>File:</strong> ${snapshot.filename}</p>
    `;
    
    lightbox.classList.add('active');
    document.body.style.overflow = 'hidden';
}

function closeLightbox() {
    lightbox.classList.remove('active');
    document.body.style.overflow = '';
}

function navigateLightbox(direction) {
    currentLightboxIndex += direction;
    
    if (currentLightboxIndex < 0) {
        currentLightboxIndex = filteredSnapshots.length - 1;
    } else if (currentLightboxIndex >= filteredSnapshots.length) {
        currentLightboxIndex = 0;
    }
    
    openLightbox(currentLightboxIndex);
}

function downloadCurrentSnapshot() {
    const snapshot = filteredSnapshots[currentLightboxIndex];
    downloadSnapshot(snapshot);
}

function deleteCurrentSnapshot() {
    const snapshot = filteredSnapshots[currentLightboxIndex];
    if (confirm(`Delete this snapshot?\n\n${snapshot.filename}`)) {
        deleteSnapshot(snapshot.id);
    }
}

// Download Functions
function downloadSelected() {
    selectedSnapshots.forEach(id => {
        const snapshot = snapshots.find(s => s.id === id);
        if (snapshot) {
            downloadSnapshot(snapshot);
        }
    });
}

function downloadSnapshot(snapshot) {
    const link = document.createElement('a');
    link.href = snapshot.path;
    link.download = snapshot.filename;
    link.target = '_blank';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    showToast('Download started', 'info');
}

// Delete Functions
async function deleteSelected() {
    const count = selectedSnapshots.size;
    if (confirm(`Delete ${count} selected snapshot${count > 1 ? 's' : ''}?`)) {
        for (const id of selectedSnapshots) {
            await deleteSnapshot(id);
        }
        selectedSnapshots.clear();
        updateSelectionUI();
        showToast(`${count} snapshot${count > 1 ? 's' : ''} deleted`, 'success');
    }
}

async function deleteSnapshot(id) {
    try {
        const response = await fetch('/api/snapshots/delete', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ id })
        });
        
        if (response.ok) {
            // Remove from local data
            snapshots = snapshots.filter(s => s.id !== id);
            filteredSnapshots = filteredSnapshots.filter(s => s.id !== id);
            updateStats();
            renderSnapshots();
        }
    } catch (error) {
        console.error('Error deleting snapshot:', error);
        // For demo, just remove locally
        snapshots = snapshots.filter(s => s.id !== id);
        filteredSnapshots = filteredSnapshots.filter(s => s.id !== id);
        updateStats();
        renderSnapshots();
    }
}

// Pagination
function updatePagination() {
    const totalPages = Math.ceil(filteredSnapshots.length / ITEMS_PER_PAGE);
    const pagination = document.getElementById('pagination');
    
    if (totalPages <= 1) {
        pagination.style.display = 'none';
        return;
    }
    
    pagination.style.display = 'block';
    
    const prevBtn = document.getElementById('prevPage');
    const nextBtn = document.getElementById('nextPage');
    
    prevBtn.classList.toggle('disabled', currentPage === 1);
    nextBtn.classList.toggle('disabled', currentPage === totalPages);
    
    // Update page numbers
    const pageList = pagination.querySelector('.pagination');
    let html = `
        <li class="page-item ${currentPage === 1 ? 'disabled' : ''}" id="prevPage">
            <a class="page-link" href="#" tabindex="-1">Previous</a>
        </li>
    `;
    
    for (let i = 1; i <= totalPages; i++) {
        html += `
            <li class="page-item ${i === currentPage ? 'active' : ''}">
                <a class="page-link" href="#">${i}</a>
            </li>
        `;
    }
    
    html += `
        <li class="page-item ${currentPage === totalPages ? 'disabled' : ''}" id="nextPage">
            <a class="page-link" href="#">Next</a>
        </li>
    `;
    
    pageList.innerHTML = html;
    
    // Add click handlers
    pageList.querySelectorAll('.page-link').forEach((link, index) => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const pageNum = parseInt(link.textContent);
            if (!isNaN(pageNum)) {
                currentPage = pageNum;
                renderSnapshots();
                window.scrollTo({ top: 0, behavior: 'smooth' });
            }
        });
    });
    
    document.getElementById('prevPage').addEventListener('click', (e) => {
        e.preventDefault();
        if (currentPage > 1) {
            currentPage--;
            renderSnapshots();
            window.scrollTo({ top: 0, behavior: 'smooth' });
        }
    });
    
    document.getElementById('nextPage').addEventListener('click', (e) => {
        e.preventDefault();
        if (currentPage < totalPages) {
            currentPage++;
            renderSnapshots();
            window.scrollTo({ top: 0, behavior: 'smooth' });
        }
    });
}

// Toast Notifications
function showToast(message, type = 'info') {
    const toast = document.getElementById('toast');
    toast.className = `toast ${type} show`;
    toast.querySelector('.toast-message').textContent = message;
    
    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}

// Help Modal
function showHelp() {
    alert(`Keyboard Shortcuts:

Space - Toggle selection
Ctrl+A - Select all
Ctrl+D - Deselect all
Delete - Delete selected
← → - Navigate lightbox
Esc - Close lightbox
? - Show this help`);
}

// Utility Functions
function formatDate(timestamp) {
    const date = new Date(timestamp);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

function formatDateTime(timestamp) {
    return new Date(timestamp).toLocaleString();
}

function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Make functions globally accessible
window.handleCardClick = handleCardClick;
window.toggleSelection = toggleSelection;

