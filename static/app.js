const $ = (s, r = document) => r.querySelector(s);
const $$ = (s, r = document) => [...r.querySelectorAll(s)];
const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

const VIEWS = ['inicio', 'gerar', 'editor', 'treinos', 'exercicios', 'academia'];
const HEAVY = ['squat', 'hinge', 'push_h', 'push_incl'];
const MEDIUM = ['pull_v', 'pull_h', 'push_v', 'dip', 'lunge', 'hip_thrust', 'tri_compound'];
const LIGHT = ['lat_raise', 'rear_delt', 'front_raise', 'calf', 'calf_seated', 'abs_flex', 'abs_leg', 'abs_stab', 'wrist', 'back_ext'];
const ROT = { iniciante: 'Iniciante', intermediario: 'Intermediário', avancado: 'Avançado', hipertrofia: 'Hipertrofia', forca: 'Força + hipertrofia', definicao: 'Definição' };

let DATA, EX = {}, EQ_NOME = {}, TOTAL_EQ = 0;
let equip = new Set(), plan, aval = null, picker = null, timer = null;

async function api(url, method = 'GET', body) {
  const r = await fetch(url, { method, headers: { 'Content-Type': 'application/json' }, body: body === undefined ? undefined : JSON.stringify(body) });
  if (!r.ok) throw new Error((await r.json().catch(() => ({}))).erro || 'Erro de comunicação com o servidor');
  return r.json();
}

function toast(texto) {
  const t = $('#toast');
  t.textContent = texto; t.hidden = false;
  clearTimeout(toast.t); toast.t = setTimeout(() => (t.hidden = true), 2600);
}

const novoPlano = () => ({ nome: 'Meu treino', nivel: 'intermediario', objetivo: 'hipertrofia', agenda: '', avisos: [], dias: [{ nome: 'Treino A', exercicios: [] }] });
const disponivel = e => e.equip.every(q => equip.has(q));
const estrelas = n => '★'.repeat(n) + '☆'.repeat(3 - n);
const video = e => 'https://www.youtube.com/results?search_query=' + encodeURIComponent('como fazer ' + e.nome + ' execução correta');

function prescricao(ex) {
  const p = ex.padrao, forca = plan.objetivo === 'forca';
  if (p === 'abs_stab') return ['30-60s', 60];
  if (HEAVY.includes(p)) return forca ? ['4-6', 210] : [plan.nivel === 'iniciante' ? '8-12' : '6-10', 150];
  if (MEDIUM.includes(p)) return forca ? ['6-10', 150] : ['8-12', 120];
  if (LIGHT.includes(p)) return [p === 'lat_raise' || p === 'rear_delt' ? '12-20' : '10-15', 60];
  return ['10-15', 75];
}

function tagsEx(e, comMusculo = true) {
  const eq = e.equip.length ? e.equip.map(q => EQ_NOME[q]).join(' + ') : 'Peso corporal';
  return `<div class="tags">${comMusculo ? `<span class="tag">${DATA.musculos[e.musculo]}</span>` : ''}
    <span class="tag star" title="Qualidade para hipertrofia">${estrelas(e.nivel)}</span>
    <span class="tag">${esc(eq)}</span>
    ${disponivel(e) ? '' : '<span class="tag red">Não tem na sua academia</span>'}</div>`;
}

/* ------------------------------------------------------------ navegação */
function rota() {
  let v = location.hash.slice(1);
  if (!VIEWS.includes(v)) v = 'inicio';
  VIEWS.forEach(n => ($('#v-' + n).hidden = n !== v));
  $$('#nav a').forEach(a => a.classList.toggle('on', a.getAttribute('href') === '#' + v));
  window.scrollTo(0, 0);
  if (v === 'gerar') $('#equip-resumo').textContent = `Usando ${equip.size} de ${TOTAL_EQ} equipamentos da sua academia.`;
  if (v === 'editor') { renderEditor(); avaliarAgora(); }
  if (v === 'treinos') carregarTreinos();
  if (v === 'exercicios') renderBib();
}

