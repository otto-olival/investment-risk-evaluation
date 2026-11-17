const state = { mode: 'regular', selected: null, assessment: null, learning: null, tab: 'risk' };
const $ = (selector) => document.querySelector(selector);

async function request(path, options = {}) {
  const response = await fetch(path, options);
  if (!response.ok) throw new Error((await response.json()).detail || 'Não foi possível carregar os dados.');
  return response.json();
}

function rate(offer) { return `${offer.benchmark || 'Taxa'} + ${offer.spread_annual ?? '—'}% a.a.`; }
function escapeHtml(value = '') { return String(value).replace(/[&<>'"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c])); }

async function selectOffer(slug) {
  state.selected = await request(`/offerings/${slug}`);
  try { state.assessment = await request(`/offerings/${slug}/assessments/latest`); } catch (_) { state.assessment = null; }
  renderOffers(); renderOffer(); renderLesson();
}

function renderOffers() {
  const holder = $('#offers');
  holder.querySelectorAll('.offer').forEach(button => button.classList.toggle('selected', button.dataset.slug === state.selected?.slug));
}

function renderOffer() {
  const root = $('#content'); const offer = state.selected;
  if (!offer) { root.innerHTML = '<p class="placeholder">Escolha uma oferta para iniciar a análise.</p>'; return; }
  const a = state.assessment; const band = a?.risk_band || 'não avaliado';
  root.innerHTML = `
    <div class="title-row"><div><p class="eyebrow">${escapeHtml(offer.asset_type)} · ${escapeHtml(offer.status)}</p><h2>${escapeHtml(offer.name)}</h2><p class="meta">Observado em ${escapeHtml(offer.observed_at)} · ${rate(offer)}</p></div><span class="badge ${band}">${escapeHtml(band)}</span></div>
    <div class="score-panel"><div class="score">${a?.score ?? '—'}<span>/100</span></div><div><strong>${a ? `Confiança ${a.confidence}` : 'Avaliação pendente'}</strong><p>${a ? 'Quanto maior o número, maior o risco conforme a metodologia atual.' : 'A análise só é gerada quando você solicitar.'}</p></div></div>
    <button id="assess" class="primary">${a ? 'Recalcular avaliação' : 'Gerar avaliação'}</button>
    <div class="grid"><div class="box"><h3>Garantias</h3><ul>${offer.guarantees.length ? offer.guarantees.map(g => `<li>${escapeHtml(g.description)} <small>(${escapeHtml(g.registration_status)})</small></li>`).join('') : '<li>Não documentadas na fonte inicial.</li>'}</ul></div>
    <div class="box"><h3>Evidências</h3><ul>${offer.evidence.map(e => `<li><a href="${escapeHtml(e.source_url)}" target="_blank" rel="noreferrer">Fonte de ${escapeHtml(e.collected_at)}</a><br>${escapeHtml(e.excerpt)}</li>`).join('')}</ul></div></div>`;
  $('#assess').onclick = async () => { const button = $('#assess'); button.disabled = true; button.textContent = 'Analisando...'; state.assessment = await request(`/offerings/${offer.slug}/assessments`, { method: 'POST' }); renderOffer(); renderLesson(); };
}

function renderLesson() {
  if (state.mode !== 'didactic') return;
  const root = $('#tab-content'); const offer = state.selected; const assessment = state.assessment;
  if (state.tab === 'risk') { root.innerHTML = !offer ? '<p>Selecione uma oferta no painel acima para ver a explicação.</p>' : `<h3>Como a análise chegou aqui</h3><p>A rota <code>POST /offerings/${offer.slug}/assessments</code> lê fatos persistidos e aplica regras em ordem. Este resultado não é previsão de inadimplência.</p>${assessment ? assessment.findings.map(f => `<div class="finding ${f.score_delta > 0 ? 'positive' : ''}"><strong>${f.score_delta > 0 ? '+' : ''}${f.score_delta} — ${escapeHtml(f.title)}</strong><small>${escapeHtml(f.rationale)}</small></div>`).join('') : '<p>Gere a avaliação para visualizar as regras aplicadas.</p>'}`; }
  if (state.tab === 'database') { const d = state.learning.database; root.innerHTML = `<h3>SQLite: as relações do sistema</h3><p>${escapeHtml(d.explanation)}</p><div class="flow">${d.tables.map(t => `<span><b>${t.name}</b><br>${escapeHtml(t.purpose)}</span>`).join('<b>→</b>')}</div><p>Consulta usada na tela: <code>${escapeHtml(d.example_query)}</code></p>`; }
  if (state.tab === 'api') { const a = state.learning.api; root.innerHTML = `<h3>O caminho de uma requisição</h3><div class="flow">${a.flow.map(item => `<span>${escapeHtml(item)}</span>`).join('<b>→</b>')}</div><p>${escapeHtml(a.explanation)}</p><ul>${a.endpoints.map(e => `<li><code>${escapeHtml(e.method)} ${escapeHtml(e.path)}</code> — ${escapeHtml(e.purpose)}</li>`).join('')}</ul>`; }
  if (state.tab === 'dependencies') { const deps = state.learning.dependencies; root.innerHTML = `<h3>Dependências em execução</h3><p>Dependências são bibliotecas externas declaradas em <code>pyproject.toml</code>. Fixar faixas de versão torna a instalação repetível.</p><ul>${deps.map(d => `<li><code>${escapeHtml(d.name)} ${escapeHtml(d.version)}</code> — ${escapeHtml(d.purpose)}</li>`).join('')}</ul>`; }
}

async function boot() {
  const offers = await request('/offerings'); $('#offer-count').textContent = `${offers.length} itens`;
  $('#offers').innerHTML = offers.map(o => `<button class="offer" data-slug="${o.slug}"><strong>${escapeHtml(o.name)}</strong><small>${o.asset_type} · ${rate(o)}</small></button>`).join('');
  $('#offers').onclick = e => { const button = e.target.closest('.offer'); if (button) selectOffer(button.dataset.slug); };
  state.learning = await request('/learning/overview');
  document.querySelectorAll('.mode').forEach(button => button.onclick = () => { state.mode = button.dataset.mode; document.querySelectorAll('.mode').forEach(b => b.classList.toggle('active', b === button)); $('#didactic').classList.toggle('hidden', state.mode !== 'didactic'); $('#mode-description').textContent = state.mode === 'didactic' ? 'Explore as decisões técnicas, os dados e as regras que formam cada avaliação.' : 'Selecione uma oferta para consultar dados, evidências e sua avaliação de risco.'; renderLesson(); });
  document.querySelectorAll('.tab').forEach(button => button.onclick = () => { state.tab = button.dataset.tab; document.querySelectorAll('.tab').forEach(b => b.classList.toggle('active', b === button)); renderLesson(); });
  if (offers.length) selectOffer(offers[0].slug);
}
boot().catch(error => { $('#content').innerHTML = `<p class="placeholder">Erro ao iniciar: ${escapeHtml(error.message)}</p>`; });
