/* Coffee Origin Monitor — single-page app (hash routing, no build step). */
'use strict';

// ------------------------------------------------------------------ helpers
const $ = (s, r = document) => r.querySelector(s);
const $$ = (s, r = document) => [...r.querySelectorAll(s)];
const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const fmt = (n, d = 2) => n == null || isNaN(n) ? '—' : Number(n).toLocaleString('en-US', {minimumFractionDigits: d, maximumFractionDigits: d});
const big = n => n == null ? '—' : Math.abs(n) >= 1e9 ? fmt(n / 1e9, 1) + 'B' : Math.abs(n) >= 1e6 ? fmt(n / 1e6, 1) + 'M' : Math.abs(n) >= 1e3 ? fmt(n / 1e3, 1) + 'k' : fmt(n, 0);
const ago = ts => { const s = Date.now() / 1000 - ts; if (s < 3600) return Math.max(1, Math.round(s / 60)) + 'm ago';
  if (s < 86400) return Math.round(s / 3600) + 'h ago'; if (s < 86400 * 30) return Math.round(s / 86400) + 'd ago';
  return new Date(ts * 1000).toLocaleDateString(); };
const api = async p => { const r = await fetch(p); if (!r.ok) throw new Error(`${p}: ${r.status}`); return r.json(); };
const store = {
  get(k, d) { try { return JSON.parse(localStorage.getItem(k)) ?? d; } catch { return d; } },
  set(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch {} },
};
const MONTHS = ['J','F','M','A','M','J','J','A','S','O','N','D'];
const MONTH_NAMES = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
const TOPIC_LABEL = {prices:'Prices', weather:'Weather', crop:'Crop', trade:'Trade', policy:'Policy', logistics:'Logistics',
  stocks:'Stocks', disease:'Disease', specialty:'Specialty', business:'Business', sustainability:'Sustainability',
  labor:'Labor', demand:'Demand', general:'General'};
let META = null, SNAP = null, charts = [], timers = [];
const pageTimer = (fn, ms) => timers.push(setInterval(fn, ms));

function spark(vals, w = 78, h = 28, color) {
  vals = (vals || []).filter(v => v != null);
  if (vals.length < 2) return '';
  const mn = Math.min(...vals), mx = Math.max(...vals), r = (mx - mn) || 1;
  const pts = vals.map((v, i) => `${(i / (vals.length - 1) * w).toFixed(1)},${(h - (v - mn) / r * h).toFixed(1)}`).join(' ');
  const c = color || (vals.at(-1) >= vals[0] ? 'var(--up)' : 'var(--down)');
  return `<svg width="${w}" height="${h}" viewBox="0 0 ${w} ${h}" preserveAspectRatio="none"><polyline points="${pts}" fill="none" stroke="${c}" stroke-width="1.5"/></svg>`;
}
function bars(vals, w = 120, h = 34, color = 'var(--rain)', split = null) {
  vals = vals || []; if (!vals.length) return '';
  const mx = Math.max(1, ...vals.map(v => v || 0)), bw = w / vals.length;
  return `<svg width="${w}" height="${h}" viewBox="0 0 ${w} ${h}" preserveAspectRatio="none">` + vals.map((v, i) => {
    const bh = (v || 0) / mx * h;
    return `<rect x="${(i * bw + .5).toFixed(1)}" y="${(h - bh).toFixed(1)}" width="${Math.max(1, bw - 1).toFixed(1)}" height="${bh.toFixed(1)}" fill="${color}" opacity="${split != null && i >= split ? .45 : .9}"/>`;
  }).join('') + '</svg>';
}
const chg = (q, d = 2) => q && q.change_pct != null
  ? `<span class="${q.change_pct >= 0 ? 'up' : 'down'}">${q.change_pct >= 0 ? '▲' : '▼'} ${fmt(Math.abs(q.change ?? 0), d)} (${fmt(q.change_pct, 2)}%)</span>`
  : '<span class="faint">—</span>';

function originName(id) {
  if (!META) return id;
  if (id.includes('.')) { const r = META.cr_regions.find(x => 'cr.' + x.id === id); return r ? r.name : id; }
  const o = META.origins.find(x => x.id === id); return o ? `${o.flag} ${o.country}` : id;
}
function newsItem(a, opts = {}) {
  const chips = (a.origins || []).filter(o => opts.showRegions ? true : !o.includes('.')).slice(0, 4)
    .map(o => `<span class="chip ${o.startsWith('cr') ? 'cr' : 'o'}">${esc(originName(o))}</span>`).join('');
  const topics = (a.topics || []).filter(t => t !== 'general').slice(0, 3).map(t => `<span class="chip">${TOPIC_LABEL[t] || t}</span>`).join('');
  const tr = a.lang && a.lang !== 'en' ? ` · <a href="https://translate.google.com/translate?sl=auto&tl=en&u=${encodeURIComponent(a.url)}" target="_blank" rel="noopener">translate</a>` : '';
  return `<div class="item">
    <a class="t" href="${esc(a.url)}" target="_blank" rel="noopener">${esc(a.title)}</a>
    <div class="side">${a.signal !== 'neutral' ? `<span class="sig ${a.signal}">${a.signal === 'bullish' ? '▲ bullish' : '▼ bearish'}</span>` : ''}</div>
    <div class="m"><span>${esc(a.source_name)}</span><span>${ago(a.published)}</span><span class="mono">${(a.lang || 'en').toUpperCase()}</span>${chips}${topics}<span class="faint">${tr}</span></div>
    ${a.summary && !opts.compact ? `<div class="s">${esc(a.summary)}</div>` : ''}
  </div>`;
}

// ------------------------------------------------------------------ charts
const CH_OPTS = () => ({
  autoSize: true,
  layout: {background: {color: 'transparent'}, textColor: '#a39587', fontFamily: 'IBM Plex Mono', fontSize: 11},
  grid: {vertLines: {color: '#241e1a'}, horzLines: {color: '#241e1a'}},
  rightPriceScale: {borderColor: '#332b25'},
  timeScale: {borderColor: '#332b25', timeVisible: true, secondsVisible: false},
  crosshair: {mode: 0}, handleScroll: false, handleScale: false,
});
function mkChart(el) { const c = LightweightCharts.createChart(el, CH_OPTS()); charts.push(c); return c; }
const pts = arr => (arr || []).filter(p => p[1] != null).map(([t, v]) => ({time: t, value: v}));
function lineChart(el, series, opts = {}) {
  const c = mkChart(el);
  series.forEach(s => {
    const kind = s.type === 'hist' ? 'addHistogramSeries' : s.type === 'area' ? 'addAreaSeries' : 'addLineSeries';
    const ser = c[kind]({color: s.color, lineWidth: 2, priceLineVisible: false, lastValueVisible: true,
      title: s.title || '', priceScaleId: s.scale || 'right', ...(s.type === 'area' ? {topColor: s.color + '55', bottomColor: s.color + '05', lineColor: s.color} : {})});
    ser.setData(s.data.map(p => s.colorFn ? {...p, color: s.colorFn(p.value)} : p));
  });
  if (opts.left) c.priceScale('left').applyOptions({visible: true, borderColor: '#332b25'});
  c.timeScale().fitContent();
  return c;
}

