/* ═══════════════════════════════════════════════════════════════════════
   Equi Content Engine — Frontend Logic
   SPA navigation, API calls, state management
   ═══════════════════════════════════════════════════════════════════════ */

// ── State ───────────────────────────────────────────────────────────────
let currentPage = 'dashboard';
let lastGenerateResult = null;
let lastVideoResult = null;
let reviewDetailPieceId = null;
let selectedVideoFile = null;
let currentInputMethod = 'upload'; // 'upload' or 'paste'

// ── Sample data ─────────────────────────────────────────────────────────
const SAMPLES = {
    1: {
        founder: 'itay',
        text: `So I was looking at the numbers this morning and it's striking — RIAs are sitting on 60/40 portfolios that had a 95% correlation between stocks and bonds in 2022. That's not diversification, that's just concentration with extra steps. The firms we're talking to, the $2 to $10 billion independent RIAs, they know this intuitively but they don't have the infrastructure to access institutional-quality hedge fund programs. That's literally what we built Equi to solve. The tender offer fund we're launching is going to be a game-changer because it gives RIAs a way to allocate their clients into a diversified hedge fund portfolio without the operational nightmare of managing five separate LP agreements and quarterly capital calls.`
    },
    2: {
        founder: 'tory',
        text: `- BlackRock just told investors to increase hedge fund allocations
- This validates what we've been saying for 2 years
- The difference: most RIAs can't access institutional hedge funds
- Equi's fund of funds solves the access + diligence + operations gap
- Our tender offer fund makes this even simpler — one allocation, full diversification
- Key stat: hedge fund industry saw $21B in net inflows Q1 2025`
    },
    3: {
        founder: 'tory',
        text: `Just got back from the Titan Investors roundtable in DC. The energy around alternatives was palpable — every advisor I spoke to is thinking about how to add hedge fund exposure but they're all hitting the same wall: they don't have the team, the relationships, or the operational infrastructure to do it right. One CIO of a $4B firm literally said 'I know I need this but I don't know where to start.' That's our pitch in one sentence.`
    }
};

// ── Initialization ──────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    setupNavigation();
    setupTabs();
    setupVideoTabs();
    setupInputMethodTabs();
    setupUploadZone();
    setupCalendarFilters();
    loadDashboard();
});

// ── Navigation ──────────────────────────────────────────────────────────
function setupNavigation() {
    document.querySelectorAll('.nav-item').forEach(item => {
        item.addEventListener('click', () => {
            const page = item.dataset.page;
            navigateTo(page);
        });
    });
}

function navigateTo(page) {
    currentPage = page;
    document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
    document.querySelector(`[data-page="${page}"]`).classList.add('active');
    document.querySelectorAll('.page-section').forEach(s => s.classList.remove('active'));
    document.getElementById(`page-${page}`).classList.add('active');

    // Load data for page
    if (page === 'dashboard') loadDashboard();
    if (page === 'calendar') loadCalendar();
    if (page === 'review') loadReviewQueue();
}

// ── Tabs (Workflow 1) ───────────────────────────────────────────────────
function setupTabs() {
    document.querySelectorAll('#content-tabs .tab').forEach(tab => {
        tab.addEventListener('click', () => {
            const target = tab.dataset.tab;
            document.querySelectorAll('#content-tabs .tab').forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            document.querySelectorAll('.tab-content').forEach(c => c.style.display = 'none');
            document.getElementById(`tab-${target}`).style.display = 'block';
        });
    });
}

// ── Tabs (Workflow 2) ───────────────────────────────────────────────────
function setupVideoTabs() {
    document.querySelectorAll('#video-tabs .tab').forEach(tab => {
        tab.addEventListener('click', () => {
            const target = tab.dataset.vtab;
            document.querySelectorAll('#video-tabs .tab').forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            document.querySelectorAll('.vtab-content').forEach(c => c.style.display = 'none');
            document.getElementById(`vtab-${target}`).style.display = 'block';
        });
    });
}

// ── Input Method Tabs (Upload / Paste) ──────────────────────────────────
function setupInputMethodTabs() {
    document.querySelectorAll('#input-method-tabs .tab').forEach(tab => {
        tab.addEventListener('click', () => {
            const target = tab.dataset.input;
            currentInputMethod = target;
            document.querySelectorAll('#input-method-tabs .tab').forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            document.querySelectorAll('.input-method-content').forEach(c => {
                c.style.display = 'none';
                c.classList.remove('active');
            });
            const el = document.getElementById(`input-${target}`);
            el.style.display = 'block';
            el.classList.add('active');
        });
    });
}

