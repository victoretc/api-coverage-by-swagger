# Architecture Review: api-coverage-by-swagger

## 1. Проблемы организации кода

### 🔴 Глобальный синглтон `CoverageService` (`src/main.py:16`)

```python
coverage_service = CoverageService()
```

Сервис создаётся на уровне модуля и мутирует внутри хендлеров. Это убивает тестируемость — нельзя подменить real-объект, нельзя создать изолированный инстанс под каждый тест. При запуске с несколькими воркерами (gunicorn + uvicorn) каждый процесс получит свой синглтон, состояние рассинхронизируется.

### 🔴 `main.py` делает всё сразу

Файл занимается:
- созданием и настройкой FastAPI-приложения (строки 11–14)
- определением Pydantic-схемы (строка 19)
- маршрутами (строки 24–76)
- middleware (строки 40–49)
- созданием HTTP-клиента и монтированием прокси (строки 34–35)
- работой с шаблонами (строки 13, 69–77)
- управлением глобальным состоянием (строка 16)

Нарушение **Single Responsibility Principle**. При добавлении фич файл будет только расти.

### 🔴 Монтирование прокси на `/set_urls` (строки 34–35)

```python
client = httpx.AsyncClient(timeout=10)
app.mount("/proxy", reverse_http_app(base_url=data.base_url, client=client))
```

Прокси монтируется **в рантайме в хендлере**. Если вызвать `/set_urls` дважды — `app.mount("/proxy", ...)` упадёт с ошибкой (путь уже занят). Клиент `httpx.AsyncClient` создаётся без cleanup — никогда не закрывается, утечка соединений.

### 🔴 `_current_swagger_url` — приватный атрибут, но используется снаружи (строка 60)

```python
coverage_service.initialize(coverage_service._current_swagger_url)
```

Если атрибут приватный, к нему не должно быть доступа извне. Это нарушение инкапсуляции и сигнал, что API плохо спроектирован.

### 🔴 Синхронный HTTP в асинхронном приложении (`src/core/loader.py:5`)

```python
response = httpx.get(swagger_url)
```

`httpx.get()` — синхронный вызов. Блокирует event loop FastAPI на время загрузки спецификации. При медленном ответе swagger-сервера упадет пропускная способность всего приложения.

### 🔴 Тестовые зависимости в main-секции (`pyproject.toml:15-18`)

`pytest`, `allure-pytest`, `faker` находятся в `[tool.poetry.dependencies]`, а не в `[tool.poetry.group.dev.dependencies]`. Они будут устанавливаться в production-окружение.

---

## 2. Проблемы качества кода

### 🟡 Перекомпиляция regex на каждый запрос (`src/core/utils.py:5`)

```python
def swagger_path_to_regex(path: str) -> re.Pattern:
    ...
    return re.compile("^/" + "/".join(regex_parts) + "$")
```

В `match_endpoint` (строка 27) regex перекомпилируется для **каждого эндпоинта из спецификации** на **каждый входящий запрос**. Для спецификации с 100 эндпоинтами — 100 компиляций regex на запрос. Нет кэширования.

### 🟡 Хрупкое удаление `/proxy` из пути (`src/core/utils.py:24`)

```python
parsed_path = parsed_url.path.replace("/proxy", "").split("?")[0]
```

`str.replace()` удалит **все вхождения** `/proxy` в пути. Если путь будет `/proxy/api/proxy/endpoint`, результат будет `//api//endpoint`.

### 🟡 Голый `dict` для эндпоинтов

Эндпоинты передаются как `dict[str, str]` с ключами `"method"` и `"path"` — магические строки, размазанные по парсеру, сервису, утилитам и шаблону. Нет единого типа — компилятор не поймает опечатку в `"metod"`.

### 🟡 Нет обработки ошибок в `load_spec`

```python
def load_spec(swagger_url: str) -> dict:
    response = httpx.get(swagger_url)
    response.raise_for_status()
    return response.json()
```

Любая ошибка (сеть, DNS, таймаут, не-JSON ответ, 4xx/5xx) вызовет необработанное исключение → FastAPI вернёт 500. `CoverageService.initialize()` вызывает `load_spec` без `try/except`.

### 🟡 `match_endpoint` не отличает `/proxy/*` от остальных путей

Middleware (строка 40–49) перехватывает **все** запросы — и к прокси, и к статике, и к API самого приложения. При совпадении он отметит эндпоинт как покрытый. Запросы к `/static/css/style.css` будут проверяться на совпадение с путями из Swagger (не найдут совпадения, но лишняя работа).

В идеале middleware должен отслеживать только запросы, прошедшие через `/proxy`.

### 🟡 `get_endpoints_by_tags` и `get_endpoints` не обрабатывают OpenAPI 3.x

Функции предполагают структуру Swagger 2.0. OpenAPI 3.0 использует `requestBody` вместо `parameters` и другую структуру. Для `get_endpoints_by_tags` это менее критично, но `details.get("tags", ["default"])` подразумевает, что каждый метод — это dict с ключом `tags`.