// ------------------------------------------------------------------ status
function renderStatus(s) {
  const b = s.benchmarks;
  const mode = META?.mode;
  const modePill = mode === 'demo' ? '<a class="pill warn" href="#/dev" title="Offline demo data">DEMO</a>'
    : mode === 'live' ? '<a class="pill" href="#/dev" style="color:var(--up)" title="Real data, local archive">LIVE · local</a>' : '';
  $('#status').innerHTML = modePill +
    Object.values(b).map(x => `<span class="pill"><span class="dot ${x.session.open ? 'on' : ''}"></span><b>${x.short}</b> ${x.quote?.price != null ? fmt(x.quote.price, 2) : '—'}</span>`).join('') +
    `<span class="pill">delayed</span>`;
}
async function refreshSnap() {
  try { SNAP = await api('/api/snapshot'); renderStatus(SNAP); } catch (e) { console.error(e); }
  return SNAP;
}

// ================================================================= OVERVIEW
const RANGES = [
  {label: '1D', interval: '5m', range: '1d'}, {label: '5D', interval: '15m', range: '5d'},
  {label: '1M', interval: '60m', range: '1mo'}, {label: '6M', interval: '1d', range: '6mo'},
  {label: '5Y', interval: '1wk', range: '5y'},
];
const ov = {market: 'arabica', range: 0};

async function pageOverview(view) {
  view.innerHTML = `
    <div class="grid g3" id="tiles"></div>
    <div class="split" style="margin-top:12px">
      <div class="panel" style="display:flex;flex-direction:column">
        <div class="chartbar"><h3 id="ctitle" style="margin:0">Arabica</h3><div class="seg" id="ranges"></div></div>
        <div class="chart" id="pxchart" style="flex:1;min-height:300px"></div>
      </div>
      <a class="panel feature" href="#/costa-rica" style="color:var(--text);display:block" id="crcard"><div class="loading">Loading Costa Rica…</div></a>
    </div>
    <div class="split">
      <div><h2>Latest coffee news</h2><div class="panel tight"><div class="news" id="latest"><div class="loading">Loading…</div></div>
        <div style="padding:8px 2px"><a href="#/news">All news →</a></div></div></div>
      <div><h2>Last 7 days</h2><div class="panel" id="pulse"><div class="loading">Loading…</div></div>
        <h2>Speculator positioning</h2><div class="panel"><div class="small muted" style="margin-bottom:6px">Managed-money net position in Coffee C (contracts, CFTC weekly)</div><div class="chart xs" id="cotmini"></div></div></div>
    </div>`;
  const s = SNAP || await refreshSnap();
  renderTiles(s);
  $('#ranges').innerHTML = RANGES.map((r, i) => `<button data-i="${i}" class="${i === ov.range ? 'on' : ''}">${r.label}</button>`).join('');
  $$('#ranges button').forEach(b => b.onclick = () => { ov.range = +b.dataset.i; $$('#ranges button').forEach(x => x.classList.toggle('on', x === b)); loadPx(); });
  const c = mkChart($('#pxchart'));
  ov.series = c.addCandlestickSeries({upColor: '#6fbf8a', downColor: '#e0705f', wickUpColor: '#6fbf8a', wickDownColor: '#e0705f', borderVisible: false});
  ov.chart = c;
  loadPx();
  const loadLatest = () => api('/api/news?limit=14').then(d => { if ($('#latest')) $('#latest').innerHTML = d.items.map(a => newsItem(a)).join('') || '<div class="muted">No articles yet. Ingestion runs every 15 minutes.</div>'; });
  loadLatest();
  pageTimer(loadLatest, META.mode === 'demo' ? 20000 : 60000);
  api('/api/news/stats?days=7').then(renderPulse);
  api('/api/series/cot:mm_net').then(d => {
    if (!d.points.length) { $('#cotmini').innerHTML = '<div class="faint small">Waiting for first data run.</div>'; return; }
    lineChart($('#cotmini'), [{type: 'hist', data: pts(d.points.slice(-104)), colorFn: v => v >= 0 ? '#6fbf8a' : '#e0705f'}]);
  });
  crCard();
}
function renderTiles(s) {
  const items = [
    ...Object.entries(s.benchmarks).map(([k, x]) => ({key: k, name: x.name, q: x.quote, unit: x.unit, d: 2})),
    ...Object.entries(s.context).map(([k, x]) => ({key: k, name: x.name, q: x.quote, unit: '', d: k === 'brl' ? 4 : 2})),
  ];
  $('#tiles').innerHTML = items.map(it => { const q = it.q || {};
    return `<div class="tile ${ov.market === it.key ? 'sel' : ''}" data-k="${it.key}"><div class="lbl">${it.name}</div>
      ${q.price != null ? `<div class="px">${fmt(q.price, it.d)}<small>${it.unit}</small></div><div class="chg">${chg(q, it.d)}</div>${spark(q.spark)}`
        : `<div class="err" style="margin-top:8px">Unavailable from free source</div>`}</div>`; }).join('');
  $$('.tile').forEach(t => t.onclick = () => { ov.market = t.dataset.k; renderTiles(SNAP); loadPx(); });
}
async function loadPx() {
  const r = RANGES[ov.range], s = SNAP;
  const names = {...Object.fromEntries(Object.entries(s.benchmarks).map(([k, v]) => [k, v.name])), ...Object.fromEntries(Object.entries(s.context).map(([k, v]) => [k, v.name]))};
  $('#ctitle').textContent = `${names[ov.market]} · ${r.label}`;
  try { const d = await api(`/api/chart?market=${ov.market}&interval=${r.interval}&range=${r.range}`);
    ov.series.setData(d.bars.map(b => ({time: b.time, open: b.open, high: b.high, low: b.low, close: b.close}))); ov.chart.timeScale().fitContent();
  } catch { ov.series.setData([]); $('#ctitle').textContent += ' — unavailable'; }
}
function renderPulse(c) {
  const top = Object.entries(c.origins).filter(([k]) => !k.includes('.')).sort((a, b) => b[1] - a[1]).slice(0, 8);
  const mx = Math.max(1, ...top.map(x => x[1]));
  const sg = c.signal || {}, bull = sg.bullish || 0, bear = sg.bearish || 0, tot = Math.max(1, bull + bear);
  const topics = Object.entries(c.topics).filter(([k]) => k !== 'general').sort((a, b) => b[1] - a[1]).slice(0, 8);
  $('#pulse').innerHTML = `
    <div class="row small"><span class="mono">${c.total}</span><span class="muted">articles</span><span class="spacer"></span>
      <span class="up mono">▲ ${bull}</span><span class="down mono">▼ ${bear}</span></div>
    <div style="display:flex;height:6px;border-radius:4px;overflow:hidden;margin:8px 0 14px;background:var(--panel2)">
      <div style="width:${bull / tot * 100}%;background:var(--up)"></div><div style="width:${bear / tot * 100}%;background:var(--down)"></div></div>
    <div class="k" style="margin-bottom:6px">Most-covered origins</div>
    ${top.map(([k, v]) => `<a href="#/origin/${k}" class="row small" style="color:var(--text);margin:3px 0"><span style="width:120px">${originName(k)}</span>
      <span style="flex:1;height:6px;background:var(--panel2);border-radius:3px"><span style="display:block;height:6px;width:${v / mx * 100}%;background:var(--accent);border-radius:3px"></span></span><span class="mono faint" style="width:28px;text-align:right">${v}</span></a>`).join('') || '<div class="faint small">No data yet</div>'}
    <div class="k" style="margin:14px 0 6px">Topics</div>
    <div class="togs">${topics.map(([k, v]) => `<a class="tog" href="#/news?topic=${k}">${TOPIC_LABEL[k] || k} <span class="faint">${v}</span></a>`).join('')}</div>`;
}
async function crCard() {
  const d = await api('/api/costa-rica');
  const now = new Date(), m = now.getMonth() + 1;
  const active = d.regions.filter(r => inHarvest(r.harvest, m));
  const rain7 = d.regions.map(r => (r.forecast?.rain || []).slice(0, 7).reduce((a, b) => a + (b || 0), 0));
  const kcP = d.kc?.price, crcKg = kcP && d.fx?.price ? kcP / 100 * d.lb_per_kg * d.fx.price : null;
  $('#crcard').innerHTML = `
    <div class="row"><span class="k" style="color:var(--cr)">Featured origin</span><span class="spacer"></span><span class="small">Open →</span></div>
    <h3 style="font-size:22px;margin:6px 0 2px">🇨🇷 Costa Rica</h3>
    <div class="small muted">${active.length ? `Harvest under way in <b style="color:var(--text)">${active.map(r => r.name).join(', ')}</b>` : 'Between harvests in most regions'}</div>
    <div class="grid g2" style="margin-top:12px">
      <div class="kv"><div class="k">USD/CRC</div><div class="v">${fmt(d.fx?.price, 1)}</div></div>
      <div class="kv"><div class="k">KC at origin (no diff)</div><div class="v">${crcKg ? fmt(crcKg, 0) + ' ₡/kg' : '—'}</div></div>
    </div>
    <div class="k" style="margin:12px 0 4px">Rain next 7 days by region (mm)</div>
    ${d.regions.map((r, i) => `<div class="row small" style="margin:2px 0"><span style="width:110px">${r.name}</span>
      <span style="flex:1;height:6px;background:var(--panel2);border-radius:3px"><span style="display:block;height:6px;width:${Math.min(100, rain7[i] / Math.max(1, ...rain7) * 100)}%;background:var(--rain);border-radius:3px"></span></span>
      <span class="mono faint" style="width:34px;text-align:right">${fmt(rain7[i], 0)}</span></div>`).join('')}
    <div class="k" style="margin:12px 0 2px">Latest</div>
    <div class="news">${d.news.slice(0, 3).map(a => newsItem(a, {compact: true})).join('') || '<div class="faint small">No Costa Rica news yet</div>'}</div>`;
}

