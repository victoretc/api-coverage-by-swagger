
document.getElementById('urlForm').addEventListener('submit', function(event) {
    event.preventDefault();

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
    .then(response => {
        if (!response.ok) {
            throw new Error('Ошибка при сохранении данных');
        }
        return response.json();
    })
    .then(data => {
        loader.style.display = 'none';

        const notification = document.getElementById('notification');
        notification.textContent = data.message;
        notification.style.display = 'block';

        setTimeout(() => {
            window.location.reload();
        }, 1500);
    })
    .catch(error => {
        console.error('Error:', error);
        loader.style.display = 'none';

        const notification = document.getElementById('notification');
        notification.textContent = 'Ошибка при сохранении данных';
        notification.style.display = 'block';

        setTimeout(() => {
            notification.style.display = 'none';
        }, 3000);
    });
});
