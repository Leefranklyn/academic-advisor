/* Academic Advisor — front end. No frameworks. */
const GRADES = [[70, 'A'], [60, 'B'], [50, 'C'], [45, 'D'], [40, 'E'], [0, 'F']];
const letter = s => (GRADES.find(g => s >= g[0]) || [0, 'F'])[1];
const semLabel = i => `${Math.floor((i - 1) / 2) * 100 + 100} level, ${(i - 1) % 2 ? 'second' : 'first'} semester`;
const pct = v => Math.round(v * 100);
const bandClass = b => b === 'At Risk' ? 'risk' : b === 'Average' ? 'avg' : 'strong';
const reducedMotion = () => matchMedia('(prefers-reduced-motion: reduce)').matches;

const ICONS = {
  x: '<svg class="icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M6 6l12 12M18 6L6 18" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="square"/></svg>',
};

const state = { courses: [], rows: [] };   // rows: {code, score}
const $ = id => document.getElementById(id);

function el(tag, attrs = {}, ...kids) {
  const n = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (k === 'class') n.className = v; else if (k === 'text') n.textContent = v; else n.setAttribute(k, v);
  }
  kids.flat().forEach(k => k != null && n.append(k));
  return n;
}

const corners = () => ['tl', 'tr', 'bl', 'br'].map(p => el('b', { class: 'corner ' + p, 'aria-hidden': 'true' }));