// ============================================================== COSTA RICA
const inHarvest = ([s, e], m) => s <= e ? (m >= s && m <= e) : (m >= s || m <= e);
function tripMonths(trip) {
  if (!trip?.start) return new Set();
  const a = new Date(trip.start), b = new Date(trip.end || trip.start), out = new Set();
  for (let d = new Date(a.getFullYear(), a.getMonth(), 1); d <= b; d.setMonth(d.getMonth() + 1)) out.add(d.getMonth() + 1);
  return out;
}
function harvestStrip(h, trip) {
  const now = new Date().getMonth() + 1, tm = tripMonths(trip);
  return `<div class="months">${MONTHS.map((l, i) => `<div class="${inHarvest(h, i + 1) ? 'h' : ''} ${i + 1 === now ? 'now' : ''} ${tm.has(i + 1) ? 'trip' : ''}" title="${MONTH_NAMES[i]}">${l}</div>`).join('')}</div>`;
}
function regionStatus(r, trip) {
  const m = new Date().getMonth() + 1;
  if (trip?.start) {
    const tm = [...tripMonths(trip)];
    const hit = tm.some(x => inHarvest(r.harvest, x));
    return hit ? '<span class="badge on">harvest during your trip</span>' : '<span class="badge off">no harvest during trip</span>';
  }
  if (inHarvest(r.harvest, m)) return '<span class="badge on">harvesting now</span>';
  if (inHarvest(r.harvest, m % 12 + 1)) return '<span class="badge soon">starts next month</span>';
  return '<span class="badge off">off-season</span>';
}

