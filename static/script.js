/**
 * PAA Extractor — Frontend Logic
 * Handles form submission, API calls, and results rendering.
 */

(function () {
    'use strict';

    const form = document.getElementById('paaForm');
    const keywordsInput = document.getElementById('keywords');
    const regionSelect = document.getElementById('region');
    const submitBtn = document.getElementById('submitBtn');
    const btnText = submitBtn.querySelector('.btn-text');
    const btnLoading = submitBtn.querySelector('.btn-loading');
    const resultsArea = document.getElementById('resultsArea');
    const resultsContainer = document.getElementById('resultsContainer');
    const errorArea = document.getElementById('errorArea');
    const errorMessage = document.getElementById('errorMessage');
    const copyAllBtn = document.getElementById('copyAllBtn');

    let lastResults = [];

    // ---------- Form Submit ----------
    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        const keywords = keywordsInput.value.trim();
        const region = regionSelect.value;

        if (!keywords) return;

        setLoading(true);
        hideError();
        hideResults();

        try {
            const response = await fetch('/api/paa', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ keywords, region }),
            });

            if (!response.ok) {
                const err = await response.json().catch(() => ({}));
                throw new Error(err.detail || `Server error (${response.status})`);
            }

            const data = await response.json();
            lastResults = data.results || [];
            renderResults(lastResults);

            if (data.sheet_status && data.sheet_status.status === 'success') {
                setTimeout(() => {
                    showToast(`Saved ${data.sheet_status.count} questions to Google Sheets!`);
                }, 500);
            } else if (data.sheet_status && data.sheet_status.status === 'error') {
                console.error("Sheet save error:", data.sheet_status.message);
            }
        } catch (err) {
            showError(err.message || 'Something went wrong. Please try again.');
        } finally {
            setLoading(false);
        }
    });

    // ---------- Copy All ----------
    copyAllBtn.addEventListener('click', () => {
        const allQuestions = lastResults
            .filter(r => r.questions && r.questions.length > 0)
            .map(r => {
                const header = `--- ${r.keyword} (${r.region}) ---`;
                const qs = r.questions.map((q, i) => `${i + 1}. ${q}`).join('\n');
                return `${header}\n${qs}`;
            })
            .join('\n\n');

        if (allQuestions) {
            copyToClipboard(allQuestions);
            showToast('All questions copied!');
        }
    });

    // ---------- Render Results ----------
    function renderResults(results) {
        resultsContainer.innerHTML = '';

        results.forEach(result => {
            const card = document.createElement('div');
            card.className = 'keyword-card' + (result.error ? ' error' : '');

            if (result.error) {
                card.innerHTML = `
                    <div class="keyword-card-header">
                        <span class="keyword-title">${escapeHtml(result.keyword)}</span>
                        <span class="keyword-count">Error</span>
                    </div>
                    <div class="keyword-error">${escapeHtml(result.error)}</div>
                `;
            } else {
                const questions = result.questions || [];
                const questionsHtml = questions.map((q, i) => `
                    <div class="question-item">
                        <span class="question-number">${i + 1}</span>
                        <span class="question-text">${escapeHtml(q)}</span>
                    </div>
                `).join('');

                card.innerHTML = `
                    <div class="keyword-card-header">
                        <span class="keyword-title">${escapeHtml(result.keyword)}</span>
                        <div style="display:flex;align-items:center;gap:8px;">
                            <button class="keyword-copy-btn" data-keyword="${escapeAttr(result.keyword)}">
                                <svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5">
                                    <rect x="5" y="5" width="9" height="9" rx="1.5"/>
                                    <path d="M3 11V3a1.5 1.5 0 011.5-1.5H11"/>
                                </svg>
                                Copy
                            </button>
                            <span class="keyword-count">${questions.length} questions</span>
                        </div>
                    </div>
                    <div class="keyword-questions">${questionsHtml}</div>
                `;
            }

            resultsContainer.appendChild(card);
        });

        // Bind per-keyword copy buttons
        resultsContainer.querySelectorAll('.keyword-copy-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const keyword = btn.getAttribute('data-keyword');
                const result = lastResults.find(r => r.keyword === keyword);
                if (result && result.questions) {
                    const text = result.questions.map((q, i) => `${i + 1}. ${q}`).join('\n');
                    copyToClipboard(text);
                    showToast(`Copied ${result.questions.length} questions!`);
                }
            });
        });

        resultsArea.style.display = 'block';
    }

    // ---------- Helpers ----------
    function setLoading(loading) {
        submitBtn.disabled = loading;
        btnText.style.display = loading ? 'none' : 'inline';
        btnLoading.style.display = loading ? 'flex' : 'none';
    }

    function showError(msg) {
        errorMessage.textContent = msg;
        errorArea.style.display = 'block';
    }

    function hideError() {
        errorArea.style.display = 'none';
    }

    function hideResults() {
        resultsArea.style.display = 'none';
        resultsContainer.innerHTML = '';
    }

    function escapeHtml(str) {
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }

    function escapeAttr(str) {
        return str.replace(/"/g, '&quot;').replace(/'/g, '&#39;');
    }

    function copyToClipboard(text) {
        if (navigator.clipboard && navigator.clipboard.writeText) {
            navigator.clipboard.writeText(text);
        } else {
            const ta = document.createElement('textarea');
            ta.value = text;
            ta.style.position = 'fixed';
            ta.style.left = '-9999px';
            document.body.appendChild(ta);
            ta.select();
            document.execCommand('copy');
            document.body.removeChild(ta);
        }
    }

    function showToast(message) {
        let toast = document.querySelector('.toast');
        if (!toast) {
            toast = document.createElement('div');
            toast.className = 'toast';
            document.body.appendChild(toast);
        }
        toast.textContent = message;
        toast.classList.add('show');
        setTimeout(() => toast.classList.remove('show'), 2000);
    }
})();
