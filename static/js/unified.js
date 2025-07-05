// Unified Web Crawler & AI Summarization JavaScript

// Global variables
let currentTab = 'crawler';
let summaryCurrentPage = 1;
let summaryTotalPages = 1;
let dataCurrentPage = 1;
let dataTotalPages = 1;
let autoRefreshInterval = null;

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    showTab('crawler');
    loadInitialData();
    setupAutoRefresh();
});

// ==================== TAB MANAGEMENT ====================

function showTab(tabName) {
    // Hide all tabs
    const tabs = document.querySelectorAll('.tab-content');
    tabs.forEach(tab => tab.classList.remove('active'));
    
    // Remove active class from all buttons
    const buttons = document.querySelectorAll('.tab-button');
    buttons.forEach(button => button.classList.remove('active'));
    
    // Show selected tab
    const selectedTab = document.getElementById(tabName + '-tab');
    if (selectedTab) {
        selectedTab.classList.add('active');
    }
    
    // Activate selected button
    const selectedButton = document.querySelector(`.tab-button[onclick="showTab('${tabName}')"]`);
    if (selectedButton) {
        selectedButton.classList.add('active');
    }
    
    currentTab = tabName;
    
    // Load data for the selected tab
    switch(tabName) {
        case 'crawler':
            loadCrawlerData();
            break;
        case 'processing':
            loadProcessingData();
            break;
        case 'summaries':
            loadSummaries();
            break;
        case 'data':
            loadCrawledData();
            break;
        case 'stats':
            loadSystemStats();
            break;
    }
}

// ==================== UTILITY FUNCTIONS ====================