async function pageCostaRica(view) {
  view.innerHTML = '<div class="loading">Loading Costa Rica…</div>';
  const d = await api('/api/costa-rica');
  const trip = store.get('cr_trip', {});
  const diffs = store.get('diffs', {});
  const crRegion = new URLSearchParams(location.hash.split('?')[1] || '').get('region');
  view.innerHTML = `
    <div class="hero">
      <div class="row"><span class="k" style="color:var(--cr)">Featured origin · Other Milds · Arabica only by law</span></div>
      <h1 class="page">🇨🇷 Costa Rica</h1>
      <p class="lede" style="margin-bottom:12px">Eight ICAFE growing regions, live weather and 16-day forecasts, the harvest calendar, local-press news in Spanish and English, and prices converted to colones.</p>
      <div class="grid g4">
        <div class="kv"><div class="k">USD/CRC</div><div class="v">${fmt(d.fx?.price, 2)}</div><div class="tiny faint">${esc(d.fx?.source || '')}</div></div>
        <div class="kv"><div class="k">Arabica KC</div><div class="v">${fmt(d.kc?.price, 2)} ¢/lb</div><div class="tiny">${chg(d.kc)}</div></div>
        <div class="kv"><div class="k">Regions harvesting now</div><div class="v">${d.regions.filter(r => inHarvest(r.harvest, new Date().getMonth() + 1)).length} / 8</div></div>
        <div class="kv"><div class="k">CR news, last 30 days</div><div class="v">${d.counts.origins?.cr || 0}</div></div>
      </div>
    </div>

    <div class="split">
      <div class="panel">
        <h3>Trip planner</h3>
        <div class="small muted" style="margin-bottom:8px">Add your dates to see which regions will be picking and processing while you're there, plus the forecast once your trip is within 16 days.</div>
        <div class="row"><label class="small muted">Arrive <input type="date" id="tstart" value="${trip.start || ''}"></label>
          <label class="small muted">Leave <input type="date" id="tend" value="${trip.end || ''}"></label>
          <button class="btn" id="tclear">Clear</button></div>
        <div id="tripout" style="margin-top:12px"></div>
      </div>
      <div class="panel">
        <h3>Price at origin</h3>
        <div class="small muted" style="margin-bottom:8px">KC futures plus the differential from an offer sheet, converted to the units Costa Rican mills and exporters quote.</div>
        <div class="calc">Differential <input type="number" step="1" id="crdiff" value="${diffs.cr ?? ''}" placeholder="0"> ¢/lb over KC</div>
        <div id="crcalc" style="margin-top:10px"></div>
      </div>
    </div>

    <h2>Growing regions</h2>
    <div class="grid g4" id="regions"></div>

    <div class="split">
      <div>
        <h2>Costa Rica news</h2>
        <div class="togs" id="crfilter" style="margin-bottom:10px"></div>
        <div class="panel tight"><div class="news" id="crnews"></div></div>
      </div>
      <div>
        <h2>US imports from Costa Rica</h2>
        <div class="panel"><div class="small muted" style="margin-bottom:6px">Monthly green coffee (HS 090111), tonnes · implied $/kg line</div><div class="chart sm" id="crimp"></div>
          <div class="tiny faint" style="margin-top:6px">Source: US Census</div></div>
        <h2>Colón vs dollar</h2>
        <div class="panel"><div class="small muted" style="margin-bottom:6px">USD/CRC, daily close · rising = weaker colón</div><div class="chart xs" id="crfx"></div></div>
      </div>
    </div>`;

  // trip planner
  const renderTrip = () => {
    const t = store.get('cr_trip', {});
    const out = $('#tripout');
    if (!t.start) { out.innerHTML = '<div class="faint small">No dates set.</div>'; renderRegions(d, t); return; }
    const start = new Date(t.start + 'T00:00'), end = new Date((t.end || t.start) + 'T00:00');
    const days = Math.round((start - new Date()) / 86400000);
    const harv = d.regions.filter(r => [...tripMonths(t)].some(m => inHarvest(r.harvest, m)));
    let fc = '';
    const fdates = d.regions[0]?.forecast?.dates || [];
    const inWin = fdates.filter(x => x >= t.start && x <= (t.end || t.start));
    if (inWin.length) {
      fc = `<table class="t" style="margin-top:8px"><tr><th>Region</th><th>Rain over trip (mm)</th><th>Wettest day chance</th><th>Temp range</th></tr>` +
        d.regions.map(r => { const f = r.forecast, ix = f.dates.map((x, i) => inWin.includes(x) ? i : -1).filter(i => i >= 0);
          const rain = ix.reduce((a, i) => a + (f.rain[i] || 0), 0), pr = Math.max(...ix.map(i => f.rain_prob?.[i] || 0));
          const lo = Math.min(...ix.map(i => f.tmin[i])), hi = Math.max(...ix.map(i => f.tmax[i]));
          return `<tr><td>${r.name}</td><td class="mono">${fmt(rain, 0)}</td><td class="mono">${pr}%</td><td class="mono">${fmt(lo, 0)}–${fmt(hi, 0)}°C</td></tr>`; }).join('') + '</table>';
    } else if (days > 0) fc = `<div class="small faint" style="margin-top:6px">Forecast appears ${days - 15} days from now (16-day window).</div>`;
    out.innerHTML = `<div class="small">${days > 0 ? `<b class="mono">${days}</b> days to go · ` : days >= -((end - start) / 86400000) ? '<b>You\'re there now</b> · ' : ''}
      ${harv.length ? `Harvest during your trip in <b style="color:var(--cr)">${harv.map(r => r.name).join(', ')}</b>.` : 'None of the regions are typically harvesting then; mills will be quieter.'}</div>${fc}`;
    renderRegions(d, t);
  };
  const saveTrip = () => { store.set('cr_trip', {start: $('#tstart').value, end: $('#tend').value || $('#tstart').value}); renderTrip(); };
  $('#tstart').onchange = saveTrip; $('#tend').onchange = saveTrip;
  $('#tclear').onclick = () => { store.set('cr_trip', {}); $('#tstart').value = ''; $('#tend').value = ''; renderTrip(); };
  renderTrip();

  // price calc
  const calc = () => {
    const diff = parseFloat($('#crdiff').value) || 0; const ds = store.get('diffs', {}); ds.cr = $('#crdiff').value; store.set('diffs', ds);
    const kc = d.kc?.price, fx = d.fx?.price;
    if (kc == null) { $('#crcalc').innerHTML = '<div class="err">KC unavailable</div>'; return; }
    const usdLb = (kc + diff) / 100, usdKg = usdLb * d.lb_per_kg, crcKg = fx ? usdKg * fx : null;
    // Costa Rican trade units: 46 kg quintal (oro / green) and the 400-L fanega of cherry (~46 kg green equivalent)
    $('#crcalc').innerHTML = `<div class="grid g2">
      <div class="kv"><div class="k">USD</div><div class="big">$${fmt(usdLb, 2)}<span class="small faint">/lb</span></div><div class="small mono muted">$${fmt(usdKg, 2)}/kg</div></div>
      <div class="kv"><div class="k">Colones</div><div class="big">₡${fmt(crcKg, 0)}<span class="small faint">/kg</span></div><div class="small mono muted">₡${fmt(crcKg && crcKg * 46, 0)} per 46-kg quintal</div></div></div>
      <div class="tiny faint" style="margin-top:6px">A 46-kg quintal of green coffee is roughly one fanega of cherry, the unit farmers are paid in. This is the green FOB-equivalent value, not the farmgate price.</div>`;
  };
  $('#crdiff').oninput = calc; calc();

  // news with region filter
  let sel = crRegion || 'all';
  const renderNews = async () => {
    $('#crfilter').innerHTML = [['all', 'All Costa Rica'], ...d.regions.map(r => ['cr.' + r.id, r.name])]
      .map(([k, l]) => `<button class="tog ${sel === k ? 'on' : ''}" data-k="${k}">${l}</button>`).join('');
    $$('#crfilter .tog').forEach(b => b.onclick = () => { sel = b.dataset.k; renderNews(); });
    const items = sel === 'all' ? d.news : (await api(`/api/news?origin=${sel}&limit=40`)).items;
    $('#crnews').innerHTML = items.map(a => newsItem(a, {showRegions: true})).join('') || '<div class="muted small" style="padding:10px">No stories tagged to this region yet.</div>';
  };
  renderNews();

  // imports + fx
  const kg = d.imports.kg.points, usd = Object.fromEntries(d.imports.usd.points);
  if (kg.length) lineChart($('#crimp'), [
    {type: 'hist', color: '#d9a06699', data: kg.map(([t, v]) => ({time: t, value: v / 1000}))},
    {color: '#efe7de', scale: 'left', data: kg.filter(([t, v]) => v && usd[t]).map(([t, v]) => ({time: t, value: usd[t] / v}))},
  ], {left: true});
  else $('#crimp').innerHTML = '<div class="faint small">Waiting for first data run.</div>';
  if (d.fx_series.points.length) lineChart($('#crfx'), [{type: 'area', color: '#e2b25a', data: pts(d.fx_series.points)}]);
  else $('#crfx').innerHTML = '<div class="faint small">Waiting for first data run.</div>';
}

