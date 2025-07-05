// Summary Display Server JavaScript
let currentPage = 1;
let totalPages = 1;
let currentSearch = '';

// Load initial data
document.addEventListener('DOMContentLoaded', function() {
    loadStatus();
    loadSummaries();
});

function loadStatus() {
    fetch('/api/status')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                document.getElementById('total-summaries').textContent = data.data.total_summaries || 0;
                document.getElementById('processing-status').textContent = data.data.processing_status || 'Idle';
                document.getElementById('llm-model').textContent = data.data.llm_model || 'Unknown';
            }
        })
        .catch(error => {
            console.error('Error loading status:', error);
        });
}

function loadSummaries(page = 1, search = '') {
    const container = document.getElementById('summaries-container');
    container.innerHTML = '<div class="loading">Loading summaries...</div>';
    
    const params = new URLSearchParams({
        page: page,
        limit: 12
    });
    
    if (search) {
        params.append('search', search);
    }
    
    fetch(`/api/summaries?${params}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                displaySummaries(data.data.summaries);
                updatePagination(data.data.total_pages, page);
                currentPage = page;
                totalPages = data.data.total_pages;
                currentSearch = search;
            } else {
                container.innerHTML = `<div class="error">Error: ${data.error}</div>`;
            }
        })
        .catch(error => {
            console.error('Error loading summaries:', error);
            container.innerHTML = '<div class="error">Failed to load summaries</div>';
        });
}

function displaySummaries(summaries) {
    const container = document.getElementById('summaries-container');
    
    if (summaries.length === 0) {
        container.innerHTML = '<div class="loading">No summaries found</div>';
        return;
    }
    
    const grid = document.createElement('div');
    grid.className = 'summaries-grid';
    
    summaries.forEach(summary => {
        const card = document.createElement('div');
        card.className = 'summary-card';
        
        const tags = summary.tags ? summary.tags.split(',').map(tag => tag.trim()) : [];
        const tagHtml = tags.map(tag => `<span class="tag">${tag}</span>`).join('');
        
        card.innerHTML = `
            <div class="card-header">
                <div class="card-title">${summary.title || 'Untitled'}</div>
                <a href="${summary.url}" target="_blank" class="card-url">${summary.url}</a>
            </div>
            <div class="card-meta">
                <span>${new Date(summary.created_at).toLocaleDateString()}</span>
                <span>${summary.word_count || 0} words</span>
            </div>
            <div class="card-content">${summary.summary || 'No summary available'}</div>
            <div class="card-tags">${tagHtml}</div>
        `;
        
        grid.appendChild(card);
    });
    
    container.innerHTML = '';
    container.appendChild(grid);
}

function updatePagination(totalPages, currentPage) {
    const pagination = document.getElementById('pagination');
    const prevBtn = document.getElementById('prev-btn');
    const nextBtn = document.getElementById('next-btn');
    const pageInfo = document.getElementById('page-info');
    
    if (totalPages <= 1) {
        pagination.style.display = 'none';
        return;
    }
    
    pagination.style.display = 'flex';
    prevBtn.disabled = currentPage <= 1;
    nextBtn.disabled = currentPage >= totalPages;
    pageInfo.textContent = `Page ${currentPage} of ${totalPages}`;
}

function changePage(delta) {
    const newPage = currentPage + delta;
    if (newPage >= 1 && newPage <= totalPages) {
        loadSummaries(newPage, currentSearch);
    }
}

function searchSummaries() {
    const searchInput = document.getElementById('search-input');
    const searchTerm = searchInput.value.trim();
    loadSummaries(1, searchTerm);
}

function processAllContent() {
    const btn = event.target;
    const originalText = btn.textContent;
    btn.textContent = 'Processing...';
    btn.disabled = true;
    
    fetch('/api/process-all', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('Processing started successfully!');
            setTimeout(() => {
                loadStatus();
                loadSummaries();
            }, 2000);
        } else {
            alert(`Error: ${data.error}`);
        }
    })
    .catch(error => {
        console.error('Error processing content:', error);
        alert('Error processing content');
    })
    .finally(() => {
        btn.textContent = originalText;
        btn.disabled = false;
    });
} 