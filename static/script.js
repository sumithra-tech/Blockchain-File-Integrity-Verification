// ==========================================================================
// Blockchain File Integrity Verification System
// Frontend Controller (Modern Dark Navy & Blue Dashboard)
// ==========================================================================

document.addEventListener('DOMContentLoaded', () => {
    // --- Cached State ---
    let currentUploadedFile = null;
    let calculatedHashData = null;
    let currentVerifyFile = null;

    // --- DOM Elements: Navigation ---
    const navItems = document.querySelectorAll('.nav-item');
    const navChainStatus = document.getElementById('nav-chain-status');
    const validateChainBtn = document.getElementById('validate-chain-btn');

    // --- DOM Elements: Stats ---
    const statTotalBlocks = document.getElementById('stat-total-blocks');
    const statChainStatus = document.getElementById('stat-chain-status');
    const statChainMsg = document.getElementById('stat-chain-msg');

    // --- DOM Elements: Upload & Hash Card ---
    const uploadDropzone = document.getElementById('upload-dropzone');
    const uploadFileInput = document.getElementById('upload-file-input');
    const uploadFilePreview = document.getElementById('upload-file-preview');
    const uploadFilenameText = document.getElementById('upload-filename-text');
    const uploadFilesizeText = document.getElementById('upload-filesize-text');
    const uploadClearBtn = document.getElementById('upload-clear-btn');
    const btnGenerateHash = document.getElementById('btn-generate-hash');
    const hashSpinner = document.getElementById('hash-spinner');
    const btnStoreBlockchain = document.getElementById('btn-store-blockchain');
    const storeSpinner = document.getElementById('store-spinner');
    const uploadOutputArea = document.getElementById('upload-output-area');

    // --- DOM Elements: Verify File Card ---
    const verifyDropzone = document.getElementById('verify-dropzone');
    const verifyFileInput = document.getElementById('verify-file-input');
    const verifyFilePreview = document.getElementById('verify-file-preview');
    const verifyFilenameText = document.getElementById('verify-filename-text');
    const verifyFilesizeText = document.getElementById('verify-filesize-text');
    const verifyClearBtn = document.getElementById('verify-clear-btn');
    const verifyRecordSelect = document.getElementById('verify-record-select');
    const btnVerifyFile = document.getElementById('btn-verify-file');
    const verifySpinner = document.getElementById('verify-spinner');
    const verifyOutputArea = document.getElementById('verify-output-area');

    // --- DOM Elements: Blockchain Records Explorer ---
    const blockchainListContainer = document.getElementById('blockchain-list-container');
    const btnRefreshRecords = document.getElementById('btn-refresh-records');
    const btnValidateLedger = document.getElementById('btn-validate-ledger');
    const toastContainer = document.getElementById('toast-container');

    // --- Initialization ---
    initNavigation();
    loadBlockchainRecords();
    validateBlockchainHealth();

    // ======================================================================
    // 1. Navigation Controller (Smooth Scroll & Active Link Tracking)
    // ======================================================================
    function initNavigation() {
        navItems.forEach(item => {
            item.addEventListener('click', (e) => {
                navItems.forEach(link => link.classList.remove('active'));
                item.classList.add('active');
            });
        });

        // Click nav badge or validate button to run health check
        validateChainBtn.addEventListener('click', () => {
            validateBlockchainHealth(true);
        });

        btnValidateLedger.addEventListener('click', () => {
            validateBlockchainHealth(true);
        });

        btnRefreshRecords.addEventListener('click', () => {
            loadBlockchainRecords(true);
        });
    }

    // ======================================================================
    // 2. Drag & Drop Setup
    // ======================================================================
    setupDropzone(
        uploadDropzone, 
        uploadFileInput, 
        (file) => {
            currentUploadedFile = file;
            calculatedHashData = null; // reset previously computed hash
            uploadFilenameText.textContent = file.name;
            uploadFilesizeText.textContent = formatBytes(file.size);
            uploadFilePreview.classList.remove('hidden');
            btnGenerateHash.disabled = false;
            btnStoreBlockchain.disabled = false;
            uploadOutputArea.classList.add('hidden');
        }
    );

    uploadClearBtn.addEventListener('click', () => {
        currentUploadedFile = null;
        calculatedHashData = null;
        uploadFileInput.value = '';
        uploadFilePreview.classList.add('hidden');
        btnGenerateHash.disabled = true;
        btnStoreBlockchain.disabled = true;
        uploadOutputArea.classList.add('hidden');
    });

    setupDropzone(
        verifyDropzone, 
        verifyFileInput, 
        (file) => {
            currentVerifyFile = file;
            verifyFilenameText.textContent = file.name;
            verifyFilesizeText.textContent = formatBytes(file.size);
            verifyFilePreview.classList.remove('hidden');
            btnVerifyFile.disabled = false;
            verifyOutputArea.classList.add('hidden');
        }
    );

    verifyClearBtn.addEventListener('click', () => {
        currentVerifyFile = null;
        verifyFileInput.value = '';
        verifyFilePreview.classList.add('hidden');
        btnVerifyFile.disabled = true;
        verifyOutputArea.classList.add('hidden');
    });

    function setupDropzone(zone, input, onSelect) {
        zone.addEventListener('click', () => input.click());

        input.addEventListener('change', (e) => {
            if (input.files && input.files.length > 0) {
                onSelect(input.files[0]);
            }
        });

        ['dragenter', 'dragover'].forEach(name => {
            zone.addEventListener(name, (e) => {
                e.preventDefault();
                e.stopPropagation();
                zone.classList.add('dragover');
            });
        });

        ['dragleave', 'drop'].forEach(name => {
            zone.addEventListener(name, (e) => {
                e.preventDefault();
                e.stopPropagation();
                zone.classList.remove('dragover');
            });
        });

        zone.addEventListener('drop', (e) => {
            if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
                input.files = e.dataTransfer.files;
                onSelect(input.files[0]);
            }
        });
    }

    // ======================================================================
    // 3. Action 1: Generate SHA-256 Hash (POST /upload)
    // ======================================================================
    btnGenerateHash.addEventListener('click', async () => {
        if (!currentUploadedFile) {
            showToast('Please select a document first.', 'error');
            return;
        }

        const formData = new FormData();
        formData.append('file', currentUploadedFile);

        setLoading(btnGenerateHash, hashSpinner, true);
        uploadOutputArea.classList.add('hidden');

        try {
            const response = await fetch('/upload', {
                method: 'POST',
                body: formData
            });
            const data = await response.json();

            if (response.ok && data.success) {
                calculatedHashData = data;
                uploadOutputArea.className = 'output-area output-info';
                uploadOutputArea.innerHTML = `
                    <div class="output-title">
                        <span>🔍 SHA-256 Digest Generated</span>
                    </div>
                    <div class="output-msg">${escapeHtml(data.message)}</div>
                    <div class="meta-grid">
                        <div class="meta-item">
                            <span class="meta-key">File Name:</span>
                            <strong>${escapeHtml(data.filename)}</strong>
                        </div>
                        <div class="meta-item">
                            <span class="meta-key">File Size:</span>
                            <span>${data.file_size}</span>
                        </div>
                        <div class="meta-item">
                            <span class="meta-key">SHA-256 Hash:</span>
                            <div class="hash-container">
                                <span class="hash-text">${data.file_hash}</span>
                                <button type="button" class="btn-copy" onclick="copyToClipboard('${data.file_hash}')" title="Copy SHA-256 hash">📋 Copy</button>
                            </div>
                        </div>
                    </div>
                `;
                uploadOutputArea.classList.remove('hidden');
                btnStoreBlockchain.disabled = false;
                showToast('SHA-256 fingerprint generated successfully.', 'success');
            } else {
                throw new Error(data.message || 'Failed to generate hash.');
            }
        } catch (error) {
            uploadOutputArea.className = 'output-area output-danger';
            uploadOutputArea.innerHTML = `
                <div class="output-title">❌ Hashing Failed</div>
                <div class="output-msg">${escapeHtml(error.message)}</div>
            `;
            uploadOutputArea.classList.remove('hidden');
            showToast(error.message, 'error');
        } finally {
            setLoading(btnGenerateHash, hashSpinner, false);
        }
    });

    // ======================================================================
    // 4. Action 2: Store in Blockchain (POST /store)
    // ======================================================================
    btnStoreBlockchain.addEventListener('click', async () => {
        if (!currentUploadedFile) {
            showToast('Please select a document first.', 'error');
            return;
        }

        const formData = new FormData();
        formData.append('file', currentUploadedFile);

        setLoading(btnStoreBlockchain, storeSpinner, true);

        try {
            const response = await fetch('/store', {
                method: 'POST',
                body: formData
            });
            const data = await response.json();

            if (response.ok && data.success) {
                uploadOutputArea.className = 'output-area output-success';
                uploadOutputArea.innerHTML = `
                    <div class="output-title">
                        <span>✅ Block #${data.block.index} Successfully Mined & Sealed</span>
                    </div>
                    <div class="output-msg">${escapeHtml(data.message)}</div>
                    <div class="meta-grid">
                        <div class="meta-item">
                            <span class="meta-key">File Name:</span>
                            <strong>${escapeHtml(data.filename)}</strong>
                        </div>
                        <div class="meta-item">
                            <span class="meta-key">File SHA-256:</span>
                            <div class="hash-container">
                                <span class="hash-text">${data.file_hash}</span>
                                <button type="button" class="btn-copy" onclick="copyToClipboard('${data.file_hash}')" title="Copy Hash">📋 Copy</button>
                            </div>
                        </div>
                        <div class="meta-item">
                            <span class="meta-key">Block Hash:</span>
                            <div class="hash-container">
                                <span class="hash-text">${data.block.hash || data.block.current_hash}</span>
                                <button type="button" class="btn-copy" onclick="copyToClipboard('${data.block.hash || data.block.current_hash}')" title="Copy Block Hash">📋 Copy</button>
                            </div>
                        </div>
                        <div class="meta-item">
                            <span class="meta-key">Proof of Work (Nonce):</span>
                            <span>${data.block.nonce}</span>
                        </div>
                    </div>
                `;
                uploadOutputArea.classList.remove('hidden');
                showToast(`Block #${data.block.index} successfully recorded into ledger!`, 'success');

                // Refresh ledger and update dropdown
                loadBlockchainRecords();
                validateBlockchainHealth();
            } else if (data.already_exists) {
                uploadOutputArea.className = 'output-area output-danger';
                uploadOutputArea.innerHTML = `
                    <div class="output-title">⚠️ Duplicate File Record</div>
                    <div class="output-msg">${escapeHtml(data.message)}</div>
                    <div class="meta-grid">
                        <div class="meta-item">
                            <span class="meta-key">Existing Block:</span>
                            <strong>Block #${data.block.index}</strong>
                        </div>
                        <div class="meta-item">
                            <span class="meta-key">SHA-256 Hash:</span>
                            <div class="hash-container">
                                <span class="hash-text">${data.file_hash}</span>
                                <button type="button" class="btn-copy" onclick="copyToClipboard('${data.file_hash}')" title="Copy Hash">📋 Copy</button>
                            </div>
                        </div>
                    </div>
                `;
                uploadOutputArea.classList.remove('hidden');
                showToast('This file is already registered on the blockchain.', 'warning');
            } else {
                throw new Error(data.message || 'Storage into block failed.');
            }
        } catch (error) {
            uploadOutputArea.className = 'output-area output-danger';
            uploadOutputArea.innerHTML = `
                <div class="output-title">❌ Blockchain Storage Error</div>
                <div class="output-msg">${escapeHtml(error.message)}</div>
            `;
            uploadOutputArea.classList.remove('hidden');
            showToast(error.message, 'error');
        } finally {
            setLoading(btnStoreBlockchain, storeSpinner, false);
        }
    });

    // ======================================================================
    // 5. Action 3: Verify File Integrity (POST /verify)
    // ======================================================================
    btnVerifyFile.addEventListener('click', async () => {
        if (!currentVerifyFile) {
            showToast('Please select a file to verify.', 'error');
            return;
        }

        const formData = new FormData();
        formData.append('file', currentVerifyFile);

        // Optional specific block selection
        if (verifyRecordSelect && verifyRecordSelect.value !== '') {
            formData.append('block_index', verifyRecordSelect.value);
        }

        setLoading(btnVerifyFile, verifySpinner, true);
        verifyOutputArea.classList.add('hidden');

        try {
            const response = await fetch('/verify', {
                method: 'POST',
                body: formData
            });
            const data = await response.json();

            if (data.verified) {
                // Authentic Result
                const matched = data.matched_block || data.selected_block;
                verifyOutputArea.className = 'output-area output-success';
                verifyOutputArea.innerHTML = `
                    <div class="output-title">
                        <span>🛡️ File Integrity Verified (Authentic)</span>
                    </div>
                    <div class="output-msg">${escapeHtml(data.message)}</div>
                    <div class="meta-grid">
                        <div class="meta-item">
                            <span class="meta-key">Verification Result:</span>
                            <strong style="color: #34d399;">100% Original & Authentic</strong>
                        </div>
                        <div class="meta-item">
                            <span class="meta-key">Matched Block:</span>
                            <strong>Block #${matched ? matched.index : 'N/A'}</strong>
                        </div>
                        <div class="meta-item">
                            <span class="meta-key">Registration Time:</span>
                            <span>${matched ? matched.formatted_time : 'N/A'}</span>
                        </div>
                        <div class="meta-item">
                            <span class="meta-key">SHA-256 Digest:</span>
                            <div class="hash-container">
                                <span class="hash-text">${data.file_hash}</span>
                                <button type="button" class="btn-copy" onclick="copyToClipboard('${data.file_hash}')" title="Copy Hash">📋 Copy</button>
                            </div>
                        </div>
                    </div>
                `;
                showToast('Integrity confirmed: File matches blockchain record!', 'success');
            } else {
                // Tampered Result
                verifyOutputArea.className = 'output-area output-danger';
                verifyOutputArea.innerHTML = `
                    <div class="output-title">
                        <span>⚠️ Integrity Check Failed (File Altered)</span>
                    </div>
                    <div class="output-msg">${escapeHtml(data.message)}</div>
                    <div class="meta-grid">
                        <div class="meta-item">
                            <span class="meta-key">Verification Result:</span>
                            <strong style="color: #f87171;">Integrity Mismatch / Document Modified</strong>
                        </div>
                        <div class="meta-item">
                            <span class="meta-key">Tested File SHA-256:</span>
                            <div class="hash-container">
                                <span class="hash-text">${data.file_hash}</span>
                                <button type="button" class="btn-copy" onclick="copyToClipboard('${data.file_hash}')" title="Copy Hash">📋 Copy</button>
                            </div>
                        </div>
                        ${data.selected_block ? `
                        <div class="meta-item">
                            <span class="meta-key">Expected Block #${data.selected_block.index} Hash:</span>
                            <div class="hash-container">
                                <span class="hash-text">${data.selected_block.file_hash}</span>
                                <button type="button" class="btn-copy" onclick="copyToClipboard('${data.selected_block.file_hash}')" title="Copy Hash">📋 Copy</button>
                            </div>
                        </div>
                        ` : ''}
                    </div>
                `;
                showToast('Integrity warning: File content does not match ledger!', 'error');
            }
            verifyOutputArea.classList.remove('hidden');
        } catch (error) {
            verifyOutputArea.className = 'output-area output-danger';
            verifyOutputArea.innerHTML = `
                <div class="output-title">❌ Verification Error</div>
                <div class="output-msg">${escapeHtml(error.message)}</div>
            `;
            verifyOutputArea.classList.remove('hidden');
            showToast(error.message, 'error');
        } finally {
            setLoading(btnVerifyFile, verifySpinner, false);
        }
    });

    // ======================================================================
    // 6. Action 4: Load Blockchain Records (GET /records)
    // ======================================================================
    async function loadBlockchainRecords(showUserToast = false) {
        try {
            const response = await fetch('/records');
            const data = await response.json();

            if (data.success && data.records) {
                statTotalBlocks.textContent = data.total_records;
                updateRecordDropdown(data.records);
                renderBlockchainBlocks(data.records);
                if (showUserToast) {
                    showToast(`Ledger refreshed: ${data.total_records} blocks loaded.`, 'success');
                }
            }
        } catch (error) {
            console.error('Error fetching records:', error);
            blockchainListContainer.innerHTML = `
                <div class="empty-state">
                    <p style="color: var(--danger);">Failed to load blockchain records. Check Flask server connection.</p>
                </div>
            `;
        }
    }

    function updateRecordDropdown(blocks) {
        if (!verifyRecordSelect) return;
        const currentVal = verifyRecordSelect.value;
        let html = '<option value="">-- Auto-Search All Blockchain Records --</option>';

        blocks.forEach(block => {
            if (block.index > 0) {
                html += `<option value="${block.index}">Block #${block.index}: ${escapeHtml(block.file_name)}</option>`;
            }
        });

        verifyRecordSelect.innerHTML = html;
        if (currentVal) {
            verifyRecordSelect.value = currentVal;
        }
    }

    function renderBlockchainBlocks(blocks) {
        if (!blocks || blocks.length === 0) {
            blockchainListContainer.innerHTML = '<div class="empty-state"><p>No blocks found in ledger.</p></div>';
            return;
        }

        let html = '';
        blocks.forEach((block, idx) => {
            const isGenesis = block.index === 0;
            const blockClass = isGenesis ? 'is-genesis' : 'is-data';
            const badgeClass = isGenesis ? 'tag-genesis' : 'tag-data';
            const badgeTitle = isGenesis ? 'Genesis Block' : 'Mined Block';

            html += `
                <div class="block-item ${blockClass}">
                    <div class="block-header-bar">
                        <div class="block-badge-group">
                            <span class="block-num">Block #${block.index}</span>
                            <span class="block-type-tag ${badgeClass}">${badgeTitle}</span>
                        </div>
                        <div class="block-time">
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <circle cx="12" cy="12" r="10"></circle>
                                <polyline points="12 6 12 12 16 14"></polyline>
                            </svg>
                            <span>${block.formatted_time}</span>
                        </div>
                    </div>

                    <div class="block-fields-grid">
                        <div class="field-cell">
                            <div class="cell-caption">Current Block Hash (SHA-256)</div>
                            <div class="hash-container">
                                <span class="cell-value">${block.current_hash || block.hash}</span>
                                <button type="button" class="btn-copy" onclick="copyToClipboard('${block.current_hash || block.hash}')" title="Copy Block Hash">📋</button>
                            </div>
                        </div>

                        <div class="field-cell">
                            <div class="cell-caption">Previous Block Hash</div>
                            <div class="hash-container">
                                <span class="cell-value">${block.previous_hash}</span>
                                <button type="button" class="btn-copy" onclick="copyToClipboard('${block.previous_hash}')" title="Copy Prev Hash">📋</button>
                            </div>
                        </div>

                        <div class="field-cell">
                            <div class="cell-caption">Payload / Document Data</div>
                            <div class="payload-info">
                                ${isGenesis 
                                    ? `<strong>System:</strong> ${escapeHtml(block.file_name || 'System Genesis')}` 
                                    : `<strong>File:</strong> ${escapeHtml(block.file_name)} (${block.file_size})<br>
                                       <strong>SHA-256:</strong> 
                                       <span class="hash-text" style="font-size: 0.72rem;">${block.file_hash}</span>`
                                }
                            </div>
                        </div>

                        <div class="field-cell">
                            <div class="cell-caption">Proof of Work (Nonce)</div>
                            <div class="cell-value" style="color: #60a5fa; font-weight: 700;">
                                ${block.nonce}
                            </div>
                        </div>
                    </div>
                </div>
            `;

            // Draw chain connection arrow if not last block
            if (idx < blocks.length - 1) {
                html += `
                    <div class="chain-link-connector">
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <line x1="12" y1="5" x2="12" y2="19"></line>
                            <polyline points="19 12 12 19 5 12"></polyline>
                        </svg>
                        <span>Cryptographically Chained to Block #${blocks[idx + 1].index}</span>
                    </div>
                `;
            }
        });

        blockchainListContainer.innerHTML = html;
    }

    // ======================================================================
    // 7. Action 5: Validate Blockchain Health (GET /validate-chain)
    // ======================================================================
    async function validateBlockchainHealth(showUserToast = false) {
        try {
            const response = await fetch('/validate-chain');
            const data = await response.json();

            if (data.is_valid) {
                navChainStatus.textContent = 'Ledger Verified';
                validateChainBtn.className = 'chain-status-pill status-valid';
                statChainStatus.textContent = 'Intact';
                statChainStatus.className = 'stat-number text-emerald';
                statChainMsg.textContent = 'All blocks linked properly';
                if (showUserToast) {
                    showToast('Blockchain integrity confirmed: 0 broken links.', 'success');
                }
            } else {
                navChainStatus.textContent = 'Chain Altered!';
                validateChainBtn.className = 'chain-status-pill status-invalid';
                statChainStatus.textContent = 'Compromised';
                statChainStatus.className = 'stat-number';
                statChainStatus.style.color = '#f87171';
                statChainMsg.textContent = data.message;
                if (showUserToast) {
                    showToast(`Alert: ${data.message}`, 'error');
                }
            }
        } catch (err) {
            navChainStatus.textContent = 'Status Offline';
            validateChainBtn.className = 'chain-status-pill status-invalid';
        }
    }

    // ======================================================================
    // 8. Clipboard Copy & Toast Feedback
    // ======================================================================
    window.copyToClipboard = function(text) {
        if (!text) return;
        navigator.clipboard.writeText(text).then(() => {
            showToast('Hash copied to clipboard!', 'info');
        }).catch(() => {
            showToast('Failed to copy to clipboard.', 'error');
        });
    };

    function showToast(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = 'toast';
        
        let icon = 'ℹ️';
        if (type === 'success') icon = '✅';
        if (type === 'error') icon = '❌';
        if (type === 'warning') icon = '⚠️';

        toast.innerHTML = `<span>${icon}</span><span>${escapeHtml(message)}</span>`;
        toastContainer.appendChild(toast);

        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transform = 'translateX(100%)';
            toast.style.transition = 'all 0.3s ease';
            setTimeout(() => toast.remove(), 300);
        }, 3200);
    }

    // ======================================================================
    // Helpers
    // ======================================================================
    function setLoading(btn, spinner, isLoading) {
        btn.disabled = isLoading;
        if (isLoading) {
            spinner.classList.remove('hidden');
        } else {
            spinner.classList.add('hidden');
        }
    }

    function formatBytes(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    function escapeHtml(text) {
        if (!text) return '';
        const map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        };
        return String(text).replace(/[&<>"']/g, m => map[m]);
    }
});
