/**
 * O'Reilly Downloader - Frontend Application
 * Extracted and organized JavaScript
 */

const API = '';
let currentExpandedCard = null;
let selectedResultIndex = -1;
let defaultOutputDir = '';
const chaptersCache = {};

// ============================================
// Authentication
// ============================================

async function checkAuth() {
    try {
        const res = await fetch(`${API}/api/status`);
        const data = await res.json();
        const el = document.getElementById('auth-status');
        const loginBtn = document.getElementById('login-btn');
        const statusText = el.querySelector('.status-text');

        if (data.valid) {
            if (statusText) statusText.textContent = 'Session Valid';
            el.className = 'auth-status valid';
            loginBtn.classList.add('hidden');
        } else {
            if (statusText) statusText.textContent = data.reason || 'Invalid';
            el.className = 'auth-status invalid';
            loginBtn.classList.remove('hidden');
        }
    } catch (err) {
        console.error('Auth check failed:', err);
    }
}

// ============================================
// Cookie Modal
// ============================================

function showCookieModal() {
    document.getElementById('cookie-modal').classList.remove('hidden');
    document.getElementById('cookie-input').value = '';
    document.getElementById('cookie-error').classList.add('hidden');
    document.body.style.overflow = 'hidden';
}

function hideCookieModal() {
    document.getElementById('cookie-modal').classList.add('hidden');
    document.body.style.overflow = '';
}

async function saveCookies() {
    const input = document.getElementById('cookie-input').value.trim();
    const errorEl = document.getElementById('cookie-error');

    if (!input) {
        errorEl.textContent = 'Please paste your cookie JSON';
        errorEl.classList.remove('hidden');
        return;
    }

    let cookies;
    try {
        cookies = JSON.parse(input);
        if (typeof cookies !== 'object' || Array.isArray(cookies)) {
            throw new Error('Must be a JSON object');
        }
    } catch (e) {
        errorEl.textContent = 'Invalid JSON format: ' + e.message;
        errorEl.classList.remove('hidden');
        return;
    }

    try {
        const res = await fetch(`${API}/api/cookies`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(cookies)
        });
        const data = await res.json();

        if (data.error) {
            errorEl.textContent = data.error;
            errorEl.classList.remove('hidden');
            return;
        }

        hideCookieModal();
        checkAuth();
    } catch (err) {
        errorEl.textContent = 'Failed to save cookies';
        errorEl.classList.remove('hidden');
    }
}

// ============================================
// Settings
// ============================================

async function loadDefaultOutputDir() {
    try {
        const res = await fetch(`${API}/api/settings`);
        const data = await res.json();
        defaultOutputDir = data.output_dir;
    } catch (err) {
        console.error('Failed to load default output dir:', err);
    }
}

// ============================================
// Search
// ============================================

