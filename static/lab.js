(() => {
  'use strict';
  const $ = id => document.getElementById(id);
  let token = '';
  const el = (tag, text, cls) => {const n = document.createElement(tag); if (text !== undefined) n.textContent = text; if (cls) n.className = cls; return n;};
  const percent = x => `${Math.round(x * 100)}%`;
  function link(label, url, cls) {
    const a = el('a', label, cls);
    if (typeof url === 'string' && /^https?:\/\//.test(url)) {a.href = url; a.target = '_blank'; a.rel = 'noopener noreferrer';}
    return a;
  }
  async function get(path) {
    const r = await fetch(path, {headers: token ? {Authorization: `Bearer ${token}`} : {}});
    if (!r.ok) {const error = new Error(`Evidence request failed (${r.status})`); error.status = r.status; throw error;}
    return r.json();
  }
  function detail(run) {
    const target = $('lab-detail'); target.replaceChildren();
    const meta = el('div', undefined, 'detail-meta');
    meta.append(el('span', run.mode, 'tag'), el('span', run.retrieval_mode, 'tag'), el('span', run.prompt_version, 'tag'));
    target.append(meta, el('p', `${run.focus} / ${run.theme} · ${run.id.slice(0, 10)}`, 'muted'));
    if (run.cached) target.append(el('p', 'Saved adventure: no new provider calls. Source run evidence is shown below.', 'lab-footnote'));
    const words = el('div', undefined, 'detail-list');
    for (const row of (run.candidates || [])) {
      const w = el('div', undefined, 'detail-word');
      w.append(el('strong', `${row.word.badaga} · ${row.word.english}`));
      w.append(el('span', row.reason === 'requested-review' ? 'Requested review priority' : `BM25 rank ${row.lexical_rank || '—'} / vector rank ${row.semantic_rank || '—'} / RRF ${row.rrf_score}`));
      words.append(w);
    }
    target.append(words);
    for (const s of run.stages || []) {
      const row = el('div', undefined, 'detail-stage');
      row.append(el('span', `${s.provider} / ${s.stage}`), el('strong', `${s.latency_ms} ms`)); target.append(row);
    }
    if (run.degraded_reason) target.append(el('p', `Retrieval/fallback note: ${run.degraded_reason}`, 'lab-footnote'));
    if (run.trace_url) target.append(link('Inspect this Braintrust trace ↗', run.trace_url, 'detail-trace'));
  }
  function renderStatus(data) {
    $('lab-services').replaceChildren(...['nebius', 'pinecone', 'braintrust'].map(name => {
      const item = el('div', undefined, 'service-chip');
      const status = data[name].status;
      item.append(el('span', undefined, `service-dot ${status === 'connected' ? 'connected' : ''}`), el('strong', name), el('span', status)); return item;
    }));
    const runs = data.runs || [], latest = runs[0];
    const stats = [[data.word_count, 'source-documented words'], [data.dimensions, 'embedding dimensions'],
      [runs.reduce((sum, r) => sum + r.input_tokens + r.output_tokens, 0).toLocaleString(), 'reported tokens · last 20 requests'],
      [latest ? `${(latest.latency_ms / 1000).toFixed(2)}s` : '—', 'latest request latency']];
    $('lab-stats').replaceChildren(...stats.map(([value, label]) => {const div = el('div', undefined, 'lab-stat'); div.append(el('strong', value), el('span', label)); return div;}));
    $('lab-runs').replaceChildren(...runs.map(r => {
      const row = el('tr'); const mode = el('td'); mode.append(el('span', r.mode, 'mode-pill'));
      const action = el('td'); const b = el('button', 'Inspect ↗', 'text-button'); b.addEventListener('click', () => detail(r)); action.append(b);
      row.append(el('td', `${r.focus} / ${r.theme}`), mode, el('td', r.input_tokens + r.output_tokens), el('td', `${(r.latency_ms/1000).toFixed(2)}s`), action); return row;
    }));
    if (!runs.length) {$('lab-runs').append(el('tr', 'Create an adventure to start the ledger.'));}
    if (latest) detail(runs.find(r => !r.cached) || latest);
    $('grafana-link').href = data.grafana_url; $('prometheus-link').href = data.prometheus_url;
  }
  function renderEvals(data) {
    if (data.status === 'not-run') {$('eval-description').textContent = 'Run python -m hatti.cli eval to measure this installation.'; return;}
    $('eval-description').textContent = `${data.retrieval_cases.length} public retrieval cases · ${data.story_cases.length} generated adventures · ${data.guard_cases.length} grounding checks · ${data.generated_at}. Dataset ${data.dataset_version}.`;
    const items = [[percent(data.metrics.bm25.recall_at_5), 'BM25 recall@5'], [percent(data.metrics.hybrid.recall_at_5), 'Hybrid recall@5'],
      [percent(data.metrics.hybrid.mrr), 'Hybrid mean reciprocal rank'], [percent(data.metrics.story_grounding), 'Story word references grounded'], [percent(data.metrics.guard_pass_rate), 'Grounding checks passed']];
    $('eval-metrics').replaceChildren(...items.map(([v,l]) => {const div = el('div', undefined, 'eval-metric'); div.append(el('strong', v),el('span',l)); return div;}));
    $('eval-cases').replaceChildren(...data.retrieval_cases.map(c => {
      const row = el('tr'); row.append(el('td', c.query), el('td', c.expected.join(', ')), el('td', percent(c.bm25.recall_at_5)), el('td', percent(c.hybrid.recall_at_5))); return row;
    }));
    if (data.braintrust_url) {$('eval-braintrust').href = data.braintrust_url; $('eval-braintrust').hidden = false;}
  }
  async function refresh() {
    $('refresh-lab').disabled = true;
    try {
      const [status, evals] = await Promise.all([get('/api/ai/status'), get('/api/ai/evals')]);
      renderStatus(status); renderEvals(evals); $('lab-error').hidden = true; $('ops-unlock').hidden = true;
    } catch (error) {
      $('lab-error').textContent = error.status === 403 ? 'Operations evidence is private. Open from localhost or supply the configured operations token.' : error.message;
      $('lab-error').hidden = false; $('ops-unlock').hidden = error.status !== 403;
    } finally {$('refresh-lab').disabled = false;}
  }
  $('refresh-lab').addEventListener('click', refresh);
  $('ops-unlock').addEventListener('submit', event => {event.preventDefault(); token = $('ops-token').value; $('ops-token').value = ''; refresh();});
  refresh();
})();
