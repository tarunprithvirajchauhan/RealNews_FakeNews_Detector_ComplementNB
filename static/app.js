// VeriFact AI - Fake News Detection Platform JavaScript Core

let sampleData = [];
let metricsChartInstance = null;
let isServerOnline = false;
let currentTheme = localStorage.getItem('theme') || 'dark';

document.addEventListener('DOMContentLoaded', () => {
  applyTheme(currentTheme);
  initTabs();
  checkServerStatus();
  fetchSamples();
  initAnalyticsChart();
});

function toggleTheme() {
  currentTheme = currentTheme === 'dark' ? 'light' : 'dark';
  localStorage.setItem('theme', currentTheme);
  applyTheme(currentTheme);
}

function applyTheme(theme) {
  const icon = document.getElementById('themeIcon');
  const label = document.getElementById('themeLabel');

  if (theme === 'light') {
    document.documentElement.setAttribute('data-theme', 'light');
    if (icon) icon.innerText = '☀️';
    if (label) label.innerText = 'Light Mode';
  } else {
    document.documentElement.removeAttribute('data-theme');
    if (icon) icon.innerText = '🌙';
    if (label) label.innerText = 'Dark Mode';
  }
  
  if (metricsChartInstance) {
    updateChartTheme(theme);
  }
}

function updateChartTheme(theme) {
  const textColor = theme === 'light' ? '#475569' : '#94a3b8';
  const gridColor = theme === 'light' ? 'rgba(0, 0, 0, 0.08)' : 'rgba(255, 255, 255, 0.05)';
  
  metricsChartInstance.options.scales.y.grid.color = gridColor;
  metricsChartInstance.options.scales.y.ticks.color = textColor;
  metricsChartInstance.options.scales.x.grid.color = gridColor;
  metricsChartInstance.options.scales.x.ticks.color = textColor;
  metricsChartInstance.options.plugins.legend.labels.color = theme === 'light' ? '#0f172a' : '#f8fafc';
  metricsChartInstance.update();
}

// Tab Switching Handler
function initTabs() {
  const tabs = document.querySelectorAll('.nav-tab');
  tabs.forEach(tab => {
    tab.addEventListener('click', () => {
      tabs.forEach(t => t.classList.remove('active'));
      document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));

      tab.classList.add('active');
      const targetId = tab.getAttribute('data-tab');
      const targetContent = document.getElementById(targetId);
      if (targetContent) {
        targetContent.classList.add('active');
      }
    });
  });
}

// Check Backend Server Status
async function checkServerStatus() {
  const badge = document.getElementById('backendStatusBadge');
  const text = document.getElementById('statusText');

  try {
    const res = await fetch('/api/status');
    if (res.ok) {
      const data = await res.json();
      isServerOnline = true;
      text.innerText = 'Models Active: Clean & Noisy (95.9%)';
      badge.style.background = 'rgba(16, 185, 129, 0.12)';
      badge.style.color = 'var(--accent-emerald)';
    } else {
      throw new Error('Server returned non-200');
    }
  } catch (err) {
    isServerOnline = false;
    text.innerText = 'Fallback Client Engine Active';
    badge.style.background = 'rgba(245, 158, 11, 0.15)';
    badge.style.color = 'var(--accent-amber)';
  }
}

// Fetch Pre-configured Sample Articles
async function fetchSamples() {
  try {
    const res = await fetch('/api/samples');
    if (res.ok) {
      sampleData = await res.json();
    } else {
      sampleData = getFallbackSamples();
    }
  } catch (e) {
    sampleData = getFallbackSamples();
  }
}

function loadSample(sampleId) {
  const sample = sampleData.find(s => s.id === sampleId);
  if (sample) {
    document.getElementById('articleTitle').value = sample.title;
    document.getElementById('articleText').value = sample.text;
  }
}

// Prediction Logic
async function runPrediction() {
  const title = document.getElementById('articleTitle').value.trim();
  const text = document.getElementById('articleText').value.trim();
  const mode = document.getElementById('modelMode').value;
  const resultsContainer = document.getElementById('predictorResults');
  const btnPredict = document.getElementById('btnPredict');

  if (!title && !text) {
    alert('Please enter an article title or body text to analyze.');
    return;
  }

  btnPredict.disabled = true;
  btnPredict.innerHTML = `<div class="spinner"></div> Analyzing...`;

  try {
    let data;
    if (isServerOnline) {
      const res = await fetch('/api/predict', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title, text, mode })
      });
      data = await res.json();
    } else {
      data = simulateFallbackPrediction(title, text, mode);
    }

    renderPredictionCards(data, resultsContainer);
  } catch (err) {
    console.error('Prediction Error:', err);
    alert('Failed to execute prediction. Using client fallback engine.');
    const data = simulateFallbackPrediction(title, text, mode);
    renderPredictionCards(data, resultsContainer);
  } finally {
    btnPredict.disabled = false;
    btnPredict.innerHTML = `<span>🔍</span> Analyze Authenticity`;
  }
}