function showMessage(message, type = 'success') {
    const container = document.getElementById('message-container');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}`;
    messageDiv.textContent = message;
    
    container.appendChild(messageDiv);
    
    // Remove message after 5 seconds
    setTimeout(() => {
        if (messageDiv.parentNode) {
            messageDiv.parentNode.removeChild(messageDiv);
        }
    }, 5000);
}

function formatDateTime(dateString) {
    if (!dateString) return 'N/A';
    try {
        return new Date(dateString).toLocaleString();
    } catch (e) {
        return 'N/A';
    }
}

function formatNumber(num) {
    if (num === null || num === undefined) return '-';
    return num.toLocaleString();
}

// ==================== CRAWLER FUNCTIONALITY ====================

function loadCrawlerData() {
    loadQueueStats();
    loadPendingUrls();
}

function loadQueueStats() {
    fetch('/api/crawler/queue-stats')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const stats = data.data;
                document.getElementById('pending-count').textContent = formatNumber(stats.pending_urls || 0);
                document.getElementById('completed-count').textContent = formatNumber(stats.completed_urls || 0);
                document.getElementById('failed-count').textContent = formatNumber(stats.failed_urls || 0);
            }
        })
        .catch(error => {
            console.error('Error loading queue stats:', error);
        });
    
    fetch('/api/crawler/worker-stats')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const stats = data.data;
                document.getElementById('worker-count').textContent = formatNumber(stats.running_workers || 0);
            }
        })
        .catch(error => {
            console.error('Error loading worker stats:', error);
        });
}

function loadPendingUrls() {
    fetch('/api/crawler/pending-urls?limit=10')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const container = document.getElementById('pending-urls');
                const urls = data.data.pending_urls || [];
                
                if (urls.length === 0) {
                    container.innerHTML = '<p>No pending URLs</p>';
                    return;
                }
                
                let html = '';
                urls.forEach(url => {
                    html += `<div class="url-item">${url}</div>`;
                });
                
                container.innerHTML = html;
            }
        })
        .catch(error => {
            console.error('Error loading pending URLs:', error);
            document.getElementById('pending-urls').innerHTML = '<p>Error loading pending URLs</p>';
        });
}

function addUrlToQueue() {
    const urlInput = document.getElementById('url-input');
    const prioritySelect = document.getElementById('priority-select');
    const url = urlInput.value.trim();
    
    if (!url) {
        showMessage('Please enter a URL', 'error');
        return;
    }
    
    if (!url.startsWith('http://') && !url.startsWith('https://')) {
        showMessage('Please enter a valid URL starting with http:// or https://', 'error');
        return;
    }
    
    const priority = parseInt(prioritySelect.value);
    
    fetch('/api/crawler/add-url', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            url: url,
            priority: priority
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showMessage(`Successfully added ${url} to queue`);
            urlInput.value = '';
            loadCrawlerData();
        } else {
            showMessage(`Error adding URL: ${data.error}`, 'error');
        }
    })
    .catch(error => {
        console.error('Error adding URL:', error);
        showMessage('Error adding URL to queue', 'error');
    });
}

function startWorkers() {
    fetch('/api/crawler/start-workers', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ num_workers: 2 })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showMessage('Workers started successfully');
            loadCrawlerData();
        } else {
            showMessage(`Error starting workers: ${data.error}`, 'error');
        }
    })
    .catch(error => {
        console.error('Error starting workers:', error);
        showMessage('Error starting workers', 'error');
    });
}

function stopWorkers() {
    fetch('/api/crawler/stop-workers', {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showMessage('Workers stopped successfully');
            loadCrawlerData();
        } else {
            showMessage(`Error stopping workers: ${data.error}`, 'error');
        }
    })
    .catch(error => {
        console.error('Error stopping workers:', error);
        showMessage('Error stopping workers', 'error');
    });
}

function clearQueue() {
    if (!confirm('Are you sure you want to clear the queue?')) {
        return;
    }
    
    fetch('/api/crawler/clear-queue', {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showMessage('Queue cleared successfully');
            loadCrawlerData();
        } else {
            showMessage(`Error clearing queue: ${data.error}`, 'error');
        }
    })
    .catch(error => {
        console.error('Error clearing queue:', error);
        showMessage('Error clearing queue', 'error');
    });
}

// ==================== PROCESSING FUNCTIONALITY ====================

function loadProcessingData() {
    loadProcessingStats();
}

function loadProcessingStats() {
    fetch('/api/llm/status')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const stats = data.data;
                document.getElementById('unprocessed-count').textContent = formatNumber(stats.unprocessed_count || 0);
                document.getElementById('processed-count').textContent = formatNumber(stats.processed_count || 0);
                document.getElementById('llm-status').textContent = stats.local_llm_available ? 'Online' : 'Offline';
                document.getElementById('processing-status').textContent = stats.processing_in_progress ? 'Processing' : 'Idle';
            }
        })
        .catch(error => {
            console.error('Error loading processing stats:', error);
        });
}

function processAllContent() {
    if (!confirm('This will process all unprocessed content. This may take a long time. Continue?')) {
        return;
    }
    
    fetch('/api/llm/process-all', {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showMessage('Processing started in background');
            loadProcessingStats();
        } else {
            showMessage(`Error starting processing: ${data.error}`, 'error');
        }
    })
    .catch(error => {
        console.error('Error starting processing:', error);
        showMessage('Error starting processing', 'error');
    });
}

function refreshProcessingStats() {
    loadProcessingStats();
    showMessage('Processing stats refreshed');
}

// ==================== SUMMARIES FUNCTIONALITY ====================

function loadSummaries(page = 1, search = '') {
    const container = document.getElementById('summaries-container');
    container.innerHTML = '<div class="loading">Loading summaries...</div>';
    
    let url = `/api/summaries?page=${page}&per_page=12`;
    if (search) {
        url += `&search=${encodeURIComponent(search)}`;
    }
    
    fetch(url)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const summaries = data.data.summaries || [];
                const pagination = data.data.pagination || {};
                
                summaryCurrentPage = pagination.page || 1;
                summaryTotalPages = pagination.total_pages || 1;
                
                if (summaries.length === 0) {
                    container.innerHTML = '<p>No summaries found</p>';
                    return;
                }
                
                let html = '';
                summaries.forEach(summary => {
                    html += `
                        <div class="summary-card">
                            <div class="summary-title">${summary.title || 'Untitled'}</div>
                            <div class="summary-url">${summary.url}</div>
                            <div class="summary-content">${summary.summary || 'No summary available'}</div>
                            <div class="summary-meta">
                                <span>Words: ${summary.word_count || 0}</span>
                                <span>Sentiment: ${summary.sentiment || 'Unknown'}</span>
                                <span>${formatDateTime(summary.created_at)}</span>
                            </div>
                        </div>
                    `;
                });
                
                container.innerHTML = html;
                updateSummaryPagination();
            } else {
                container.innerHTML = '<p>Error loading summaries</p>';
            }
        })
        .catch(error => {
            console.error('Error loading summaries:', error);
            container.innerHTML = '<p>Error loading summaries</p>';
        });
}

function searchSummaries() {
    const searchInput = document.getElementById('search-input');
    const searchTerm = searchInput.value.trim();
    loadSummaries(1, searchTerm);
}

function updateSummaryPagination() {
    const pagination = document.getElementById('pagination');
    const pageInfo = document.getElementById('page-info');
    const prevBtn = document.getElementById('prev-btn');
    const nextBtn = document.getElementById('next-btn');
    
    pageInfo.textContent = `Page ${summaryCurrentPage} of ${summaryTotalPages}`;
    prevBtn.disabled = summaryCurrentPage <= 1;
    nextBtn.disabled = summaryCurrentPage >= summaryTotalPages;
    
    pagination.style.display = summaryTotalPages > 1 ? 'flex' : 'none';
}

function changePage(direction) {
    const newPage = summaryCurrentPage + direction;
    if (newPage >= 1 && newPage <= summaryTotalPages) {
        const searchTerm = document.getElementById('search-input').value.trim();
        loadSummaries(newPage, searchTerm);
    }
}

// ==================== DATA FUNCTIONALITY ====================

function loadCrawledData(page = 1) {
    const container = document.getElementById('data-container');
    container.innerHTML = '<div class="loading">Loading data...</div>';
    
    const offset = (page - 1) * 20;
    
    fetch(`/api/crawler/crawled-data?limit=20&offset=${offset}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const crawledData = data.data.crawled_data || [];
                const totalCount = data.data.total_count || 0;
                
                dataTotalPages = Math.ceil(totalCount / 20);
                dataCurrentPage = page;
                
                if (crawledData.length === 0) {
                    container.innerHTML = '<p>No crawled data found</p>';
                    return;
                }
                
                let html = '';
                crawledData.forEach(item => {
                    html += `
                        <div class="data-item">
                            <div class="data-url">${item.url}</div>
                            <div class="data-title">${item.title || 'Untitled'}</div>
                            <div class="data-content">${item.text_content || 'No content available'}</div>
                            <div class="data-meta">
                                <small>Created: ${formatDateTime(item.created_at)}</small>
                            </div>
                        </div>
                    `;
                });
                
                container.innerHTML = html;
                updateDataPagination();
            } else {
                container.innerHTML = '<p>Error loading data</p>';
            }
        })
        .catch(error => {
            console.error('Error loading crawled data:', error);
            container.innerHTML = '<p>Error loading data</p>';
        });
}