/* --------------------------------------------------------------- editor */
function renderEditor() {
  $('#plano-nome').value = plan.nome;
  $('#plano-nivel').value = plan.nivel;
  $('#plano-objetivo').value = plan.objetivo;
  $('#plano-agenda').textContent = plan.agenda ? 'Sugestão de dias: ' + plan.agenda : '';
  $('#plano-avisos').innerHTML = (plan.avisos || []).map(a => `<div class="aviso">${esc(a)}</div>`).join('');
  $('#editor-dias').innerHTML = plan.dias.map((d, di) => `
    <section class="day" data-d="${di}">
      <header class="day-head">
        <span class="day-num">${di + 1}</span>
        <input class="day-name" data-f="dia-nome" maxlength="40" value="${esc(d.nome)}" aria-label="Nome do dia">
        <span class="day-time" id="tempo-${di}"></span>
        <button class="icon-btn" data-a="del-dia" title="Remover dia">✕</button>
      </header>
      ${d.exercicios.length ? '<div class="ex-cols"><span>Exercício</span><span>Séries</span><span>Reps</span><span>Desc. (s)</span><span></span></div>' : '<p class="empty">Nenhum exercício ainda.</p>'}
      ${d.exercicios.map((x, xi) => linhaEx(x, xi, d.exercicios.length)).join('')}
      <div class="day-foot"><button class="btn outline small" data-a="add-ex">+ Adicionar exercício</button></div>
    </section>`).join('');
  pintarTempos();
}

function linhaEx(x, xi, total) {
  const e = EX[x.id];
  return `<div class="ex-row" data-x="${xi}">
    <div><div class="ex-name">${esc(e.nome)}</div>${tagsEx(e)}</div>
    <input type="number" min="1" max="10" data-f="series" value="${x.series}" aria-label="Séries">
    <input type="text" maxlength="12" data-f="reps" value="${esc(x.reps)}" aria-label="Repetições">
    <input type="number" min="15" max="600" step="15" data-f="descanso" value="${x.descanso}" aria-label="Descanso em segundos">
    <div class="ex-actions">
      <button class="icon-btn" data-a="up" title="Subir" ${xi === 0 ? 'disabled' : ''}>↑</button>
      <button class="icon-btn" data-a="down" title="Descer" ${xi === total - 1 ? 'disabled' : ''}>↓</button>
      <button class="icon-btn txt" data-a="trocar" title="Trocar por um exercício equivalente">TROCAR</button>
      <a class="icon-btn" href="${video(e)}" target="_blank" rel="noopener" title="Ver execução no YouTube" style="display:grid;place-items:center">▶</a>
      <button class="icon-btn" data-a="del-ex" title="Remover">✕</button>
    </div></div>`;
}

function mudou(redesenhar) {
  try { localStorage.setItem('forja-rascunho', JSON.stringify(plan)); } catch { /* sem armazenamento local */ }
  if (redesenhar) renderEditor();
  clearTimeout(timer);
  timer = setTimeout(avaliarAgora, 300);
}

async function avaliarAgora() {
  try {
    aval = await api('/api/avaliar', 'POST', plan);
    renderAval();
  } catch (e) { toast(e.message); }
}

function pintarTempos() {
  if (!aval) return;
  aval.dias.forEach((d, i) => {
    const el = $('#tempo-' + i);
    if (el) el.innerHTML = d.exercicios ? `<b>~${d.minutos} min</b> · ${d.series} séries` : '';
  });
}