// ── Upload Zone ─────────────────────────────────────────────────────────
function setupUploadZone() {
    const zone = document.getElementById('upload-zone');
    const input = document.getElementById('video-file-input');
    if (!zone || !input) return;

    zone.addEventListener('click', () => input.click());

    zone.addEventListener('dragover', (e) => {
        e.preventDefault();
        zone.classList.add('dragover');
    });
    zone.addEventListener('dragleave', () => {
        zone.classList.remove('dragover');
    });
    zone.addEventListener('drop', (e) => {
        e.preventDefault();
        zone.classList.remove('dragover');
        if (e.dataTransfer.files.length > 0) {
            handleFileSelect(e.dataTransfer.files[0]);
        }
    });

    input.addEventListener('change', () => {
        if (input.files.length > 0) {
            handleFileSelect(input.files[0]);
        }
    });
}

function handleFileSelect(file) {
    const validExts = ['.mp4', '.mov', '.webm', '.mp3', '.wav', '.m4a'];
    const ext = '.' + file.name.split('.').pop().toLowerCase();
    if (!validExts.includes(ext)) {
        toast('Unsupported file format. Use MP4, MOV, WebM, MP3, WAV, or M4A.', 'error');
        return;
    }
    const maxSize = 500 * 1024 * 1024; // 500 MB
    if (file.size > maxSize) {
        toast('File too large. Maximum size is 500 MB.', 'error');
        return;
    }

    selectedVideoFile = file;
    document.getElementById('upload-zone').style.display = 'none';
    document.getElementById('upload-file-info').style.display = 'block';
    document.getElementById('upload-file-name').textContent = file.name;
    document.getElementById('upload-file-size').textContent = formatFileSize(file.size);

    // Auto-fill duration estimate from file size
    const isAudio = ['.mp3', '.wav', '.m4a'].includes(ext);
    const estMin = isAudio ? Math.round(file.size / (1024 * 1024) / 1.5) : Math.round(file.size / (1024 * 1024) / 10);
    if (estMin > 0 && !document.getElementById('video-duration').value) {
        document.getElementById('video-duration').value = Math.max(1, estMin);
    }
}

function clearUpload() {
    selectedVideoFile = null;
    document.getElementById('upload-zone').style.display = '';
    document.getElementById('upload-file-info').style.display = 'none';
    document.getElementById('upload-progress-container').style.display = 'none';
    document.getElementById('transcription-status').style.display = 'none';
    document.getElementById('video-file-input').value = '';
}

function formatFileSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    if (bytes < 1024 * 1024 * 1024) return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
    return (bytes / (1024 * 1024 * 1024)).toFixed(2) + ' GB';
}

function showUploadProgress(pct, statusText) {
    const container = document.getElementById('upload-progress-container');
    container.style.display = 'block';
    document.getElementById('upload-progress-bar').style.width = pct + '%';
    document.getElementById('upload-progress-pct').textContent = Math.round(pct) + '%';
    if (statusText) document.getElementById('upload-progress-text').textContent = statusText;
}

function showTranscriptionStatus(step, detail) {
    const el = document.getElementById('transcription-status');
    el.style.display = 'flex';
    document.getElementById('transcription-step').textContent = step;
    document.getElementById('transcription-detail').textContent = detail || '';
}

function hideTranscriptionStatus() {
    document.getElementById('transcription-status').style.display = 'none';
}

// ── Calendar filters ────────────────────────────────────────────────────
function setupCalendarFilters() {
    document.querySelectorAll('#calendar-filters .filter-chip').forEach(chip => {
        chip.addEventListener('click', () => {
            document.querySelectorAll('#calendar-filters .filter-chip').forEach(c => c.classList.remove('active'));
            chip.classList.add('active');
            filterCalendar(chip.dataset.filter);
        });
    });
}

// ── Loading / Toast ─────────────────────────────────────────────────────
function showLoading(text = 'Generating content...', sub = 'This may take a moment') {
    document.getElementById('loading-text').textContent = text;
    document.getElementById('loading-sub').textContent = sub;
    document.getElementById('loading-overlay').classList.add('visible');
}

function hideLoading() {
    document.getElementById('loading-overlay').classList.remove('visible');
}

function toast(message, type = '') {
    const container = document.getElementById('toast-container');
    const t = document.createElement('div');
    t.className = `toast ${type}`;
    t.textContent = message;
    container.appendChild(t);
    setTimeout(() => t.remove(), 4000);
}

// ── Dashboard ───────────────────────────────────────────────────────────
async function loadDashboard() {
    try {
        const res = await fetch('/api/dashboard');
        const data = await res.json();

        document.getElementById('stat-total').textContent = data.total || 0;
        document.getElementById('stat-review').textContent = (data.draft || 0) + (data.review || 0);
        document.getElementById('stat-approved').textContent = data.approved || 0;
        document.getElementById('stat-scheduled').textContent = data.scheduled || 0;
        document.getElementById('stat-published').textContent = data.published || 0;

        // Activity feed
        const feed = document.getElementById('activity-feed');
        if (data.recent && data.recent.length > 0) {
            feed.innerHTML = data.recent.map(item => `
                <div class="activity-item">
                    <div class="activity-icon ${item.platform}">${platformIcon(item.platform)}</div>
                    <div class="activity-text">
                        <div class="title">${escapeHtml(item.title || item.content_type)}</div>
                        <div class="meta">
                            <span class="badge badge-${item.status}">${item.status}</span>
                            · ${item.platform} · ${timeAgo(item.updated_at || item.created_at)}
                        </div>
                    </div>
                </div>
            `).join('');
        }
    } catch (e) {
        console.error('Dashboard load error:', e);
    }
}