async function search(query) {
    const loader = document.getElementById('search-loader');
    const container = document.getElementById('search-results');

    loader.classList.remove('hidden');

    try {
        const res = await fetch(`${API}/api/search?q=${encodeURIComponent(query)}`);
        const data = await res.json();

        loader.classList.add('hidden');
        container.innerHTML = '';
        container.classList.remove('has-expanded');
        currentExpandedCard = null;
        selectedResultIndex = -1;

        if (!data.results || data.results.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <p>No books found for "${query}"</p>
                    <p class="text-sm text-gray-500 mt-2">Try a different search term or ISBN</p>
                </div>
            `;
            return;
        }

        for (const book of data.results) {
            const div = document.createElement('article');
            div.className = 'book-card';
            div.dataset.bookId = book.id;
            div.innerHTML = createBookCardHTML(book);

            setupBookCardEvents(div, book);
            container.appendChild(div);
        }
    } catch (err) {
        loader.classList.add('hidden');
        container.innerHTML = `
            <div class="empty-state error">
                <p>Search failed. Please try again.</p>
            </div>
        `;
    }
}

function createBookCardHTML(book) {
    return `
        <div class="book-summary">
            <img src="${book.cover_url}" alt="${book.title} cover" class="book-cover-thumb" loading="lazy">
            <div class="book-summary-info">
                <h3 class="book-title">${book.title}</h3>
                <p class="book-meta">${book.authors?.join(', ') || 'Unknown Author'}</p>
            </div>
            <svg class="expand-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M6 9l6 6 6-6"/>
            </svg>
        </div>
        <div class="book-expanded hidden">
            <button class="close-btn" aria-label="Close">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M18 6L6 18M6 6l12 12"/>
                </svg>
            </button>
            <div class="book-detail">
                <img class="book-cover-large" src="${book.cover_url}" alt="${book.title} cover">
                <div class="book-info">
                    <h2 class="book-detail-title">${book.title}</h2>
                    <p class="book-authors">by ${book.authors?.join(', ') || 'Unknown Author'}</p>
                    <p class="book-publisher"><span class="label">Publisher:</span> <span class="value loading-text">Loading...</span></p>
                    <p class="book-pages"><span class="label">Pages:</span> <span class="value loading-text">Loading...</span></p>
                    <div class="book-description loading-text">Loading description...</div>
                </div>
            </div>

            <div class="format-scope-section">
                <!-- Step 1: Format Selection -->
                <div class="format-selection">
                    <h4 class="section-label">
                        <span class="step-number">1</span>
                        Format
                    </h4>
                    <div class="format-options">
                        <label class="format-option" data-format="epub">
                            <input type="radio" name="format" value="epub" checked>
                            <span class="format-option-inner">
                                <svg class="format-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                                    <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/>
                                    <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>
                                </svg>
                                <span class="format-label">EPUB</span>
                            </span>
                        </label>
                        <label class="format-option" data-format="pdf">
                            <input type="radio" name="format" value="pdf">
                            <span class="format-option-inner">
                                <svg class="format-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                                    <polyline points="14 2 14 8 20 8"/>
                                    <line x1="16" y1="13" x2="8" y2="13"/>
                                    <line x1="16" y1="17" x2="8" y2="17"/>
                                </svg>
                                <span class="format-label">PDF</span>
                            </span>
                        </label>
                        <label class="format-option" data-format="markdown">
                            <input type="radio" name="format" value="markdown">
                            <span class="format-option-inner">
                                <svg class="format-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                                    <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/>
                                    <path d="M7 15V9l2.5 3L12 9v6"/>
                                    <path d="M17 9v6l-2-2"/>
                                </svg>
                                <span class="format-label">Markdown</span>
                            </span>
                        </label>
                        <label class="format-option" data-format="plaintext">
                            <input type="radio" name="format" value="plaintext">
                            <span class="format-option-inner">
                                <svg class="format-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                                    <polyline points="14 2 14 8 20 8"/>
                                    <line x1="16" y1="13" x2="8" y2="13"/>
                                </svg>
                                <span class="format-label">Plain Text</span>
                            </span>
                        </label>
                        <label class="format-option" data-format="json">
                            <input type="radio" name="format" value="json">
                            <span class="format-option-inner">
                                <svg class="format-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                                    <path d="M8 3H7a2 2 0 0 0-2 2v5a2 2 0 0 1-2 2 2 2 0 0 1 2 2v5c0 1.1.9 2 2 2h1"/>
                                    <path d="M16 3h1a2 2 0 0 1 2 2v5a2 2 0 0 0 2 2 2 2 0 0 0-2 2v5a2 2 0 0 1-2 2h-1"/>
                                </svg>
                                <span class="format-label">JSON</span>
                            </span>
                        </label>
                        <label class="format-option" data-format="chunks">
                            <input type="radio" name="format" value="chunks">
                            <span class="format-option-inner">
                                <svg class="format-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                                    <rect x="3" y="3" width="7" height="7"/>
                                    <rect x="14" y="3" width="7" height="7"/>
                                    <rect x="3" y="14" width="7" height="7"/>
                                    <rect x="14" y="14" width="7" height="7"/>
                                </svg>
                                <span class="format-label">Chunks</span>
                                <span class="format-badge">RAG</span>
                            </span>
                        </label>
                    </div>
                </div>

                <!-- Step 2: Scope Selection -->
                <div class="scope-selection">
                    <h4 class="section-label">
                        <span class="step-number">2</span>
                        Scope
                    </h4>
                    <div class="scope-options">
                        <label class="scope-option" data-scope="book">
                            <input type="radio" name="scope" value="book" checked>
                            <span class="scope-option-inner">
                                <span class="scope-icon">
                                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                                        <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/>
                                        <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>
                                    </svg>
                                </span>
                                <span class="scope-text">
                                    <span class="scope-label">Entire Book</span>
                                    <span class="scope-desc">Single file with all content</span>
                                </span>
                            </span>
                        </label>
                        <label class="scope-option" data-scope="chapters">
                            <input type="radio" name="scope" value="chapters">
                            <span class="scope-option-inner">
                                <span class="scope-icon">
                                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                                        <path d="M8 6h13M8 12h13M8 18h13M3 6h.01M3 12h.01M3 18h.01"/>
                                    </svg>
                                </span>
                                <span class="scope-text">
                                    <span class="scope-label">All Chapters</span>
                                    <span class="scope-desc">Separate file per chapter</span>
                                </span>
                            </span>
                        </label>
                        <label class="scope-option" data-scope="select">
                            <input type="radio" name="scope" value="select">
                            <span class="scope-option-inner">
                                <span class="scope-icon">
                                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                                        <path d="M9 11l3 3L22 4"/>
                                        <path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/>
                                    </svg>
                                </span>
                                <span class="scope-text">
                                    <span class="scope-label">Select Chapters</span>
                                    <span class="scope-desc">Choose specific chapters</span>
                                </span>
                            </span>
                        </label>
                    </div>
                    <div class="scope-locked-notice hidden">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                            <circle cx="12" cy="12" r="10"/>
                            <line x1="12" y1="16" x2="12" y2="12"/>
                            <line x1="12" y1="8" x2="12.01" y2="8"/>
                        </svg>
                        <span class="locked-text">Entire book only for this format</span>
                    </div>
                </div>

                <!-- Chapter Picker (shown when scope = select) -->
                <div class="chapters-picker hidden">
                    <div class="chapters-header">
                        <span class="chapters-summary">All chapters</span>
                        <div class="chapters-actions">
                            <button class="btn-text select-all-btn">All</button>
                            <button class="btn-text select-none-btn">None</button>
                        </div>
                    </div>
                    <div class="chapters-list"></div>
                </div>
            </div>

            <details class="advanced-options">
                <summary class="advanced-toggle">
                    <svg class="toggle-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M9 18l6-6-6-6"/>
                    </svg>
                    Advanced Options
                </summary>
                <div class="advanced-content">
                    <div class="option-group">
                        <label class="option-label">Save Location</label>
                        <div class="output-control">
                            <input type="text" class="output-dir-input" placeholder="Loading..." readonly>
                            <button class="btn-secondary btn-sm browse-btn">Browse</button>
                        </div>
                    </div>

                    <div class="option-group">
                        <label class="checkbox-label">
                            <input type="checkbox" class="skip-images">
                            <span>Skip images</span>
                            <span class="option-hint">Faster download, smaller files</span>
                        </label>
                    </div>

                    <div class="chunking-options hidden">
                        <div class="option-group">
                            <label class="option-label">Chunk Size (tokens)</label>
                            <input type="number" class="chunk-size-input" value="4000" min="500" max="16000">
                        </div>
                        <div class="option-group">
                            <label class="option-label">Overlap (tokens)</label>
                            <input type="number" class="chunk-overlap-input" value="200" min="0" max="1000">
                        </div>
                    </div>
                </div>
            </details>

            <div class="progress-section hidden">
                <div class="progress-header">
                    <span class="progress-label">Downloading...</span>
                    <span class="progress-percent">0%</span>
                </div>
                <div class="progress-bar">
                    <div class="progress-fill"></div>
                </div>
                <p class="progress-status"></p>
            </div>

            <div class="result-section hidden">
                <div class="result-success">
                    <svg class="result-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
                        <polyline points="22 4 12 14.01 9 11.01"/>
                    </svg>
                    <span>Download Complete</span>
                </div>
                <div class="result-files"></div>
            </div>

            <div class="action-bar">
                <button class="btn-cancel cancel-btn hidden">Cancel</button>
                <button class="btn-primary download-btn">Download</button>
            </div>
        </div>
    `;
}

function setupBookCardEvents(div, book) {
    // Click on summary to expand
    div.querySelector('.book-summary').onclick = () => expandBook(div, book.id);

    // Close button
    div.querySelector('.close-btn').onclick = (e) => {
        e.stopPropagation();
        collapseBook();
    };

    // Download button
    div.querySelector('.download-btn').onclick = (e) => {
        e.stopPropagation();
        download(div);
    };

    // Cancel button
    div.querySelector('.cancel-btn').onclick = (e) => {
        e.stopPropagation();
        cancelDownload(div);
    };

    // Format selection - update scope visibility
    div.querySelectorAll('input[name="format"]').forEach(radio => {
        radio.addEventListener('change', (e) => {
            handleFormatChange(div, e.target.value, book.id);
        });
    });

    // Scope selection - show/hide chapter picker
    div.querySelectorAll('input[name="scope"]').forEach(radio => {
        radio.addEventListener('change', (e) => {
            handleScopeChange(div, e.target.value, book.id);
        });
    });

    // Chapter selection buttons
    div.querySelector('.select-all-btn').onclick = (e) => {
        e.stopPropagation();
        selectAllChapters(div, true);
    };
    div.querySelector('.select-none-btn').onclick = (e) => {
        e.stopPropagation();
        selectAllChapters(div, false);
    };

    // Browse button
    div.querySelector('.browse-btn').onclick = (e) => {
        e.stopPropagation();
        browseOutputDir(div);
    };
}

// Formats that only support entire book scope
const BOOK_ONLY_FORMATS = ['epub', 'chunks'];

function handleFormatChange(cardElement, format, bookId) {
    const scopeSection = cardElement.querySelector('.scope-selection');
    const scopeOptions = cardElement.querySelector('.scope-options');
    const lockedNotice = cardElement.querySelector('.scope-locked-notice');
    const chunkingOptions = cardElement.querySelector('.chunking-options');
    const chaptersPicker = cardElement.querySelector('.chapters-picker');

    // Show/hide chunking options
    chunkingOptions.classList.toggle('hidden', format !== 'chunks');

    if (BOOK_ONLY_FORMATS.includes(format)) {
        // Lock to "Entire Book" for EPUB and Chunks
        scopeOptions.classList.add('hidden');
        lockedNotice.classList.remove('hidden');
        chaptersPicker.classList.add('hidden');

        // Reset to book scope
        const bookRadio = cardElement.querySelector('input[name="scope"][value="book"]');
        if (bookRadio) bookRadio.checked = true;
    } else {
        // Show all scope options
        scopeOptions.classList.remove('hidden');
        lockedNotice.classList.add('hidden');

        // Check current scope and show chapter picker if needed
        const currentScope = cardElement.querySelector('input[name="scope"]:checked')?.value;
        if (currentScope === 'select') {
            loadChaptersIfNeeded(cardElement, bookId);
            chaptersPicker.classList.remove('hidden');
        }
    }
}

function handleScopeChange(cardElement, scope, bookId) {
    const chaptersPicker = cardElement.querySelector('.chapters-picker');

    if (scope === 'select') {
        loadChaptersIfNeeded(cardElement, bookId);
        chaptersPicker.classList.remove('hidden');
    } else {
        chaptersPicker.classList.add('hidden');
    }
}

async function loadChaptersIfNeeded(cardElement, bookId) {
    if (chaptersCache[bookId]) {
        // Already loaded
        if (cardElement.querySelector('.chapters-list').children.length === 0) {
            renderChapters(cardElement, chaptersCache[bookId]);
        }
        return;
    }

    const listContainer = cardElement.querySelector('.chapters-list');
    listContainer.innerHTML = '<p class="loading-text">Loading chapters...</p>';

    try {
        const res = await fetch(`${API}/api/book/${bookId}/chapters`);
        const data = await res.json();
        chaptersCache[bookId] = data.chapters;
        renderChapters(cardElement, data.chapters);
    } catch (err) {
        listContainer.innerHTML = '<p class="error-text">Failed to load chapters</p>';
    }
}

// ============================================
// Book Expansion
// ============================================

async function expandBook(cardElement, bookId) {
    if (currentExpandedCard && currentExpandedCard !== cardElement) {
        collapseBook();
    }

    if (cardElement.classList.contains('expanded')) {
        return;
    }

    const expanded = cardElement.querySelector('.book-expanded');
    cardElement.classList.add('expanded', 'loading');
    expanded.classList.remove('hidden');
    document.getElementById('search-results').classList.add('has-expanded');
    currentExpandedCard = cardElement;

    // Smooth scroll into view
    setTimeout(() => {
        cardElement.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }, 100);

    // Set output directory
    const outputDirInput = expanded.querySelector('.output-dir-input');
    outputDirInput.value = defaultOutputDir || 'Loading...';

    // Fetch book details
    try {
        const res = await fetch(`${API}/api/book/${bookId}`);
        const book = await res.json();

        expanded.querySelector('.book-publisher .value').textContent = book.publishers?.join(', ') || 'Unknown';
        expanded.querySelector('.book-publisher .value').classList.remove('loading-text');
        expanded.querySelector('.book-pages .value').textContent = book.virtual_pages || 'N/A';
        expanded.querySelector('.book-pages .value').classList.remove('loading-text');
        expanded.querySelector('.book-description').innerHTML = book.description || 'No description available.';
        expanded.querySelector('.book-description').classList.remove('loading-text');
    } catch (error) {
        expanded.querySelector('.book-description').textContent = 'Failed to load details.';
        expanded.querySelector('.book-description').classList.remove('loading-text');
    }

    cardElement.classList.remove('loading');
}

function collapseBook() {
    if (currentExpandedCard) {
        currentExpandedCard.classList.remove('expanded');
        currentExpandedCard.querySelector('.book-expanded').classList.add('hidden');

        // Reset sections
        const progressSection = currentExpandedCard.querySelector('.progress-section');
        const resultSection = currentExpandedCard.querySelector('.result-section');
        progressSection.classList.add('hidden');
        resultSection.classList.add('hidden');

        document.getElementById('search-results').classList.remove('has-expanded');
        currentExpandedCard = null;
    }
}

// ============================================
// Chapter Selection
// ============================================

function renderChapters(cardElement, chapters) {
    const listContainer = cardElement.querySelector('.chapters-list');

    listContainer.innerHTML = chapters.map((ch) => `
        <label class="chapter-item">
            <input type="checkbox" class="chapter-checkbox" data-index="${ch.index}" checked>
            <span class="chapter-title">${ch.title || 'Chapter ' + (ch.index + 1)}</span>
            ${ch.pages ? `<span class="chapter-pages">${ch.pages}p</span>` : ''}
        </label>
    `).join('');

    updateChapterCount(cardElement);

    listContainer.querySelectorAll('.chapter-checkbox').forEach(cb => {
        cb.addEventListener('change', () => updateChapterCount(cardElement));
    });
}

function updateChapterCount(cardElement) {
    const checkboxes = cardElement.querySelectorAll('.chapter-checkbox');
    const checked = cardElement.querySelectorAll('.chapter-checkbox:checked');
    const summaryEl = cardElement.querySelector('.chapters-summary');

    if (checked.length === checkboxes.length) {
        summaryEl.textContent = `All ${checkboxes.length} chapters`;
    } else if (checked.length === 0) {
        summaryEl.textContent = 'No chapters selected';
    } else {
        summaryEl.textContent = `${checked.length} of ${checkboxes.length} chapters`;
    }
}

function selectAllChapters(cardElement, selectAll) {
    cardElement.querySelectorAll('.chapter-checkbox').forEach(cb => cb.checked = selectAll);
    updateChapterCount(cardElement);
}

// ============================================
// Download
// ============================================

async function download(cardElement) {
    const bookId = cardElement.dataset.bookId;

    // Get selected format
    const formatRadio = cardElement.querySelector('input[name="format"]:checked');
    const format = formatRadio ? formatRadio.value : null;

    if (!format) {
        // Shake animation for format options
        const formatOptions = cardElement.querySelector('.format-options');
        formatOptions.classList.add('shake');
        setTimeout(() => formatOptions.classList.remove('shake'), 500);
        return;
    }

    // Get selected scope
    const scopeRadio = cardElement.querySelector('input[name="scope"]:checked');
    const scope = scopeRadio ? scopeRadio.value : 'book';

    // Determine final format string based on format + scope
    let finalFormat = format;
    if (scope === 'chapters' && !BOOK_ONLY_FORMATS.includes(format)) {
        // For chapter scope, append -chapters to format (e.g., pdf-chapters, markdown-chapters)
        finalFormat = `${format}-chapters`;
    }

    // Get selected chapters if scope is 'select'
    let selectedChapters = null;
    if (scope === 'select') {
        const chapterCheckboxes = cardElement.querySelectorAll('.chapter-checkbox');
        const checkedBoxes = cardElement.querySelectorAll('.chapter-checkbox:checked');

        if (checkedBoxes.length === 0) {
            // No chapters selected - shake the chapter picker
            const chaptersPicker = cardElement.querySelector('.chapters-picker');
            chaptersPicker.classList.add('shake');
            setTimeout(() => chaptersPicker.classList.remove('shake'), 500);
            return;
        }

        if (checkedBoxes.length < chapterCheckboxes.length) {
            selectedChapters = Array.from(checkedBoxes).map(cb => parseInt(cb.dataset.index));
        }
        // If all chapters are selected, treat as "chapters" scope (separate files)
        finalFormat = `${format}-chapters`;
    }

    const progressSection = cardElement.querySelector('.progress-section');
    const resultSection = cardElement.querySelector('.result-section');
    const downloadBtn = cardElement.querySelector('.download-btn');
    const cancelBtn = cardElement.querySelector('.cancel-btn');
    const progressFill = cardElement.querySelector('.progress-fill');

    progressSection.classList.remove('hidden');
    resultSection.classList.add('hidden');
    downloadBtn.classList.add('hidden');
    cancelBtn.classList.remove('hidden');
    progressFill.style.width = '0%';

    const outputDirInput = cardElement.querySelector('.output-dir-input');
    const outputDir = outputDirInput.value.trim();

    const requestBody = { book_id: bookId, format: finalFormat };
    if (selectedChapters !== null) {
        requestBody.chapters = selectedChapters;
    }
    if (outputDir && outputDir !== defaultOutputDir) {
        requestBody.output_dir = outputDir;
    }
    if (format === 'chunks') {
        const chunkSize = parseInt(cardElement.querySelector('.chunk-size-input').value) || 4000;
        const chunkOverlap = parseInt(cardElement.querySelector('.chunk-overlap-input').value) || 200;
        requestBody.chunking = {
            chunk_size: chunkSize,
            overlap: chunkOverlap
        };
    }
    if (cardElement.querySelector('.skip-images').checked) {
        requestBody.skip_images = true;
    }

    try {
        const res = await fetch(`${API}/api/download`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(requestBody)
        });

        const result = await res.json();

        if (result.error) {
            cardElement.querySelector('.progress-status').textContent = `Error: ${result.error}`;
            downloadBtn.classList.remove('hidden');
            cancelBtn.classList.add('hidden');
            return;
        }

        pollProgress(cardElement);
    } catch (err) {
        cardElement.querySelector('.progress-status').textContent = 'Download failed. Please try again.';
        downloadBtn.classList.remove('hidden');
        cancelBtn.classList.add('hidden');
    }
}

async function cancelDownload(cardElement) {
    const cancelBtn = cardElement.querySelector('.cancel-btn');
    cancelBtn.disabled = true;
    cancelBtn.textContent = 'Cancelling...';

    try {
        await fetch(`${API}/api/cancel`, { method: 'POST' });
    } catch (err) {
        console.error('Cancel request failed:', err);
    }
}

// ============================================
// Progress Polling
// ============================================

function formatETA(seconds) {
    if (seconds < 60) return `${seconds}s`;
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    if (mins < 60) return secs > 0 ? `${mins}m ${secs}s` : `${mins}m`;
    const hours = Math.floor(mins / 60);
    const remainMins = mins % 60;
    return `${hours}h ${remainMins}m`;
}

async function pollProgress(cardElement) {
    try {
        const res = await fetch(`${API}/api/progress`);
        const data = await res.json();

        const progressFill = cardElement.querySelector('.progress-fill');
        const progressStatus = cardElement.querySelector('.progress-status');
        const progressPercent = cardElement.querySelector('.progress-percent');
        const progressSection = cardElement.querySelector('.progress-section');
        const resultSection = cardElement.querySelector('.result-section');
        const downloadBtn = cardElement.querySelector('.download-btn');
        const cancelBtn = cardElement.querySelector('.cancel-btn');

        let status = data.status || 'waiting';
        const details = [];

        if (data.current_chapter && data.total_chapters) {
            details.push(`Chapter ${data.current_chapter}/${data.total_chapters}`);
        }

        if (typeof data.percentage === 'number') {
            progressFill.style.width = `${data.percentage}%`;
            progressPercent.textContent = `${data.percentage}%`;
        }

        if (data.eta_seconds && data.eta_seconds > 0) {
            details.push(`~${formatETA(data.eta_seconds)} remaining`);
        }

        if (data.chapter_title) {
            const title = data.chapter_title.length > 40
                ? data.chapter_title.substring(0, 40) + '...'
                : data.chapter_title;
            status = title;
        }

        progressStatus.textContent = details.length > 0 ? details.join(' • ') : status;

        function restoreButtons() {
            downloadBtn.classList.remove('hidden');
            downloadBtn.disabled = false;
            cancelBtn.classList.add('hidden');
            cancelBtn.disabled = false;
            cancelBtn.textContent = 'Cancel';
        }

        if (data.status === 'completed') {
            restoreButtons();
            progressSection.classList.add('hidden');
            resultSection.classList.remove('hidden');

            let filesHTML = '';
            if (data.epub) filesHTML += createFileResultHTML('EPUB', data.epub);
            if (data.pdf) {
                if (Array.isArray(data.pdf)) {
                    filesHTML += `<div class="file-result"><span class="file-label">PDF</span><span class="file-path">${data.pdf.length} chapter files</span></div>`;
                } else {
                    filesHTML += createFileResultHTML('PDF', data.pdf);
                }
            }
            if (data.markdown) filesHTML += createFileResultHTML('Markdown', data.markdown);
            if (data.plaintext) filesHTML += createFileResultHTML('Plain Text', data.plaintext);
            if (data.json) filesHTML += createFileResultHTML('JSON', data.json);
            if (data.chunks) filesHTML += createFileResultHTML('Chunks', data.chunks);

            cardElement.querySelector('.result-files').innerHTML = filesHTML;
        } else if (data.status === 'error') {
            restoreButtons();
            progressStatus.textContent = `Error: ${data.error}`;
        } else {
            setTimeout(() => pollProgress(cardElement), 500);
        }
    } catch (err) {
        console.error('Progress polling failed:', err);
        setTimeout(() => pollProgress(cardElement), 1000);
    }
}

function createFileResultHTML(label, path) {
    const escapedPath = path.replace(/'/g, "\\'");
    return `
        <div class="file-result">
            <span class="file-label">${label}</span>
            <span class="file-path" title="${path}">${path}</span>
            <button class="btn-text btn-reveal" onclick="revealFile('${escapedPath}')">Reveal</button>
        </div>
    `;
}

async function revealFile(path) {
    try {
        const res = await fetch(`${API}/api/reveal`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ path })
        });
        const data = await res.json();
        if (data.error) {
            console.error('Reveal failed:', data.error);
        }
    } catch (err) {
        console.error('Reveal request failed:', err);
    }
}

// ============================================
// Output Directory
// ============================================

async function browseOutputDir(cardElement) {
    const browseBtn = cardElement.querySelector('.browse-btn');
    const outputDirInput = cardElement.querySelector('.output-dir-input');

    browseBtn.disabled = true;
    browseBtn.textContent = 'Opening...';

    try {
        const res = await fetch(`${API}/api/settings/output-dir`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ browse: true })
        });
        const data = await res.json();

        if (data.success && data.path) {
            outputDirInput.value = data.path;
        }
    } catch (err) {
        console.error('Browse request failed:', err);
    }

    browseBtn.disabled = false;
    browseBtn.textContent = 'Browse';
}

// ============================================
// Keyboard Navigation
// ============================================

function updateSelectedResult() {
    const results = document.querySelectorAll('.book-card');
    results.forEach((r, i) => {
        r.classList.toggle('keyboard-selected', i === selectedResultIndex);
    });
    if (selectedResultIndex >= 0 && results[selectedResultIndex]) {
        results[selectedResultIndex].scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
}

// ============================================
// Event Listeners
// ============================================

document.addEventListener('DOMContentLoaded', () => {
    // Auth
    checkAuth();
    loadDefaultOutputDir();

    // Cookie modal
    document.getElementById('login-btn').onclick = showCookieModal;
    document.getElementById('cancel-modal-btn').onclick = hideCookieModal;
    document.getElementById('save-cookies-btn').onclick = saveCookies;
    document.getElementById('cookie-modal').onclick = (e) => {
        if (e.target.id === 'cookie-modal') hideCookieModal();
    };

    // Search
    let searchTimeout;
    const searchInput = document.getElementById('search-input');

    searchInput.addEventListener('input', (e) => {
        clearTimeout(searchTimeout);
        const query = e.target.value.trim();
        if (query.length >= 2) {
            searchTimeout = setTimeout(() => search(query), 300);
        } else if (query.length === 0) {
            document.getElementById('search-results').innerHTML = '';
            currentExpandedCard = null;
        }
    });

    // Click outside to collapse
    document.addEventListener('click', (e) => {
        if (currentExpandedCard && !currentExpandedCard.contains(e.target)) {
            collapseBook();
        }
    });

    // Keyboard navigation
    document.addEventListener('keydown', (e) => {
        const results = document.querySelectorAll('.book-card');
        const searchInput = document.getElementById('search-input');

        if (e.key === 'Escape') {
            if (currentExpandedCard) {
                collapseBook();
                e.preventDefault();
            }
            return;
        }

        if (e.key === 'Enter' && document.activeElement === searchInput) {
            clearTimeout(searchTimeout);
            const query = searchInput.value.trim();
            if (query.length >= 2) {
                search(query);
            }
            e.preventDefault();
            return;
        }

        if (!results.length || currentExpandedCard) return;

        if (e.key === 'ArrowDown') {
            e.preventDefault();
            selectedResultIndex = Math.min(selectedResultIndex + 1, results.length - 1);
            updateSelectedResult();
        } else if (e.key === 'ArrowUp') {
            e.preventDefault();
            selectedResultIndex = Math.max(selectedResultIndex - 1, 0);
            updateSelectedResult();
        } else if (e.key === 'Enter' && selectedResultIndex >= 0) {
            e.preventDefault();
            const selected = results[selectedResultIndex];
            if (selected) {
                expandBook(selected, selected.dataset.bookId);
            }
        }
    });
});
