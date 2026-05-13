/**
 * TalentLens AI — Frontend Application Logic
 * Handles uploads, API calls, and result rendering.
 */

const API_BASE = window.location.origin;

// ─── DOM References ───
const athleteDropzone = document.getElementById('athlete-dropzone');
const userDropzone = document.getElementById('user-dropzone');
const athleteFileInput = document.getElementById('athlete-file-input');
const userFileInput = document.getElementById('user-file-input');
const athletePreview = document.getElementById('athlete-preview');
const userPreview = document.getElementById('user-preview');
const athletePreviewVideo = document.getElementById('athlete-preview-video');
const userPreviewVideo = document.getElementById('user-preview-video');
const athleteFilename = document.getElementById('athlete-filename');
const userFilename = document.getElementById('user-filename');
const athleteRemove = document.getElementById('athlete-remove');
const userRemove = document.getElementById('user-remove');
const exerciseSelect = document.getElementById('exercise-select');
const btnCompare = document.getElementById('btn-compare');
const btnRestart = document.getElementById('btn-restart');
const processingOverlay = document.getElementById('processing-overlay');
const processingText = document.getElementById('processing-text');
const uploadSection = document.getElementById('upload-section');
const heroSection = document.getElementById('hero-section');
const resultsSection = document.getElementById('results-section');
const navStatus = document.getElementById('nav-status');

// ─── State ───
let athleteFile = null;
let userFile = null;
let currentResult = null;

// ─── Helpers ───
function setStatus(text, type) {
  const dot = navStatus.querySelector('.status-dot');
  navStatus.querySelector('.status-dot + *') || navStatus.lastChild;
  const colors = { ready: '#22c55e', processing: '#f59e0b', error: '#ef4444' };
  dot.style.background = colors[type] || colors.ready;
  dot.style.boxShadow = `0 0 8px ${colors[type] || colors.ready}80`;
  navStatus.childNodes[navStatus.childNodes.length - 1].textContent = ' ' + text;
}

function updateCompareButton() {
  btnCompare.disabled = !(athleteFile && userFile);
}

function scoreColor(value, max) {
  const ratio = value / max;
  if (ratio >= 0.75) return 'var(--success)';
  if (ratio >= 0.5) return 'var(--warning)';
  return 'var(--danger)';
}

// ─── Upload Logic ───
function setupDropzone(dropzone, fileInput, previewEl, videoEl, filenameEl, removeBtn, setFile) {
  const card = dropzone.parentElement;

  dropzone.addEventListener('click', () => fileInput.click());
  dropzone.addEventListener('keydown', (e) => { if (e.key === 'Enter') fileInput.click(); });

  dropzone.addEventListener('dragover', (e) => { e.preventDefault(); dropzone.classList.add('drag-over'); });
  dropzone.addEventListener('dragleave', () => dropzone.classList.remove('drag-over'));
  dropzone.addEventListener('drop', (e) => {
    e.preventDefault(); dropzone.classList.remove('drag-over');
    const files = e.dataTransfer.files;
    if (files.length > 0) handleFile(files[0]);
  });

  fileInput.addEventListener('change', () => {
    if (fileInput.files.length > 0) handleFile(fileInput.files[0]);
  });

  removeBtn.addEventListener('click', () => {
    setFile(null);
    previewEl.hidden = true;
    dropzone.hidden = false;
    videoEl.src = '';
    fileInput.value = '';
    updateCompareButton();
  });

  function handleFile(file) {
    if (!file.type.startsWith('video/') && !file.name.match(/\.(mp4|mov|avi|mkv)$/i)) {
      alert('Please upload a video file (MP4, MOV, AVI, or MKV)');
      return;
    }
    setFile(file);
    const url = URL.createObjectURL(file);
    videoEl.src = url;
    filenameEl.textContent = file.name;
    dropzone.hidden = true;
    previewEl.hidden = false;
    updateCompareButton();
  }
}

setupDropzone(athleteDropzone, athleteFileInput, athletePreview, athletePreviewVideo, athleteFilename, athleteRemove, (f) => { athleteFile = f; });
setupDropzone(userDropzone, userFileInput, userPreview, userPreviewVideo, userFilename, userRemove, (f) => { userFile = f; });