// Render Prediction Cards
function renderPredictionCards(data, container) {
  container.innerHTML = '';
  container.style.display = 'grid';

  const cardsToRender = [];
  if (data.clean_model && !data.clean_model.error) {
    cardsToRender.push({ name: 'Clean Pipeline Model', key: 'clean_model', res: data.clean_model });
  }
  if (data.noisy_model && !data.noisy_model.error) {
    cardsToRender.push({ name: 'Noisy Robust Model', key: 'noisy_model', res: data.noisy_model });
  }

  cardsToRender.forEach(item => {
    const r = item.res;
    const isFake = r.prediction === 'FAKE';
    const cardClass = isFake ? 'fake' : 'real';

    const card = document.createElement('div');
    card.className = `prediction-card ${cardClass}`;

    const fakeChips = (r.indicators.fake_indicators || []).map(i => `<span class="chip fake">🚨 ${i.word} (${i.impact})</span>`).join(' ');
    const realChips = (r.indicators.real_indicators || []).map(i => `<span class="chip real">✅ ${i.word} (${i.impact})</span>`).join(' ');

    card.innerHTML = `
      <div class="card-header">
        <div class="model-title-tag">
          <span>🧠</span> ${item.name}
        </div>
        <div class="verdict-badge ${cardClass}">${r.prediction}</div>
      </div>

      <div class="confidence-meter-container">
        <div class="meter-header">
          <span>Confidence Score</span>
          <span>${r.confidence}% Confidence</span>
        </div>
        <div class="meter-bar">
          <div class="meter-segment ${cardClass}" style="width: ${r.confidence}%"></div>
        </div>
        <div style="display:flex; justify-content:space-between; font-size:12px; color:var(--text-secondary); margin-top:6px;">
          <span>Real Prob: ${Math.round(r.probability_real * 100)}%</span>
          <span>Fake Prob: ${Math.round(r.probability_fake * 100)}%</span>
        </div>
      </div>

      <div class="indicators-section">
        <div class="indicators-title">Key TF-IDF Term Indicators:</div>
        <div class="chips-container">
          ${fakeChips || realChips ? (fakeChips + ' ' + realChips) : '<span style="font-size:12px; color:var(--text-muted)">Standard vocabulary terms detected</span>'}
        </div>
      </div>

      <div class="accordion-box" style="margin-top:16px;">
        <strong>Cleaned Preprocessed Tokens (${r.token_count || 0}):</strong><br>
        <code>${r.cleaned_text || 'No tokens retained'}</code>
      </div>
    `;

    container.appendChild(card);
  });
}

// Noise Sandbox Simulation
async function runNoiseSimulation() {
  const title = document.getElementById('articleTitle').value.trim() || "Breaking News: Major Official Announcement";
  const text = document.getElementById('articleText').value.trim() || "The government committee released their annual evaluation report on infrastructure developments across major urban transportation sectors.";
  const noiseLevel = parseFloat(document.getElementById('noiseSlider').value);

  const noiseTypes = [];
  if (document.getElementById('chkSwap').checked) noiseTypes.push('swap');
  if (document.getElementById('chkDropChar').checked) noiseTypes.push('drop_char');
  if (document.getElementById('chkDropWord').checked) noiseTypes.push('drop_word');

  const container = document.getElementById('sandboxResults');
  const compGrid = document.getElementById('sandboxComparisonGrid');

  try {
    let data;
    if (isServerOnline) {
      const res = await fetch('/api/simulate-noise', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title, text, noise_level: noiseLevel, noise_types: noiseTypes })
      });
      data = await res.json();
    } else {
      data = simulateFallbackNoise(title, text, noiseLevel);
    }

    document.getElementById('origTextPreview').innerText = title + '\n' + text;
    document.getElementById('noisyTextPreview').innerText = data.noisy_title + '\n' + data.noisy_text;

    compGrid.innerHTML = '';
    renderPredictionCards({ clean_model: data.corrupted_clean_pred, noisy_model: data.corrupted_noisy_pred }, compGrid);

    container.style.display = 'block';
  } catch (e) {
    console.error('Noise simulation error:', e);
  }
}

