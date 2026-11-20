const pages = ['dashboard', 'analyze', 'performance', 'about'];
const $ = id => document.getElementById(id);
let modelChart;

function route() {
  let name = location.hash.slice(1) || 'dashboard';
  if (!pages.includes(name)) name = 'dashboard';
  pages.forEach(page => $(`page-${page}`).classList.toggle('active', page === name));
  document.querySelectorAll('.nav-link').forEach(link => link.classList.toggle('active', link.dataset.page === name));
  closeNavigation();
  if (name === 'performance') loadMetrics();
}

function closeNavigation() {
  $('main-nav').classList.remove('open');
  $('menu-toggle').setAttribute('aria-expanded', 'false');
  $('menu-toggle').setAttribute('aria-label', 'Open navigation');
}

function toggleNavigation() {
  const open = !$('main-nav').classList.contains('open');
  $('main-nav').classList.toggle('open', open);
  $('menu-toggle').setAttribute('aria-expanded', String(open));
  $('menu-toggle').setAttribute('aria-label', open ? 'Close navigation' : 'Open navigation');
}

async function checkHealth() {
  const fileMode = location.protocol === 'file:';
  $('file-warning').hidden = !fileMode;
  let label = fileMode ? 'Open local web server' : 'Backend unavailable';
  let detail = fileMode ? 'Use http://localhost:5500 for API access' : 'Java API could not be reached';
  let ready = false;
  if (!fileMode) {
    try {
      const health = await api('/health');
      if (!health || health.status !== 'ok') {
        label = 'Backend unavailable';
        detail = 'Java API returned an unhealthy or invalid response';
      } else if (!health.ml || health.ml.status !== 'ok') {
        label = 'ML service offline';
        detail = 'Java is online; Python ML service is unavailable';
      } else if (health.ml.model_available !== true) {
        label = 'Model unavailable';
        detail = 'ML service is online; saved model is unavailable';
      } else {
        ready = true;
        label = 'Services online';
        detail = 'Java API, ML service, and model are ready';
      }
    } catch (error) {
      label = 'Backend unavailable';
      detail = error.message.includes('wake') ? 'Render service is waking; retry shortly' : 'Java API could not be reached';
    }
  }
  $('service-label').textContent = label;
  $('service-detail').textContent = detail;
  $('dashboard-service-label').textContent = ready ? 'Java and ML services are ready' : label;
  $('top-status').textContent = ready ? 'Model Ready' : label;
  document.querySelectorAll('.service-pulse').forEach(dot => dot.classList.toggle('online', ready));
  document.querySelector('.model-status i').classList.toggle('status-offline', !ready);
}

function esc(value) {
  return String(value ?? '').replace(/[&<>"']/g, character => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
  })[character]);
}

function renderBrandIndicators(result) {
  const source = result.brandIndicators ?? result.brand_indicators ?? result.signals?.brandImpersonation;
  if (!source) return '';
  const values = Array.isArray(source) ? source : [source];
  const labels = values.map(value => typeof value === 'string' ? value : value?.message || value?.indicator || value?.brand).filter(Boolean);
  if (!labels.length) return '';
  return `<section class="result-section"><h3>Brand indicators</h3><ul class="reason-list">${labels.map(label => `<li>${esc(label)}</li>`).join('')}</ul></section>`;
}