// ── Workflow 1: Generate Content ────────────────────────────────────────
async function generateContent() {
    const text = document.getElementById('raw-input').value.trim();
    const founder = document.getElementById('founder-select').value;

    if (!text) {
        toast('Please enter some text first', 'error');
        return;
    }

    showLoading('Generating content...', 'Analyzing input and creating multi-platform content');
    document.getElementById('btn-generate').disabled = true;

    try {
        const res = await fetch('/api/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text, founder }),
        });

        const data = await res.json();
        if (!res.ok) throw new Error(data.error || 'Generation failed');

        lastGenerateResult = data;
        displayQuickResults(data);
        toast('Content generated successfully!', 'success');
    } catch (e) {
        toast(`Error: ${e.message}`, 'error');
    } finally {
        hideLoading();
        document.getElementById('btn-generate').disabled = false;
    }
}

function displayQuickResults(data) {
    document.getElementById('quick-results').style.display = 'block';

    // Analysis bar
    const a = data.analysis;
    document.getElementById('analysis-bar').innerHTML = `
        <div class="analysis-item"><span class="label">Topic:</span><span class="value">${escapeHtml(a.topic)}</span></div>
        <div class="analysis-item"><span class="label">Input:</span><span class="value">${a.input_type.replace('_', ' ')}</span></div>
        <div class="analysis-item"><span class="label">Sentiment:</span><span class="value">${a.sentiment}</span></div>
        <div class="analysis-item"><span class="label">Method:</span><span class="value">${data.method}</span></div>
    `;

    // Content
    document.getElementById('linkedin-content').textContent = data.content.linkedin;
    document.getElementById('newsletter-content').textContent = data.content.newsletter;
    document.getElementById('email-content').textContent = data.content.email;

    // Twitter thread — special formatting
    const twitterEl = document.getElementById('twitter-content');
    twitterEl.innerHTML = data.content.twitter_thread.map((tweet, i) => {
        const charCount = tweet.length;
        const overClass = charCount > 280 ? 'over' : '';
        return `<div class="tweet-card">
            <span class="tweet-num">${i + 1}/${data.content.twitter_thread.length}</span>
            ${escapeHtml(tweet)}
            <div class="char-count ${overClass}">${charCount}/280</div>
        </div>`;
    }).join('');

    // Compliance
    ['linkedin', 'newsletter', 'twitter', 'email'].forEach(p => {
        const c = data.compliance[p];
        const el = document.getElementById(`${p}-compliance`);
        if (c.passed && c.warnings === 0) {
            el.innerHTML = `<div class="compliance-dot pass"></div> Compliance passed`;
        } else if (c.passed) {
            el.innerHTML = `<div class="compliance-dot warn"></div> Passed with ${c.warnings} warning(s)`;
        } else {
            el.innerHTML = `<div class="compliance-dot fail"></div> ${c.flags} issue(s) — must revise`;
        }
    });

    // Scroll to results
    document.getElementById('quick-results').scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function loadSampleInput(n) {
    const sample = SAMPLES[n];
    document.getElementById('raw-input').value = sample.text;
    document.getElementById('founder-select').value = sample.founder;
    toast(`Loaded sample ${n}`, '');
}

// ── Workflow 2: Process Video ───────────────────────────────────────────
async function processVideo() {
    const title = document.getElementById('video-title').value.trim() || 'Video Conversation';
    const speakers = document.getElementById('video-speakers').value.trim() || 'Speaker';
    const duration = parseInt(document.getElementById('video-duration').value) || 30;

    // Determine input method
    const useUpload = currentInputMethod === 'upload' && selectedVideoFile;
    const transcriptEl = document.getElementById('video-transcript');
    const transcript = transcriptEl ? transcriptEl.value.trim() : '';

    if (!useUpload && !transcript) {
        toast(currentInputMethod === 'upload' ? 'Please select a video or audio file' : 'Please enter a transcript', 'error');
        return;
    }

    document.getElementById('btn-process-video').disabled = true;

    try {
        let data;

        if (useUpload) {
            // File upload flow
            showUploadProgress(0, 'Uploading file...');

            const formData = new FormData();
            formData.append('file', selectedVideoFile);
            formData.append('title', title);
            formData.append('speakers', speakers);
            formData.append('duration', duration.toString());

            data = await uploadWithProgress('/api/process-video-upload', formData);

        } else {
            // Text transcript flow (original)
            showLoading('Processing video transcript...', 'Extracting segments, generating content library and calendar');

            const res = await fetch('/api/process-video', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ transcript, title, speakers, duration }),
            });

            data = await res.json();
            if (!res.ok) throw new Error(data.error || 'Processing failed');
        }

        lastVideoResult = data;
        displayVideoResults(data);
        toast('Video processed successfully!', 'success');
    } catch (e) {
        toast(`Error: ${e.message}`, 'error');
    } finally {
        hideLoading();
        hideTranscriptionStatus();
        const progEl = document.getElementById('upload-progress-container');
        if (progEl) progEl.style.display = 'none';
        document.getElementById('btn-process-video').disabled = false;
    }
}