function updateDataPagination() {
    const pagination = document.getElementById('data-pagination');
    const pageInfo = document.getElementById('data-page-info');
    const prevBtn = document.getElementById('data-prev-btn');
    const nextBtn = document.getElementById('data-next-btn');
    
    pageInfo.textContent = `Page ${dataCurrentPage} of ${dataTotalPages}`;
    prevBtn.disabled = dataCurrentPage <= 1;
    nextBtn.disabled = dataCurrentPage >= dataTotalPages;
    
    pagination.style.display = dataTotalPages > 1 ? 'flex' : 'none';
}

function changeDataPage(direction) {
    const newPage = dataCurrentPage + direction;
    if (newPage >= 1 && newPage <= dataTotalPages) {
        loadCrawledData(newPage);
    }
}

// ==================== STATISTICS FUNCTIONALITY ====================

function loadSystemStats() {
    fetch('/api/unified-stats')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const stats = data.data;
                
                // Update overall stats
                document.getElementById('total-urls').textContent = formatNumber(stats.mongodb.web_content_count || 0);
                document.getElementById('total-summaries').textContent = formatNumber(stats.mongodb.summaries_count || 0);
                document.getElementById('redis-queue').textContent = formatNumber(stats.redis.queue_length || 0);
                
                // Update system health
                updateSystemHealth(stats);
            }
        })
        .catch(error => {
            console.error('Error loading system stats:', error);
        });
    
    // Load health check
    fetch('/api/health')
        .then(response => response.json())
        .then(data => {
            document.getElementById('system-health').textContent = data.status || 'Unknown';
        })
        .catch(error => {
            console.error('Error loading health check:', error);
        });
}

function updateSystemHealth(stats) {
    const healthContainer = document.getElementById('service-health');
    
    const services = [
        { name: 'MongoDB', healthy: stats.mongodb && Object.keys(stats.mongodb).length > 0 },
        { name: 'Redis', healthy: stats.redis && stats.redis.queue_length !== undefined },
        { name: 'LLM Processing', healthy: stats.llm_processing && stats.llm_processing.local_llm_available },
        { name: 'Crawler', healthy: stats.crawler && Object.keys(stats.crawler).length > 0 }
    ];
    
    let html = '';
    services.forEach(service => {
        const statusClass = service.healthy ? 'healthy' : 'unhealthy';
        const statusText = service.healthy ? '✅ Healthy' : '❌ Unhealthy';
        
        html += `
            <div class="health-item">
                <h4>${service.name}</h4>
                <div class="health-status ${statusClass}">${statusText}</div>
            </div>
        `;
    });
    
    healthContainer.innerHTML = html;
}

// ==================== AUTO REFRESH ====================

function setupAutoRefresh() {
    // Auto refresh every 30 seconds for active tab
    autoRefreshInterval = setInterval(() => {
        if (document.visibilityState === 'visible') {
            switch(currentTab) {
                case 'crawler':
                    loadCrawlerData();
                    break;
                case 'processing':
                    loadProcessingData();
                    break;
                case 'stats':
                    loadSystemStats();
                    break;
            }
        }
    }, 30000);
}

function loadInitialData() {
    loadCrawlerData();
}

// ==================== KEYBOARD SHORTCUTS ====================

document.addEventListener('keydown', function(e) {
    // Ctrl/Cmd + number keys to switch tabs
    if ((e.ctrlKey || e.metaKey) && e.key >= '1' && e.key <= '5') {
        e.preventDefault();
        const tabs = ['crawler', 'processing', 'summaries', 'data', 'stats'];
        const tabIndex = parseInt(e.key) - 1;
        if (tabs[tabIndex]) {
            showTab(tabs[tabIndex]);
        }
    }
});

// ==================== CLEANUP ====================

window.addEventListener('beforeunload', function() {
    if (autoRefreshInterval) {
        clearInterval(autoRefreshInterval);
    }
}); 