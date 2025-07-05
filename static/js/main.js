// Main JavaScript for Queue-Based Web Crawler
let autoRefreshInterval;
let currentPage = 1;
let totalPages = 1;
let currentSearch = '';

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    // Set up auto-refresh checkbox
    document.getElementById('auto-refresh').addEventListener('change', function() {
        if (this.checked && document.querySelector('.nav-tabs a.active').getAttribute('href') === '#status') {
            startAutoRefresh();
        } else {
            stopAutoRefresh();
        }
    });
    
    // Initial load
    refreshQueueStatus();
    refreshWorkerStatus();
    
    // Load chart on page load and every 2 minutes
    loadQueueTrendChart();
    setInterval(loadQueueTrendChart, 120000);
    
    // Auto-refresh Redis stats every 2 seconds if on status tab
    setInterval(function() {
        if (document.getElementById('status-tab').style.display !== 'none') {
            updateRedisQueueStats();
        }
    }, 2000);
});

// Tab Management
function showTab(tabName, event) {
    event.preventDefault();
    
    // Hide all tabs
    document.querySelectorAll('[id$="-tab"]').forEach(tab => {
        tab.style.display = 'none';
    });
    
    // Remove active class from all tab links
    document.querySelectorAll('.nav-tabs a').forEach(link => {
        link.classList.remove('active');
    });
    
    // Show selected tab
    document.getElementById(tabName + '-tab').style.display = 'block';
    
    // Add active class to clicked link
    event.target.classList.add('active');
    
    // Handle tab-specific actions
    if (tabName === 'status') {
        startAutoRefresh();
        setTimeout(() => {
            refreshQueueStatus();
            refreshWorkerStatus();
        }, 100);
    } else {
        stopAutoRefresh();
    }
}

// URL Management
function addUrlToQueue() {
    const url = document.getElementById('url').value.trim();
    const priority = document.getElementById('priority').value;
    
    if (!url) {
        showMessage('Please enter a URL', 'error');
        return;
    }
    
    const addBtn = document.getElementById('add-url-btn');
    addBtn.disabled = true;
    addBtn.innerHTML = '<span class="loading"></span> Adding...';
    
    fetch('/api/add-url', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ url: url, priority: parseInt(priority) })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showMessage(data.message, 'success');
            document.getElementById('url').value = '';
        } else {
            showMessage(data.error || 'Error adding URL to queue', 'error');
        }
    })
    .catch(error => {
        console.error('Error adding URL to queue:', error);
        showMessage('Error adding URL to queue', 'error');
    })
    .finally(() => {
        addBtn.disabled = false;
        addBtn.innerHTML = '➕ Add to Queue';
    });
}

// Message Display
function showMessage(message, type) {
    const messageDiv = document.getElementById('queue-message');
    messageDiv.innerHTML = `<div class="${type}">${message}</div>`;
    setTimeout(() => {
        messageDiv.innerHTML = '';
    }, 5000);
}

// Queue Status Management
function refreshQueueStatus() {
    fetch('/api/queue-stats')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                updateQueueStats(data.data);
            }
        })
        .catch(error => console.error('Error refreshing queue status:', error));
    
    fetch('/api/database-stats')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                updateDatabaseStats(data.data);
            }
        })
        .catch(error => console.error('Error refreshing database stats:', error));
    
    fetch('/api/pending-urls')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                updatePendingUrls(data.data);
            }
        })
        .catch(error => console.error('Error fetching pending URLs:', error));
}

function updateQueueStats(stats) {
    document.getElementById('completed-urls').textContent = stats.completed_urls || 0;
    document.getElementById('failed-urls').textContent = stats.failed_urls || 0;
}

function updateDatabaseStats(stats) {
    document.getElementById('content-records').textContent = stats.content_records || 0;
    document.getElementById('total-visits').textContent = stats.total_visits || 0;
}