function uploadWithProgress(url, formData) {
    return new Promise((resolve, reject) => {
        const xhr = new XMLHttpRequest();
        xhr.open('POST', url);

        xhr.upload.addEventListener('progress', (e) => {
            if (e.lengthComputable) {
                const pct = (e.loaded / e.total) * 100;
                showUploadProgress(pct, pct >= 100 ? 'Upload complete — processing...' : 'Uploading file...');
            }
        });

        xhr.upload.addEventListener('load', () => {
            showUploadProgress(100, 'Upload complete');
            showTranscriptionStatus(
                'Transcribing audio with Whisper...',
                'This may take a few minutes depending on file length'
            );
        });

        xhr.addEventListener('load', () => {
            hideTranscriptionStatus();
            if (xhr.status >= 200 && xhr.status < 300) {
                try {
                    resolve(JSON.parse(xhr.responseText));
                } catch {
                    reject(new Error('Invalid response from server'));
                }
            } else {
                try {
                    const err = JSON.parse(xhr.responseText);
                    reject(new Error(err.error || `Upload failed (${xhr.status})`));
                } catch {
                    reject(new Error(`Upload failed (${xhr.status})`));
                }
            }
        });

        xhr.addEventListener('error', () => reject(new Error('Upload failed — network error')));
        xhr.addEventListener('abort', () => reject(new Error('Upload cancelled')));

        xhr.send(formData);
    });
}