function showResult(result) {
  $('result-placeholder').hidden = true;
  const card = $('result-card');
  card.hidden = false;

  const classification = String(result.classification || 'UNKNOWN').toUpperCase();
  const phishing = classification === 'PHISHING';
  const risk = String(result.riskLevel || 'LOW').toUpperCase();
  const riskClass = ['LOW', 'MEDIUM', 'HIGH'].includes(risk) ? risk.toLowerCase() : 'low';
  const confidence = result.confidence == null
    ? 'Not available'
    : `${Math.round(Number(result.confidence) * 100)}%${result.confidenceType === 'uncalibrated_model_probability' ? ' model confidence · uncalibrated' : ' decision score · not calibrated'}`;
  const keywords = Object.values(result.keywords || {}).flat().filter(Boolean);
  const urls = Array.isArray(result.urls) ? result.urls : [];
  const reasons = Array.isArray(result.reasons) ? result.reasons : [];
  const features = result.features || {};
  const explanation = reasons.length
    ? `<ul class="reason-list">${reasons.map(reason => `<li>${esc(reason)}</li>`).join('')}</ul>`
    : '<span class="signal-empty">No explanation was provided by the analysis service.</span>';
  const keywordContent = keywords.length
    ? `<div class="keyword-pills">${keywords.map(word => `<span class="keyword-pill">${esc(word)}</span>`).join('')}</div>`
    : '<span class="signal-empty">No configured phrases detected.</span>';
  const urlContent = urls.length
    ? urls.map(item => `<div class="url-item">${esc(item.url || item.host || 'URL detected')}${item.indicators?.length ? `<small>${esc(item.indicators.join(' · '))}</small>` : ''}</div>`).join('')
    : '<span class="signal-empty">No links found. Submitted URLs are never opened.</span>';

  card.innerHTML = `
    <div class="result-banner ${phishing ? 'phishing' : ''}">
      <div class="result-topline"><div><div class="result-kicker">MODEL CLASSIFICATION</div>
        <div class="result-classification">${phishing ? 'Phishing' : esc(classification === 'SAFE' ? 'Likely safe' : classification)}</div>
        <div class="confidence">${esc(confidence)}</div></div>
        <span class="risk-pill ${riskClass}">${esc(risk)} risk</span>
      </div>
    </div>
    <section class="result-section"><h3>Why it was flagged</h3>${explanation}</section>
    <section class="result-section"><h3>Suspicious language</h3>${keywordContent}</section>
    ${renderBrandIndicators(result)}
    <section class="result-section"><h3>Extracted links · ${urls.length}</h3>${urlContent}</section>
    <section class="result-section"><h3>Message details</h3><div class="message-details">${Number(features.emailLength || 0).toLocaleString()} characters · ${Number(features.wordCount || 0).toLocaleString()} words · ${Number(features.urlCount ?? urls.length)} links</div></section>`;
}

async function analyze() {
  const content = $('email-text').value;
  const error = $('form-error');
  error.hidden = true;
  if (!content.trim()) {
    error.textContent = 'Paste some email content before starting the analysis.';
    error.hidden = false;
    return;
  }

  const button = $('analyze-button');
  button.disabled = true;
  $('loading-label').hidden = false;
  try {
    showResult(await api('/analyze', { method: 'POST', body: JSON.stringify({ emailText: content }) }));
  } catch (exception) {
    error.textContent = exception.message || 'The analysis could not be completed. Try again.';
    error.hidden = false;
  } finally {
    button.disabled = false;
    $('loading-label').hidden = true;
  }
}

function metricValue(value) {
  return Number.isFinite(Number(value)) ? `${(Number(value) * 100).toFixed(1)}%` : 'Not available';
}

function renderMetricSummary(metrics) {
  const selected = metrics || {};
  const cards = [
    ['Accuracy', selected.accuracy],
    ['Precision', selected.precision],
    ['Recall', selected.recall],
    ['F1 score', selected.f1]
  ];
  $('metric-summary-grid').innerHTML = cards.map(([label, value]) => `
    <article class="metric-card glass-card"><span>${label}</span><strong>${metricValue(value)}</strong><small>Held-out test split</small></article>`).join('');
}