function renderRegions(d, trip) {
  $('#regions').innerHTML = d.regions.map(r => {
    const w = r.weather || {}, f = r.forecast || {};
    const r90 = (r.rain90 || []).map(p => p[1]);
    const r30 = r90.slice(-30).reduce((a, b) => a + (b || 0), 0);
    return `<div class="panel region">
      <div class="head"><div><h3 style="margin:0">${r.name}</h3><div class="tiny faint">${esc(r.town)} · ${r.alt}</div></div>${regionStatus(r, trip)}</div>
      ${harvestStrip(r.harvest, trip)}
      <div class="tiny faint">Harvest ≈ ${MONTH_NAMES[r.harvest[0] - 1]}–${MONTH_NAMES[r.harvest[1] - 1]} · ${esc(r.note)}</div>
      <div class="grid g2">
        <div class="kv"><div class="k">Now</div><div class="v">${w.error ? '—' : fmt(w.temp_c, 0) + '°C'}</div><div class="tiny faint">RH ${w.humidity ?? '—'}%</div></div>
        <div class="kv"><div class="k">Rain 30d</div><div class="v">${fmt(r30, 0)} mm</div><div class="tiny faint">YTD ${fmt(r.rain_ytd_mm, 0)} mm</div></div>
      </div>
      <div><div class="k">Next 16 days rain</div>${bars(f.rain, 260, 34)}<div class="tiny faint mono">${fmt((f.rain || []).reduce((a, b) => a + (b || 0), 0), 0)} mm total · lows ${fmt(Math.min(...(f.tmin || [NaN])), 0)}°C</div></div>
      ${r.news?.length ? `<div class="tiny"><span class="k">Latest</span><br><a href="${esc(r.news[0].url)}" target="_blank" rel="noopener">${esc(r.news[0].title)}</a></div>` : ''}
    </div>`;
  }).join('');
}

// ==================================================================== NEWS
async function pageNews(view, params) {
  const f = {q: params.get('q') || '', origin: params.get('origin') || '', topic: params.get('topic') || '',
    signal: params.get('signal') || '', channel: params.get('channel') || '', lang: params.get('lang') || ''};
  view.innerHTML = `
    <h1 class="page">News</h1>
    <p class="lede">Every coffee story the platform has collected from trade press, origin-country press in six languages, Google News and GDELT, de-duplicated and tagged by origin, topic and likely price direction.</p>
    <div class="filters">
      <input type="search" id="nq" placeholder="Search headlines… (e.g. frost, EUDR, Tarrazú)" value="${esc(f.q)}">
      <select id="norigin"><option value="">All origins</option>${META.origins.map(o => `<option value="${o.id}" ${f.origin === o.id ? 'selected' : ''}>${o.flag} ${o.country}</option>`).join('')}</select>
      <select id="nsignal"><option value="">Any signal</option><option value="bullish" ${f.signal === 'bullish' ? 'selected' : ''}>▲ Bullish</option><option value="bearish" ${f.signal === 'bearish' ? 'selected' : ''}>▼ Bearish</option></select>
      <select id="nchannel"><option value="">All channels</option>${[['rss', 'Publisher RSS'], ['gnews', 'Google News'], ['gdelt', 'GDELT']].map(([k, l]) => `<option value="${k}" ${f.channel === k ? 'selected' : ''}>${l}</option>`).join('')}</select>
      <select id="nlang"><option value="">Any language</option>${['en', 'es', 'pt', 'vi', 'id', 'fr'].map(l => `<option value="${l}" ${f.lang === l ? 'selected' : ''}>${l.toUpperCase()}</option>`).join('')}</select>
    </div>
    <div class="togs" id="ntopics" style="margin-bottom:12px"></div>
    <div class="panel tight"><div class="news" id="nlist"><div class="loading">Loading…</div></div>
      <div style="padding:10px 2px"><button class="btn" id="nmore" hidden>Load more</button></div></div>`;
  const go = () => { const p = new URLSearchParams(Object.entries(f).filter(([, v]) => v)); location.hash = '#/news' + (p.toString() ? '?' + p : ''); };
  $('#ntopics').innerHTML = META.topics.map(t => `<button class="tog ${f.topic === t ? 'on' : ''}" data-t="${t}">${TOPIC_LABEL[t] || t}</button>`).join('');
  $$('#ntopics .tog').forEach(b => b.onclick = () => { f.topic = f.topic === b.dataset.t ? '' : b.dataset.t; go(); });
  let tmr; $('#nq').oninput = e => { clearTimeout(tmr); tmr = setTimeout(() => { f.q = e.target.value.trim(); go(); }, 450); };
  for (const k of ['origin', 'signal', 'channel', 'lang']) $('#n' + k).onchange = e => { f[k] = e.target.value; go(); };
  let before = null;
  const load = async (append) => {
    const p = new URLSearchParams(Object.entries(f).filter(([, v]) => v)); p.set('limit', 40); if (before) p.set('before', before);
    const d = await api('/api/news?' + p);
    const html = d.items.map(a => newsItem(a, {showRegions: f.origin === 'cr'})).join('');
    $('#nlist').innerHTML = append ? $('#nlist').innerHTML + html : (html || '<div class="muted" style="padding:12px">No matching articles.</div>');
    before = d.next_before; $('#nmore').hidden = !before;
  };
  $('#nmore').onclick = () => load(true);
  load(false);
  if (f.q) { const i = $('#nq'); i.focus(); i.setSelectionRange(i.value.length, i.value.length); }
}

// ================================================================= ORIGINS
async function pageOrigins(view) {
  const s = SNAP || await refreshSnap();
  const stats = await api('/api/news/stats?days=7');
  const diffs = store.get('diffs', {});
  const sorted = [...s.origins].sort((a, b) => (b.id === 'cr') - (a.id === 'cr'));
  view.innerHTML = `<h1 class="page">Origins</h1>
    <p class="lede">18 specialty origins. Implied price = front-month futures plus your differential, converted at the delayed exchange rate. Differentials are saved in this browser.</p>
    <div class="grid g3" id="ogrid"></div>`;
  $('#ogrid').innerHTML = sorted.map(o => {
    const b = s.benchmarks[o.benchmark], w = o.weather || {}, fx = o.fx || {};
    const diff = parseFloat(diffs[o.id]) || 0, fut = b?.quote?.price;
    const usdKg = fut == null ? null : (fut + diff) / 100 * s.lb_per_kg;
    const loc = usdKg && fx.price ? usdKg * fx.price : null;
    return `<a class="ocard ${o.id === 'cr' ? 'feature' : ''}" href="#/${o.id === 'cr' ? 'costa-rica' : 'origin/' + o.id}">
      <div class="row"><div><div class="name">${o.flag} ${o.country}</div><div class="tiny faint">${esc(o.region)} · harvest ${esc(o.harvest)}</div></div><span class="spacer"></span>
        <span class="tag ${b ? '' : 'rob'}">${b ? b.short + ' · ' : ''}${esc(o.group)}</span></div>
      <div class="grid g3">
        <div class="kv"><div class="k">USD/${o.currency}</div><div class="v small">${o.currency === 'USD' ? '—' : fmt(fx.price, fx.price > 100 ? 0 : 3)}</div></div>
        <div class="kv"><div class="k">Implied ${!b ? '' : diff ? '' : '(no diff)'}</div><div class="v small">${b ? '$' + fmt(usdKg, 2) + '/kg' : '—'}</div>${b ? '' : '<div class="tiny faint">no free robusta quote</div>'}<div class="tiny faint">${loc && o.currency !== 'USD' ? fmt(loc, loc > 1000 ? 0 : 2) + ' ' + o.currency + '/kg' : ''}</div></div>
        <div class="kv"><div class="k">News 7d</div><div class="v small">${stats.origins[o.id] || 0}</div></div>
      </div>
      <div class="row tiny muted"><span>Rain past 7d <b class="mono">${fmt(w.rain_past7_mm, 0)}</b> · next 7d <b class="mono">${fmt(w.rain_next7_mm, 0)}</b> mm</span><span class="spacer"></span>${bars(w.daily_rain, 90, 22, 'var(--rain)', 7)}</div>
    </a>`;
  }).join('');
}