function updatePendingUrls(urls) {
    const container = document.getElementById('pending-urls-table');
    if (urls.length === 0) {
        container.innerHTML = '<p>No pending URLs in queue.</p>';
        return;
    }
    
    const table = `
        <table class="data-table">
            <thead>
                <tr>
                    <th>URL</th>
                    <th>Domain</th>
                    <th>Priority</th>
                </tr>
            </thead>
            <tbody>
                ${urls.map(urlString => {
                    try {
                        const url = new URL(urlString);
                        const domain = url.hostname;
                        return `
                            <tr>
                                <td><a href="${urlString}" target="_blank">${urlString}</a></td>
                                <td>${domain}</td>
                                <td>
                                    <span class="priority-medium">Normal</span>
                                </td>
                            </tr>
                        `;
                    } catch (e) {
                        return `
                            <tr>
                                <td><a href="${urlString}" target="_blank">${urlString}</a></td>
                                <td>Invalid URL</td>
                                <td>
                                    <span class="priority-medium">Normal</span>
                                </td>
                            </tr>
                        `;
                    }
                }).join('')}
            </tbody>
        </table>
    `;
    container.innerHTML = table;
}

function updateRedisQueueStats() {
    fetch('/queue/redis-status')
        .then(response => response.json())
        .then(data => {
            document.getElementById('redis-queue-length').textContent = data.queue_length;
            document.getElementById('redis-visited-count').textContent = data.visited_count;
        });
}

// Worker Management
function refreshWorkerStatus() {
    // Fetch both worker stats and detailed timing data
    Promise.all([
        fetch('/api/worker-stats', { 
            method: 'GET',
            signal: AbortSignal.timeout(5000)
        }),
        fetch('/api/worker-timing-details', { 
            method: 'GET',
            signal: AbortSignal.timeout(5000)
        })
    ])
    .then(responses => Promise.all(responses.map(r => r.json())))
    .then(([statsData, timingData]) => {
        if (statsData.success) {
            updateWorkerStats(statsData.data, timingData.success ? timingData.data : {});
        } else {
            console.error('Worker stats API error:', statsData.error);
            refreshWorkerStatusFallback();
        }
    })
    .catch(error => {
        console.error('Error refreshing worker status:', error);
        refreshWorkerStatusFallback();
    });
}

function refreshWorkerStatusFallback() {
    // Fallback to health endpoint for basic worker status
    fetch('/api/health', { 
        method: 'GET',
        signal: AbortSignal.timeout(3000) // 3 second timeout
    })
        .then(response => response.json())
        .then(data => {
            if (data.workers_running !== undefined) {
                document.getElementById('total-workers').textContent = '2'; // Default worker count
                document.getElementById('running-workers').textContent = data.workers_running ? '2' : '0';
                document.getElementById('system-status').textContent = data.workers_running ? 'Running' : 'Stopped';
                
                // Show basic worker info
                const container = document.getElementById('worker-details-display');
                container.innerHTML = `
                    <div class="worker-card ${data.workers_running ? 'running' : 'stopped'}">
                        <h4>Worker Status (Basic)</h4>
                        <p><strong>Status:</strong> ${data.workers_running ? '🟢 Running' : '🔴 Stopped'}</p>
                        <p><strong>Note:</strong> Detailed stats unavailable due to database lock</p>
                        <p><strong>Queue:</strong> ${data.queue_stats ? data.queue_stats.completed_urls : 'Unknown'} completed URLs</p>
                    </div>
                `;
            }
        })
        .catch(error => {
            console.error('Error with fallback worker status:', error);
            // Show error in UI
            document.getElementById('total-workers').textContent = 'Error';
            document.getElementById('running-workers').textContent = 'Error';
            document.getElementById('system-status').textContent = 'Error';
        });
}

