// Bloginator Web UI JavaScript

// API base URL
const API_BASE = '/api';

// Global state
let currentIndexPath = '';
let currentOutlineData = null;
let currentDraftData = null;

// ===== Search Functionality =====
if (document.getElementById('search-form')) {
    document.getElementById('search-form').addEventListener('submit', async (e) => {
        e.preventDefault();

        const formData = new FormData(e.target);
        const query = formData.get('query');
        const indexPath = formData.get('index_path');
        const nResults = parseInt(formData.get('n_results'));

        currentIndexPath = indexPath;

        // Show loading
        document.getElementById('search-results').classList.add('hidden');
        document.getElementById('search-error').classList.add('hidden');
        document.getElementById('search-loading').classList.remove('hidden');

        try {
            const response = await fetch(`${API_BASE}/documents/search`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({query, index_path: indexPath, n_results: nResults})
            });

            if (!response.ok) throw new Error('Search failed');

            const data = await response.json();
            displaySearchResults(data.results);
        } catch (error) {
            showError('search-error', error.message);
        } finally {
            document.getElementById('search-loading').classList.add('hidden');
        }
    });
}

function displaySearchResults(results) {
    const container = document.getElementById('results-list');
    container.innerHTML = '';

    if (results.length === 0) {
        container.innerHTML = '<p class="text-gray-500">No results found.</p>';
    } else {
        results.forEach((result, index) => {
            const card = document.createElement('div');
            card.className = 'result-card bg-white border border-gray-200 rounded-lg p-4 hover:shadow-lg';
            card.innerHTML = `
                <div class="flex justify-between items-start mb-2">
                    <h3 class="text-lg font-medium text-gray-900">${result.filename}</h3>
                    <span class="text-sm text-gray-500">${(result.similarity_score * 100).toFixed(1)}% match</span>
                </div>
                <p class="text-sm text-gray-700">${result.content.substring(0, 300)}${result.content.length > 300 ? '...' : ''}</p>
            `;
            container.appendChild(card);
        });
    }

    document.getElementById('search-results').classList.remove('hidden');
}

// ===== Outline Generation =====
if (document.getElementById('outline-form')) {
    document.getElementById('outline-form').addEventListener('submit', async (e) => {
        e.preventDefault();

        const formData = new FormData(e.target);
        const title = formData.get('title');
        const keywords = formData.get('keywords').split(',').map(k => k.trim());
        const thesis = formData.get('thesis');
        const indexPath = formData.get('index_path');

        currentIndexPath = indexPath;

        try {
            const response = await fetch(`${API_BASE}/documents/outline/generate`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({title, keywords, thesis, index_path: indexPath})
            });

            if (!response.ok) throw new Error('Outline generation failed');

            const data = await response.json();
            currentOutlineData = data.outline;
            displayOutline(data.outline);
        } catch (error) {
            alert('Error: ' + error.message);
        }
    });
}

function displayOutline(outline) {
    const display = document.getElementById('outline-display');
    let html = `<h2 class="font-bold text-lg">${outline.title}</h2>`;

    if (outline.thesis) {
        html += `<p class="mt-2 text-sm italic">${outline.thesis}</p>`;
    }

    html += '<ul class="mt-4 space-y-2">';
    outline.sections.forEach(section => {
        html += `<li class="text-sm"><strong>${section.title}</strong>`;
        if (section.description) {
            html += `: ${section.description}`;
        }
        html += '</li>';
    });
    html += '</ul>';

    display.innerHTML = html;
    document.getElementById('outline-result').classList.remove('hidden');
}

// ===== Draft Generation =====
if (document.getElementById('draft-form')) {
    document.getElementById('draft-form').addEventListener('submit', async (e) => {
        e.preventDefault();

        const formData = new FormData(e.target);
        const validateSafety = formData.get('validate_safety') === 'on';
        const scoreVoice = formData.get('score_voice') === 'on';

        if (!currentOutlineData) {
            alert('Please generate an outline first');
            return;
        }

        try {
            const response = await fetch(`${API_BASE}/documents/draft/generate`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    outline_json: JSON.stringify(currentOutlineData),
                    index_path: currentIndexPath,
                    validate_safety: validateSafety,
                    score_voice: scoreVoice
                })
            });

            if (!response.ok) throw new Error('Draft generation failed');

            const data = await response.json();
            currentDraftData = data.draft;
            displayDraft(data.draft);
        } catch (error) {
            alert('Error: ' + error.message);
        }
    });
}

function displayDraft(draft) {
    const display = document.getElementById('draft-display');
    let html = `<h1>${draft.title}</h1>`;

    if (draft.thesis) {
        html += `<p class="italic">${draft.thesis}</p>`;
    }

    draft.sections.forEach(section => {
        html += `<h2>${section.title}</h2>`;
        html += `<p>${section.content}</p>`;
    });

    display.innerHTML = html;
    document.getElementById('draft-result').classList.remove('hidden');
}

// ===== Utilities =====
function showError(elementId, message) {
    const errorEl = document.getElementById(elementId);
    const messageEl = document.getElementById('error-message');
    if (messageEl) messageEl.textContent = message;
    errorEl.classList.remove('hidden');
}

function hideError(elementId) {
    document.getElementById(elementId).classList.add('hidden');
}

// File upload handling
if (document.getElementById('upload-form')) {
    document.getElementById('upload-form').addEventListener('submit', async (e) => {
        e.preventDefault();

        const formData = new FormData(e.target);

        try {
            const response = await fetch(`${API_BASE}/corpus/upload`, {
                method: 'POST',
                body: formData
            });

            if (!response.ok) throw new Error('Upload failed');

            const data = await response.json();
            const resultEl = document.getElementById('upload-result');
            document.getElementById('upload-result-text').textContent =
                `Successfully extracted ${data.extracted_count} documents.`;
            resultEl.classList.remove('hidden');
        } catch (error) {
            alert('Error: ' + error.message);
        }
    });
}

// Index creation
if (document.getElementById('index-form')) {
    document.getElementById('index-form').addEventListener('submit', async (e) => {
        e.preventDefault();

        const formData = new FormData(e.target);
        const corpusPath = formData.get('corpus_path');
        const indexPath = formData.get('index_path');

        try {
            const response = await fetch(`${API_BASE}/corpus/index/create`, {
                method: 'POST',
                headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                body: new URLSearchParams({corpus_path: corpusPath, index_path: indexPath})
            });

            if (!response.ok) throw new Error('Index creation failed');

            const data = await response.json();
            const resultEl = document.getElementById('index-result');
            document.getElementById('index-result-text').textContent =
                `Indexed ${data.total_documents} documents with ${data.total_chunks} chunks.`;
            resultEl.classList.remove('hidden');
        } catch (error) {
            alert('Error: ' + error.message);
        }
    });
}

console.log('Bloginator Web UI loaded');
