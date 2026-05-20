/* ── 定数 ── */
const UPLOAD_URL = 'https://e3dsi33knk.execute-api.ap-northeast-1.amazonaws.com/upload';
const API_BASE   = 'https://e3dsi33knk.execute-api.ap-northeast-1.amazonaws.com';

const MAX_FILES        = 3;
const MAX_FILE_SIZE    = 10 * 1024 * 1024;
const POLL_INTERVAL_MS = 2000;
const POLL_TIMEOUT_MS  = 10 * 60 * 1000;
const ALLOWED_EXTS     = ['pdf', 'docx', 'doc', 'txt', 'xlsx'];
const LABEL_OPTIONS    = ['履歴書', '業務経歴書', 'その他'];

/* ── DOM参照 ── */
const fileList       = document.getElementById('fileList');
const fileListEmpty  = document.getElementById('fileListEmpty');
const addFileArea    = document.getElementById('addFileArea');
const addFileInput   = document.getElementById('addFileInput');
const addFileHint    = document.getElementById('addFileHint');
const uploadBtn      = document.getElementById('uploadBtn');
const loadingOverlay = document.getElementById('loadingOverlay');
const loadingMsg     = document.getElementById('loadingMsg');
const loadingElapsed = document.getElementById('loadingElapsed');
const loadingSteps   = document.getElementById('loadingSteps');
const toast          = document.getElementById('toast');

/* ── ファイルリスト状態 ── */
let fileEntries = []; // [{file: File, label: string}, ...]
let elapsedTimer = null;

/* ── ファイル追加エリア ── */
addFileInput.addEventListener('change', () => {
  if (addFileInput.files[0]) addFile(addFileInput.files[0]);
  addFileInput.value = '';
});

addFileArea.addEventListener('dragover', (e) => {
  e.preventDefault();
  if (fileEntries.length < MAX_FILES) addFileArea.classList.add('drag-over');
});
addFileArea.addEventListener('dragleave', () => addFileArea.classList.remove('drag-over'));
addFileArea.addEventListener('drop', (e) => {
  e.preventDefault();
  addFileArea.classList.remove('drag-over');
  if (fileEntries.length < MAX_FILES && e.dataTransfer.files[0]) {
    addFile(e.dataTransfer.files[0]);
  }
});

/* ── ファイル操作 ── */
function addFile(file) {
  if (fileEntries.length >= MAX_FILES) return;

  const ext = file.name.split('.').pop().toLowerCase();
  if (!ALLOWED_EXTS.includes(ext)) {
    showToast('PDF・DOCX・XLSX・TXT形式のファイルを選択してください', 'error');
    return;
  }
  if (file.size > MAX_FILE_SIZE) {
    showToast('ファイルサイズは10MB以下にしてください', 'error');
    return;
  }

  // 追加順に応じたデフォルトラベルを自動割り当て
  const label = LABEL_OPTIONS[fileEntries.length] ?? 'その他';
  fileEntries.push({ file, label });
  _renderFileList();
  _updateUI();
}

function removeFile(index) {
  fileEntries.splice(index, 1);
  _renderFileList();
  _updateUI();
}

function updateLabel(index, label) {
  fileEntries[index].label = label;
}

/* ── レンダリング ── */
function _renderFileList() {
  // 既存のfile-itemだけ削除（file-list-emptyは保持）
  fileList.querySelectorAll('.file-item').forEach(el => el.remove());

  if (fileEntries.length === 0) {
    fileListEmpty.style.display = 'block';
    return;
  }
  fileListEmpty.style.display = 'none';

  fileEntries.forEach(({ file, label }, i) => {
    fileList.appendChild(_createFileItem(file, label, i));
  });
}

function _createFileItem(file, label, index) {
  const ext  = file.name.split('.').pop().toLowerCase();
  const icon = ext === 'pdf' ? '📕' : ext === 'txt' ? '📃' : ext === 'xlsx' ? '📊' : '📘';

  const item = document.createElement('div');
  item.className = 'file-item';
  item.innerHTML = `
    <span class="file-item-icon">${icon}</span>
    <div class="file-item-info">
      <p class="file-item-name">${_esc(file.name)}</p>
      <p class="file-item-size">${_formatBytes(file.size)}</p>
    </div>
    <select class="file-label-select" aria-label="ドキュメント種別">
      ${LABEL_OPTIONS.map(opt =>
        `<option value="${opt}"${opt === label ? ' selected' : ''}>${opt}</option>`
      ).join('')}
    </select>
    <button class="file-item-remove" title="削除">✕</button>
  `;

  item.querySelector('.file-label-select').addEventListener('change', (e) => updateLabel(index, e.target.value));
  item.querySelector('.file-item-remove').addEventListener('click', () => removeFile(index));
  return item;
}