function updateWorkerStats(stats, timingDetails = {}) {
    document.getElementById('total-workers').textContent = stats.total_workers || 0;
    document.getElementById('running-workers').textContent = Object.values(stats.workers || {}).filter(w => w.running).length;
    document.getElementById('system-status').textContent = stats.running ? 'Running' : 'Stopped';
    
    const container = document.getElementById('worker-details-display');
    const workerCards = Object.entries(stats.workers || {}).map(([id, worker]) => {
        const startedAt = worker.started_at ? new Date(parseFloat(worker.started_at) * 1000).toLocaleString() : 'N/A';
        
        // Enhanced step timings display with charts and detailed breakdown
        let stepTimingsHtml = '';
        if (worker.step_timings_summary && Object.keys(worker.step_timings_summary).length > 0) {
            // Create chart data for this worker
            const chartId = `timing-chart-${id}`;
            const chartData = Object.entries(worker.step_timings_summary);
            
            stepTimingsHtml = `
                <div class="timing-section">
                    <div class="timing-header">
                        <strong>📊 Step Timing Performance</strong>
                        <small>(Last 100 URLs processed)</small>
                    </div>
                    
                    <!-- Performance Summary Cards -->
                    <div class="timing-cards">
                        ${chartData.map(([step, stats]) => `
                            <div class="timing-card ${step}">
                                <div class="step-name">${step.charAt(0).toUpperCase() + step.slice(1)}</div>
                                <div class="avg-time">${stats.avg.toFixed(3)}s</div>
                                <div class="time-range">${stats.min.toFixed(3)}s - ${stats.max.toFixed(3)}s</div>
                                <div class="process-count">${stats.count} processed</div>
                                <div class="performance-indicator ${getPerformanceClass(step, stats.avg)}"></div>
                            </div>
                        `).join('')}
                    </div>
                    
                    <!-- Timing Chart -->
                    <div class="chart-container">
                        <canvas id="${chartId}" width="400" height="200"></canvas>
                    </div>
                    
                    <!-- Detailed Statistics Table -->
                    <div class="detailed-stats">
                        <table class="timing-table">
                            <thead>
                                <tr>
                                    <th>Processing Step</th>
                                    <th>Average</th>
                                    <th>Min</th>
                                    <th>Max</th>
                                    <th>Count</th>
                                    <th>Efficiency</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${chartData.map(([step, stats]) => {
                                    const efficiency = calculateEfficiency(step, stats.avg);
                                    return `
                                        <tr>
                                            <td><span class="step-icon ${step}"></span>${step.charAt(0).toUpperCase() + step.slice(1)}</td>
                                            <td class="time-value">${stats.avg.toFixed(3)}s</td>
                                            <td class="time-value">${stats.min.toFixed(3)}s</td>
                                            <td class="time-value">${stats.max.toFixed(3)}s</td>
                                            <td class="count-value">${stats.count}</td>
                                            <td><span class="efficiency ${efficiency.class}">${efficiency.label}</span></td>
                                        </tr>
                                    `;
                                }).join('')}
                            </tbody>
                        </table>
                    </div>
                </div>
            `;
            
            // Store chart data for later rendering
            setTimeout(() => renderTimingChart(chartId, chartData), 100);
        } else {
            stepTimingsHtml = '<div class="no-timing-data">⏱️ No timing data available yet</div>';
        }
        
        // Add recent URL processing details
        let recentUrlsHtml = '';
        const workerTimingData = timingDetails[id];
        if (workerTimingData && workerTimingData.recent_timings && workerTimingData.recent_timings.length > 0) {
            recentUrlsHtml = `
                <div class="recent-urls-section">
                    <div class="section-header">
                        <strong>🕒 Recent URL Processing</strong>
                        <small>(Last ${workerTimingData.recent_timings.length} URLs)</small>
                    </div>
                    <div class="recent-urls-list">
                        ${workerTimingData.recent_timings.map(urlData => {
                            const totalTime = urlData.total_time.toFixed(3);
                            const timeAgo = formatTimeAgo(urlData.timestamp);
                            const statusClass = urlData.error ? 'error' : 'success';
                            const domain = new URL(urlData.url).hostname;
                            
                            return `
                                <div class="recent-url-item ${statusClass}">
                                    <div class="url-header">
                                        <span class="url-domain">${domain}</span>
                                        <span class="url-status status-${statusClass}">${urlData.error ? 'Error' : 'Success'}</span>
                                        <span class="url-total-time">${totalTime}s</span>
                                    </div>
                                    <div class="url-timings">
                                        ${Object.entries(urlData.timings).map(([step, time]) => `
                                            <span class="step-timing ${step}">
                                                ${step}: ${time.toFixed(3)}s
                                            </span>
                                        `).join('')}
                                    </div>
                                    <div class="url-time">${timeAgo}</div>
                                    ${urlData.error ? `<div class="url-error">Error: ${urlData.error}</div>` : ''}
                                </div>
                            `;
                        }).join('')}
                    </div>
                </div>
            `;
        }
        
        return `
        <div class="worker-card ${worker.running ? 'running' : 'stopped'}">
            <div class="worker-header">
                <h4>🔧 Worker ${id}</h4>
                <div class="worker-status ${worker.running ? 'online' : 'offline'}">
                    ${worker.running ? '🟢 Running' : '🔴 Stopped'}
                </div>
            </div>
            
            <div class="worker-stats">
                <div class="stat-group">
                    <div class="stat-item">
                        <span class="stat-label">Processed URLs</span>
                        <span class="stat-value">${worker.processed_urls || 0}</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-label">Failed URLs</span>
                        <span class="stat-value failed">${worker.failed_urls || 0}</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-label">Success Rate</span>
                        <span class="stat-value">${calculateSuccessRate(worker.processed_urls, worker.failed_urls)}%</span>
                    </div>
                </div>
                
                <div class="worker-details">
                    <p><strong>Started:</strong> ${startedAt}</p>
                    <p><strong>Thread:</strong> ${worker.thread_alive ? '✅ Active' : '❌ Inactive'}</p>
                    <p><strong>Total Processed:</strong> ${worker.total_urls || 0} URLs</p>
                </div>
            </div>
            
            ${stepTimingsHtml}
            ${recentUrlsHtml}
        </div>
        `;
    }).join('');
    
    container.innerHTML = workerCards;
}

