# WB-Tech Store API

REST API интернет-магазина на Django 6 / Python 3.14 с JWT-авторизацией.

Проект упакован в Docker Compose с PostgreSQL и покрыт интеграционными тестами на `pytest`.

---

## Функционал

- **Пользователи**: регистрация, JWT-авторизация, профиль, пополнение баланса.
- **Товары**: просмотр доступен всем, CRUD доступен только администраторам.
- **Корзина**: просмотр корзины; добавление, удаление, изменение количества товаров.
- **Заказы**: оформление закза со списанием баланса пользователя и остатков на складе.
- **Документация Swagger**: доступна по адресу `/api/docs/`.

---

## Технологический стек

- **Язык и среда:** Python 3.14+, `uv`
- **Бэкенд:** Django 5, Django REST Framework
- **Аутентификация:** JWT
- **База данных:** PostgreSQL 16
- **Документация:** OpenAPI / Swagger UI (`drf-spectacular`)
- **Статика:** WhiteNoise
- **Контейнеризация:** Docker, Docker Compose
- **Тестирование:** `pytest`, `pytest-django`

---

## Ключевые архитектурные решения

1. **Декомпозиция бизнес-логики:** views / services / serializers / models и т.д.
2. **Защита от состояния гонки при списании товаров и денег:** Оформление заказа выполняется в транзакции с блокировкой строк (`select_for_update()`)..
3. **Централизованная обработка ошибок и трейсинг:** Кастомные исключения перехватываются глобальным обработчиком `custom_exception_handler`, возвращая предсказуемый JSON:

   ```json
   {
     "error": true,
     "error_id": "...",
     "timestamp": "...",
     "path": "...",
     "method": "...",
     "error_type": "...",
     "message": "...",
     "code": "..."
   }
   ```

---

## Как запустить проект

### 1. Подготовка окружения

Склонируйте репозиторий и создайте локальный конфигурационный файл:

```bash
cp .env.example .env
```

### 2. Сборка и запуск контейнеров

```bash
docker compose up -d --build
```

### 3. Создание администратора

Создайте суперпользователя для доступа к админ-панели и управления каталогом товаров:

```bash
docker compose exec web python manage.py createsuperuser
```

---

## Документация API и панель управления

- **Интерактивная документация Swagger UI:** [http://127.0.0.1:8000/api/docs/](http://127.0.0.1:8000/api/docs/)
- **Схема OpenAPI (JSON):** [http://127.0.0.1:8000/api/schema/](http://127.0.0.1:8000/api/schema/)
- **Админ-панель Django:** [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)

---

## Запуск тестов

### Локальный запуск на хосте (через `uv`):

```bash
uv run pytest
```

---

## Основные зависимости

### [django rest framework](https://www.django-rest-framework.org/)

### [django debug toolbar](https://django-debug-toolbar.readthedocs.io/en/latest/)

### [django-filter](https://django-filter.readthedocs.io/en/stable/)

### [drf-nested-routers](https://github.com/alanjds/drf-nested-routers)

### [drf-spectacular](https://drf-spectacular.readthedocs.io/en/latest/readme.html)

### [django-stubs](https://github.com/typeddjango/django-stubs) для аннотаций типов джанги

### [serializer mixin for viewset](https://stackoverflow.com/questions/75641706/django-rest-framework-nested-serializer-on-reads-only-not-nested-on-writes/75662820#75662820)