async function pageOrigin(view, oid) {
  if (oid === 'cr') { location.hash = '#/costa-rica'; return; }
  view.innerHTML = '<div class="loading">Loading…</div>';
  const d = await api('/api/origin/' + oid), o = d.origin, s = SNAP || await refreshSnap();
  const live = s.origins.find(x => x.id === oid) || {};
  const diffs = store.get('diffs', {});
  view.innerHTML = `
    <div class="row"><a href="#/origins" class="small">← Origins</a></div>
    <h1 class="page">${o.flag} ${o.country}</h1>
    <p class="lede">${esc(o.region)} · ${esc(o.group)} · ${o.benchmark === 'arabica' ? 'priced off Arabica KC' : 'Robustas (no free live futures; see IMF monthly prices on the Data page)'} · harvest ${esc(o.harvest)}</p>
    <div class="grid g4">
      <div class="kv"><div class="k">USD/${o.currency}</div><div class="v">${o.currency === 'USD' ? '1 (dollarized)' : fmt(live.fx?.price, 2)}</div></div>
      <div class="kv"><div class="k">Temp now · ${esc(o.region)}</div><div class="v">${fmt(live.weather?.temp_c, 0)}°C</div></div>
      <div class="kv"><div class="k">Rain next 7d</div><div class="v">${fmt(live.weather?.rain_next7_mm, 0)} mm</div></div>
      ${o.benchmark === 'arabica' ? `<div class="kv"><div class="k">Differential</div><div class="calc"><input type="number" id="odiff" value="${diffs[oid] ?? ''}" placeholder="0"> ¢/lb</div></div>` : ''}
    </div>
    <div class="split">
      <div><h2>News</h2><div class="panel tight"><div class="news">${d.news.map(a => newsItem(a)).join('') || '<div class="muted small" style="padding:10px">No stories yet.</div>'}</div></div></div>
      <div>
        <h2>Rainfall, past year</h2><div class="panel"><div class="small muted" style="margin-bottom:6px">${esc(o.region)} · daily mm</div><div class="chart xs" id="orain"></div></div>
        <h2>US imports</h2><div class="panel"><div class="small muted" style="margin-bottom:6px">Monthly tonnes · implied $/kg</div><div class="chart sm" id="oimp"></div></div>
        ${o.currency !== 'USD' ? `<h2>USD/${o.currency}</h2><div class="panel"><div class="chart xs" id="ofx"></div></div>` : ''}
        ${Object.keys(d.psd).length ? `<h2>USDA supply &amp; demand</h2><div class="panel"><table class="t">${Object.values(d.psd).map(p => `<tr><td>${esc(p.meta.name)}</td>${p.points.slice(-4).map(([y, v]) => `<td class="mono">${y}<br>${fmt(v, 0)}</td>`).join('')}</tr>`).join('')}</table><div class="tiny faint">1,000 × 60-kg bags · USDA FAS PSD</div></div>` : ''}
      </div>
    </div>`;
  if ($('#odiff')) $('#odiff').oninput = e => { const ds = store.get('diffs', {}); ds[oid] = e.target.value; store.set('diffs', ds); };
  const S = d.series, rain = S[`wx:${oid}:rain`].points;
  if (rain.length) lineChart($('#orain'), [{type: 'hist', color: '#6aa6d6', data: pts(rain)}]); else $('#orain').innerHTML = '<div class="faint small">Waiting for first data run.</div>';
  const kg = S[`us_imports:${oid}:kg`].points, usd = Object.fromEntries(S[`us_imports:${oid}:usd`].points);
  if (kg.length) lineChart($('#oimp'), [{type: 'hist', color: '#d9a06699', data: kg.map(([t, v]) => ({time: t, value: v / 1000}))},
    {color: '#efe7de', scale: 'left', data: kg.filter(([t, v]) => v && usd[t]).map(([t, v]) => ({time: t, value: usd[t] / v}))}], {left: true});
  else $('#oimp').innerHTML = '<div class="faint small">No US import data.</div>';
  const fxs = S[`fx:${o.currency}`];
  if (fxs && fxs.points.length) lineChart($('#ofx'), [{type: 'area', color: '#d9a066', data: pts(fxs.points)}]);
}

// ==================================================================== DATA
async function pageData(view) {
  view.innerHTML = `<h1 class="page">Market data</h1>
    <p class="lede">Structured datasets from free official sources, refreshed daily and archived so history builds up over time.</p>
    <div class="grid g2">
      <div class="panel"><h3>Speculator positioning (COT)</h3><div class="small muted">Managed money net (bars) vs producer/merchant net (line), Coffee C, contracts</div><div class="chart" id="dcot"></div><div class="tiny faint">CFTC disaggregated futures-only, weekly</div></div>
      <div class="panel"><h3>Physical price benchmarks</h3><div class="small muted">IMF monthly prices, ¢/lb: Other Milds Arabica vs Robustas</div><div class="chart" id="dimf"></div><div class="tiny faint">IMF Primary Commodity Prices via FRED</div></div>
      <div class="panel"><h3>ENSO (El Niño / La Niña)</h3><div class="small muted">Oceanic Niño Index · ≥ +0.5 El Niño (dry risk Central America, Vietnam, Indonesia) · ≤ −0.5 La Niña (dry risk southern Brazil)</div><div class="chart" id="doni"></div><div class="tiny faint">NOAA Climate Prediction Center</div></div>
      <div class="panel"><h3>US green coffee imports by origin</h3><div class="small muted">Last 12 months, tonnes · avg $/kg</div><div id="dimp" style="margin-top:8px"></div><div class="tiny faint">US Census, HS 090111</div></div>
    </div>`;
  const [mm, pm, otm, rob, oni] = await Promise.all(['cot:mm_net', 'cot:pm_net', 'imf:PCOFFOTMUSDM', 'imf:PCOFFROBUSDM', 'enso:oni'].map(s => api('/api/series/' + s)));
  const empty = id => $(id).innerHTML = '<div class="faint small" style="padding:20px 0">Waiting for first data run.</div>';
  mm.points.length ? lineChart($('#dcot'), [{type: 'hist', data: pts(mm.points), colorFn: v => v >= 0 ? '#6fbf8a99' : '#e0705f99'}, {color: '#d9a066', data: pts(pm.points), title: 'producers'}]) : empty('#dcot');
  otm.points.length ? lineChart($('#dimf'), [{color: '#d9a066', data: pts(otm.points.filter(p => p[0] >= '2005')), title: 'Other Milds'}, {color: '#8fbf7f', data: pts(rob.points.filter(p => p[0] >= '2005')), title: 'Robustas'}]) : empty('#dimf');
  oni.points.length ? lineChart($('#doni'), [{type: 'hist', data: pts(oni.points.filter(p => p[0] >= '2010')), colorFn: v => v >= .5 ? '#e0705f' : v <= -.5 ? '#6aa6d6' : '#6f6358'}]) : empty('#doni');
  const list = await api('/api/series?prefix=us_imports:');
  const kgIds = list.filter(s => s.sid.endsWith(':kg') && !s.sid.includes(':total:'));
  if (!kgIds.length) { empty('#dimp'); return; }
  const rows = await Promise.all(kgIds.map(async s => { const oid = s.sid.split(':')[1];
    const [kg, usd] = await Promise.all([api('/api/series/' + s.sid), api(`/api/series/us_imports:${oid}:usd`)]);
    const k = kg.points.slice(-12).reduce((a, p) => a + p[1], 0), u = usd.points.slice(-12).reduce((a, p) => a + p[1], 0);
    return {oid, t: k / 1000, p: k ? u / k : null}; }));
  rows.sort((a, b) => b.t - a.t); const mx = rows[0].t || 1;
  $('#dimp').innerHTML = rows.map(r => `<a href="#/${r.oid === 'cr' ? 'costa-rica' : 'origin/' + r.oid}" class="row small" style="color:var(--text);margin:4px 0">
    <span style="width:130px">${originName(r.oid)}</span><span style="flex:1;height:7px;background:var(--panel2);border-radius:3px"><span style="display:block;height:7px;width:${r.t / mx * 100}%;background:${r.oid === 'cr' ? 'var(--cr)' : 'var(--accent)'};border-radius:3px"></span></span>
    <span class="mono" style="width:70px;text-align:right">${big(r.t)} t</span><span class="mono faint" style="width:60px;text-align:right">$${fmt(r.p, 2)}</span></a>`).join('');
}