// Performance Analysis Functions
function getPerformanceClass(step, avgTime) {
    // Define performance thresholds for each step
    const thresholds = {
        fetch: { good: 2.0, warning: 5.0 },
        parse: { good: 0.1, warning: 0.5 },
        extract: { good: 0.2, warning: 1.0 },
        save: { good: 0.5, warning: 2.0 },
        add_links: { good: 0.1, warning: 0.5 }
    };
    
    const threshold = thresholds[step] || { good: 1.0, warning: 3.0 };
    
    if (avgTime <= threshold.good) return 'excellent';
    if (avgTime <= threshold.warning) return 'good';
    return 'needs-attention';
}

function calculateEfficiency(step, avgTime) {
    const performance = getPerformanceClass(step, avgTime);
    switch (performance) {
        case 'excellent': return { class: 'excellent', label: '🚀 Excellent' };
        case 'good': return { class: 'good', label: '👍 Good' };
        default: return { class: 'warning', label: '⚠️ Slow' };
    }
}

function calculateSuccessRate(processed, failed) {
    const total = (processed || 0) + (failed || 0);
    if (total === 0) return 100;
    return ((processed || 0) / total * 100).toFixed(1);
}

function formatTimeAgo(timestamp) {
    const now = Date.now() / 1000;
    const diff = now - timestamp;
    
    if (diff < 60) return `${Math.floor(diff)}s ago`;
    if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
    if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
    return `${Math.floor(diff / 86400)}d ago`;
}