function renderAval() {
  pintarTempos();
  const el = $('#aval');
  if (aval.vazio) {
    el.innerHTML = `<h3>Avaliação</h3><p class="muted">Adicione exercícios ao treino e a nota aparece aqui, atualizada em tempo real.</p>`;
    return;
  }
  const C = 2 * Math.PI * 50;
  const nomes = { critico: 'Crítico', alerta: 'Atenção', dica: 'Dica', ok: 'Ponto forte' };
  el.innerHTML = `
    <div class="score">
      <div class="ring"><svg width="112" height="112" viewBox="0 0 112 112">
        <circle class="bg" cx="56" cy="56" r="50"/><circle class="fg" cx="56" cy="56" r="50" stroke-dasharray="${C}" stroke-dashoffset="${C * (1 - aval.nota / 100)}"/></svg>
        <div class="score-num">${aval.nota}</div></div>
      <div><div class="muted">Nota do treino</div><div class="score-label">${aval.conceito}</div>
        <div class="muted" style="font-size:13px">${ROT[plan.nivel]} · ${ROT[plan.objetivo]}</div></div>
    </div>
    <h4>Critérios</h4>
    ${aval.criterios.map(c => `<div class="crit"><span>${c.nome}</span><span>${c.pontos.toFixed(0)}/${c.max}</span>
      <div class="bar"><i style="width:${100 * c.pontos / c.max}%"></i></div></div>`).join('')}
    <h4>Diagnóstico</h4>
    ${aval.mensagens.map(m => `<div class="msg ${m.tipo}"><b>${nomes[m.tipo]}</b>${esc(m.texto)}</div>`).join('')}
    <h4>Séries semanais por músculo</h4>
    ${aval.volume.filter(v => v.min > 0 || v.series > 0).map(v => {
      const esc_ = v.max * 1.3;
      return `<div class="vol ${v.status}" title="Recomendado: ${v.min}–${v.max} séries · ${v.freq}x por semana">
        <span>${v.nome}</span>
        <div class="vbar"><div class="zone" style="left:${100 * v.min / esc_}%;width:${100 * (v.max - v.min) / esc_}%"></div>
          <div class="fill" style="width:${Math.min(100, 100 * v.series / esc_)}%"></div></div>
        <span class="n">${v.series} · ${v.freq}x</span></div>`;
    }).join('')}
    <p class="legend">Faixa clara = volume recomendado para o seu nível. Músculos secundários contam meia série. “2x” = frequência semanal.</p>
    <h4>Tempo por sessão</h4>
    ${aval.dias.map(d => `<div class="daytime"><span>${esc(d.nome)}</span><span>${d.exercicios ? `~${d.minutos} min · ${d.exercicios} exercícios` : 'vazio'}</span></div>`).join('')}
    <p class="legend">Inclui aquecimento, execução, descansos e troca de aparelho.</p>`;
}

/* ------------------------------------------------- seletor de exercícios */
function abrirPicker(di, xi = null) {
  picker = { di, xi };
  const ref = xi === null ? null : EX[plan.dias[di].exercicios[xi].id];
  $('#modal-titulo').textContent = ref ? 'Trocar: ' + ref.nome : 'Adicionar exercício';
  $('#pk-busca').value = '';
  $('#pk-musculo').value = ref ? ref.musculo : '';
  $('#modal').hidden = false;
  renderPicker();
  $('#pk-busca').focus();
}

function itemPicker(e) {
  return `<button class="pk-item ${disponivel(e) ? '' : 'off'}" data-a="escolher" data-id="${e.id}">
    <div class="ex-name">${esc(e.nome)}</div>${tagsEx(e)}</button>`;
}

function renderPicker() {
  const q = $('#pk-busca').value.trim().toLowerCase(), m = $('#pk-musculo').value, so = $('#pk-disp').checked;
  const ref = picker.xi === null ? null : EX[plan.dias[picker.di].exercicios[picker.xi].id];
  const noDia = new Set(plan.dias[picker.di].exercicios.map(x => x.id));
  let lista = DATA.exercicios.filter(e => (!m || e.musculo === m) && (!q || e.nome.toLowerCase().includes(q)) &&
    (!so || disponivel(e)) && !noDia.has(e.id));
  lista.sort((a, b) => b.nivel - a.nivel);
  let html;
  if (ref && !q && m === ref.musculo) {
    const mesmo = lista.filter(e => e.padrao === ref.padrao), outros = lista.filter(e => e.padrao !== ref.padrao);
    html = (mesmo.length ? '<p class="pk-sep">Mesmo movimento — substitutos diretos</p>' + mesmo.map(itemPicker).join('') : '') +
      (outros.length ? '<p class="pk-sep">Mesmo músculo — outras opções</p>' + outros.map(itemPicker).join('') : '');
  } else html = lista.map(itemPicker).join('');
  $('#pk-lista').innerHTML = html || '<p class="empty">Nada encontrado. Desmarque “Só os que tenho” para ver todas as opções.</p>';
}