// ─── Fetch Actions ───
async function loadActions() {
  try {
    const res = await fetch(`${API_BASE}/api/actions`);
    const data = await res.json();
    exerciseSelect.innerHTML = '';
    (data.actions || []).forEach(action => {
      const opt = document.createElement('option');
      opt.value = action;
      opt.textContent = action.charAt(0).toUpperCase() + action.slice(1);
      exerciseSelect.appendChild(opt);
    });
  } catch (e) {
    console.warn('Could not load actions, using defaults');
  }
}
loadActions();

// ─── Compare ───
btnCompare.addEventListener('click', async () => {
  if (!athleteFile || !userFile) return;

  processingOverlay.hidden = false;
  setStatus('Processing', 'processing');
  processingText.textContent = 'Uploading videos and extracting poses...';

  const formData = new FormData();
  formData.append('athlete_video', athleteFile);
  formData.append('user_video', userFile);
  formData.append('action', exerciseSelect.value);

  try {
    const res = await fetch(`${API_BASE}/api/compare`, { method: 'POST', body: formData });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Server error' }));
      throw new Error(err.detail || `HTTP ${res.status}`);
    }
    const data = await res.json();
    currentResult = data;
    renderResults(data);
    heroSection.style.display = 'none';
    uploadSection.style.display = 'none';
    resultsSection.hidden = false;
    resultsSection.scrollIntoView({ behavior: 'smooth' });
    setStatus('Complete', 'ready');
  } catch (err) {
    alert('Analysis failed: ' + err.message);
    setStatus('Error', 'error');
  } finally {
    processingOverlay.hidden = true;
  }
});

// ─── Restart ───
btnRestart.addEventListener('click', () => {
  resultsSection.hidden = true;
  heroSection.style.display = '';
  uploadSection.style.display = '';
  currentResult = null;
  setStatus('Ready', 'ready');
  window.scrollTo({ top: 0, behavior: 'smooth' });
});