// Chart Management
function renderTimingChart(chartId, chartData) {
    const canvas = document.getElementById(chartId);
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    const labels = chartData.map(([step]) => step.charAt(0).toUpperCase() + step.slice(1));
    const avgTimes = chartData.map(([, stats]) => stats.avg);
    const minTimes = chartData.map(([, stats]) => stats.min);
    const maxTimes = chartData.map(([, stats]) => stats.max);
    
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Average Time (s)',
                    data: avgTimes,
                    backgroundColor: 'rgba(102, 126, 234, 0.8)',
                    borderColor: 'rgba(102, 126, 234, 1)',
                    borderWidth: 1
                },
                {
                    label: 'Min Time (s)',
                    data: minTimes,
                    backgroundColor: 'rgba(46, 204, 113, 0.6)',
                    borderColor: 'rgba(46, 204, 113, 1)',
                    borderWidth: 1
                },
                {
                    label: 'Max Time (s)',
                    data: maxTimes,
                    backgroundColor: 'rgba(231, 76, 60, 0.6)',
                    borderColor: 'rgba(231, 76, 60, 1)',
                    borderWidth: 1
                }
            ]
        },
        options: {
            responsive: true,
            plugins: {
                title: {
                    display: true,
                    text: 'Step Processing Times'
                },
                legend: {
                    position: 'top'
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Time (seconds)'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Processing Steps'
                    }
                }
            }
        }
    });
}

// Chart.js for queue trend
let queueTrendChart;
function loadQueueTrendChart() {
    fetch('/queue/history')
        .then(res => res.json())
        .then(data => {
            const labels = data.map(d => new Date(d.timestamp * 1000).toLocaleTimeString());
            const values = data.map(d => d.queue_length);
            const ctx = document.getElementById('queueTrendChart').getContext('2d');
            if (queueTrendChart) queueTrendChart.destroy();
            queueTrendChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: labels,
                    datasets: [{ label: 'Queue Size', data: values, borderColor: '#667eea', fill: false }]
                },
                options: {
                    responsive: true,
                    plugins: { legend: { display: false } },
                    scales: { x: { display: true }, y: { beginAtZero: true } }
                }
            });
        });
}

// Auto-refresh Management
function startAutoRefresh() {
    if (autoRefreshInterval) {
        clearInterval(autoRefreshInterval);
    }
    autoRefreshInterval = setInterval(() => {
        if (document.getElementById('auto-refresh').checked) {
            // Check if status tab is active and refresh both queue and worker data
            if (document.getElementById('status-tab').style.display !== 'none') {
                refreshQueueStatus();
                refreshWorkerStatus();
            }
        }
    }, 2000);
}

function stopAutoRefresh() {
    if (autoRefreshInterval) {
        clearInterval(autoRefreshInterval);
        autoRefreshInterval = null;
    }
}

// Queue Actions
function clearQueue() {
    if (confirm('Are you sure you want to clear the queue? This will remove all pending URLs.')) {
        fetch('/api/clear-queue', { method: 'POST' })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showMessage('Queue cleared successfully', 'success');
                    refreshQueueStatus();
                } else {
                    showMessage(data.error || 'Error clearing queue', 'error');
                }
            })
            .catch(error => {
                console.error('Error clearing queue:', error);
                showMessage('Error clearing queue', 'error');
            });
    }
}

// Worker Actions
function startWorkers() {
    fetch('/api/start-workers', { method: 'POST' })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showMessage('Workers started successfully', 'success');
                refreshWorkerStatus();
            } else {
                showMessage(data.error || 'Error starting workers', 'error');
            }
        })
        .catch(error => {
            console.error('Error starting workers:', error);
            showMessage('Error starting workers', 'error');
        });
}

function stopWorkers() {
    fetch('/api/stop-workers', { method: 'POST' })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showMessage('Workers stopped successfully', 'success');
                refreshWorkerStatus();
            } else {
                showMessage(data.error || 'Error stopping workers', 'error');
            }
        })
        .catch(error => {
            console.error('Error stopping workers:', error);
            showMessage('Error stopping workers', 'error');
        });
}

function addWorker() {
    fetch('/api/add-worker', { method: 'POST' })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showMessage('Worker added successfully', 'success');
                refreshWorkerStatus();
            } else {
                showMessage(data.error || 'Error adding worker', 'error');
            }
        })
        .catch(error => {
            console.error('Error adding worker:', error);
            showMessage('Error adding worker', 'error');
        });
} 