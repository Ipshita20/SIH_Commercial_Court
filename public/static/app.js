const $ = (id) => document.getElementById(id);

function showToast(message) {
  const toast = $('toast');
  toast.textContent = message;
  toast.classList.add('show');
  setTimeout(() => toast.classList.remove('show'), 2400);
}

function setView(view) {
  $('researchView').classList.toggle('hidden', view !== 'research');
  $('documentsView').classList.toggle('hidden', view !== 'documents');
  document.querySelectorAll('.nav-item').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.view === view);
  });
}

document.querySelectorAll('.nav-item').forEach(btn => {
  btn.addEventListener('click', () => setView(btn.dataset.view));
});

$('heroResearch').addEventListener('click', () => {
  setView('research');
  $('query').focus();
  $('searchCard').scrollIntoView({behavior:'smooth', block:'center'});
});

$('heroDemo').addEventListener('click', () => {
  setView('research');
  $('query').value = 'Is pre-institution mediation mandatory before filing a commercial suit?';
  $('searchCard').scrollIntoView({behavior:'smooth', block:'center'});
  runSearch();
});

document.querySelectorAll('.suggestions button').forEach(btn => {
  btn.addEventListener('click', () => {
    $('query').value = btn.dataset.query;
    runSearch();
  });
});

function renderEvidence(results, targetId) {
  const target = $(targetId);
  target.innerHTML = '';

  if (!results.length) {
    target.innerHTML = '<div class="evidence-card"><div class="evidence-text">No supporting sources found.</div></div>';
    return;
  }

  results.forEach(r => {
    const card = document.createElement('div');
    card.className = 'evidence-card';
    card.innerHTML = `
      <div class="evidence-top">
        <div class="evidence-title">${escapeHtml(r.title)}${r.is_demo ? '<span class="demo-tag">DEMO</span>' : ''}</div>
        <div class="score">${(r.score * 100).toFixed(1)}%</div>
      </div>
      <div class="evidence-source">${escapeHtml(r.source)}</div>
      <div class="evidence-text">${escapeHtml(r.text)}</div>
      <span class="ref">${escapeHtml(r.id)}</span>
    `;
    target.appendChild(card);
  });
}

async function runSearch() {
  const query = $('query').value.trim();
  if (!query) {
    showToast('Enter a legal research question first.');
    $('query').focus();
    return;
  }

  const btn = $('searchBtn');
  btn.disabled = true;
  btn.innerHTML = 'Searching…';

  try {
    const response = await fetch('/api/search', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({query})
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'Search failed');

    const answer = $('answerCard');
    const a = data.answer;
    answer.innerHTML = `
      <h3>${escapeHtml(a.heading)}</h3>
      <div class="answer-summary">${escapeHtml(a.summary)}</div>
      ${a.points.map(p => `<div class="answer-point">${escapeHtml(p)}</div>`).join('')}
    `;

    renderEvidence(data.results, 'evidenceList');
    $('emptyState').classList.add('hidden');
    $('researchResults').classList.remove('hidden');
  } catch (err) {
    showToast(err.message);
  } finally {
    btn.disabled = false;
    btn.innerHTML = '<span>⌕</span> Search';
  }
}

$('searchBtn').addEventListener('click', runSearch);
$('query').addEventListener('keydown', (e) => {
  if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') runSearch();
});

$('pdfInput').addEventListener('change', async (e) => {
  const file = e.target.files[0];
  if (!file) return;
  $('uploadName').textContent = `${file.name} • ${(file.size / 1024).toFixed(0)} KB`;

  const form = new FormData();
  form.append('file', file);
  showToast('Analyzing document…');

  try {
    const response = await fetch('/api/summarize', {method:'POST', body:form});
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'Document analysis failed');

    $('docParties').textContent = data.summary.parties;
    $('docFacts').textContent = data.summary.facts;
    $('docIssues').textContent = data.summary.issues;
    renderEvidence(data.results, 'docSources');
    $('documentResult').classList.remove('hidden');
    showToast('Document analysis complete.');
  } catch (err) {
    showToast(err.message);
  }
});

function escapeHtml(value) {
  return String(value)
    .replaceAll('&','&amp;')
    .replaceAll('<','&lt;')
    .replaceAll('>','&gt;')
    .replaceAll('"','&quot;')
    .replaceAll("'",'&#039;');
}
