function filterEndpoints(tag) {
    const tagGroups = document.querySelectorAll('.tag-group');
    const noResultsMessage = document.getElementById('no-results-message');
    let hasVisibleResults = false;

    tagGroups.forEach(function (group) {
        const groupEndpoints = group.querySelectorAll('.endpoint');
        let groupHasVisibleEndpoints = false;

        groupEndpoints.forEach(function (endpoint) {
            const isCovered = endpoint.getAttribute('data-covered') === 'true';
            const endpointTag = endpoint.getAttribute('data-tag');
            let visible = false;

            if (tag === 'all') {
                visible = true;
            } else if (tag === 'covered') {
                visible = isCovered;
            } else {
                visible = endpointTag === tag;
            }

            endpoint.style.display = visible ? 'grid' : 'none';

            if (visible) {
                groupHasVisibleEndpoints = true;
            }
        });

        group.style.display = groupHasVisibleEndpoints ? 'block' : 'none';

        if (groupHasVisibleEndpoints) {
            hasVisibleResults = true;
        }
    });

    noResultsMessage.style.display = hasVisibleResults ? 'none' : 'block';
}

function showNotification(message) {
    const notification = document.getElementById('notification');
    const notificationMessage = document.getElementById('notification-message');

    notificationMessage.textContent = message;
    notification.style.display = 'block';

    setTimeout(function () {
        notification.style.display = 'none';
    }, 2000);
}

function clearCoverage() {
    fetch('/clear_coverage', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
    })
        .then(function (response) {
            return response.json();
        })
        .then(function (data) {
            showNotification(data.message);

            setTimeout(function () {
                location.reload();
            }, 1000);
        })
        .catch(function (error) {
            console.error('Ошибка:', error);
            showNotification('Произошла ошибка при очистке покрытия.');
        });
}

async function refreshCoverage() {
    try {
        const response = await fetch('/refresh_spec', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
        });

        if (response.ok) {
            showNotification('Спецификация успешно обновлена');
            setTimeout(function () {
                location.reload();
            }, 1500);
        } else {
            const error = await response.json();
            showNotification(error.detail || 'Ошибка при обновлении');
        }
    } catch (error) {
        showNotification('Ошибка сети: ' + error.message);
    }
}