/* ---------- theme ---------- */
function setTheme(t) {
  document.documentElement.dataset.theme = t;
  try { localStorage.setItem('theme', t); } catch (e) {}
  const btn = $('theme-toggle');
  btn.setAttribute('aria-label', t === 'dark' ? 'Switch to light theme' : 'Switch to dark theme');
  document.dispatchEvent(new CustomEvent('themechange'));
}
$('theme-toggle').addEventListener('click', () =>
  setTheme(document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark'));

/* ---------- particles ---------- */
function particles() {
  const c = $('particles');
  if (!c || reducedMotion()) return;
  const ctx = c.getContext('2d');
  let w = 0, h = 0, parts = [], last = performance.now();
  const colorOf = () => getComputedStyle(document.documentElement).getPropertyValue('--particle').trim() || '#cfd6e0';
  const spawn = init => ({
    x: Math.random() * w, y: init ? Math.random() * h : h + 4,
    s: 1.5 + Math.random(), v: 8 + Math.random() * 12,
    ph: Math.random() * Math.PI * 2, o: .12 + Math.random() * .18,
  });
  const resize = () => {
    const dpr = Math.min(devicePixelRatio || 1, 2);
    w = innerWidth; h = innerHeight;
    c.width = w * dpr; c.height = h * dpr;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    parts = w < 700 ? [] : Array.from({ length: 36 }, () => spawn(true));
  };
  const frame = now => {
    requestAnimationFrame(frame);
    if (document.hidden) { last = now; return; }
    const dt = Math.min((now - last) / 1000, .05); last = now;
    ctx.clearRect(0, 0, w, h);
    ctx.fillStyle = colorOf();
    for (const p of parts) {
      p.y -= p.v * dt;
      p.x += Math.sin(now / 900 + p.ph) * 6 * dt;
      if (p.y < -4) Object.assign(p, spawn(false));
      ctx.globalAlpha = p.o;
      ctx.fillRect(p.x, p.y, p.s, p.s);
    }
    ctx.globalAlpha = 1;
  };
  addEventListener('resize', resize);
  resize();
  requestAnimationFrame(frame);
}

/* ---------- range fill ---------- */
function paintRange(input) {
  const k = (input.value - input.min) / (input.max - input.min) * 100;
  input.style.setProperty('--fill', k + '%');
}

/* ---------- number count-up ---------- */
function countUp(node, target, decimals, dur = 600) {
  if (reducedMotion()) { node.textContent = target.toFixed(decimals); return; }
  const t0 = performance.now();
  const step = now => {
    const k = Math.min(1, (now - t0) / dur);
    node.textContent = (target * k).toFixed(decimals);
    if (k < 1) requestAnimationFrame(step);
  };
  requestAnimationFrame(step);
}

/* ---------- setup ---------- */
async function init() {
  const [courses, health] = await Promise.all([
    fetch('/api/courses').then(r => r.json()),
    fetch('/api/health').then(r => r.json()).catch(() => null),
  ]);
  state.courses = courses;
  if (health) {
    $('model-badge').textContent = `${health.model} / ACC ${(health.metrics.accuracy * 100).toFixed(1)}%`;
  }
  fillSelects(); renderRows();
}

function fillSelects() {
  const sel = $('course-select'); sel.textContent = '';
  const taken = new Set(state.rows.map(r => r.code));
  const groups = {};
  state.courses.filter(c => !taken.has(c.course_code)).forEach(c => (groups[c.sem_index] ||= []).push(c));
  Object.keys(groups).forEach(i => {
    const og = el('optgroup', { label: semLabel(+i) });
    groups[i].forEach(c => og.append(el('option', { value: c.course_code, text: `${c.course_code} · ${c.title}${c.type === 'elective' ? ' (elective)' : ''}` })));
    sel.append(og);
  });
  const ss = $('sem-select');
  if (!ss.options.length) for (let i = 1; i <= 8; i++) ss.append(el('option', { value: i, text: semLabel(i) }));
}

/* ---------- results table ---------- */
function renderRows() {
  const box = $('rows'); box.textContent = '';
  $('rows-count').textContent = String(state.rows.length).padStart(2, '0') + ' COURSES';
  renderGradeChart();
  if (!state.rows.length) {
    box.append(el('div', { class: 'empty' }, el('b', { text: 'NO DATA' }), el('p', { text: 'Add a course above to start your record.' })));
    fillSelects(); return;
  }
  const tb = el('tbody');
  state.rows.forEach((r, idx) => {
    const c = state.courses.find(x => x.course_code === r.code);
    const g = el('span', { class: 'grade', text: '–' });
    const paint = () => {
      const ok = r.score !== null && r.score !== '';
      g.textContent = ok ? letter(+r.score) : '–';
      g.className = 'grade' + (ok && 'EF'.includes(letter(+r.score)) ? ' gold' : '');
    };
    const inp = el('input', { type: 'number', min: 0, max: 100, 'aria-label': `Score for ${r.code}` });
    inp.value = r.score ?? '';
    inp.addEventListener('input', () => { r.score = inp.value === '' ? null : Number(inp.value); paint(); });
    paint();
    const rm = el('button', { class: 'btn icon-btn row-x', type: 'button', 'aria-label': `Remove ${r.code}` });
    rm.innerHTML = ICONS.x;
    rm.addEventListener('click', () => { state.rows.splice(idx, 1); renderRows(); });
    tb.append(el('tr', {}, el('td', { class: 'code', text: r.code }), el('td', { class: 'title', text: c ? c.title : '' }), el('td', {}, inp), el('td', {}, g), el('td', {}, rm)));
  });
  box.append(el('table', {}, el('thead', {}, el('tr', {}, el('th', { text: 'Code' }), el('th', { text: 'Course' }), el('th', { text: 'Score' }), el('th', { text: 'Grade' }), el('th'))), tb));
  fillSelects();
}

function showError(msg) { const e = $('error'); e.querySelector('span').textContent = msg || ''; e.classList.toggle('hidden', !msg); }

/* ---------- form wiring ---------- */
$('add-btn').addEventListener('click', () => {
  const code = $('course-select').value; if (!code) return;
  const v = $('score-input').value;
  state.rows.push({ code, score: v === '' ? null : Number(v) });
  $('score-input').value = ''; showError(''); renderRows();
});
$('score-input').addEventListener('keydown', e => { if (e.key === 'Enter') $('add-btn').click(); });

$('add-sem-btn').addEventListener('click', () => {
  const sem = +$('sem-select').value;
  const have = new Set(state.rows.map(r => r.code));
  state.courses.filter(c => c.sem_index === sem && c.type === 'core' && !have.has(c.course_code))
    .forEach(c => state.rows.push({ code: c.course_code, score: null }));
  showError(''); renderRows();
});

['hours', 'att'].forEach(id => {
  const i = $(id);
  paintRange(i);
  i.addEventListener('input', () => paintRange(i));
});
$('hours').addEventListener('input', e => $('hours-out').textContent = e.target.value);
$('att').addEventListener('input', e => $('att-out').textContent = e.target.value + '%');
$('clear-btn').addEventListener('click', () => { state.rows = []; showError(''); renderRows(); resetOutput(); });

$('sample-btn').addEventListener('click', async () => {
  showError('');
  const s = await fetch('/api/sample?seed=' + Math.floor(Math.random() * 100000)).then(r => r.json());
  $('jamb').value = s.jamb_score;
  $('hours').value = Math.round(s.study_hours); $('hours-out').textContent = Math.round(s.study_hours);
  $('att').value = Math.round(s.attendance * 100); $('att-out').textContent = Math.round(s.attendance * 100) + '%';
  ['hours', 'att'].forEach(id => paintRange($(id)));
  state.rows = s.results.map(r => ({ code: r.course_code, score: r.score }));
  renderRows(); advise();
});

/* ---------- advise ---------- */
$('advise-btn').addEventListener('click', advise);

async function advise() {
  showError('');
  if (!state.rows.length) return showError('Add at least one completed course first.');
  const bad = state.rows.filter(r => r.score === null || r.score === '' || isNaN(r.score) || r.score < 0 || r.score > 100);
  if (bad.length) return showError(`Enter a score between 0 and 100 for: ${bad.map(b => b.code).join(', ')}.`);
  const body = {
    jamb_score: Number($('jamb').value), study_hours: Number($('hours').value),
    attendance: Number($('att').value) / 100,
    results: state.rows.map(r => ({ course_code: r.code, score: r.score })),
  };
  const btn = $('advise-btn'); btn.disabled = true; btn.textContent = 'Thinking…';
  try {
    const res = await fetch('/api/advise', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
    const data = await res.json();
    if (!res.ok) {
      const d = data.detail;
      throw new Error(Array.isArray(d) ? d.map(x => `${x.loc.slice(1).join('.')}: ${x.msg}`).join('; ') : d || 'Request failed');
    }
    renderAdvice(data);
  } catch (e) { showError(e.message); }
  finally { btn.disabled = false; btn.textContent = 'Get advice'; }
}

/* ---------- rendering ---------- */
function resetOutput() {
  $('output-title').textContent = 'Predictions';
  $('output-meta').textContent = '';
  const body = $('output-body'); body.textContent = '';
  body.append(el('div', { class: 'empty-state' },
    el('b', { text: 'NO DATA' }),
    el('p', { text: 'Load the sample student to see how it works, or add your own results and press Get advice.' })));
}

function stat(label, node) {
  const w = el('div', { class: 'window stat' }, el('div', { class: 'win-body' }, node, el('div', { class: 'stat-label', text: label })));
  w.append(...corners());
  return w;
}
function statNum(label, value, decimals) {
  const n = el('div', { class: 'stat-num' });
  countUp(n, value, decimals);
  return stat(label, n);
}
function statText(label, value, small) {
  return stat(label, el('div', { class: 'stat-num' + (small ? ' sm' : ''), text: value }));
}

function meterEl(p) {
  const bands = [['At Risk', 'r'], ['Average', 'a'], ['Strong', 's']];
  let counts = bands.map(([b]) => Math.round(p[b] * 20));
  let total = counts.reduce((a, b) => a + b, 0), i = 0;
  while (total !== 20) {
    const j = i++ % 3;
    if (total > 20 && counts[j] > 0) { counts[j]--; total--; }
    else if (total < 20) { counts[j]++; total++; }
  }
  const m = el('div', { class: 'meter', role: 'img', 'aria-label': `At risk ${pct(p['At Risk'])}%, average ${pct(p['Average'])}%, strong ${pct(p['Strong'])}%` });
  let k = 0;
  bands.forEach(([b, cls], bi) => {
    for (let n = 0; n < counts[bi]; n++) {
      const seg = el('i', { class: cls });
      seg.style.animationDelay = (k++ * 12) + 'ms';
      m.append(seg);
    }
  });
  return m;
}
function meterRead(p) {
  return el('div', { class: 'meter-read' },
    el('span', {}, el('b', { class: 'w-r', text: 'At Risk' }), ` ${pct(p['At Risk'])}%`),
    el('span', {}, el('b', { class: 'w-a', text: 'Average' }), ` ${pct(p['Average'])}%`),
    el('span', {}, el('b', { class: 'w-s', text: 'Strong' }), ` ${pct(p['Strong'])}%`));
}

function courseCard(c, i) {
  const w = el('article', { class: 'window course' });
  w.style.setProperty('--i', i);
  w.append(...corners());
  w.append(el('header', { class: 'win-head' },
    el('i', { class: 'tick', 'aria-hidden': 'true' }),
    el('span', { class: 'code-head', text: c.course_code }),
    el('span', { class: 'band ' + bandClass(c.predicted_band), text: c.predicted_band })));
  w.append(el('div', { class: 'win-body' },
    el('h3', { class: 'c-title', text: c.title }),
    el('div', { class: 'c-meta' },
      el('span', { text: c.type }),
      el('span', { text: `${c.units} units` }),
      el('span', { text: c.category.replace(/_/g, ' ') }),
      c.type === 'elective' && c.recommended ? el('span', { class: 'chip sug', text: 'suggested elective' }) : null),
    meterEl(c.probabilities),
    meterRead(c.probabilities),
    issuesEl(c),
    el('p', { class: 'advice', text: c.advice })));
  return w;
}
function issuesEl(c) {
  const items = [...c.prerequisite_issues, ...c.watch_points];
  if (!items.length) return null;
  return el('ul', { class: 'points' }, items.map(t => el('li', { text: t })));
}

/* ---------- charts ---------- */
function chartSVG(items, opts = {}) {
  const W = 360, H = opts.h || 150;
  const top = 16, labelH = 24;
  const baseY = H - labelH;
  const max = Math.max(1, ...items.map(i => i.value));
  const n = items.length, gap = 36, pad = 16;
  const bw = Math.min(64, (W - pad * 2 - gap * (n - 1)) / n);
  const totalW = n * bw + (n - 1) * gap;
  let s = `<svg class="chart" viewBox="0 0 ${W} ${H}" role="img" aria-label="${opts.label}">`;
  s += `<line class="base" x1="0" y1="${baseY + .5}" x2="${W}" y2="${baseY + .5}"/>`;
  items.forEach((it, i) => {
    const bh = it.value / max * (baseY - top);
    const x = pad + (W - pad * 2 - totalW) / 2 + i * (bw + gap);
    const y = baseY - bh;
    s += `<rect class="bar" x="${x.toFixed(1)}" y="${y.toFixed(1)}" width="${bw.toFixed(1)}" height="${Math.max(bh, it.value ? 2 : 0).toFixed(1)}" fill="var(--${it.color})" style="animation-delay:${i * 40}ms"/>`;
    s += `<text class="val" x="${(x + bw / 2).toFixed(1)}" y="${(y - 6).toFixed(1)}" text-anchor="middle">${it.value}</text>`;
    s += `<text x="${(x + bw / 2).toFixed(1)}" y="${baseY + 16}" text-anchor="middle">${it.label}</text>`;
  });
  return s + '</svg>';
}
function chartEl(items, opts) {
  const d = el('div', { class: 'chart-box' });
  d.innerHTML = chartSVG(items, opts);
  return d;
}

function outlookWindow(courses, i) {
  const counts = { 'At Risk': 0, Average: 0, Strong: 0 };
  courses.forEach(c => counts[c.predicted_band] = (counts[c.predicted_band] || 0) + 1);
  const w = el('section', { class: 'window outlook' });
  w.style.setProperty('--i', i);
  w.append(...corners());
  w.append(el('header', { class: 'win-head' },
    el('i', { class: 'tick', 'aria-hidden': 'true' }),
    el('h2', { text: 'Semester outlook' }),
    el('span', { class: 'win-meta', text: `${String(courses.length).padStart(2, '0')} COURSES` })));
  w.append(el('div', { class: 'win-body' },
    chartEl([
      { label: 'At Risk', value: counts['At Risk'], color: 'gold' },
      { label: 'Average', value: counts.Average, color: 'muted' },
      { label: 'Strong', value: counts.Strong, color: 'azure' },
    ], { h: 150, label: `Predicted bands across ${courses.length} courses: ${counts['At Risk']} at risk, ${counts.Average} average, ${counts.Strong} strong` })));
  return w;
}

function renderGradeChart() {
  const box = $('grade-chart');
  const scored = state.rows.filter(r => r.score !== null && r.score !== '').map(r => +r.score);
  if (!scored.length) { box.textContent = ''; box.classList.add('hidden'); return; }
  box.classList.remove('hidden');
  box.textContent = '';
  const w = el('section', { class: 'window' });
  w.append(...corners());
  w.append(el('header', { class: 'win-head' },
    el('i', { class: 'tick', 'aria-hidden': 'true' }),
    el('h2', { text: 'Grade distribution' }),
    el('span', { class: 'win-meta', text: `${String(scored.length).padStart(2, '0')} GRADED` })));
  w.append(el('div', { class: 'win-body' },
    chartEl(['A', 'B', 'C', 'D', 'E', 'F'].map(l => ({
      label: l,
      value: scored.filter(s => letter(s) === l).length,
      color: 'EF'.includes(l) ? 'gold' : 'muted',
    })), { h: 130, label: 'Distribution of entered scores by grade letter' })));
  box.append(w);
}

function renderAdvice(d) {
  const s = d.summary;
  $('output-title').textContent = s.next_semester ? `Next up: ${s.next_semester}` : 'Predictions';
  $('output-meta').textContent = `${String(d.courses.length).padStart(2, '0')} COURSES`;
  const body = $('output-body'); body.textContent = '';
  const stats = el('div', { class: 'stats' },
    statNum('CGPA so far', s.cgpa, 2),
    statText('Courses on record', `${s.courses_on_record}${s.courses_failed ? ` (${s.courses_failed} failed)` : ''}`),
    s.recommended_units != null ? statNum('Recommended load', s.recommended_units, 0) : null,
    statText('Last completed', s.last_semester, true));
  [...stats.children].forEach((w, i) => w.style.setProperty('--i', i));
  body.append(stats);
  let i = stats.children.length;
  if (d.courses.length) body.append(outlookWindow(d.courses, i++));
  if (d.notes.length) {
    const w = el('section', { class: 'window notes-w' });
    w.style.setProperty('--i', i++);
    w.append(...corners());
    w.append(el('header', { class: 'win-head' },
      el('i', { class: 'tick', 'aria-hidden': 'true' }),
      el('h2', { text: 'Notes' })));
    w.append(el('div', { class: 'win-body' }, el('ul', { class: 'notes' }, d.notes.map(n => el('li', { text: n })))));
    body.append(w);
  }
  d.courses.forEach(c => body.append(courseCard(c, i++)));
}

/* ---------- go ---------- */
resetOutput();
init();
particles();