// ================================================================= SOURCES
async function pageSources(view) {
  const rows = await api('/api/sources');
  const ok = rows.filter(r => r.ok).length, bad = rows.filter(r => r.ok === false).length, never = rows.filter(r => r.ok == null).length;
  const label = {rss: 'Publisher RSS', gnews: 'Google News', gdelt: 'GDELT', data: 'Data'};
  view.innerHTML = `<h1 class="page">Sources</h1>
    <p class="lede">Every feed and dataset the platform pulls, with the result of its last run. Free sources change and break; this page is how you see it. Failing sources keep being retried.</p>
    <div class="row" style="margin-bottom:12px"><span class="pill"><span class="okdot" style="background:var(--up)"></span> ${ok} working</span>
      <span class="pill"><span class="okdot" style="background:var(--down)"></span> ${bad} failing</span><span class="pill">${never} skipped / not run yet</span></div>
    ${['data', 'rss', 'gdelt', 'gnews'].map(ch => `<h2>${label[ch]}</h2><div class="panel tight" style="overflow-x:auto"><table class="t">
      <tr><th></th><th>Source</th><th>Last run</th><th>Items</th><th>New</th><th>Detail</th></tr>
      ${rows.filter(r => r.channel === ch).map(r => `<tr><td><span class="okdot" style="background:${r.ok ? 'var(--up)' : r.ok === false ? 'var(--down)' : 'var(--faint)'}"></span></td>
        <td>${esc(r.name)}${r.url ? `<div class="tiny faint">${esc(r.url)}</div>` : ''}</td>
        <td class="mono">${r.last_run ? ago(r.last_run) : '—'}</td><td class="mono">${r.fetched ?? '—'}</td><td class="mono">${r.new ?? '—'}</td>
        <td class="small ${r.ok === false ? 'down' : r.error ? 'muted' : 'faint'}">${esc((r.error || '').replace(/^ValueError: /, '') || (r.duration != null ? r.duration + 's' : ''))}</td></tr>`).join('')}
    </table></div>`).join('')}`;
}