function escolher(id) {
  const dia = plan.dias[picker.di], [reps, descanso] = prescricao(EX[id]);
  if (picker.xi === null) dia.exercicios.push({ id, series: plan.nivel === 'iniciante' ? 2 : 3, reps, descanso });
  else Object.assign(dia.exercicios[picker.xi], { id, reps, descanso });
  $('#modal').hidden = true;
  mudou(true);
}

/* ---------------------------------------------------------- meus treinos */
async function carregarTreinos() {
  const lista = await api('/api/treinos');
  $('#lista-treinos').innerHTML = lista.length ? lista.map(t => `
    <article class="card treino">
      <div class="treino-top"><h3>${esc(t.nome)}</h3><span class="nota" title="Nota">${t.nota}</span></div>
      <div class="tags"><span class="tag">${ROT[t.nivel]}</span><span class="tag">${ROT[t.objetivo]}</span>
        <span class="tag">${t.dias} dias</span><span class="tag">${t.exercicios} exercícios</span></div>
      <span class="muted" style="font-size:12px">Atualizado em ${new Date(t.atualizado).toLocaleString('pt-BR', { dateStyle: 'short', timeStyle: 'short' })}</span>
      <div class="treino-acoes">
        <button class="btn primary small" data-a="abrir-treino" data-id="${t.id}">Abrir</button>
        <button class="btn outline small" data-a="dup-treino" data-id="${t.id}">Duplicar</button>
        <button class="btn outline small" data-a="del-treino" data-id="${t.id}">Excluir</button>
      </div></article>`).join('')
    : '<div class="card"><p>Nenhum treino salvo ainda. <a href="#gerar">Gere um treino</a> ou <a href="#editor">monte o seu</a>.</p></div>';
}

async function salvar() {
  if (!plan.dias.some(d => d.exercicios.length)) return toast('Adicione pelo menos um exercício antes de salvar.');
  let r;
  try { r = plan.id ? await api('/api/treinos/' + plan.id, 'PUT', plan) : await api('/api/treinos', 'POST', plan); }
  catch { r = await api('/api/treinos', 'POST', plan); }
  plan.id = r.id;
  mudou(false);
  toast('Treino salvo em “Meus treinos”.');
}

/* ------------------------------------------------------------ biblioteca */
function renderBib() {
  const q = $('#bib-busca').value.trim().toLowerCase(), m = $('#bib-musculo').value, so = $('#bib-disp').checked;
  let html = '';
  for (const [id, nome] of Object.entries(DATA.musculos)) {
    if (m && m !== id) continue;
    const exs = DATA.exercicios.filter(e => e.musculo === id && (!q || e.nome.toLowerCase().includes(q)) && (!so || disponivel(e)))
      .sort((a, b) => b.nivel - a.nivel);
    if (!exs.length) continue;
    html += `<h3 class="grupo-titulo">${nome} <span class="muted">(${exs.length})</span></h3>` + exs.map(e => `
      <div class="bib-item ${disponivel(e) ? '' : 'off'}"><div class="ex-name">${esc(e.nome)}</div>${tagsEx(e, false)}
        <div class="tags"><span class="tag">${e.composto ? 'Composto' : 'Isolado'}</span><span class="tag">${DATA.padroes[e.padrao]}</span>
        ${e.alongado ? '<span class="tag">Tensão no alongamento</span>' : ''}
        <a href="${video(e)}" target="_blank" rel="noopener">▶ Ver execução</a></div></div>`).join('');
  }
  $('#bib-lista').innerHTML = html || '<p class="empty">Nenhum exercício encontrado.</p>';
}

