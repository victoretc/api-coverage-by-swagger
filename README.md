# Понимайте на какие эндпоинты при тестировании вы уже обратили внимание, а на какие нет.

## Запуск

1. Ставим poetry: <https://python-poetry.org/docs/>
2. ```task install-deps``` или ```poetry install```
3. ```task run``` или ```cd src && poetry run uvicorn main:app --port 8000```
4. Открываем <http://127.0.0.1:8000> для интеграции через веб интерфейс и <http://127.0.0.1:8000/docs> для интеграции через апи. 