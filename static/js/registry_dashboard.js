// static/js/registry_dashboard.js
(function(){
  const D = window.REG_DATA || {};
  const NF = new Intl.NumberFormat('ru-RU');

  // KPI
  const setText = (id, v)=> { const el = document.getElementById(id); if (el) el.textContent = NF.format(v ?? 0); };
  setText('kpi-total',   D.kpi?.total);
  setText('kpi-issued',  D.kpi?.issued);
  setText('kpi-revoked', D.kpi?.revoked);

  // --- NEW: ранний выход, если ApexCharts не подключен ---
  if (typeof window.ApexCharts === 'undefined') {
    console.error('[Analytics] ApexCharts не загружен. Проверь блок vendor_js и путь к apexcharts.js');
    return;
  }

  const exists = (id)=> document.getElementById(id);
  const safeMount = (fn, name)=> { try { fn(); } catch (e) { console.error(`[Analytics] Ошибка в ${name}:`, e); } };

  const commonTooltip = { y: { formatter: (val)=> NF.format(val) } };

  const bar = (id, labels, data, opts={})=> exists(id) && new ApexCharts(document.querySelector('#'+id), {
    chart:{ type:'bar', height:320, toolbar:{show:false} },
    // NB: если у тебя очень старая версия ApexCharts и ругается на borderRadius — закомментируй строку ниже
    plotOptions:{ bar:{ horizontal: !!opts.horizontal, borderRadius: 6 } },
    series:[{ name:'Количество', data }],
    xaxis:{ categories: labels },
    dataLabels:{ enabled:false },
    tooltip: commonTooltip
  }).render();

  const pie = (id, labels, data, kind='pie')=> exists(id) && new ApexCharts(document.querySelector('#'+id), {
    chart:{ type: kind, height:320 },
    series: data, labels: labels,
    legend:{position:'bottom'},
    tooltip: commonTooltip,
    dataLabels:{ formatter: (_val, opt)=> NF.format(opt.w.config.series[opt.seriesIndex]) }
  }).render();

  const area = (id, labels, data)=> exists(id) && new ApexCharts(document.querySelector('#'+id), {
    chart:{ type:'area', height:320, toolbar:{show:false} },
    series:[{ name:'Выдано', data }],
    xaxis:{ categories: labels, type:'category' },
    dataLabels:{enabled:false},
    stroke:{curve:'smooth'},
    tooltip: commonTooltip
  }).render();

  // Helpers
  const toPairs = (arr, k, v)=> (arr||[]).map(o=> [o[k] ?? '—', o[v] ?? 0]);

  // Статусы
  safeMount(()=> {
    const s = (D.status||[]).map(o => [o.label || o.status || '—', o.c || 0]);
    bar('chartStatus', s.map(i=>i[0]), s.map(i=>i[1]));
  }, 'chartStatus');

  // Регионы рождения — горизонтальные бары
  safeMount(()=> {
    const r = toPairs(D.region, 'horse__place_of_birth__name', 'c');
    bar('chartRegion', r.map(i=>i[0]), r.map(i=>i[1]), { horizontal: true });
  }, 'chartRegion');

  // Породы — пончик
  safeMount(()=> {
    const b = toPairs(D.breed, 'horse__breed__name', 'c');
    pie('chartBreed', b.map(i=>i[0]), b.map(i=>i[1]), 'donut');
  }, 'chartBreed');

  // 30 дней — area
  safeMount(()=> {
    const d = (D.daily||[]).map(x=> [x.d, x.c]);
    area('chartDaily', d.map(i=>i[0]), d.map(i=>i[1]));
  }, 'chartDaily');

  // НОВОЕ: типы лошадей — пончик
  safeMount(()=> {
    const ht = toPairs(D.horse_type, 'label', 'c');
    pie('chartHorseType', ht.map(i=>i[0]), ht.map(i=>i[1]), 'donut');
  }, 'chartHorseType');

  // НОВОЕ: тип владельца — пончик (был контейнер, но не рисовали)
  safeMount(()=> {
    const ok = (D.owner_kind || []).map(x => [x.label || '—', x.value || 0]);
    pie('chartOwnerKind', ok.map(i=>i[0]), ok.map(i=>i[1]), 'donut');
  }, 'chartOwnerKind');

  // НОВОЕ: 12 месяцев — area
  safeMount(()=> {
    const m = (D.monthly||[]).map(x=> [x.m, x.c]);
    area('chartMonthly', m.map(i=>i[0]), m.map(i=>i[1]));
  }, 'chartMonthly');
})();
