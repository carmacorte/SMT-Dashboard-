/* TraceOps Maintenance Andon Module v0.1
   Standalone module. Does not require changes inside the React App.
   Mounts into #maintenance-section when available and stores events in localStorage.
*/
(function(){
  'use strict';

  var KEY = 'traceops_maintenance_andon_v1';
  var USER_KEY = 'traceops_current_user_v1';
  var CHANNEL = 'traceops-maintenance-andon';
  var mounted = false;
  var events = [];
  var filters = { status: 'ACTIVE', line: 'ALL', priority: 'ALL' };

  function nowIso(){ return new Date().toISOString(); }
  function dateOnly(iso){ return String(iso || '').slice(0,10); }
  function timeOnly(iso){ return String(iso || '').slice(11,16); }
  function pad(n){ return String(n).padStart(2,'0'); }
  function uid(){
    var d = new Date();
    return 'ANDON-' + d.getFullYear() + pad(d.getMonth()+1) + pad(d.getDate()) + '-' + pad(d.getHours()) + pad(d.getMinutes()) + pad(d.getSeconds());
  }
  function esc(s){
    return String(s == null ? '' : s)
      .replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')
      .replace(/"/g,'&quot;').replace(/'/g,'&#39;');
  }
  function getUser(){
    try { return localStorage.getItem(USER_KEY) || ''; } catch(_) { return ''; }
  }
  function setUser(v){
    try { localStorage.setItem(USER_KEY, String(v || '').trim()); } catch(_) {}
  }
  function load(){
    try { events = JSON.parse(localStorage.getItem(KEY) || '[]') || []; }
    catch(_) { events = []; }
  }
  function save(){
    try { localStorage.setItem(KEY, JSON.stringify(events || [])); } catch(_) {}
    broadcast({ type:'andon-sync', at: nowIso() });
  }
  function broadcast(msg){
    try {
      if (window.BroadcastChannel) {
        var bc = new BroadcastChannel(CHANNEL);
        bc.postMessage(msg || {});
        bc.close();
      }
    } catch(_) {}
  }
  function notify(title, body){
    renderToast(title, body);
    try {
      if ('Notification' in window && Notification.permission === 'granted') {
        new Notification(title, { body: body || '', tag: 'traceops-andon' });
      }
    } catch(_) {}
  }
  function requestNotifyPermission(){
    try {
      if (!('Notification' in window)) return;
      if (Notification.permission === 'default') Notification.requestPermission();
    } catch(_) {}
  }
  function renderToast(title, body){
    var old = document.getElementById('traceops-andon-toast');
    if (old) old.remove();
    var box = document.createElement('div');
    box.id = 'traceops-andon-toast';
    box.style.cssText = 'position:fixed;right:18px;bottom:18px;z-index:99999;width:min(360px,calc(100vw - 36px));background:#102A43;color:#fff;border:1px solid rgba(255,255,255,.18);box-shadow:0 18px 50px rgba(0,0,0,.24);border-radius:18px;padding:14px 16px;font-family:Inter,-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif';
    box.innerHTML = '<div style="font-size:12px;font-weight:800;margin-bottom:4px">' + esc(title) + '</div><div style="font-size:11px;line-height:1.45;color:rgba(255,255,255,.78)">' + esc(body || '') + '</div>';
    document.body.appendChild(box);
    setTimeout(function(){ try { box.remove(); } catch(_) {} }, 4200);
  }
  function minsBetween(a,b){
    var aa = new Date(a || 0).getTime();
    var bb = new Date(b || nowIso()).getTime();
    if (!aa || !bb || bb < aa) return 0;
    return Math.round((bb-aa)/60000);
  }
  function activeRows(){
    return events.filter(function(e){ return ['OPEN','ASSIGNED','IN_PROGRESS','ESCALATED'].indexOf(e.status) >= 0; });
  }
  function filteredRows(){
    return (events || []).filter(function(e){
      if (filters.status === 'ACTIVE' && ['DONE','CANCELLED'].indexOf(e.status) >= 0) return false;
      if (filters.status !== 'ALL' && filters.status !== 'ACTIVE' && e.status !== filters.status) return false;
      if (filters.line !== 'ALL' && e.line !== filters.line) return false;
      if (filters.priority !== 'ALL' && e.priority !== filters.priority) return false;
      return true;
    });
  }
  function uniq(field){
    var m = {};
    events.forEach(function(e){ if (e[field]) m[e[field]] = true; });
    return Object.keys(m).sort();
  }
  function priorityColor(p){
    if (p === 'Critical') return '#C0392B';
    if (p === 'High') return '#B87820';
    if (p === 'Medium') return '#2F6FB3';
    return '#1A7A3C';
  }
  function statusLabel(s){
    return ({OPEN:'Open',ASSIGNED:'Assigned',IN_PROGRESS:'In progress',DONE:'Done',ESCALATED:'Escalated',CANCELLED:'Cancelled'})[s] || s || 'Open';
  }
  function kpis(){
    var open = events.filter(function(e){ return e.status === 'OPEN'; }).length;
    var progress = events.filter(function(e){ return e.status === 'IN_PROGRESS' || e.status === 'ASSIGNED'; }).length;
    var doneToday = events.filter(function(e){ return e.status === 'DONE' && dateOnly(e.closed_at) === dateOnly(nowIso()); }).length;
    var active = activeRows();
    var avgResponse = 0;
    var responseRows = events.filter(function(e){ return e.accepted_at; });
    if (responseRows.length) {
      avgResponse = Math.round(responseRows.reduce(function(a,e){ return a + minsBetween(e.created_at, e.accepted_at); },0) / responseRows.length);
    }
    return { open: open, progress: progress, doneToday: doneToday, active: active.length, avgResponse: avgResponse };
  }
  function seedFromForm(){
    var line = val('ta-line') || val('maintenance_line') || '';
    var station = val('ta-station') || '';
    var symptom = val('ta-symptom') || '';
    var priority = val('ta-priority') || 'Medium';
    if (!line && !station && !symptom) {
      alert('Captura al menos Line, Station/Equipment o Symptom.');
      return;
    }
    var e = {
      id: uid(),
      status: 'OPEN',
      priority: priority,
      line: line,
      station: station,
      equipment: val('ta-equipment') || station,
      issue_type: val('ta-issue-type') || 'Mechanical',
      symptom: symptom,
      created_by: getUser() || 'Production',
      created_at: nowIso(),
      assigned_to: '', accepted_at: '', started_at: '', closed_at: '',
      finding: '', action: '', parts: '', downtime_min: '', validation: '', history: []
    };
    e.history.push({ at: e.created_at, by: e.created_by, action: 'OPENED' });
    events.unshift(e);
    save();
    clearOpenForm();
    render();
    notify('Maintenance Andon abierto', e.line + ' · ' + e.station + ' · ' + e.symptom);
  }
  function val(id){ var el = document.getElementById(id); return el ? String(el.value || '').trim() : ''; }
  function clearOpenForm(){ ['ta-line','ta-station','ta-equipment','ta-symptom'].forEach(function(id){ var el=document.getElementById(id); if(el) el.value=''; }); }
  function updateEvent(id, patch, action){
    var user = getUser() || 'User';
    events = events.map(function(e){
      if (e.id !== id) return e;
      var next = Object.assign({}, e, patch || {});
      next.history = Array.isArray(e.history) ? e.history.slice() : [];
      next.history.push({ at: nowIso(), by: user, action: action || 'UPDATED' });
      return next;
    });
    save();
    render();
  }
  function acceptEvent(id){
    var user = getUser();
    if (!user) {
      user = prompt('Nombre del técnico que acepta el evento:') || '';
      if (!user.trim()) return;
      setUser(user);
    }
    var row = events.find(function(e){ return e.id === id; });
    if (!row) return;
    if (row.assigned_to && row.assigned_to !== user && row.status !== 'OPEN') {
      alert('Este evento ya fue tomado por: ' + row.assigned_to);
      return;
    }
    updateEvent(id, { status:'ASSIGNED', assigned_to:user, accepted_at: row.accepted_at || nowIso() }, 'ACCEPTED');
  }
  function startEvent(id){ updateEvent(id, { status:'IN_PROGRESS', started_at: nowIso() }, 'STARTED'); }
  function escalateEvent(id){ updateEvent(id, { status:'ESCALATED' }, 'ESCALATED'); }
  function closeEvent(id){
    var finding = prompt('Finding técnico / causa encontrada:') || '';
    var action = prompt('Acción realizada:') || '';
    var parts = prompt('Refacción usada / ajuste realizado:', '') || '';
    var row = events.find(function(e){ return e.id === id; }) || {};
    var downtime = prompt('Downtime total en minutos:', row.downtime_min || '') || row.downtime_min || '';
    updateEvent(id, { status:'DONE', finding:finding, action:action, parts:parts, downtime_min:downtime, closed_at: nowIso() }, 'DONE');
  }
  function cancelEvent(id){ if (confirm('Cancelar este Andon?')) updateEvent(id, { status:'CANCELLED', closed_at: nowIso() }, 'CANCELLED'); }
  function exportCsv(){
    var headers = ['id','status','priority','line','station','equipment','issue_type','symptom','created_by','created_at','assigned_to','accepted_at','started_at','closed_at','finding','action','parts','downtime_min','response_min','mttr_min'];
    var rows = events.map(function(e){
      var o = Object.assign({}, e);
      o.response_min = e.accepted_at ? minsBetween(e.created_at, e.accepted_at) : '';
      o.mttr_min = e.closed_at ? minsBetween(e.created_at, e.closed_at) : '';
      return o;
    });
    var csv = [headers.join(',')].concat(rows.map(function(r){
      return headers.map(function(h){ return '"' + String(r[h] == null ? '' : r[h]).replace(/"/g,'""') + '"'; }).join(',');
    })).join('\n');
    var blob = new Blob([csv], { type:'text/csv;charset=utf-8' });
    var a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = 'traceops_maintenance_andon_' + dateOnly(nowIso()) + '.csv';
    document.body.appendChild(a); a.click();
    setTimeout(function(){ URL.revokeObjectURL(a.href); a.remove(); }, 500);
  }
  function render(){
    var root = document.getElementById('traceops-maintenance-andon-root');
    if (!root) return;
    var user = getUser();
    var k = kpis();
    var rows = filteredRows();
    var lineOpts = uniq('line').map(function(x){ return '<option value="'+esc(x)+'">'+esc(x)+'</option>'; }).join('');
    root.innerHTML = ''+
      '<section class="ta-card">'+
        '<div class="ta-head">'+
          '<div><div class="ta-eyebrow">Maintenance Andon</div><h3>Live maintenance response board</h3><p>Open event → technician accepts → registers issue → closes with traceability.</p></div>'+
          '<div class="ta-user"><label>Current user</label><input id="ta-user" value="'+esc(user)+'" placeholder="Technician / Production"/><button id="ta-save-user">Save</button><button id="ta-notify">Enable alerts</button></div>'+
        '</div>'+
        '<div class="ta-kpis">'+
          metric('Open', k.open, 'Waiting maintenance')+metric('In work', k.progress, 'Assigned / progress')+metric('Done today', k.doneToday, 'Closed today')+metric('Avg response', k.avgResponse+'m', 'Open → accept')+
        '</div>'+
        '<div class="ta-open">'+
          '<div class="ta-open-grid">'+
            input('ta-line','Line','SMT L18')+input('ta-station','Station / equipment','P21SIAH2 / Printer / AOI')+select('ta-issue-type','Issue type',['Mechanical','Electrical','Pneumatic','Software','Feeder','Printer','AOI','Calibration','Other'])+select('ta-priority','Priority',['Critical','High','Medium','Low'])+
            '<div class="ta-field ta-span"><label>Symptom observed by production</label><input id="ta-symptom" placeholder="Machine alarm, no read, feeder issue, repeated stop..."/></div>'+
          '</div>'+
          '<button id="ta-open-btn" class="ta-primary">Open Andon Event</button>'+
        '</div>'+
        '<div class="ta-toolbar">'+
          '<select id="ta-filter-status"><option value="ACTIVE">Active</option><option value="ALL">All</option><option value="OPEN">Open</option><option value="ASSIGNED">Assigned</option><option value="IN_PROGRESS">In progress</option><option value="DONE">Done</option><option value="ESCALATED">Escalated</option></select>'+
          '<select id="ta-filter-line"><option value="ALL">All lines</option>'+lineOpts+'</select>'+
          '<select id="ta-filter-priority"><option value="ALL">All priorities</option><option>Critical</option><option>High</option><option>Medium</option><option>Low</option></select>'+
          '<button id="ta-export">Export CSV</button>'+
        '</div>'+
        '<div class="ta-table-wrap"><table class="ta-table"><thead><tr><th>Event</th><th>Status</th><th>Line / Station</th><th>Symptom</th><th>Owner</th><th>Timing</th><th>Actions</th></tr></thead><tbody>'+
          (rows.length ? rows.map(rowHtml).join('') : '<tr><td colspan="7" class="ta-empty">No Andon events for selected filter.</td></tr>')+
        '</tbody></table></div>'+
      '</section>';
    bind();
  }
  function metric(title, value, sub){ return '<div class="ta-metric"><div>'+esc(value)+'</div><span>'+esc(title)+'</span><small>'+esc(sub)+'</small></div>'; }
  function input(id,label,ph){ return '<div class="ta-field"><label>'+esc(label)+'</label><input id="'+id+'" placeholder="'+esc(ph)+'"/></div>'; }
  function select(id,label,opts){ return '<div class="ta-field"><label>'+esc(label)+'</label><select id="'+id+'">'+opts.map(function(o){ return '<option>'+esc(o)+'</option>'; }).join('')+'</select></div>'; }
  function rowHtml(e){
    var age = minsBetween(e.created_at, e.closed_at || nowIso());
    var response = e.accepted_at ? minsBetween(e.created_at, e.accepted_at)+'m resp.' : 'Pending accept';
    var mttr = e.closed_at ? minsBetween(e.created_at, e.closed_at)+'m total' : age+'m open';
    return '<tr data-id="'+esc(e.id)+'">'+
      '<td><b>'+esc(e.id)+'</b><br><small>'+esc(dateOnly(e.created_at))+' '+esc(timeOnly(e.created_at))+'</small></td>'+
      '<td><span class="ta-status ta-'+esc(String(e.status||'OPEN').toLowerCase())+'">'+esc(statusLabel(e.status))+'</span><br><span class="ta-priority" style="background:'+priorityColor(e.priority)+'">'+esc(e.priority)+'</span></td>'+
      '<td><b>'+esc(e.line || 'N/D')+'</b><br><small>'+esc(e.station || e.equipment || 'N/D')+'</small></td>'+
      '<td>'+esc(e.symptom || '')+'<br><small>'+esc(e.issue_type || '')+'</small></td>'+
      '<td>'+esc(e.assigned_to || 'Unassigned')+'<br><small>'+esc(e.created_by || '')+'</small></td>'+
      '<td><b>'+esc(response)+'</b><br><small>'+esc(mttr)+'</small></td>'+
      '<td class="ta-actions">'+
        '<button data-action="accept">Accept</button><button data-action="start">Start</button><button data-action="done">Done</button><button data-action="escalate">Escalate</button><button data-action="cancel">Cancel</button>'+
      '</td></tr>';
  }
  function bind(){
    var user = document.getElementById('ta-user');
    var saveUser = document.getElementById('ta-save-user');
    if (saveUser) saveUser.onclick = function(){ setUser(user ? user.value : ''); render(); };
    var notifyBtn = document.getElementById('ta-notify');
    if (notifyBtn) notifyBtn.onclick = requestNotifyPermission;
    var openBtn = document.getElementById('ta-open-btn');
    if (openBtn) openBtn.onclick = seedFromForm;
    var exp = document.getElementById('ta-export');
    if (exp) exp.onclick = exportCsv;
    [['ta-filter-status','status'],['ta-filter-line','line'],['ta-filter-priority','priority']].forEach(function(pair){
      var el = document.getElementById(pair[0]);
      if (el) { el.value = filters[pair[1]]; el.onchange = function(){ filters[pair[1]] = el.value; render(); }; }
    });
    Array.prototype.forEach.call(document.querySelectorAll('.ta-table tr[data-id] button'), function(btn){
      btn.onclick = function(){
        var tr = btn.closest('tr'); var id = tr ? tr.getAttribute('data-id') : '';
        var a = btn.getAttribute('data-action');
        if (a === 'accept') acceptEvent(id);
        else if (a === 'start') startEvent(id);
        else if (a === 'done') closeEvent(id);
        else if (a === 'escalate') escalateEvent(id);
        else if (a === 'cancel') cancelEvent(id);
      };
    });
  }
  function injectStyles(){
    if (document.getElementById('traceops-andon-styles')) return;
    var st = document.createElement('style');
    st.id = 'traceops-andon-styles';
    st.textContent = ''+
      '#traceops-maintenance-andon-root{font-family:Inter,-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif;margin:0 0 14px}'+
      '.ta-card{background:#fff;border:1px solid #D9E6F7;border-radius:20px;box-shadow:0 10px 28px rgba(20,32,51,.06);overflow:hidden;margin-bottom:14px}'+
      '.ta-head{display:flex;justify-content:space-between;gap:16px;align-items:flex-start;padding:16px 18px;background:linear-gradient(135deg,#102A43,#1F3A5F);color:#fff;flex-wrap:wrap}.ta-head h3{font-size:18px;margin:2px 0 4px}.ta-head p{font-size:12px;color:rgba(255,255,255,.72);margin:0}.ta-eyebrow{font-size:9px;font-weight:900;letter-spacing:.16em;text-transform:uppercase;color:#7FB3F4}'+
      '.ta-user{display:flex;gap:6px;align-items:end;flex-wrap:wrap}.ta-user label{font-size:9px;font-weight:800;text-transform:uppercase;color:rgba(255,255,255,.62);width:100%}.ta-user input{height:34px;border-radius:10px;border:1px solid rgba(255,255,255,.22);background:rgba(255,255,255,.08);color:#fff;padding:0 10px;font-size:12px}.ta-user input::placeholder{color:rgba(255,255,255,.45)}.ta-user button,.ta-toolbar button{height:34px;border-radius:10px;border:1px solid #C7DBF7;background:#fff;color:#1F3A5F;font-size:11px;font-weight:800;padding:0 10px;cursor:pointer}'+
      '.ta-kpis{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px;padding:14px 16px;background:#F8F7F5;border-bottom:1px solid #EEECEA}.ta-metric{background:#fff;border:1px solid #E5E2DC;border-radius:14px;padding:12px}.ta-metric div{font-size:24px;font-weight:900;color:#1F3A5F}.ta-metric span{display:block;font-size:11px;font-weight:800;color:#1A1714}.ta-metric small{font-size:10px;color:#8A8580}'+
      '.ta-open{padding:14px 16px;border-bottom:1px solid #EEECEA}.ta-open-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px;margin-bottom:10px}.ta-field label{display:block;font-size:9px;font-weight:900;text-transform:uppercase;color:#6A6560;margin-bottom:4px}.ta-field input,.ta-field select,.ta-toolbar select{width:100%;height:36px;border:1px solid #D7D3CC;border-radius:10px;padding:0 10px;font-size:12px;background:#fff;color:#1A1714}.ta-span{grid-column:span 4}.ta-primary{height:38px;border:0;border-radius:12px;background:#1F3A5F;color:#fff;font-size:12px;font-weight:900;padding:0 16px;cursor:pointer}'+
      '.ta-toolbar{display:flex;gap:8px;align-items:center;flex-wrap:wrap;padding:12px 16px;background:#fff;border-bottom:1px solid #EEECEA}.ta-toolbar select{width:auto;min-width:140px}'+
      '.ta-table-wrap{overflow:auto}.ta-table{width:100%;border-collapse:collapse;font-size:11.5px}.ta-table th{background:#F8F7F5;color:#6A6560;text-align:left;font-size:9px;text-transform:uppercase;letter-spacing:.06em;padding:9px 10px;border-bottom:1px solid #E5E2DC}.ta-table td{padding:10px;border-bottom:1px solid #EEECEA;vertical-align:top;color:#3D3A36}.ta-table small{font-size:9.5px;color:#8A8580}.ta-status{display:inline-block;border-radius:999px;padding:3px 8px;font-size:9px;font-weight:900;background:#EAF2FF;color:#1F3A5F}.ta-open{color:inherit}.ta-status.ta-open{background:#FDF0EE;color:#922B21}.ta-status.ta-assigned,.ta-status.ta-in_progress{background:#FEF6E0;color:#8A5C10}.ta-status.ta-done{background:#EEF6FF;color:#145A28}.ta-status.ta-escalated{background:#F2ECFB;color:#521DA8}.ta-priority{display:inline-block;color:#fff;border-radius:999px;font-size:8.5px;font-weight:900;padding:2px 7px;margin-top:4px}.ta-actions{white-space:nowrap}.ta-actions button{border:1px solid #D7D3CC;background:#fff;border-radius:9px;margin:0 3px 4px 0;padding:5px 8px;font-size:10px;font-weight:800;color:#1F3A5F;cursor:pointer}.ta-empty{text-align:center;color:#8A8580;padding:24px!important}'+
      '@media(max-width:760px){.ta-kpis{grid-template-columns:repeat(2,minmax(0,1fr))}.ta-open-grid{grid-template-columns:1fr}.ta-span{grid-column:auto}.ta-head{display:block}.ta-user{margin-top:12px}.ta-toolbar select{width:100%}.ta-actions{white-space:normal}}';
    document.head.appendChild(st);
  }
  function mount(){
    if (mounted) return;
    var host = document.getElementById('maintenance-section') || document.getElementById('module-workspace') || document.getElementById('root');
    if (!host) return;
    injectStyles();
    var root = document.createElement('div');
    root.id = 'traceops-maintenance-andon-root';
    if (host.id === 'maintenance-section') host.insertBefore(root, host.firstChild);
    else host.appendChild(root);
    mounted = true;
    load();
    render();
  }
  function tryMount(){
    if (mounted) return;
    if (document.getElementById('maintenance-section')) mount();
  }
  function init(){
    load();
    tryMount();
    var obs = new MutationObserver(tryMount);
    try { obs.observe(document.body, { childList:true, subtree:true }); } catch(_) {}
    try {
      if (window.BroadcastChannel) {
        var bc = new BroadcastChannel(CHANNEL);
        bc.onmessage = function(ev){
          if (ev && ev.data && ev.data.type === 'andon-sync') { load(); render(); }
        };
      }
    } catch(_) {}
    window.TraceOpsMaintenanceAndon = { mount: mount, render: render, load: load, exportCsv: exportCsv };
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
