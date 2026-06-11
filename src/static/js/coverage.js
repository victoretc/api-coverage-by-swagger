function filterEndpoints(tag) {
    const tagGroups = document.querySelectorAll('.tag-group');
    const endpoints = document.querySelectorAll('.endpoint');
    const noResultsMessage = document.getElementById('no-results-message');
    let hasVisibleResults = false;

    tagGroups.forEach(group => {
        const groupTag = group.getAttribute('data-tag');
        const groupEndpoints = group.querySelectorAll('.endpoint');
        let groupHasVisibleEndpoints = false;

        groupEndpoints.forEach(endpoint => {
            const isCovered = endpoint.getAttribute('data-covered') === 'true';
            const endpointTag = endpoint.getAttribute('data-tag');

            if (tag === 'all') {
                endpoint.style.display = 'grid';
                groupHasVisibleEndpoints = true;
            } else if (tag === 'covered') {
                if (isCovered) {
                    endpoint.style.display = 'grid';
                    groupHasVisibleEndpoints = true;
                } else {
                    endpoint.style.display = 'none';
                }
            } else {
                if (endpointTag === tag) {
                    endpoint.style.display = 'grid';
                    groupHasVisibleEndpoints = true;
                } else {
                    endpoint.style.display = 'none';
                }
            }
        });

        if (groupHasVisibleEndpoints) {
            group.style.display = 'block';
            hasVisibleResults = true;
        } else {
            group.style.display = 'none';
        }
    });

    if (hasVisibleResults) {
        noResultsMessage.style.display = 'none';
    } else {
        noResultsMessage.style.display = 'block';
    }
}

function clearCoverage() {
    fetch('/clear_coverage', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        showNotification(data.message);
        setTimeout(() => {
            location.reload();
        }, 1000);
    })
    .catch(error => {
        console.error('Ошибка:', error);
        showNotification('Произошла ошибка при очистке покрытия.');
    });
}

function showNotification(message) {
    const notification = document.getElementById('notification');
    const notificationMessage = document.getElementById('notification-message');
    notificationMessage.textContent = message;
    notification.style.display = 'block';
    setTimeout(() => {
        notification.style.display = 'none';
    }, 2000);
}


async function refreshCoverage() {
    try {
        const response = await fetch('/refresh_spec', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        });

        if (response.ok) {
            showNotification('Спецификация успешно обновлена', 'success');
            setTimeout(() => location.reload(), 1500);
        } else {
            const error = await response.json();
            showNotification(error.detail || 'Ошибка при обновлении', 'error');
        }
    } catch (error) {
        showNotification('Ошибка сети: ' + error.message, 'error');
    }
}