/* -------------------------------------------------------------- academia */
function renderAcademia() {
  $('#presets').innerHTML = Object.entries(DATA.presets).map(([k, p]) =>
    `<button class="btn outline small" data-a="preset" data-id="${k}">${p.nome}</button>`).join('') +
    `<button class="btn outline small" data-a="preset" data-id="">Desmarcar tudo</button>`;
  $('#equip-grupos').innerHTML = DATA.equipamentos.map(g => `
    <div class="eq-grupo"><h3>${g.grupo}</h3><div class="eq-itens">${g.itens.map(i =>
      `<label class="eq-item"><input type="checkbox" value="${i.id}" ${equip.has(i.id) ? 'checked' : ''}> ${i.nome}</label>`).join('')}</div></div>`).join('');
}

async function salvarEquip() {
  try { await api('/api/equipamentos', 'PUT', [...equip]); } catch (e) { toast(e.message); }
}

/* ---------------------------------------------------------------- eventos */
document.addEventListener('click', async ev => {
  if (ev.target.id === 'modal') return ($('#modal').hidden = true);
  const seg = ev.target.closest('.seg button');
  if (seg) return $$('button', seg.parentElement).forEach(b => b.classList.toggle('on', b === seg));
  const chip = ev.target.closest('#prioridades button');
  if (chip) {
    if (!chip.classList.contains('on') && $$('#prioridades .on').length >= 3) return toast('Escolha no máximo 3 músculos.');
    return chip.classList.toggle('on');
  }
  const b = ev.target.closest('[data-a]');
  if (!b) return;
  const a = b.dataset.a, id = b.dataset.id;
  const di = +b.closest('.day')?.dataset.d, xi = +b.closest('.ex-row')?.dataset.x;
  const exs = plan.dias[di]?.exercicios;
  try {
    if (a === 'fechar-modal') $('#modal').hidden = true;
    else if (a === 'escolher') escolher(id);
    else if (a === 'add-ex') abrirPicker(di);
    else if (a === 'trocar') abrirPicker(di, xi);
    else if (a === 'del-ex') { exs.splice(xi, 1); mudou(true); }
    else if (a === 'up') { [exs[xi - 1], exs[xi]] = [exs[xi], exs[xi - 1]]; mudou(true); }
    else if (a === 'down') { [exs[xi + 1], exs[xi]] = [exs[xi], exs[xi + 1]]; mudou(true); }
    else if (a === 'add-dia') {
      if (plan.dias.length >= 7) return toast('Máximo de 7 dias.');
      plan.dias.push({ nome: 'Treino ' + String.fromCharCode(65 + plan.dias.length), exercicios: [] }); mudou(true);
    }
    else if (a === 'del-dia') {
      if (exs.length && !confirm(`Remover "${plan.dias[di].nome}" e seus exercícios?`)) return;
      plan.dias.splice(di, 1); mudou(true);
    }
    else if (a === 'novo') {
      if (plan.dias.some(d => d.exercicios.length) && !confirm('Começar um treino novo? Alterações não salvas serão perdidas.')) return;
      plan = novoPlano(); mudou(true);
    }
    else if (a === 'imprimir') window.print();
    else if (a === 'salvar') await salvar();
    else if (a === 'abrir-treino') { plan = { ...await api('/api/treinos/' + id), avisos: [] }; mudou(false); location.hash = '#editor'; }
    else if (a === 'dup-treino') {
      const t = await api('/api/treinos/' + id);
      await api('/api/treinos', 'POST', { ...t, nome: (t.nome + ' (cópia)').slice(0, 60) }); carregarTreinos();
    }
    else if (a === 'del-treino') {
      if (!confirm('Excluir este treino definitivamente?')) return;
      await api('/api/treinos/' + id, 'DELETE');
      if (plan.id === +id) delete plan.id;
      carregarTreinos();
    }
    else if (a === 'preset') {
      equip = new Set(id ? DATA.presets[id].itens : []);
      renderAcademia(); salvarEquip(); toast(id ? DATA.presets[id].nome + ' aplicada.' : 'Tudo desmarcado.');
    }
  } catch (e) { toast(e.message); }
});