function displayVideoResults(data) {
    document.getElementById('video-results').style.display = 'block';

    // Analysis bar
    const v = data.video;
    document.getElementById('video-analysis-bar').innerHTML = `
        <div class="analysis-item"><span class="label">Segments:</span><span class="value">${v.segments}</span></div>
        <div class="analysis-item"><span class="label">Words:</span><span class="value">${v.word_count.toLocaleString()}</span></div>
        <div class="analysis-item"><span class="label">Topics:</span><span class="value">${v.topics.length}</span></div>
        <div class="analysis-item"><span class="label">Clips:</span><span class="value">${data.clips.length}</span></div>
        <div class="analysis-item"><span class="label">Social Posts:</span><span class="value">${data.social_posts.length}</span></div>
    `;

    // Clips
    const hasVideoFile = !!(data.video_file_id);
    document.getElementById('vtab-clips').innerHTML = data.clips.map((clip, i) => {
        const hasFile = !!clip.clip_file;
        const downloadBtn = hasFile
            ? `<a class="btn-download" href="/api/clips/${clip.clip_file}" download>⬇ Download Clip</a>`
            : hasVideoFile
                ? `<a class="btn-download disabled">⬇ Cutting...</a>`
                : `<span class="clip-download-note">Upload video file to generate downloadable clips</span>`;

        return `<div class="clip-card">
            <div class="clip-header">
                <span class="clip-title">${i + 1}. ${escapeHtml(clip.title)}</span>
                <span class="clip-time">${clip.start_time} → ${clip.end_time}</span>
            </div>
            <p style="font-size:0.82rem;color:var(--slate)">${escapeHtml(clip.description)}</p>
            <div class="clip-quote">${escapeHtml(clip.key_quote.substring(0, 200))}${clip.key_quote.length > 200 ? '...' : ''}</div>
            <div class="clip-platforms">
                ${clip.platform_fit.map(p => `<span class="badge badge-${p}">${p}</span>`).join('')}
            </div>
            <div class="clip-actions">${downloadBtn}</div>
        </div>`;
    }).join('');

    // Blog
    document.getElementById('vtab-blog').innerHTML = `
        <div class="panel"><div class="panel-body">
            <div class="content-preview">${escapeHtml(data.blog)}</div>
            <div style="margin-top:12px;font-size:0.75rem;color:var(--slate)">${data.blog.split(/\s+/).length} words</div>
        </div></div>
    `;

    // Social posts
    document.getElementById('vtab-social').innerHTML = data.social_posts.map((post, i) => `
        <div class="panel" style="margin-bottom:12px">
            <div class="panel-header">
                <h3>${escapeHtml(post.title)}</h3>
                <span class="badge badge-${post.platform}">${post.platform}</span>
            </div>
            <div class="panel-body">
                <div class="content-preview" style="max-height:200px">${escapeHtml(post.body)}</div>
                <div style="margin-top:6px;font-size:0.72rem;color:var(--slate)">Source: ${escapeHtml(post.source)}</div>
            </div>
        </div>
    `).join('');

    // Email teaser
    document.getElementById('vtab-email-teaser').innerHTML = `
        <div class="panel"><div class="panel-body">
            <div class="content-preview">${escapeHtml(data.email_teaser)}</div>
        </div></div>
    `;

    // Calendar
    const cal = data.calendar;
    document.getElementById('vtab-vcalendar').innerHTML = `
        <div style="margin-bottom:12px;font-size:0.82rem;color:var(--slate)">
            ${cal.total_entries} entries · ${cal.weeks} weeks · ${cal.start_date} → ${cal.end_date}
        </div>
        <div class="panel"><div class="table-container"><table>
            <thead><tr><th>Date</th><th>Day</th><th>Time</th><th>Platform</th><th>Type</th><th>Preview</th></tr></thead>
            <tbody>
                ${cal.entries.map(e => `
                    <tr>
                        <td>${e.date}</td>
                        <td>${e.day}</td>
                        <td>${e.time}</td>
                        <td><span class="badge badge-${e.platform}">${e.platform}</span></td>
                        <td>${e.content_type}</td>
                        <td class="truncate">${escapeHtml(e.content_preview.substring(0, 80))}...</td>
                    </tr>
                `).join('')}
            </tbody>
        </table></div></div>
    `;

    document.getElementById('video-results').scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function loadSampleTranscript() {
    // Switch to paste tab
    currentInputMethod = 'paste';
    document.querySelectorAll('#input-method-tabs .tab').forEach(t => t.classList.remove('active'));
    document.querySelector('#input-method-tabs .tab[data-input="paste"]').classList.add('active');
    document.querySelectorAll('.input-method-content').forEach(c => {
        c.style.display = 'none';
        c.classList.remove('active');
    });
    const pasteEl = document.getElementById('input-paste');
    pasteEl.style.display = 'block';
    pasteEl.classList.add('active');

    // Fill in sample data
    document.getElementById('video-title').value = 'The Case for Multi-Strategy Hedge Fund Allocations in RIA Portfolios';
    document.getElementById('video-speakers').value = 'Itay, Tory';
    document.getElementById('video-duration').value = '32';
    document.getElementById('video-transcript').value = SAMPLE_TRANSCRIPT;
    toast('Sample transcript loaded', '');
}

// ── Calendar Page ───────────────────────────────────────────────────────
let calendarData = [];

async function loadCalendar() {
    try {
        const res = await fetch('/api/calendar');
        calendarData = await res.json();
        renderCalendar(calendarData);
    } catch (e) {
        console.error('Calendar load error:', e);
    }
}

function renderCalendar(entries) {
    const tbody = document.getElementById('calendar-body');
    if (entries.length === 0) {
        tbody.innerHTML = `<tr><td colspan="6"><div class="empty-state"><div class="icon">📅</div><h3>No calendar entries</h3><p>Process video content to generate a calendar</p></div></td></tr>`;
        return;
    }
    tbody.innerHTML = entries.map(e => `
        <tr data-platform="${e.platform}">
            <td><strong>${e.scheduled_date}</strong></td>
            <td>${e.scheduled_time || '—'}</td>
            <td><span class="badge badge-${e.platform}">${e.platform}</span></td>
            <td>${e.content_type || '—'}</td>
            <td class="truncate">${escapeHtml((e.content_preview || '').substring(0, 100))}</td>
            <td><span class="badge badge-${e.status}">${e.status}</span></td>
        </tr>
    `).join('');
}

function filterCalendar(platform) {
    if (platform === 'all') {
        renderCalendar(calendarData);
    } else {
        renderCalendar(calendarData.filter(e => e.platform === platform));
    }
}

// ── Review Queue ────────────────────────────────────────────────────────
async function loadReviewQueue() {
    try {
        const res = await fetch('/api/review');
        const data = await res.json();
        renderReviewQueue(data);
    } catch (e) {
        console.error('Review load error:', e);
    }
}

function renderReviewQueue(pieces) {
    const tbody = document.getElementById('review-body');
    if (pieces.length === 0) {
        tbody.innerHTML = `<tr><td colspan="7"><div class="empty-state"><div class="icon">✅</div><h3>Review queue empty</h3><p>All caught up!</p></div></td></tr>`;
        return;
    }
    tbody.innerHTML = pieces.map(p => `
        <tr>
            <td>${p.id}</td>
            <td><span class="badge badge-${p.platform}">${p.platform}</span></td>
            <td>${p.content_type}</td>
            <td class="truncate">${escapeHtml(p.title || '—')}</td>
            <td><span class="badge badge-${p.status}">${p.status}</span></td>
            <td>${timeAgo(p.created_at)}</td>
            <td>
                <div class="btn-group">
                    <button class="btn btn-ghost btn-sm" onclick="openReviewDetail(${p.id})">View</button>
                    <button class="btn btn-success btn-sm" onclick="quickApprove(${p.id})">✓</button>
                </div>
            </td>
        </tr>
    `).join('');
}

async function openReviewDetail(pieceId) {
    try {
        const res = await fetch(`/api/content/${pieceId}`);
        const piece = await res.json();
        reviewDetailPieceId = pieceId;

        document.getElementById('review-detail-title').textContent =
            `${piece.platform} — ${piece.title || piece.content_type}`;
        document.getElementById('review-detail-body').textContent = piece.body;
        document.getElementById('review-notes').value = piece.compliance_notes || '';
        document.getElementById('review-detail').style.display = 'block';
        document.getElementById('review-detail').scrollIntoView({ behavior: 'smooth' });
    } catch (e) {
        toast('Error loading content', 'error');
    }
}

function closeReviewDetail() {
    document.getElementById('review-detail').style.display = 'none';
    reviewDetailPieceId = null;
}

async function reviewAction(newStatus) {
    if (!reviewDetailPieceId) return;
    const notes = document.getElementById('review-notes').value;

    try {
        await fetch(`/api/content/${reviewDetailPieceId}/status`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ status: newStatus, notes }),
        });
        toast(`Content ${newStatus}`, 'success');
        closeReviewDetail();
        loadReviewQueue();
    } catch (e) {
        toast('Error updating status', 'error');
    }
}