function _updateUI() {
  const n = fileEntries.length;
  uploadBtn.disabled = n === 0;

  if (n >= MAX_FILES) {
    addFileArea.classList.add('disabled');
    addFileHint.textContent = `（最大${MAX_FILES}つ）`;
  } else {
    addFileArea.classList.remove('disabled');
    addFileHint.textContent = n === 0
      ? `（最大${MAX_FILES}つまで）`
      : `（あと${MAX_FILES - n}つ追加できます）`;
  }
}

/* ── アップロード → ポーリング ── */
uploadBtn.addEventListener('click', startUpload);

async function startUpload() {
  if (fileEntries.length === 0) return;
  showLoading('ファイルをアップロード中...');

  try {
    const formData = new FormData();
    fileEntries.forEach(({ file, label }, i) => {
      formData.append(`file_${i}`, file);
      formData.append(`label_${i}`, label);
    });

    const res  = await fetch(UPLOAD_URL, { method: 'POST', body: formData });
    const body = await res.json();

    if (!res.ok) {
      hideLoading();
      showToast(body.error || 'アップロードに失敗しました', 'error');
      return;
    }

    const { jobId } = body;
    _enterPollingUI();
    await pollStatus(jobId);

  } catch (err) {
    hideLoading();
    showToast('通信エラーが発生しました。ネットワークを確認してください。', 'error');
    console.error(err);
  }
}

/* ── ポーリング ── */
async function pollStatus(jobId) {
  const statusUrl = `${API_BASE}/status/${jobId}`;
  const deadline  = Date.now() + POLL_TIMEOUT_MS;

  while (Date.now() < deadline) {
    await _sleep(POLL_INTERVAL_MS);

    let body;
    try {
      const res = await fetch(statusUrl);
      body = await res.json();
    } catch {
      continue;
    }

    const { status } = body;

    if (status === 'processing') {
      loadingMsg.textContent = 'ポートフォリオを生成中...';
      _setStep(3);
    }

    if (status === 'done') {
      const { sessionId } = body;
      // 無料プレビューなし: 生成完了後そのままStripe決済へ
      loadingMsg.textContent = '決済ページを準備中...';
      try {
        const checkoutRes  = await fetch(`${API_BASE}/payment/checkout`, {
          method:  'POST',
          headers: { 'Content-Type': 'application/json' },
          body:    JSON.stringify({ sessionId }),
        });
        const checkoutBody = await checkoutRes.json();
        if (!checkoutRes.ok || !checkoutBody.checkoutUrl) {
          hideLoading();
          showToast(checkoutBody.error || '決済の準備中にエラーが発生しました', 'error');
          return;
        }
        window.location.href = checkoutBody.checkoutUrl;
      } catch (err) {
        hideLoading();
        showToast('通信エラーが発生しました。ネットワークを確認してください。', 'error');
        console.error(err);
      }
      return;
    }

    if (status === 'error') {
      hideLoading();
      showToast(body.message || 'AI処理中にエラーが発生しました。再度お試しください。', 'error');
      return;
    }
  }

  hideLoading();
  showToast('処理がタイムアウトしました（10分）。しばらく後に再度お試しください。', 'error');
}

/* ── ローディング制御 ── */
function showLoading(msg) {
  loadingMsg.textContent = msg;
  loadingSteps.style.display = 'none';
  loadingElapsed.style.display = 'none';
  loadingOverlay.classList.add('active');
  uploadBtn.disabled = true;
}

function _enterPollingUI() {
  loadingMsg.textContent = 'AIが履歴書を解析中...';
  loadingSteps.style.display = 'flex';
  loadingElapsed.style.display = 'block';
  _setStep(2);
  _startElapsedTimer();
}

function hideLoading() {
  loadingOverlay.classList.remove('active');
  uploadBtn.disabled = fileEntries.length === 0;
  clearInterval(elapsedTimer);
  elapsedTimer = null;
}

function _setStep(active) {
  ['step1', 'step2', 'step3'].forEach((id, i) => {
    const el = document.getElementById(id);
    el.classList.remove('active', 'done');
    if (i + 1 < active)  el.classList.add('done');
    if (i + 1 === active) el.classList.add('active');
  });
}

function _startElapsedTimer() {
  const start = Date.now();
  elapsedTimer = setInterval(() => {
    const secs = Math.floor((Date.now() - start) / 1000);
    const m = Math.floor(secs / 60).toString().padStart(2, '0');
    const s = (secs % 60).toString().padStart(2, '0');
    loadingElapsed.textContent = `経過時間: ${m}:${s}`;
  }, 1000);
}

/* ── ユーティリティ ── */
function _sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

function _formatBytes(bytes) {
  if (bytes < 1024)         return bytes + ' B';
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}

function _esc(str) {
  return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

/* ── トースト ── */
let toastTimer;
function showToast(msg, type = 'error') {
  toast.textContent = msg;
  toast.className = `toast ${type} show`;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toast.classList.remove('show'), 4000);
}

/* ── 初期化 ── */
_updateUI();