async function loadMetrics() {
  try {
    const report = await api('/metrics');
    $('metrics-empty').hidden = true;
    $('metrics-content').hidden = false;
    $('best-model-tag').textContent = report.best_model || 'Selected model';
    $('selected-model-name').textContent = report.best_model || 'Not available';

    const entries = Object.entries(report.metrics || {});
    const selected = report.metrics?.[report.best_model];
    renderMetricSummary(selected);
    if (selected?.confusion_matrix) {
      const matrix = selected.confusion_matrix;
      $('confusion-matrix').innerHTML = `<table class="matrix"><tr><th></th><th>Predicted safe</th><th>Predicted phishing</th></tr><tr><th>Actual safe</th><td class="diagonal">${Number(matrix[0]?.[0] ?? 0).toLocaleString()}</td><td>${Number(matrix[0]?.[1] ?? 0).toLocaleString()}</td></tr><tr><th>Actual phishing</th><td>${Number(matrix[1]?.[0] ?? 0).toLocaleString()}</td><td class="diagonal">${Number(matrix[1]?.[1] ?? 0).toLocaleString()}</td></tr></table>`;
    } else {
      $('confusion-matrix').innerHTML = '<p class="signal-empty">Confusion matrix not available.</p>';
    }

    const datasets = report.dataset_report || [];
    $('dataset-details').innerHTML = datasets.map(dataset => `
      <div class="dataset-card"><strong>${esc(dataset.file)}</strong><span>${Number(dataset.usable || 0).toLocaleString()} usable of ${Number(dataset.rows || 0).toLocaleString()} rows<br>${esc(JSON.stringify(dataset.label_counts || {}))}</span></div>`).join('') + `
      <div class="dataset-card"><strong>Evaluation split</strong><span>${Number(report.train_rows || 0).toLocaleString()} train · ${Number(report.test_rows || 0).toLocaleString()} test<br>${Number(report.duplicates_removed || 0).toLocaleString()} exact duplicates removed</span></div>`;
    drawChart(entries, report.best_model);
  } catch (exception) {
    $('metrics-content').hidden = true;
    $('metrics-empty').hidden = false;
    $('metrics-error').textContent = exception.message || 'The model evaluation report could not be loaded.';
  }
}

function drawChart(entries, selectedName) {
  if (!window.Chart) return;
  const canvas = $('model-chart');
  if (modelChart) modelChart.destroy();
  const context = canvas.getContext('2d');
  const gradient = context.createLinearGradient(0, 0, 0, 230);
  gradient.addColorStop(0, 'rgba(70, 235, 255, .95)');
  gradient.addColorStop(.48, 'rgba(70, 125, 255, .83)');
  gradient.addColorStop(1, 'rgba(151, 55, 255, .58)');
  const selectedGradient = context.createLinearGradient(0, 0, 0, 230);
  selectedGradient.addColorStop(0, '#b94cff');
  selectedGradient.addColorStop(.55, '#7751ff');
  selectedGradient.addColorStop(1, 'rgba(47, 122, 255, .65)');

  modelChart = new Chart(canvas, {
    type: 'bar',
    data: {
      labels: entries.map(([name]) => name),
      datasets: [{
        data: entries.map(([, values]) => Number(values.f1) || 0),
        backgroundColor: entries.map(([name]) => name === selectedName ? selectedGradient : gradient),
        borderColor: entries.map(([name]) => name === selectedName ? '#d4a6ff' : 'rgba(89,230,255,.74)'),
        borderWidth: 1,
        borderRadius: 8,
        maxBarThickness: 46
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: { backgroundColor: 'rgba(8,13,53,.96)', borderColor: 'rgba(85,239,255,.4)', borderWidth: 1, titleColor: '#fff', bodyColor: '#d6e2ff', callbacks: { label: item => ` F1 score ${(item.raw * 100).toFixed(1)}%` } }
      },
      scales: {
        y: { beginAtZero: true, max: 1, ticks: { color: '#b4c2eb', callback: value => `${Math.round(value * 100)}%`, font: { size: 9 } }, grid: { color: 'rgba(174,194,255,.12)' }, border: { display: false } },
        x: { ticks: { color: '#c4d0f2', font: { size: 9 } }, grid: { display: false }, border: { color: 'rgba(174,194,255,.2)' } }
      }
    }
  });
}

document.querySelectorAll('.nav-link').forEach(link => link.addEventListener('click', () => {
  if (location.hash === link.getAttribute('href')) route();
}));
window.addEventListener('hashchange', route);
$('menu-toggle').addEventListener('click', toggleNavigation);
window.addEventListener('keydown', event => { if (event.key === 'Escape') closeNavigation(); });
$('analyze-button').addEventListener('click', analyze);
$('clear-button').addEventListener('click', () => {
  $('email-text').value = '';
  $('char-count').textContent = '0 / 50,000';
  $('form-error').hidden = true;
  $('result-card').hidden = true;
  $('result-placeholder').hidden = false;
  $('email-text').focus();
});
$('email-text').addEventListener('input', event => {
  $('char-count').textContent = `${event.target.value.length.toLocaleString()} / 50,000`;
});
$('email-text').addEventListener('keydown', event => {
  if ((event.ctrlKey || event.metaKey) && event.key === 'Enter') analyze();
});
route();
checkHealth();