// ─── Video Toggle ───
document.getElementById('video-toggle').addEventListener('click', (e) => {
  const btn = e.target.closest('.toggle-btn');
  if (!btn || !currentResult) return;

  document.querySelectorAll('#video-toggle .toggle-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  const mode = btn.dataset.mode;

  const athleteVideo = document.getElementById('athlete-result-video');
  const userVideo = document.getElementById('user-result-video');

  if (mode === 'original') {
    athleteVideo.src = currentResult.athlete_original_video_url;
    userVideo.src = currentResult.user_original_video_url;
  } else {
    athleteVideo.src = currentResult.athlete_comparison_video_url || currentResult.athlete.annotated_video_url;
    userVideo.src = currentResult.user_comparison_video_url || currentResult.user.annotated_video_url;
  }
});

// ─── Render Results ───
function renderResults(data) {
  const comparison = data.comparison;
  const athlete = data.athlete;
  const user = data.user;
  const simScore = comparison.similarity_score || 0;

  // Score ring
  const circumference = 2 * Math.PI * 70;
  const offset = circumference - (simScore / 100) * circumference;
  document.getElementById('score-ring-fill').style.strokeDasharray = circumference;
  setTimeout(() => {
    document.getElementById('score-ring-fill').style.strokeDashoffset = offset;
  }, 100);

  // Animated counter
  animateCounter('score-value', 0, Math.round(simScore), 1200);

  // Label
  document.getElementById('score-title').textContent = comparison.label || 'Analysis Complete';
  document.getElementById('score-assessment').textContent =
    simScore >= 75 ? 'The user\'s form closely matches the athlete reference.' :
    simScore >= 50 ? 'Moderate similarity detected — several areas need improvement.' :
    'Significant form differences detected — review the feedback below.';

  // Chips
  const chipsEl = document.getElementById('score-chips');
  chipsEl.innerHTML = '';
  (comparison.feedback_messages || []).forEach(msg => {
    const chip = document.createElement('span');
    chip.className = 'score-chip';
    chip.textContent = msg;
    chipsEl.appendChild(chip);
  });

  // Videos
  const athleteVideo = document.getElementById('athlete-result-video');
  const userVideo = document.getElementById('user-result-video');
  athleteVideo.src = data.athlete_comparison_video_url || athlete.annotated_video_url;
  userVideo.src = data.user_comparison_video_url || user.annotated_video_url;

  // Panel stats
  document.getElementById('athlete-stats').textContent =
    `${athlete.prediction.predicted_label} • ${(athlete.prediction.confidence * 100).toFixed(0)}% • ${athlete.rep_count} reps`;
  document.getElementById('user-stats').textContent =
    `${user.prediction.predicted_label} • ${(user.prediction.confidence * 100).toFixed(0)}% • ${user.rep_count} reps`;

  // Metrics grid
  const metricsData = [
    { label: 'Joint Angle Diff', value: comparison.joint_angle_difference, unit: '°', max: 50 },
    { label: 'Movement Smoothness', value: comparison.movement_smoothness, unit: '', max: 100 },
    { label: 'Temporal Consistency', value: comparison.temporal_consistency, unit: '', max: 100 },
    { label: 'Avg Posture Error', value: comparison.average_posture_error, unit: '°', max: 50 },
  ];
  const metricsGrid = document.getElementById('metrics-grid');
  metricsGrid.innerHTML = '';
  metricsData.forEach(m => {
    const pct = Math.min((m.value / m.max) * 100, 100);
    const color = m.label.includes('Error') || m.label.includes('Diff') ?
      scoreColor(m.max - m.value, m.max) : scoreColor(m.value, m.max);
    metricsGrid.innerHTML += `
      <div class="metric-card">
        <div class="metric-label">${m.label}</div>
        <div class="metric-value" style="color:${color}">${m.value.toFixed(1)}${m.unit}</div>
        <div class="metric-bar"><div class="metric-bar-fill" style="width:${pct}%;background:${color}"></div></div>
      </div>`;
  });

  // Breakdown grid (user scores)
  const userScores = user.score_details || {};
  const breakdownData = [
    { label: 'Depth Score', value: userScores.depth_score || 0 },
    { label: 'Form Score', value: userScores.form_score || 0 },
    { label: 'Consistency Score', value: userScores.consistency_score || 0 },
    { label: 'Symmetry Score', value: userScores.symmetry_score || 0 },
  ];
  const breakdownGrid = document.getElementById('breakdown-grid');
  breakdownGrid.innerHTML = '';
  breakdownData.forEach(b => {
    const color = scoreColor(b.value, 100);
    breakdownGrid.innerHTML += `
      <div class="breakdown-card">
        <div class="breakdown-header">
          <span class="breakdown-label">${b.label}</span>
          <span class="breakdown-value" style="color:${color}">${b.value.toFixed(1)}</span>
        </div>
        <div class="breakdown-bar"><div class="breakdown-bar-fill" style="width:${b.value}%;background:${color}"></div></div>
      </div>`;
  });

  // Joint error chart
  const jointErrors = comparison.per_joint_error || {};
  const barChart = document.getElementById('bar-chart');
  barChart.innerHTML = '';
  const maxError = Math.max(...Object.values(jointErrors), 1);
  const jointNames = {
    left_elbow: 'L.Elbow', right_elbow: 'R.Elbow',
    left_shoulder: 'L.Shoulder', right_shoulder: 'R.Shoulder',
    left_knee: 'L.Knee', right_knee: 'R.Knee',
    body_line: 'Body Line'
  };
  Object.entries(jointErrors).forEach(([key, val]) => {
    const pct = (val / maxError) * 100;
    const color = val < 8 ? 'var(--success)' : val < 15 ? 'var(--warning)' : 'var(--danger)';
    barChart.innerHTML += `
      <div class="bar-row">
        <span class="bar-label">${jointNames[key] || key}</span>
        <div class="bar-track"><div class="bar-fill" style="width:${pct}%;background:${color}"><span class="bar-val">${val.toFixed(1)}°</span></div></div>
      </div>`;
  });

  // Prediction bars
  const probs = user.prediction.probabilities || {};
  const predBars = document.getElementById('prediction-bars');
  predBars.innerHTML = '';
  Object.entries(probs).sort((a, b) => b[1] - a[1]).forEach(([label, prob]) => {
    const pct = (prob * 100);
    predBars.innerHTML += `
      <div class="pred-row">
        <span class="pred-label">${label}</span>
        <div class="pred-track"><div class="pred-fill" style="width:${pct}%;background:var(--accent-gradient)"><span class="pred-val">${pct.toFixed(1)}%</span></div></div>
      </div>`;
  });
}

function animateCounter(elementId, start, end, duration) {
  const el = document.getElementById(elementId);
  const range = end - start;
  const startTime = performance.now();
  function update(now) {
    const elapsed = now - startTime;
    const progress = Math.min(elapsed / duration, 1);
    const eased = 1 - Math.pow(1 - progress, 3);
    el.textContent = Math.round(start + range * eased);
    if (progress < 1) requestAnimationFrame(update);
  }
  requestAnimationFrame(update);
}