async function quickApprove(pieceId) {
    try {
        await fetch(`/api/content/${pieceId}/status`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ status: 'approved' }),
        });
        toast('Approved!', 'success');
        loadReviewQueue();
    } catch (e) {
        toast('Error', 'error');
    }
}

// ── Quick actions from Workflow 1 results ────────────────────────────────
async function approveContent(platform) {
    if (!lastGenerateResult?.pieces?.[platform]) return;
    const pieceId = lastGenerateResult.pieces[platform].id;
    try {
        await fetch(`/api/content/${pieceId}/status`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ status: 'approved' }),
        });
        document.getElementById(`${platform}-status`).className = 'badge badge-approved';
        document.getElementById(`${platform}-status`).textContent = 'Approved';
        toast(`${platform} content approved`, 'success');
    } catch (e) {
        toast('Error approving', 'error');
    }
}

async function scheduleContent(platform) {
    if (!lastGenerateResult?.pieces?.[platform]) return;
    const pieceId = lastGenerateResult.pieces[platform].id;
    try {
        await fetch(`/api/content/${pieceId}/status`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ status: 'scheduled' }),
        });
        document.getElementById(`${platform}-status`).className = 'badge badge-scheduled';
        document.getElementById(`${platform}-status`).textContent = 'Scheduled';
        toast(`${platform} content scheduled`, 'success');
    } catch (e) {
        toast('Error scheduling', 'error');
    }
}

// ── Utilities ───────────────────────────────────────────────────────────
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text || '';
    return div.innerHTML;
}

function platformIcon(platform) {
    const icons = { linkedin: '💼', twitter: '🐦', newsletter: '📰', email: '✉️', blog: '📝' };
    return icons[platform] || '📄';
}