// Batch Scanner Processing
async function runBatchScan() {
  const rawText = document.getElementById('batchInput').value.trim();
  if (!rawText) {
    alert('Please enter or paste multiple headlines in the textarea.');
    return;
  }

  const lines = rawText.split('\n').filter(l => l.trim().length > 0);
  const items = lines.map((line, idx) => ({ id: idx + 1, title: line, text: line }));

  try {
    let data;
    if (isServerOnline) {
      const res = await fetch('/api/batch-predict', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ items, mode: 'clean' })
      });
      data = await res.json();
    } else {
      data = simulateFallbackBatch(items);
    }

    document.getElementById('batchTotal').innerText = data.summary.total;
    document.getElementById('batchReal').innerText = `${data.summary.real_count} (${data.summary.real_percentage}%)`;
    document.getElementById('batchFake').innerText = `${data.summary.fake_count} (${data.summary.fake_percentage}%)`;

    const tbody = document.getElementById('batchTableBody');
    tbody.innerHTML = '';

    data.results.forEach((row, i) => {
      const tr = document.createElement('tr');
      const isFake = row.prediction === 'FAKE';
      const badgeClass = isFake ? 'fake' : 'real';

      tr.innerHTML = `
        <td>${i + 1}</td>
        <td>${row.title}</td>
        <td><span class="verdict-badge ${badgeClass}" style="font-size:11px; padding:4px 10px;">${row.prediction}</span></td>
        <td><strong>${row.confidence}%</strong></td>
        <td>${Math.round(row.probability_fake * 100)}%</td>
        <td>${Math.round(row.probability_real * 100)}%</td>
      `;
      tbody.appendChild(tr);
    });

    document.getElementById('batchResultsContainer').style.display = 'block';
  } catch (e) {
    console.error('Batch scan error:', e);
  }
}

function loadBatchSamples() {
  const samples = [
    "WASHINGTON (Reuters) - Senate passes landmark infrastructure bill with 68-32 majority vote.",
    "SHOCKING UNBELIEVABLE: Leaked documents reveal secret underground lunar city base!!",
    "Local resident wins argument in online comment section, world peace declared.",
    "BREAKNG!! Scraest rumor surfasin online bout secret govment bio-labs!",
    "Federal Reserve announces 0.25% interest rate benchmark adjustment following inflation report.",
    "Alien spacecraft lands in central park during live television broadcast, officials state.",
    "Health ministry releases updated nutritional guidance for cardiovascular wellness.",
    "MIRACLE CURE DISCOVERED! Doctors hate this one weird trick that cures everything instantly!",
    "Stock markets rally as quarterly tech earnings surpass analyst projections across major indices.",
    "Secret conspiracy committee meeting exposed by whistleblower on social media video."
  ];
  document.getElementById('batchInput').value = samples.join('\n');
}

// Chart.js Metrics Rendering
function initAnalyticsChart() {
  const ctx = document.getElementById('metricsChart');
  if (!ctx) return;

  const textColor = currentTheme === 'light' ? '#475569' : '#94a3b8';
  const gridColor = currentTheme === 'light' ? 'rgba(0, 0, 0, 0.08)' : 'rgba(255, 255, 255, 0.05)';
  const legendColor = currentTheme === 'light' ? '#0f172a' : '#f8fafc';

  metricsChartInstance = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: ['Accuracy', 'Precision (Macro)', 'Recall (Macro)', 'F1-Macro Score'],
      datasets: [
        {
          label: 'Clean Pipeline Model (Clean Data)',
          data: [0.9589, 0.9587, 0.9591, 0.9588],
          backgroundColor: 'rgba(56, 189, 248, 0.7)',
          borderColor: '#38bdf8',
          borderWidth: 1.5
        },
        {
          label: 'Noisy Robust Model (10% Noise Data)',
          data: [0.9596, 0.9595, 0.9598, 0.9595],
          backgroundColor: 'rgba(16, 185, 129, 0.7)',
          borderColor: '#10b981',
          borderWidth: 1.5
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        y: {
          min: 0.90,
          max: 1.0,
          grid: { color: gridColor },
          ticks: { color: textColor }
        },
        x: {
          grid: { color: gridColor },
          ticks: { color: textColor }
        }
      },
      plugins: {
        legend: {
          labels: { color: legendColor, font: { family: 'Inter', size: 13 } }
        }
      }
    }
  });
}

