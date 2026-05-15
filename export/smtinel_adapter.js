/* =========================================================
   TraceOps Live Adapter for SMTinel
   Adds Live WhatsApp MCP mode without modifying existing ZIP flow.
   ========================================================= */
(function(){
  'use strict';
  if (window.__SMTINEL_TRACEOPS_LIVE_ADAPTER__) return;
  window.__SMTINEL_TRACEOPS_LIVE_ADAPTER__ = true;

  var CONFIG = {
    apiBase: (localStorage.getItem('traceops_live_api_base') || 'http://127.0.0.1:8000').replace(/\/$/, ''),
    refreshMs: Number(localStorage.getItem('traceops_live_refresh_ms') || 15000),
    maxItems: 8
  };

  var state = {
    mode: localStorage.getItem('traceops_source_mode') || 'zip',
    connected: false,
    lastRefresh: null,
    timer: null,
    data: { health:null, status:null, incidents:null, alerts:null, stats:null }
  };

  function esc(v){
    return String(v == null ? '' : v).replace(/[&<>"']/g, function(c){
      return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c];
    });
  }
  function sevClass(sev){
    sev = String(sev || '').toLowerCase();
    if (sev === 'critical') return 'crit';
    if (sev === 'high') return 'high';
    if (sev === 'medium') return 'med';
    return 'low';
  }
  function fmtTime(iso){
    if(!iso) return '—';
    try { return new Date(iso).toLocaleString(); } catch(_) { return String(iso); }
  }
  function q(sel){ return document.querySelector(sel); }
  function qa(sel){ return Array.prototype.slice.call(document.querySelectorAll(sel)); }

  function injectStyles(){
    if (document.getElementById('traceops-live-style')) return;
    var css = `
      .traceops-live-dock{background:#fff;border:1px solid rgba(31,58,95,.14);border-radius:22px;margin:0 0 16px;box-shadow:0 14px 34px rgba(16,42,67,.08);overflow:hidden;color:#102A43;font-family:'Inter','Segoe UI',Arial,sans-serif;position:relative;z-index:3}
      .traceops-live-head{display:flex;align-items:flex-start;justify-content:space-between;gap:14px;padding:16px 18px;background:linear-gradient(135deg,#F7FAFF,#EEF5FF);border-bottom:1px solid rgba(31,58,95,.10);flex-wrap:wrap}
      .traceops-live-title{display:flex;flex-direction:column;gap:4px;min-width:220px}.traceops-live-kicker{font-size:10px;font-weight:900;letter-spacing:.14em;text-transform:uppercase;color:#2F6FB3}.traceops-live-title h3{font-size:18px;line-height:1.1;margin:0;font-weight:900;color:#102A43}.traceops-live-sub{font-size:12px;line-height:1.45;color:#5F766C;max-width:680px}
      .traceops-live-actions{display:flex;gap:8px;align-items:center;flex-wrap:wrap;justify-content:flex-end}.traceops-live-toggle{display:inline-flex;gap:4px;background:#EAF2FF;border:1px solid #C7DBF7;border-radius:999px;padding:5px}.traceops-live-toggle button,.traceops-live-btn{border:0;border-radius:999px;background:transparent;color:#1F3A5F;padding:9px 12px;font-size:11px;font-weight:900;cursor:pointer;white-space:nowrap}.traceops-live-toggle button.active{background:#1F3A5F;color:#fff;box-shadow:0 8px 18px rgba(31,58,95,.16)}.traceops-live-btn{border:1px solid #C7DBF7;background:#fff}.traceops-live-btn.primary{background:linear-gradient(135deg,#1E8A64,#4A90E2);color:#fff;border-color:transparent;box-shadow:0 10px 20px rgba(47,111,179,.18)}
      .traceops-live-body{padding:16px 18px;display:none}.traceops-live-dock.live-on .traceops-live-body{display:block}.traceops-live-status{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:14px}.traceops-live-pill{display:inline-flex;align-items:center;gap:6px;border-radius:999px;padding:7px 11px;font-size:10.5px;font-weight:900;border:1px solid #D9E6F7;background:#F7FAFF;color:#1F3A5F}.traceops-live-dot{width:8px;height:8px;border-radius:50%;background:#9CA3AF}.traceops-live-dot.on{background:#1E8A64}.traceops-live-dot.err{background:#C0392B}
      .traceops-live-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px;margin-bottom:14px}.traceops-live-kpi{border:1px solid #D9E6F7;border-radius:16px;background:linear-gradient(180deg,#fff,#FAFCFF);padding:12px 14px}.traceops-live-kpi .lbl{font-size:10px;font-weight:900;letter-spacing:.08em;text-transform:uppercase;color:#5F766C}.traceops-live-kpi .val{font-size:26px;font-weight:900;letter-spacing:-.04em;color:#102A43;margin-top:5px}.traceops-live-kpi .meta{font-size:10.5px;color:#5F766C;margin-top:4px;line-height:1.35}
      .traceops-live-columns{display:grid;grid-template-columns:1fr 1fr;gap:12px}.traceops-live-panel{border:1px solid #D9E6F7;border-radius:18px;overflow:hidden;background:#fff}.traceops-live-panel h4{margin:0;padding:12px 14px;background:#F7FAFF;border-bottom:1px solid #ECF3FF;color:#102A43;font-size:12px;font-weight:900;letter-spacing:.08em;text-transform:uppercase}.traceops-live-list{display:flex;flex-direction:column;gap:8px;padding:12px}.traceops-live-item{display:flex;align-items:flex-start;justify-content:space-between;gap:10px;border:1px solid #E5ECF7;border-radius:14px;padding:10px 12px;background:#fff}.traceops-live-copy{min-width:0}.traceops-live-copy b{display:block;font-size:12px;color:#102A43;line-height:1.3}.traceops-live-copy span{display:block;margin-top:3px;font-size:10.5px;color:#5F766C;line-height:1.35}.traceops-live-badge{flex:0 0 auto;border-radius:999px;padding:4px 8px;font-size:9px;font-weight:900;text-transform:uppercase}.traceops-live-badge.crit{background:#FDEEEE;color:#C44141}.traceops-live-badge.high{background:#FFF7E8;color:#9A6A16}.traceops-live-badge.med{background:#EEF5FF;color:#2F6FB3}.traceops-live-badge.low{background:#EEF6FF;color:#1E8A64}.traceops-live-empty{padding:18px;color:#5F766C;font-size:12px}.traceops-live-config{display:none;margin-top:10px;padding:12px;border:1px dashed #C7DBF7;border-radius:14px;background:#FBFDFF}.traceops-live-config.open{display:block}.traceops-live-config label{display:block;font-size:10px;font-weight:900;text-transform:uppercase;color:#5F766C;margin-bottom:5px}.traceops-live-config input{width:100%;border:1px solid #C7DBF7;border-radius:12px;padding:9px 11px;color:#102A43;font-size:12px;outline:none}
      @media(max-width:900px){.traceops-live-grid{grid-template-columns:repeat(2,minmax(0,1fr))}.traceops-live-columns{grid-template-columns:1fr}.traceops-live-actions{justify-content:flex-start}.traceops-live-head{padding:14px}.traceops-live-body{padding:14px}}
      @media(max-width:560px){.traceops-live-grid{grid-template-columns:1fr}.traceops-live-toggle,.traceops-live-actions,.traceops-live-btn{width:100%;justify-content:center}.traceops-live-toggle button{flex:1}}
    `;
    var style = document.createElement('style');
    style.id = 'traceops-live-style';
    style.textContent = css;
    document.head.appendChild(style);
  }

  function renderShell(){
    injectStyles();
    if (document.getElementById('traceops-live-dock')) return;
    var dock = document.createElement('section');
    dock.id = 'traceops-live-dock';
    dock.className = 'traceops-live-dock' + (state.mode === 'live' ? ' live-on' : '');
    dock.innerHTML = `
      <div class="traceops-live-head">
        <div class="traceops-live-title">
          <div class="traceops-live-kicker">TraceOps Live Source</div>
          <h3>ZIP Upload / Live WhatsApp MCP</h3>
          <div class="traceops-live-sub">Modo ZIP conserva el flujo manual. Modo Live consume TraceOps Live API local y actualiza incidentes, alertas y KPIs sin tocar el analizador existente.</div>
        </div>
        <div class="traceops-live-actions">
          <div class="traceops-live-toggle" role="group" aria-label="SMTinel source mode">
            <button type="button" data-traceops-mode="zip">ZIP Upload</button>
            <button type="button" data-traceops-mode="live">Live WhatsApp MCP</button>
          </div>
          <button type="button" class="traceops-live-btn primary" id="traceops-live-refresh">Refresh</button>
          <button type="button" class="traceops-live-btn" id="traceops-live-config-btn">API</button>
        </div>
        <div class="traceops-live-config" id="traceops-live-config">
          <label>TraceOps Live API Base URL</label>
          <input id="traceops-live-api-input" value="${esc(CONFIG.apiBase)}" placeholder="http://127.0.0.1:8000">
        </div>
      </div>
      <div class="traceops-live-body">
        <div class="traceops-live-status" id="traceops-live-status"></div>
        <div class="traceops-live-grid" id="traceops-live-kpis"></div>
        <div class="traceops-live-columns">
          <div class="traceops-live-panel"><h4>Sentinel Alerts</h4><div class="traceops-live-list" id="traceops-live-alerts"></div></div>
          <div class="traceops-live-panel"><h4>Open Incidents</h4><div class="traceops-live-list" id="traceops-live-incidents"></div></div>
        </div>
      </div>`;
    var main = q('.main-content') || q('#root') || document.body;
    var anchor = q('.traceops-context') || q('.ops-hero') || main.firstElementChild;
    if (anchor && anchor.parentNode) anchor.parentNode.insertBefore(dock, anchor.nextSibling);
    else main.insertBefore(dock, main.firstChild);
    bindUI();
    applyMode();
    renderData();
  }

  function bindUI(){
    qa('[data-traceops-mode]').forEach(function(btn){
      btn.addEventListener('click', function(){
        setMode(btn.getAttribute('data-traceops-mode'));
      });
    });
    var refresh = q('#traceops-live-refresh');
    if(refresh) refresh.addEventListener('click', function(){ refreshLive(true); });
    var configBtn = q('#traceops-live-config-btn');
    var configBox = q('#traceops-live-config');
    if(configBtn && configBox) configBtn.addEventListener('click', function(){ configBox.classList.toggle('open'); });
    var input = q('#traceops-live-api-input');
    if(input){
      input.addEventListener('change', function(){
        CONFIG.apiBase = String(input.value || '').replace(/\/$/, '') || 'http://127.0.0.1:8000';
        localStorage.setItem('traceops_live_api_base', CONFIG.apiBase);
        refreshLive(true);
      });
    }
  }

  function setMode(mode){
    state.mode = mode === 'live' ? 'live' : 'zip';
    localStorage.setItem('traceops_source_mode', state.mode);
    applyMode();
    if (state.mode === 'live') startLive(); else stopLive();
  }
  function applyMode(){
    var dock = q('#traceops-live-dock');
    if(dock) dock.classList.toggle('live-on', state.mode === 'live');
    qa('[data-traceops-mode]').forEach(function(btn){ btn.classList.toggle('active', btn.getAttribute('data-traceops-mode') === state.mode); });
  }
  function startLive(){
    refreshLive(true);
    if(state.timer) clearInterval(state.timer);
    state.timer = setInterval(function(){ refreshLive(false); }, Math.max(5000, CONFIG.refreshMs));
  }
  function stopLive(){ if(state.timer){ clearInterval(state.timer); state.timer = null; } }

  async function fetchJson(path, opts){
    var res = await fetch(CONFIG.apiBase + path, Object.assign({headers:{'Accept':'application/json'}}, opts || {}));
    if(!res.ok) throw new Error(path + ' HTTP ' + res.status);
    return await res.json();
  }
  async function refreshLive(forcePoll){
    try{
      if(forcePoll){ try{ await fetchJson('/ingest/poll', {method:'POST'}); }catch(_){} }
      var results = await Promise.allSettled([
        fetchJson('/health'), fetchJson('/status'), fetchJson('/incidents?limit=20'), fetchJson('/alerts?limit=20'), fetchJson('/stats')
      ]);
      state.data.health = results[0].status === 'fulfilled' ? results[0].value : null;
      state.data.status = results[1].status === 'fulfilled' ? results[1].value : null;
      state.data.incidents = results[2].status === 'fulfilled' ? results[2].value : null;
      state.data.alerts = results[3].status === 'fulfilled' ? results[3].value : null;
      state.data.stats = results[4].status === 'fulfilled' ? results[4].value : null;
      state.connected = !!state.data.health;
      state.lastRefresh = new Date();
      renderData();
      publishLiveSnapshot();
    }catch(err){
      state.connected = false;
      renderData(String(err && err.message || err));
    }
  }

  function renderData(error){
    var statusEl = q('#traceops-live-status');
    var kpiEl = q('#traceops-live-kpis');
    var alertsEl = q('#traceops-live-alerts');
    var incEl = q('#traceops-live-incidents');
    if(!statusEl || !kpiEl || !alertsEl || !incEl) return;
    var components = state.data.status && state.data.status.components || {};
    var incidents = state.data.incidents && state.data.incidents.incidents || [];
    var alerts = state.data.alerts && state.data.alerts.alerts || [];
    var parser = state.data.stats && state.data.stats.parser || {};
    var ingestor = state.data.stats && state.data.stats.ingestor || {};
    var crit = alerts.filter(function(a){ return String(a.severity || '').toLowerCase() === 'critical'; }).length;
    var high = alerts.filter(function(a){ return String(a.severity || '').toLowerCase() === 'high'; }).length;
    statusEl.innerHTML = `
      <span class="traceops-live-pill"><span class="traceops-live-dot ${state.connected ? 'on' : (error ? 'err' : '')}"></span>${state.connected ? 'API Connected' : 'API Offline'}</span>
      <span class="traceops-live-pill">Base: ${esc(CONFIG.apiBase)}</span>
      <span class="traceops-live-pill">Last refresh: ${esc(state.lastRefresh ? state.lastRefresh.toLocaleTimeString() : '—')}</span>
      ${error ? `<span class="traceops-live-pill"><span class="traceops-live-dot err"></span>${esc(error)}</span>` : ''}`;
    kpiEl.innerHTML = [
      {lbl:'Active Incidents', val: components.active_incidents != null ? components.active_incidents : incidents.length, meta:'Open / clustered manufacturing events'},
      {lbl:'Sentinel Alerts', val: components.active_alerts != null ? components.active_alerts : alerts.length, meta: crit + ' critical · ' + high + ' high'},
      {lbl:'Parser Success', val: pct(parser.success_rate), meta:(parser.successful_parses || 0) + ' parsed / ' + (parser.total_parsed || 0) + ' total'},
      {lbl:'Ingestor', val: ingestor.messages_processed || ingestor.total_messages || 0, meta:'Incremental WhatsApp messages'}
    ].map(function(k){ return `<div class="traceops-live-kpi"><div class="lbl">${esc(k.lbl)}</div><div class="val">${esc(k.val)}</div><div class="meta">${esc(k.meta)}</div></div>`; }).join('');
    alertsEl.innerHTML = alerts.length ? alerts.slice(0, CONFIG.maxItems).map(function(a){
      return `<div class="traceops-live-item"><div class="traceops-live-copy"><b>${esc(a.title || a.alert_type || 'Sentinel alert')}</b><span>${esc([a.affected_line && ('Line ' + a.affected_line), a.affected_station, a.affected_component, a.description].filter(Boolean).join(' · '))}</span><span>${esc(fmtTime(a.generated_at))}</span></div><span class="traceops-live-badge ${sevClass(a.severity)}">${esc(a.severity || 'info')}</span></div>`;
    }).join('') : '<div class="traceops-live-empty">No live alerts yet. Use Refresh after starting TraceOps Live or run demo.py.</div>';
    incEl.innerHTML = incidents.length ? incidents.slice(0, CONFIG.maxItems).map(function(i){
      return `<div class="traceops-live-item"><div class="traceops-live-copy"><b>${esc([i.primary_station, i.primary_component, i.primary_defect].filter(Boolean).join(' · ') || i.incident_id || 'Incident')}</b><span>${esc([i.primary_line && ('Line ' + i.primary_line), i.primary_model, (i.event_count || 0) + ' events', i.status].filter(Boolean).join(' · '))}</span><span>${esc(fmtTime(i.created_at))}</span></div><span class="traceops-live-badge ${sevClass(i.max_severity)}">${esc(i.max_severity || 'low')}</span></div>`;
    }).join('') : '<div class="traceops-live-empty">No open incidents detected.</div>';
  }
  function pct(v){ var n = Number(v || 0); return Math.round(n * 100) + '%'; }

  function publishLiveSnapshot(){
    window.SMTinelTraceOpsLive = {
      mode: state.mode,
      connected: state.connected,
      apiBase: CONFIG.apiBase,
      lastRefresh: state.lastRefresh,
      data: state.data,
      refresh: function(){ return refreshLive(true); },
      setMode: setMode
    };
    try { window.dispatchEvent(new CustomEvent('traceops-live:update', { detail: window.SMTinelTraceOpsLive })); } catch(_) {}
  }

  function boot(){
    renderShell();
    publishLiveSnapshot();
    if(state.mode === 'live') startLive();
  }
  if(document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot); else boot();
})();