// ===================================================================== DEV
async function pageDev(view) {
  const info = await api('/api/dev/info');
  const demo = info.mode === 'demo';
  const t = ts => ts ? ago(ts) : 'never';
  view.innerHTML = `
    <h1 class="page">Dev tools</h1>
    <p class="lede">Local-only controls for testing. ${demo
      ? 'You are in <b style="color:var(--accent)">demo mode</b>: synthetic prices, fixture news, and a new demo headline every ' + info.background.drip_every + ' seconds. Nothing touches the internet. Run <code>./dev.sh live</code> to use real sources.'
      : 'You are in <b style="color:var(--up)">live mode</b>: real sources, archived to a local SQLite file. Run <code>./dev.sh</code> for the offline demo.'}
      This page is hidden when deployed to GCP.</p>
    <div class="grid g4">
      <div class="kv"><div class="k">Mode</div><div class="v">${info.mode}</div><div class="tiny faint">prices ${info.mock_prices ? 'synthetic' : 'Yahoo (delayed)'}</div></div>
      <div class="kv"><div class="k">Archive</div><div class="v">${fmt(info.store.articles, 0)} articles</div><div class="tiny faint">${info.store.series ?? '—'} series · ${big(info.store.bytes)}B</div></div>
      <div class="kv"><div class="k">Background ingestion</div><div class="v">${info.background.on ? (info.background.busy ? 'running…' : 'on') : 'off'}</div>
        <div class="tiny faint">news ${t(info.background.last_news)} · data ${t(info.background.last_data)}</div></div>
      <div class="kv"><div class="k">Optional keys</div><div class="v small">${Object.entries(info.keys).map(([k, v]) => `<span class="${v ? 'up' : 'faint'}">${v ? '✓' : '·'} ${k}</span>`).join('<br>')}</div></div>
    </div>
    ${info.background.last_error ? `<div class="err" style="margin-top:8px">Last background error: ${esc(info.background.last_error)}</div>` : ''}
    <div class="tiny faint mono" style="margin-top:6px">${esc(info.store.path || '')} · Python ${info.python}</div>

    <h2>Actions</h2>
    <div class="panel">
      <div class="row">
        <button class="btn" data-act="news">Run news ingestion${demo ? ' (fixtures)' : ''}</button>
        <button class="btn" data-act="news-fast">News without GDELT</button>
        <button class="btn" data-act="data">Run data jobs${demo ? ' (fixtures)' : ''}</button>
        ${demo ? '<button class="btn" data-act="drip">Add 5 demo headlines</button>' : ''}
        <button class="btn" data-act="reset" style="border-color:#6a3a30">${demo ? 'Reset &amp; reseed demo' : 'Wipe local archive'}</button>
      </div>
      <div class="row" style="margin-top:10px"><span class="small muted">Single data job:</span>
        <select id="job">${Object.entries(info.data_jobs).map(([k, v]) => `<option value="${k}">${esc(v)}</option>`).join('')}</select>
        <button class="btn" data-act="job">Run</button></div>
      <pre id="actout" class="small mono" style="white-space:pre-wrap;color:var(--muted);margin:12px 0 0;max-height:260px;overflow:auto"></pre>
    </div>

    <div class="split">
      <div>
        <h2>Tagging playground</h2>
        <div class="panel">
          <div class="small muted" style="margin-bottom:8px">Paste any headline to see how it would be tagged and which keywords fired. Edit <code>app/tagging.py</code> or <code>app/config.py</code>, save, and the server reloads; try again.</div>
          <textarea id="tagin" rows="3" style="width:100%;background:var(--bg);color:var(--text);border:1px solid var(--line);border-radius:7px;padding:8px;font-family:var(--sans)">Productores de Tarrazú reportan sequía y caída en la cosecha de café</textarea>
          <div class="row" style="margin-top:8px"><button class="btn" id="tagbtn">Tag it</button></div>
          <div id="tagout" style="margin-top:10px"></div>
        </div>
      </div>
      <div>
        <h2>Test a feed</h2>
        <div class="panel">
          <div class="small muted" style="margin-bottom:8px">Fetch any RSS/Atom URL and preview the parsed, tagged items before adding it to <code>RSS_FEEDS</code> in <code>app/config.py</code>.${demo ? ' <b>Needs live mode.</b>' : ''}</div>
          <input type="search" id="feedurl" placeholder="https://example.com/feed/" style="width:100%">
          <label class="small muted row" style="margin-top:8px"><input type="checkbox" id="feedfilter"> keep only coffee stories (for general-news feeds)</label>
          <div class="row" style="margin-top:8px"><button class="btn" id="feedbtn" ${demo ? 'disabled' : ''}>Test feed</button></div>
          <div id="feedout" style="margin-top:10px"></div>
        </div>
      </div>
    </div>

    <h2>What's configured</h2>
    <div class="panel small">
      <div class="grid g4">${Object.entries(info.catalog).map(([k, v]) => `<div class="kv"><div class="k">${k.replace('_', ' ')}</div><div class="v">${v}</div></div>`).join('')}</div>
      <div class="muted" style="margin-top:10px">Where to edit: origins, feeds and queries in <code>app/config.py</code> · keyword tagging in <code>app/tagging.py</code> · data jobs in <code>app/ingest/data.py</code> · pages in <code>app/static/app.js</code> · styles in <code>app/static/app.css</code>.</div>
    </div>`;

  const out = $('#actout');
  const post = async (url, label) => {
    out.textContent = label + '…';
    $$('[data-act]').forEach(b => b.disabled = true);
    try { const r = await fetch(url, {method: 'POST'}); const j = await r.json();
      out.textContent = label + (r.ok ? ' ✓\n' : ' ✗\n') + JSON.stringify(j, null, 2); SNAP = null; await refreshSnap();
    } catch (e) { out.textContent = label + ' failed: ' + e.message; }
    $$('[data-act]').forEach(b => b.disabled = false);
  };
  $$('[data-act]').forEach(b => b.onclick = () => {
    const a = b.dataset.act;
    if (a === 'news') post('/api/dev/ingest/news', 'News ingestion');
    if (a === 'news-fast') post('/api/dev/ingest/news?gdelt=false', 'News ingestion (no GDELT)');
    if (a === 'data') post('/api/dev/ingest/data', 'Data jobs');
    if (a === 'job') post('/api/dev/ingest/data?only=' + $('#job').value, 'Data job ' + $('#job').value);
    if (a === 'drip') post('/api/dev/drip?n=5', 'Demo headlines');
    if (a === 'reset') { if (demo || confirm('Delete everything in the local live archive?')) post('/api/dev/reset' + (demo ? '' : '?confirm=yes'), 'Reset'); }
  });

  const chipList = (obj) => Object.entries(obj).map(([k, terms]) => `<span class="chip ${k.startsWith('cr') ? 'cr' : 'o'}">${esc(originName(k) || k)}</span> <span class="faint tiny">${terms.map(esc).join(', ')}</span>`).join('<br>') || '<span class="faint">none</span>';
  const runTag = async () => {
    const r = await fetch('/api/dev/tag', {method: 'POST', headers: {'content-type': 'application/json'}, body: JSON.stringify({title: $('#tagin').value})});
    const d = await r.json(), m = d.matched, res = d.result;
    $('#tagout').innerHTML = `
      <div class="row small" style="margin-bottom:8px">${d.is_coffee ? '<span class="up">✓ coffee story</span>' : '<span class="down">✗ not detected as coffee (dropped from Google News/GDELT)</span>'}
        <span class="sig ${res.signal}">${res.signal} (${res.score >= 0 ? '+' : ''}${res.score})</span></div>
      <table class="t"><tr><td class="faint">Origins</td><td>${chipList(m.origins)}</td></tr>
        <tr><td class="faint">CR regions</td><td>${chipList(m.regions)}</td></tr>
        <tr><td class="faint">Topics</td><td>${Object.entries(m.topics).map(([k, v]) => `<span class="chip">${TOPIC_LABEL[k] || k}</span> <span class="faint tiny">${v.map(esc).join(', ')}</span>`).join('<br>') || '<span class="faint">none → General</span>'}</td></tr>
        <tr><td class="faint">Bullish words</td><td class="up small">${m.bullish.map(esc).join(', ') || '<span class="faint">—</span>'}</td></tr>
        <tr><td class="faint">Bearish words</td><td class="down small">${m.bearish.map(esc).join(', ') || '<span class="faint">—</span>'}</td></tr>
        <tr><td class="faint">Coffee terms</td><td class="small">${m.coffee_terms.map(esc).join(', ') || '<span class="faint">—</span>'}</td></tr></table>`;
  };
  $('#tagbtn').onclick = runTag; runTag();

  $('#feedbtn').onclick = async () => {
    $('#feedout').innerHTML = '<div class="faint small">Fetching…</div>';
    const r = await fetch('/api/dev/test-feed', {method: 'POST', headers: {'content-type': 'application/json'},
      body: JSON.stringify({url: $('#feedurl').value, filter_coffee: $('#feedfilter').checked})});
    const d = await r.json();
    $('#feedout').innerHTML = !r.ok ? `<div class="err">${esc(d.detail)}</div>` : !d.ok ? `<div class="err">${esc(d.error)}</div>`
      : `<div class="small up" style="margin-bottom:6px">✓ ${d.count} items parsed</div><div class="news">${d.items.map(a => newsItem({...a, source_name: 'preview'}, {compact: true})).join('')}</div>`;
  };
}

// ================================================================== router
async function route() {
  charts.forEach(c => { try { c.remove(); } catch {} }); charts = [];
  timers.forEach(clearInterval); timers = [];
  const [path, qs] = (location.hash.slice(1) || '/').split('?');
  const params = new URLSearchParams(qs || '');
  $$('#nav a').forEach(a => a.classList.toggle('on', a.getAttribute('href') === '#' + (path.startsWith('/origin/') ? '/origins' : path)));
  const view = $('#view');
  try {
    if (!META) { META = await api('/api/meta'); $('#devlink').hidden = !META.dev_tools; if (SNAP) renderStatus(SNAP); }
    if (path === '/' || path === '') await pageOverview(view);
    else if (path === '/costa-rica') await pageCostaRica(view);
    else if (path === '/news') await pageNews(view, params);
    else if (path === '/origins') await pageOrigins(view);
    else if (path.startsWith('/origin/')) await pageOrigin(view, path.split('/')[2]);
    else if (path === '/data') await pageData(view);
    else if (path === '/sources') await pageSources(view);
    else if (path === '/dev' && META.dev_tools) await pageDev(view);
    else view.innerHTML = '<div class="loading">Not found</div>';
  } catch (e) { console.error(e); view.innerHTML = `<div class="err" style="padding:20px 0">Couldn't load this page: ${esc(e.message)}</div>`; }
  window.scrollTo(0, 0);
}
window.addEventListener('hashchange', route);
refreshSnap().then(route);
setInterval(async () => { await refreshSnap(); if ((location.hash || '#/') === '#/' && $('#tiles')) { renderTiles(SNAP); } }, 60000);