// Lightbox Modal
function openLightbox(src) {
  document.getElementById('lightboxImg').src = src;
  document.getElementById('lightboxModal').classList.add('active');
}
function closeLightbox() {
  document.getElementById('lightboxModal').classList.remove('active');
}

// Fallback Helper Functions (Client-side HEURISTICS when backend server is offline)
function simulateFallbackPrediction(title, text, mode) {
  const combined = (title + ' ' + text).toLowerCase();
  const fakeKeywords = ['shocking', 'unbelievable', 'leaked', 'secret', 'conspiracy', 'whistleblower', 'alien', 'miracle', 'hate this', 'breakng', 'scraest', 'govment'];
  const realKeywords = ['reuters', 'washington', 'senate', 'bipartisan', 'official', 'announced', 'report', 'infrastructure', 'passed', 'ministry', 'spokesman'];

  let fakeCount = fakeKeywords.filter(k => combined.includes(k)).length;
  let realCount = realKeywords.filter(k => combined.includes(k)).length;

  let probFake = 0.15;
  if (fakeCount > 0 || realCount > 0) {
    probFake = (fakeCount * 0.35) / ((fakeCount * 0.35) + (realCount * 0.35) + 0.1);
  } else if (title.toUpperCase() === title && title.length > 15) {
    probFake = 0.75;
  } else {
    probFake = 0.32;
  }
  probFake = Math.min(0.99, Math.max(0.01, probFake));
  const probReal = 1.0 - probFake;
  const isFake = probFake >= 0.5;

  const res = {
    prediction: isFake ? 'FAKE' : 'REAL',
    confidence: Math.round(Math.max(probFake, probReal) * 100),
    probability_fake: Math.round(probFake * 100) / 100,
    probability_real: Math.round(probReal * 100) / 100,
    cleaned_text: combined.replace(/[^a-z0-9\s]/g, '').split(' ').filter(w => w.length > 3).join(' '),
    token_count: combined.split(' ').length,
    indicators: {
      fake_indicators: fakeKeywords.filter(k => combined.includes(k)).map(k => ({ word: k, impact: 0.85 })),
      real_indicators: realKeywords.filter(k => combined.includes(k)).map(k => ({ word: k, impact: 0.88 }))
    }
  };

  return { clean_model: res, noisy_model: res };
}

function simulateFallbackNoise(title, text, level) {
  const noisy_title = title.split(' ').map(w => (Math.random() < level && w.length > 3) ? w.slice(1) + w[0] : w).join(' ');
  const noisy_text = text.split(' ').map(w => (Math.random() < level && w.length > 3) ? w.replace(/[aeiou]/, '') : w).join(' ');
  const pred = simulateFallbackPrediction(noisy_title, noisy_text, 'both');
  return {
    noisy_title,
    noisy_text,
    corrupted_clean_pred: pred.clean_model,
    corrupted_noisy_pred: pred.noisy_model
  };
}

function simulateFallbackBatch(items) {
  let fake_count = 0;
  let real_count = 0;

  const results = items.map(item => {
    const p = simulateFallbackPrediction(item.title, item.text, 'clean').clean_model;
    if (p.prediction === 'FAKE') fake_count++;
    else real_count++;

    return {
      id: item.id,
      title: item.title,
      prediction: p.prediction,
      confidence: p.confidence,
      probability_fake: p.probability_fake,
      probability_real: p.probability_real
    };
  });

  return {
    results,
    summary: {
      total: items.length,
      fake_count,
      real_count,
      fake_percentage: Math.round((fake_count / items.length) * 100),
      real_percentage: Math.round((real_count / items.length) * 100)
    }
  };
}

function getFallbackSamples() {
  return [
    {
      id: 'real_politics',
      category: 'Official News (REAL)',
      title: 'WASHINGTON (Reuters) - U.S. Senate passes bipartisan budget resolution',
      text: 'WASHINGTON (Reuters) - The United States Senate voted on Thursday to approve a bipartisan budget framework...'
    },
    {
      id: 'fake_conspiracy',
      category: 'Sensational Clickbait (FAKE)',
      title: 'SHOCKING BREAKING: Leaked Documents Prove Secret Lunar Base Discovered By Whistleblower!',
      text: 'UNBELIEVABLE! Top secret government files leaked online today reveal that high-ranking officials have been operating...'
    }
  ];
}