$('#v-editor').addEventListener('input', ev => {
  const t = ev.target, f = t.dataset.f;
  if (t.id === 'plano-nome') plan.nome = t.value;
  else if (t.id === 'plano-nivel') plan.nivel = t.value;
  else if (t.id === 'plano-objetivo') plan.objetivo = t.value;
  else if (f) {
    const dia = plan.dias[+t.closest('.day').dataset.d];
    if (f === 'dia-nome') dia.nome = t.value;
    else {
      const x = dia.exercicios[+t.closest('.ex-row').dataset.x];
      if (f === 'reps') x.reps = t.value;
      else { const n = parseInt(t.value, 10); if (!Number.isFinite(n) || n < 1) return; x[f] = n; }
    }
  } else return;
  mudou(false);
});

$('#form-gerar').addEventListener('submit', async ev => {
  ev.preventDefault();
  if (!equip.size && !confirm('Nenhum equipamento marcado em "Minha academia". Gerar só com peso corporal?')) return;
  const val = n => $(`.seg[data-name=${n}] .on`).dataset.v;
  try {
    plan = await api('/api/gerar', 'POST', {
      objetivo: val('objetivo'), nivel: val('nivel'), dias: +val('dias'), tempo: +val('tempo'),
      prioridades: $$('#prioridades .on').map(b => b.dataset.v), equip: [...equip],
    });
    aval = null;
    mudou(false);
    location.hash = '#editor';
    toast('Treino gerado! Ajuste o que quiser.');
  } catch (e) { toast(e.message); }
});

$('#equip-grupos').addEventListener('change', ev => {
  ev.target.checked ? equip.add(ev.target.value) : equip.delete(ev.target.value);
  salvarEquip();
});
['bib-busca', 'bib-musculo', 'bib-disp'].forEach(i => $('#' + i).addEventListener('input', renderBib));
['pk-busca', 'pk-musculo', 'pk-disp'].forEach(i => $('#' + i).addEventListener('input', renderPicker));
document.addEventListener('keydown', ev => { if (ev.key === 'Escape') $('#modal').hidden = true; });
window.addEventListener('hashchange', rota);

/* ------------------------------------------------------------------ início */
(async function iniciar() {
  try {
    const [dados, eq] = await Promise.all([api('/api/dados'), api('/api/equipamentos')]);
    DATA = dados; equip = new Set(eq);
  } catch (e) {
    $('main').innerHTML = '<div class="card"><h3>Servidor fora do ar</h3><p>Inicie o site com <b>python app.py</b> e recarregue a página.</p></div>';
    return;
  }
  DATA.exercicios.forEach(e => (EX[e.id] = e));
  DATA.equipamentos.forEach(g => g.itens.forEach(i => { EQ_NOME[i.id] = i.nome; TOTAL_EQ++; }));
  $('#st-ex').textContent = DATA.exercicios.length;
  $('#st-eq').textContent = TOTAL_EQ;
  const opts = '<option value="">Todos os músculos</option>' + Object.entries(DATA.musculos).map(([k, n]) => `<option value="${k}">${n}</option>`).join('');
  $('#bib-musculo').innerHTML = opts; $('#pk-musculo').innerHTML = opts;
  $('#prioridades').innerHTML = Object.entries(DATA.musculos).filter(([k]) => !['antebraco', 'lombar', 'delt_ant'].includes(k))
    .map(([k, n]) => `<button type="button" data-v="${k}">${n}</button>`).join('');
  try {
    const r = JSON.parse(localStorage.getItem('forja-rascunho'));
    r.dias.forEach(d => (d.exercicios = d.exercicios.filter(x => EX[x.id])));
    plan = r;
  } catch { plan = novoPlano(); }
  renderAcademia();
  rota();
})();