function timeAgo(dateStr) {
    if (!dateStr) return '';
    const date = new Date(dateStr + 'Z');
    const now = new Date();
    const diffMs = now - date;
    const diffMin = Math.floor(diffMs / 60000);
    if (diffMin < 1) return 'just now';
    if (diffMin < 60) return `${diffMin}m ago`;
    const diffHr = Math.floor(diffMin / 60);
    if (diffHr < 24) return `${diffHr}h ago`;
    const diffDay = Math.floor(diffHr / 24);
    return `${diffDay}d ago`;
}
const SAMPLE_TRANSCRIPT = "[00:00:15] Tory: Welcome back, everyone. I'm Tory, CEO of Equi, and today I'm sitting down with our CIO, Itay, to talk about something we get asked about every single day \u2014 why multi-strategy hedge fund allocations belong in RIA portfolios, and frankly, why most advisors are dramatically underweight in this area. Itay, let's jump right in. What's the macro setup right now?\n\n[00:00:42] Itay: Thanks, Tory. Look, the macro environment is as interesting as it's been in a decade. We've got a Fed that's navigating a narrow path between inflation and growth, equity valuations that are stretched by historical standards \u2014 the S&P is trading at roughly 21 times forward earnings \u2014 and a fixed income market that's still trying to figure out the new rate regime. The key thing for advisors to understand is that the traditional 60/40 portfolio assumption \u2014 that stocks and bonds are negatively correlated \u2014 has fundamentally broken down.\n\n[00:01:18] Tory: And when you say broken down, put some numbers on that. What did we actually see?\n\n[00:01:24] Itay: In 2022, the correlation between the S&P 500 and the Bloomberg Aggregate Bond Index hit 95%. Ninety-five percent. That means your \"diversified\" portfolio was essentially a single bet. And this wasn't a one-month anomaly \u2014 the rolling 12-month correlation stayed above 60% for most of 2023. The negative correlation that 60/40 relies on? It was a feature of a specific rate environment \u2014 ZIRP, basically \u2014 and that environment is over.\n\n[00:02:05] Tory: So what does that mean practically for an RIA managing, say, $3 to $5 billion for their clients?\n\n[00:02:12] Itay: It means they need truly uncorrelated return streams. Not just different asset classes that happen to move together, but strategies that are structurally designed to generate returns independent of market direction. And that's where multi-strategy hedge funds come in. A well-constructed multi-strategy allocation can provide 200 to 400 basis points of annual alpha with correlation to equities below 0.3. That's real diversification.\n\n[00:02:48] Tory: Let's talk about the elephant in the room though. If this is so obvious, why are most RIAs allocating less than 5% to alternatives? I talk to advisors every week who have sophisticated, high-net-worth clients and they're running basically the same portfolio they ran in 2015. What's the blocker?\n\n[00:03:15] Itay: It's three things, and none of them are about the investment case. First, access \u2014 the best multi-strategy managers have $5 to $10 million minimums, sometimes higher. An RIA managing $3 billion across 500 client accounts can't practically allocate that way. Second, diligence \u2014 evaluating hedge fund managers requires a different skillset than evaluating long-only equity managers. You need to understand the strategy's structural edge, the risk management framework, the operational infrastructure, the prime brokerage setup. Most RIAs don't have an in-house team to do that. And third, operations \u2014 managing LP agreements, capital calls, K-1s, side pockets, redemption queues across multiple hedge fund positions is an operational nightmare for a firm that's built to run model portfolios.\n\n[00:04:22] Tory: That third point is the one I hear most often. I was at the Titan Investors roundtable last month and a CIO of a $4 billion firm told me, \"I know I need hedge fund exposure but I literally don't know where to start operationally.\" And this is a smart, sophisticated investor. The infrastructure gap is massive.\n\n[00:04:48] Itay: And that's exactly the gap we built Equi to fill. Our approach is fundamentally different from what's existed in the market. We're not just picking managers and putting them in a wrapper. We're building a complete infrastructure layer \u2014 diligence, allocation, operations, reporting \u2014 that sits between the RIA and the hedge fund universe. When an advisor allocates through our tender offer fund, they make one allocation decision, and we handle everything downstream.\n\n[00:05:25] Tory: Walk through the tender offer fund structure for folks who might not be familiar with it.\n\n[00:05:31] Itay: Sure. The tender offer fund is a registered fund \u2014 it's a 1940 Act fund \u2014 which means it has the regulatory framework and transparency that RIAs expect. It's structured as a fund of hedge funds, so investors get diversified exposure across multiple strategies and managers through a single allocation. The fund offers quarterly tender offers for liquidity, which is a significant improvement over the typical hedge fund lock-up structure. And because it's a registered vehicle, advisors can allocate through their existing custodial relationships \u2014 Schwab, Fidelity, Pershing \u2014 without setting up new accounts or managing separate subscription documents.\n\n[00:06:18] Tory: That custodial compatibility point is huge. I can't overstate how much friction that removes. The number one operational complaint we hear from RIAs considering alternatives is the reporting and custody challenge. This solves it.\n\n[00:06:38] Itay: Absolutely. And on the portfolio construction side, we're not building a generic multi-strategy allocation. We're constructing what we call a \"barbell approach\" \u2014 combining high-conviction, concentrated alpha generators with lower-volatility, steady-return strategies. The goal is to maximize the portfolio's information ratio while keeping drawdown risk within institutional bounds. We target strategies with less than 0.2 correlation to the S&P and positive Sortino ratios across market cycles.\n\n[00:07:18] Tory: Let's talk about what the industry data is showing us. Because it's not just us saying this \u2014 the entire institutional community is moving in this direction.\n\n[00:07:28] Itay: The data is compelling. Hedge fund industry net inflows were $21 billion in Q1 2025 alone. That's the strongest quarter in four years. BlackRock \u2014 and this is the world's largest asset manager \u2014 just published a note telling their institutional clients to increase hedge fund allocations. Bridgewater's research arm published a paper showing that a 20% alternatives allocation improved risk-adjusted returns by 150 basis points annualized over a 15-year backtest. And if you look at endowment portfolios \u2014 Yale, Harvard, Stanford \u2014 they've been running 25 to 40% alternatives for two decades, and their returns have crushed traditional 60/40 benchmarks.\n\n[00:08:20] Tory: But those are institutions with billion-dollar endowments and 50-person investment teams. The whole point is that the independent RIA doesn't have that infrastructure. So how does an advisor with a five-person team and $3 billion in AUM get access to the same caliber of hedge fund strategy?\n\n[00:08:42] Itay: That's the question, and historically the answer has been \"you can't.\" But that's exactly what we're changing. Our diligence process is institutional-grade \u2014 we evaluate over 200 managers a year, conduct on-site visits, stress test the operational infrastructure, do deep reference checks. Out of those 200, maybe 8 to 10 make it into our portfolios. That's a 4 to 5% hit rate, which is comparable to the selection rigor at a major institutional allocator.\n\n[00:09:22] Tory: Tell me about the risk management overlay. Because I think that's something most fund-of-funds don't talk about enough.\n\n[00:09:30] Itay: Great question. We run a real-time risk management framework that monitors every underlying position across all of our managers. We're tracking factor exposures \u2014 equity beta, credit spread duration, rates sensitivity, volatility \u2014 at the portfolio level, not just the manager level. If our aggregate equity beta creeps above 0.25, we rebalance. If correlation between two of our managers spikes above 0.5, we investigate and potentially reduce. This is the kind of monitoring that a pension fund CIO would recognize, but it's never been available to the RIA channel before.\n\n[00:10:15] Tory: I want to shift to something more practical. If an advisor is listening to this and thinking \"okay, I'm convinced, but how do I actually start?\" \u2014 what's the playbook?\n\n[00:10:28] Itay: Step one is understanding what role alternatives should play in their client portfolios. For most RIA clients, we think the right allocation is 10 to 20% of the total portfolio. You don't need to go to 40% like an endowment \u2014 that's a different liquidity profile. But 10 to 20% allocated to truly uncorrelated strategies can meaningfully improve Sharpe ratios and reduce max drawdowns. Step two is selecting the right vehicle. And this is where the tender offer fund is the game-changer \u2014 it gives you institutional multi-strategy exposure in a single, operationally simple allocation. Step three is integration into the existing portfolio construction workflow. We work with advisors to model how the allocation fits alongside their existing equity and fixed income positions.\n\n[00:11:25] Tory: And the fee question always comes up. How should advisors think about fees in the context of alternatives?\n\n[00:11:33] Itay: Fees matter, but they need to be evaluated in context. The dispersion between top-quartile and bottom-quartile hedge fund managers is roughly 1,200 basis points per year. Compare that to long-only equity where the dispersion might be 200 to 300 basis points. So the value of manager selection in alternatives is 4 to 5 times greater than in traditional asset classes. A 1% management fee on a strategy generating 400 basis points of uncorrelated alpha is dramatically different from a 1% fee on a beta-driven equity strategy. Our fee structure is transparent and aligned \u2014 we don't layer unnecessary fees on top of underlying manager fees.\n\n[00:12:20] Tory: I think the advisor community is waking up to this. Every conference I go to \u2014 Titan Investors, the CAIS Summit, iCapital events \u2014 the energy around alternatives access for RIAs is palpable. It feels like we're at the beginning of a major structural shift.\n\n[00:12:42] Itay: I agree. And the data supports it. The RIA channel is the fastest-growing segment of wealth management \u2014 over $8 trillion in AUM and growing. These firms are institutionalizing rapidly, their clients are demanding more sophisticated solutions, and the competitive pressure from wirehouses and multi-family offices is real. The advisors who build an alternatives capability now will have a structural advantage for the next decade. The ones who wait will spend years trying to catch up.\n\n[00:13:18] Tory: Let's talk about what separates our approach from other fund-of-funds in the market. Because this isn't a new concept \u2014 fund of funds have been around for decades.\n\n[00:13:30] Itay: Three things differentiate us. First, technology. We've built proprietary systems for manager evaluation, portfolio construction, and risk monitoring that automate what used to require a team of 20 analysts. This lets us offer institutional-quality diligence at a cost structure that works for the RIA channel. Second, alignment. We're not a legacy fund-of-funds that's trying to pivot to serve advisors \u2014 we built this from the ground up for independent RIAs. Our entire product, operations, and reporting infrastructure is designed for how advisors actually work. And third, transparency. We provide full portfolio-level transparency \u2014 every position, every factor exposure, every risk metric \u2014 reported through the channels that advisors already use. No black boxes.\n\n[00:14:28] Tory: That transparency piece resonates deeply. One of the biggest historical objections to hedge fund allocations was \"I can't see what's in there.\" We've eliminated that objection entirely.\n\n[00:14:42] Itay: Exactly. And transparency isn't just about reporting \u2014 it's about trust. When an advisor can log in and see exactly what their clients are exposed to, what the risk metrics look like in real time, and how each manager is performing, they can have informed conversations with their clients. That's what institutional allocators have always had, and it's what we're bringing to the independent advisor.\n\n[00:15:10] Tory: As we wrap up, what's your view on where we are in the cycle for alternatives? Are we early, mid, or late in terms of RIA adoption?\n\n[00:15:22] Itay: We are firmly in the early innings. If you look at the data, independent RIAs allocate roughly 3 to 5% to alternatives on average. Institutional investors allocate 20 to 40%. That gap is going to close over the next decade, and the rate of closure is accelerating. The firms that are moving now \u2014 the ones we're working with \u2014 they're going to be the ones that define what a modern, institutionalized RIA looks like. And looking at the structural tailwinds \u2014 the correlation regime shift, the growth of the RIA channel, the technology enabling access \u2014 I think we're at the most interesting inflection point in alternatives investing in a generation.\n\n[00:16:05] Tory: Well said. For advisors who want to learn more, visit us at joinequi.com or reach out directly. We're always happy to walk through how this fits into your specific practice. Itay, thanks for the conversation.\n\n[00:16:22] Itay: Thanks, Tory. Great talking through this \u2014 it's a conversation that every advisor needs to be having right now.";
