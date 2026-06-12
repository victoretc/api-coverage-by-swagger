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

function pluralize(n, words) {
    n = Math.abs(n) % 100;
    var n1 = n % 10;
    if (n > 10 && n < 20) return words[2];
    if (n1 > 1 && n1 < 5) return words[1];
    if (n1 === 1) return words[0];
    return words[2];
}

function statusClass(code) {
    if (code < 300) return 'ok';
    if (code < 400) return 'redirect';
    return 'error';
}

function renderRecord(rec) {
    var detailHtml = '';
    if (rec.request_preview) {
        detailHtml += '<div class="history-detail-row"><span class="history-detail-label">Request</span><span class="history-detail-value">' + escapeHtml(rec.request_preview) + '</span></div>';
    }
    if (rec.response_preview) {
        detailHtml += '<div class="history-detail-row"><span class="history-detail-label">Response</span><span class="history-detail-value">' + escapeHtml(rec.response_preview) + '</span></div>';
    }
    if (rec.query_params) {
        detailHtml += '<div class="history-detail-row"><span class="history-detail-label">Params</span><span class="history-detail-value">' + escapeHtml(rec.query_params) + '</span></div>';
    }
    if (rec.content_type) {
        detailHtml += '<div class="history-detail-row"><span class="history-detail-label">Content-Type</span><span class="history-detail-value">' + escapeHtml(rec.content_type) + '</span></div>';
    }

    return '<div class="history-record">'
        + '<div class="history-record-top">'
        + '<span class="history-status ' + statusClass(rec.status_code) + '">' + rec.status_code + '</span>'
        + '<div class="history-meta">'
        + '<span class="history-timestamp">' + rec.timestamp + '</span>'
        + '<span class="history-duration">' + rec.duration_ms + ' ms</span>'
        + '</div>'
        + '</div>'
        + detailHtml
        + '</div>';
}

function escapeHtml(str) {
    if (!str) return '';
    var div = document.createElement('div');
    div.appendChild(document.createTextNode(str));
    return div.innerHTML;
}

function showEndpointHistory(method, path) {
    var modal = document.getElementById('history-modal');
    var title = document.getElementById('modal-title');
    var body = document.getElementById('modal-body');

    title.textContent = method + ' ' + path;
    body.innerHTML = '<div class="text-center" style="color:#888;padding:30px 0;">Загрузка...</div>';
    modal.style.display = 'flex';

    var params = new URLSearchParams({ method: method, path: path });
    fetch('/endpoint_history?' + params.toString())
        .then(function (r) { return r.json(); })
        .then(function (data) {
            if (!data || data.length === 0) {
                body.innerHTML = '<div class="history-empty">Запросов по этому эндпоинту не было</div>';
                return;
            }
            var word = pluralize(data.length, ['запрос', 'запроса', 'запросов']);
            var html = '<div class="history-count-line"><span class="history-count-badge">' + data.length + ' ' + word + '</span></div>';
            data.forEach(function (rec) {
                html += renderRecord(rec);
            });
            body.innerHTML = html;
        })
        .catch(function (err) {
            body.innerHTML = '<div class="history-empty">Ошибка загрузки: ' + escapeHtml(err.message) + '</div>';
        });
}

function closeHistoryModal(e) {
    if (e && e.target !== document.getElementById('history-modal')) return;
    document.getElementById('history-modal').style.display = 'none';
}

document.addEventListener('DOMContentLoaded', function () {
    document.getElementById('endpoints-container').addEventListener('click', function (e) {
        var endpoint = e.target.closest('.endpoint');
        if (endpoint) {
            var method = endpoint.getAttribute('data-method');
            var path = endpoint.getAttribute('data-path');
            showEndpointHistory(method, path);
        }
    });
});