### 🟡 `isinstance(details, dict)` стоит в `get_endpoints_by_tags`, но не в `get_endpoints`

В `get_endpoints` (строка 12–16) нет проверки `isinstance(details, dict)`. Если в `paths` попадёт `$ref` (OpenAPI 3), метод упадёт с `AttributeError`.

### 🟡 `_covered_endpoints` хранит сырые Swagger-пути

Покрытие хранится как `(method: str, swagger_path: str)`. Это работает, но сбивает с толку при отладке — разработчик видит в логах `/pet/{petId}` вместо `/pet/123`.

---

## 3. Как исправить / полный редизайн

### Предлагаемая архитектура

```
src/
├── main.py                    # FastAPI app, lifespan, wiring
├── _types.py                  # TypedDict / dataclass'ы
├── core/
│   ├── loader.py              # async загрузка spec
│   ├── parser.py              # парсинг spec → list[Endpoint]
│   └── matcher.py             # match запроса к Endpoint (с кэшем regex)
├── services/
│   └── coverage.py            # бизнес-логика, state
├── routers/
│   ├── setup.py               # POST /set_urls, POST /refresh_spec
│   ├── coverage.py            # POST /clear_coverage, GET /
│   └── __init__.py
├── static/
└── templates/
```

### Ключевые изменения

**A. Типизированная модель эндпоинта — замена `dict`**

```python
# _types.py или models.py
from dataclasses import dataclass

@dataclass(frozen=True)
class Endpoint:
    method: str
    path: str
```

Все модули работают с `Endpoint`, а не с `dict`. Это исключает опечатки в ключах, даёт IDE-автокомплит и делает код самодокументируемым.

**B. Dependency Injection вместо синглтона**

```python
# services/coverage.py
@dataclass
class CoverageService:
    state: CoverageState       # инкапсулированное хранилище

# main.py
@app.lifespan("async")
async def lifespan(app):
    state = CoverageState()
    yield {"coverage_service": CoverageService(state)}
```

Все хендлеры получают `CoverageService` через `Request.state.coverage_service`. В тестах создаём `CoverageService(CoverageState())` вручную.

**C. Прокси — через lifespan, а не в хендлере**

```python
# main.py
async_proxy: ASGIApp | None = None
proxy_client: httpx.AsyncClient | None = None

@app.post("/set_urls")
async def setup_coverage(data: CoverageSetup, request: Request):
    ...
    client = httpx.AsyncClient(base_url=data.base_url, timeout=10)
    proxy = reverse_http_app(base_url=data.base_url, client=client)
    request.app.state.proxy = proxy
    request.app.state.proxy_client = client
    # Не монтируем — используем sub-mount или dispatch
```

Либо использовать `lifespan` для предварительного конфигурирования, либо для простоты принимать `base_url` через переменные окружения.

**D. Кэширование regex**

```python
# core/matcher.py
from functools import lru_cache

@lru_cache(maxsize=None)
def swagger_path_to_regex(path: str) -> re.Pattern:
    ...
```

**E. Async loader с обработкой ошибок**

```python
# core/loader.py
async def load_spec(swagger_url: str, client: httpx.AsyncClient | None = None) -> dict | None:
    try:
        async with client or httpx.AsyncClient(timeout=10) as c:
            response = await c.get(swagger_url)
            response.raise_for_status()
            return response.json()
    except (httpx.HTTPStatusError, httpx.RequestError, json.JSONDecodeError):
        return None
```

**F. Чистый middleware**

```python
@app.middleware("http")
async def track_coverage(request: Request, call_next):
    response = await call_next(request)
    svc = request.state.coverage_service
    if svc.is_initialized and request.url.path.startswith("/proxy"):
        method = request.method
        path = request.url.path.removeprefix("/proxy")
        svc.mark_covered(method, path)
    return response
```

**G. Исправление `get_endpoints` — проверка на dict**

```python
def get_endpoints(spec: dict) -> list[Endpoint]:
    endpoints = []
    for path, methods in spec.get("paths", {}).items():
        for method, details in methods.items():
            if isinstance(details, dict):
                endpoints.append(Endpoint(method=method.upper(), path=path))
    return endpoints
```

### Что нужно сделать (приоритеты)

| Приоритет | Что делать |
|-----------|-----------|
| **High** | `Endpoint` dataclass вместо голого `dict` |
| **High** | DI вместо глобального `coverage_service` |
| **High** | Убрать монтирование прокси из хендлера |
| **High** | `load_spec` → async + обработка ошибок |
| **High** | `lru_cache` для regex |
| **Medium** | Поправить `str.replace("/proxy")` → `removeprefix` |
| **Medium** | Отфильтровать в middleware только `/proxy/*` |
| **Medium** | move `pytest`, `allure-pytest`, `faker` в dev |
| **Medium** | `_current_swagger_url` → публичное свойство |
| **Low** | Поддержка OpenAPI 3 |
| **Low** | Разделить `main.py` на роутеры (setup, report) |
