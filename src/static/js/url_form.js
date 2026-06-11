
document.getElementById('urlForm').addEventListener('submit', function(event) {
    event.preventDefault();

    // Показываем анимацию загрузки
    const loader = document.getElementById('loader');
    loader.style.display = 'block';

    const baseUrl = document.getElementById('base_url').value;
    const swaggerUrl = document.getElementById('swagger_url').value;

    fetch('/set_urls', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ base_url: baseUrl, swagger_url: swaggerUrl }),
    })
    .then(response => response.json())
    .then(data => {
        // Скрываем анимацию загрузки
        loader.style.display = 'none';

        // Показываем кастомное уведомление
        const notification = document.getElementById('notification');
        notification.textContent = data.message;
        notification.style.display = 'block';

        // Скрываем уведомление через 3 секунды
        setTimeout(() => {
            notification.style.display = 'none';
        }, 1000);

        // Перезагружаем страницу через 3 секунды
        setTimeout(() => {
            window.location.reload();
        }, 1000);
    })
    .catch(error => {
        console.error('Error:', error);
        loader.style.display = 'none';

        // Показываем ошибку в уведомлении
        const notification = document.getElementById('notification');
        notification.textContent = 'Ошибка при сохранении данных';
        notification.style.display = 'block';

        setTimeout(() => {
            notification.style.display = 'none';
        }, 1000);
    });
});
