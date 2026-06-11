document.getElementById('urlForm').addEventListener('submit', async (e) => {
  e.preventDefault();
  const loader = document.getElementById('loader');
  loader.style.display = 'block';

  try {
    const r = await fetch('/set_urls', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        base_url: document.getElementById('base_url').value,
        swagger_url: document.getElementById('swagger_url').value,
      }),
    });
    const d = await r.json();
    notify(d.message, 'ok');
    setTimeout(() => location.reload(), 1000);
  } catch {
    notify('Ошибка при сохранении', 'bad');
  } finally {
    loader.style.display = 'none';
  }
});

function notify(msg, type) {
  const el = document.getElementById('notify');
  if (!el) return;
  el.textContent = msg;
  el.className = 'notify' + (type ? ' notify--' + type : '');
  el.style.display = 'block';
  clearTimeout(el._t);
  el._t = setTimeout(() => { el.style.display = 'none'; }, 3000);
}
