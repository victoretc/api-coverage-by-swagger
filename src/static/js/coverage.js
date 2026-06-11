function filterEndpoints(tag) {
  let anyVisible = false;

  document.querySelectorAll('.filter-btn').forEach(b => {
    b.classList.toggle('filter-btn--on', b.dataset.filter === tag);
  });

  document.querySelectorAll('.tag-group').forEach(g => {
    let groupVisible = false;
    g.querySelectorAll('.endpoint').forEach(ep => {
      const covered = ep.dataset.covered === 'true';
      const show = tag === 'all' || (tag === 'covered' ? covered : ep.dataset.tag === tag);
      ep.style.display = show ? 'grid' : 'none';
      if (show) groupVisible = true;
    });
    g.style.display = groupVisible ? 'block' : 'none';
    if (groupVisible) anyVisible = true;
  });

  document.getElementById('noResults').style.display = anyVisible ? 'none' : 'block';
}

async function clearCoverage() {
  try {
    const r = await fetch('/clear_coverage', { method: 'POST' });
    const d = await r.json();
    notify(d.message, 'info');
    setTimeout(() => location.reload(), 1000);
  } catch {
    notify('Ошибка при очистке', 'bad');
  }
}

async function refreshCoverage() {
  try {
    const r = await fetch('/refresh_spec', { method: 'POST' });
    if (r.ok) {
      notify('Спецификация обновлена', 'ok');
      setTimeout(() => location.reload(), 1500);
    } else {
      const e = await r.json();
      notify(e.detail || 'Ошибка обновления', 'bad');
    }
  } catch (err) {
    notify('Ошибка сети: ' + err.message, 'bad');
  }
}

function notify(msg, type) {
  const el = document.getElementById('notify');
  const span = document.getElementById('notifyMsg');
  if (!el) return;
  span.textContent = msg;
  el.className = 'notify' + (type ? ' notify--' + type : '');
  el.style.display = 'block';
  clearTimeout(el._t);
  el._t = setTimeout(() => { el.style.display = 'none'; }, 3000);
}

document.addEventListener('DOMContentLoaded', () => {
  const bar = document.getElementById('progressFill');
  if (bar) {
    const pct = parseFloat(bar.style.width) || 0;
    if (pct >= 80) bar.style.background = '#10B981';
    else if (pct >= 50) bar.style.background = '#F59E0B';
    else bar.style.background = '#EF4444';
  }
});
