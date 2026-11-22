# Play Today App

![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-3.0-000000?style=for-the-badge&logo=flask&logoColor=white)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-D71F00?style=for-the-badge&logo=sqlalchemy&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-3-003B57?style=for-the-badge&logo=sqlite&logoColor=white)
![Bootstrap](https://img.shields.io/badge/Bootstrap-5.3-7952B3?style=for-the-badge&logo=bootstrap&logoColor=white)
![JWT](https://img.shields.io/badge/Auth-JWT-black?style=for-the-badge&logo=jsonwebtokens&logoColor=white)
![Dropbox](https://img.shields.io/badge/Storage-Dropbox-0061FF?style=for-the-badge&logo=dropbox&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

Play Today — сервис отзывов о настольных играх для антикафе «Host&Хвост».

Это веб-приложение на Flask, которое позволяет посетителям антикафе делиться впечатлениями об играх. Администратор может добавлять, редактировать и удалять игры, а гости — читать отзывы и смотреть рейтинг.

## Описание

**Play Today** — сервис, который позволяет:

- вести каталог настольных игр: добавлять, редактировать, скрывать из каталога;
- оставлять рейтинговые отзывы (оценка 1–10) с текстом и фотографиями;
- загружать фотографии коробок игр напрямую в Dropbox;
- видеть средний рейтинг и статистику по каждой игре;
- управлять пользователями: блокировать и разблокировать аккаунты;
- регистрироваться и аутентифицироваться через веб-интерфейс или JSON API (JWT).

### Основные сущности

| Сущность      | Описание                                                                                                         |
| ------------- | ---------------------------------------------------------------------------------------------------------------- |
| `User`        | Пользователь системы (логин, хеш пароля, флаг админа, статус активности)                                         |
| `Boardgame`   | Настольная игра (название, описание, `min_players`/`max_players`, `min_age`, `playtime_minutes`, `is_available`) |
| `Review`      | Отзыв (текст, рейтинг 1–10, привязка к пользователю и игре, массив ссылок на фото, timestamp)                    |

Связи: `User 1 — N Review`, `Boardgame 1 — N Review`.

### Бизнес-правила

**Пользователи**

- логин уникален (3–64 символа);
- пароль хранится в виде хеша (`werkzeug.security`);
- обычные пользователи могут читать отзывы, оставлять и редактировать свои;
- администратор (`is_admin = true`) может создавать, редактировать и удалять игры, а также блокировать/разблокировать пользователей;
- заблокированный пользователь (`is_active = false`) не может войти в систему;
- при удалении пользователя отзывы остаются в системе, но автор отображается как «Удаленный пользователь» (`user_id` обнуляется через `ondelete='SET NULL'`).

**Настольные игры**

- название уникально (1–128 символов);
- описание обязательно;
- `min_players` ≥ 1, `max_players` ≥ 1, `min_age` ≥ 0, `playtime_minutes` ≥ 1;
- обычные пользователи видят все игры в каталоге, но создавать и редактировать может только админ;
- при удалении игры все её отзывы удаляются автоматически (cascade).

**Отзывы**

- рейтинг строго от 1 до 10 (`CheckConstraint`);
- текст обязателен и не короче 10 символов;
- пользователь может редактировать и удалять только свои отзывы;
- администратор может редактировать и удалять любые отзывы;
- фотографии сохраняются в Dropbox, в базе хранятся публичные ссылки в формате JSON;
- допустимые расширения: `.jpg`, `.jpeg`, `.png`, `.gif`, `.bmp`.

## Возможности API

Все не-GET эндпоинты отключены от CSRF-защиты (`@csrf.exempt`) и работают с JSON.

### Аутентификация и пользователи

| Метод    | Путь                                 | Описание                                            | Доступ           |
| -------- | ------------------------------------ | --------------------------------------------------- | ---------------- |
| `POST`   | `/api/register/`                     | Регистрация нового пользователя, возвращает JWT     | Все              |
| `POST`   | `/api/login/`                        | Вход по username и паролю, возвращает JWT           | Все              |
| `PATCH`  | `/api/users/<id>/toggle-status/`     | Заблокировать/разблокировать пользователя           | Администратор    |
| `GET`    | `/api/users/`                        | Список всех пользователей                           | Администратор    |
| `GET`    | `/api/users/me/`                     | Данные текущего пользователя и его отзывы           | Авторизованный   |

Токен передаётся в заголовке `Authorization: Bearer <token>`. Время жизни токена — 1 час.

> **Важно:** через API нельзя забанить администратора — эндпоинт `/api/users/<id>/toggle-status/` вернёт `403 Forbidden` при попытке заблокировать пользователя с `is_admin = true`.

### Настольные игры

| Метод    | Путь                         | Описание                                | Доступ           |
| -------- | ---------------------------- | --------------------------------------- | ---------------- |
| `GET`    | `/api/boardgames/`           | Список всех игр                         | Все              |
| `GET`    | `/api/boardgames/<id>/`      | Информация об игре и её отзывы          | Все              |
| `PATCH`  | `/api/boardgames/<id>/`      | Частично обновить игру                  | Администратор    |
| `DELETE` | `/api/boardgames/<id>/`      | Удалить игру и все её отзывы            | Администратор    |

### Отзывы

| Метод    | Путь                      | Описание                          | Доступ           |
| -------- | ------------------------- | --------------------------------- | ---------------- |
| `POST`   | `/api/reviews/`           | Создать отзыв                     | Авторизованный   |
| `PATCH`  | `/api/reviews/<id>/`      | Частично обновить отзыв           | Автор или админ  |
| `DELETE` | `/api/reviews/<id>/`      | Удалить отзыв                     | Автор или админ  |

## Веб-интерфейс

### Основные страницы

| Путь                       | Описание                                        | Доступ           |
| -------------------------- | ----------------------------------------------- | ---------------- |
| `/`                        | Главная: случайная игра + отзывы                | Все              |
| `/register`                | Регистрация                                     | Гости            |
| `/login`                   | Вход                                            | Гости            |
| `/logout`                  | Выход                                           | Авторизованные   |
| `/boardgames/<id>`         | Страница конкретной игры с отзывами             | Все              |
| `/add_review`              | Форма добавления отзыва                         | Авторизованные   |
| `/edit_review/<id>`        | Редактирование отзыва                           | Автор или админ  |
| `/delete_review/<id>`      | Удаление отзыва (POST)                          | Автор или админ  |
| `/profile`                 | Профиль пользователя с историей отзывов         | Авторизованные   |

### Административные страницы

| Путь                                | Описание                        | Доступ        |
| ----------------------------------- | ------------------------------- | ------------- |
| `/add_boardgame`                    | Добавить новую игру             | Администратор |
| `/edit_boardgame/<id>`              | Редактирование игры             | Администратор |
| `/delete_boardgame/<id>`            | Удаление игры (POST)            | Администратор |
| `/admin/boardgames`                 | Управление каталогом игр        | Администратор |
| `/admin/users`                      | Управление пользователями       | Администратор |
| `/admin/toggle_user_status/<id>`    | Блокировка/разблокировка (POST) | Администратор |

> **Важно:** в веб-интерфейсе администратор не может заблокировать сам себя.

## Установка

### Требования

- Python 3.12
- pip

### 1. Клонирование и переменные окружения

```bash
git clone https://github.com/TAKOYAMItakoyami/play-today-app.git
cd play-today-app
```

Создайте файл `.env` из готового шаблона:

```bash
cp .env.example .env
```

В `.env.example` уже описаны все необходимые переменные:

```env
FLASK_APP=play_today_app
FLASK_DEBUG=1
DATABASE_URI=sqlite:///my_db.sqlite3
SECRET_KEY=very_secret_key

DROPBOX_APP_KEY=dropbox_app_key
DROPBOX_APP_SECRET=dropbox_app_secret
DROPBOX_REFRESH_TOKEN=dropbox_refresh_token

ADMIN_USERNAME=admin_username
ADMIN_PASSWORD=admin_password
```

| Переменная              | По умолчанию              | Назначение                                |
| ----------------------- | ------------------------- | ----------------------------------------- |
| `FLASK_APP`             | `play_today_app`          | Имя приложения Flask                      |
| `FLASK_DEBUG`           | `1`                       | Режим отладки                             |
| `DATABASE_URI`          | `sqlite:///my_db.sqlite3` | Строка подключения к БД                   |
| `SECRET_KEY`            | `very_secret_key`         | Секретный ключ для подписи сессий и JWT   |
| `DROPBOX_APP_KEY`       | —                         | OAuth 2.0 App Key Dropbox                 |
| `DROPBOX_APP_SECRET`    | —                         | OAuth 2.0 App Secret Dropbox              |
| `DROPBOX_REFRESH_TOKEN` | —                         | Refresh-токен для обновления access_token |
| `ADMIN_USERNAME`        | `admin`                   | Логин первого администратора              |
| `ADMIN_PASSWORD`        | `admin123`                | Пароль первого администратора             |

Файл `.env` в репозиторий не попадает (добавлен в `.gitignore`), поэтому
`cp .env.example .env` — обязательный шаг после клонирования.

### 2. Установка зависимостей

```bash
pip install -r requirements-dev.txt
```

### 3. Инициализация базы данных

```bash
flask db upgrade
```

Миграции управляются через Flask-Migrate (обёртка над Alembic).

### 4. Создание администратора

```bash
flask create_first_superuser
```

Скрипт создаёт первого суперпользователя из переменных `ADMIN_USERNAME` и
`ADMIN_PASSWORD` в файле `.env` (по умолчанию: `admin` / `admin123`). Если
администратор уже существует, команда выведет его логин и ничего не создаст.

### 5. (Опционально) Загрузка тестовых игр

```bash
flask load_boardgames boardgames.csv
```

Команда читает CSV-файл и добавляет игры, которых ещё нет в базе (проверка по
уникальному названию). Файл `boardgames.csv` уже включён в репозиторий.

### 6. Запуск

```bash
flask run --reload
```

Сервер доступен по адресу `http://127.0.0.1:5000`.

## Использование

### Примеры запросов

**Зарегистрироваться:**

```bash
curl -X POST http://127.0.0.1:5000/api/register/ \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "pass1234"}'
```

**Войти и получить JWT-токен:**

```bash
curl -X POST http://127.0.0.1:5000/api/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "pass1234"}'
```

**Получить список игр:**

```bash
curl http://127.0.0.1:5000/api/boardgames/
```

**Получить информацию об игре и отзывы:**

```bash
curl http://127.0.0.1:5000/api/boardgames/1/
```

**Обновить игру (нужен токен администратора):**

```bash
curl -X PATCH http://127.0.0.1:5000/api/boardgames/1/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <YOUR_JWT_TOKEN>" \
  -d '{"is_available": false}'
```

**Удалить игру (нужен токен администратора):**

```bash
curl -X DELETE http://127.0.0.1:5000/api/boardgames/1/ \
  -H "Authorization: Bearer <YOUR_JWT_TOKEN>"
```

**Создать отзыв (нужен токен авторизованного пользователя):**

```bash
curl -X POST http://127.0.0.1:5000/api/reviews/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <YOUR_JWT_TOKEN>" \
  -d '{
    "text": "Отличная игра, рекомендую!",
    "rating": 9,
    "boardgame_id": 1
  }'
```

**Обновить отзыв (автор или админ):**

```bash
curl -X PATCH http://127.0.0.1:5000/api/reviews/1/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <YOUR_JWT_TOKEN>" \
  -d '{"text": "Игра стала ещё лучше после патча!"}'
```

**Удалить отзыв (автор или админ):**

```bash
curl -X DELETE http://127.0.0.1:5000/api/reviews/1/ \
  -H "Authorization: Bearer <YOUR_JWT_TOKEN>"
```

**Забанить пользователя (нужен токен администратора):**

```bash
curl -X PATCH http://127.0.0.1:5000/api/users/2/toggle-status/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <YOUR_JWT_TOKEN>"
```

**Получить список пользователей (админ):**

```bash
curl http://127.0.0.1:5000/api/users/ \
  -H "Authorization: Bearer <YOUR_JWT_TOKEN>"
```

**Получить данные о себе и отзывы:**

```bash
curl http://127.0.0.1:5000/api/users/me/ \
  -H "Authorization: Bearer <YOUR_JWT_TOKEN>"
```

### Примеры ответов API

**Регистрация (`201 Created`):**

```json
{
  "message": "Пользователь успешно зарегистрирован",
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "id": 1,
    "username": "testuser"
  }
}
```

**Вход (`200 OK`):**

```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Список игр (`200 OK`):**

```json
{
  "boardgames": [
    {
      "id": 1,
      "name": "Каркассон",
      "description": "Классическая стратегия...",
      "min_players": 2,
      "max_players": 5,
      "min_age": 7,
      "playtime_minutes": 60,
      "is_available": true,
      "average_rating": 8.5
    }
  ]
}
```

**Информация об игре (`200 OK`):**

```json
{
  "boardgame": {
    "id": 1,
    "name": "Каркассон",
    "description": "Классическая стратегия...",
    "min_players": 2,
    "max_players": 5,
    "min_age": 7,
    "playtime_minutes": 60,
    "is_available": true,
    "average_rating": 8.5
  },
  "reviews": [
    {
      "id": 1,
      "text": "Игра замечательная!",
      "rating": 9,
      "author": "testuser",
      "timestamp": "2026-11-21T14:30:00+00:00",
      "boardgame_id": 1,
      "boardgame_name": "Каркассон"
    }
  ]
}
```

**Обновить игру (`200 OK`):**

```json
{
  "boardgame": {
    "id": 1,
    "name": "Каркассон",
    "description": "Классическая стратегия...",
    "min_players": 2,
    "max_players": 5,
    "min_age": 7,
    "playtime_minutes": 60,
    "is_available": false,
    "average_rating": 8.5
  }
}
```

**Создать отзыв (`201 Created`):**

```json
{
  "review": {
    "id": 1,
    "text": "Отличная игра, рекомендую!",
    "rating": 9,
    "author": "testuser",
    "timestamp": "2026-11-21T14:30:00+00:00",
    "boardgame_id": 1,
    "boardgame_name": "Каркассон"
  }
}
```

**Удалить игру/отзыв (`204 No Content`):** пустое тело ответа.

**Данные о себе (`200 OK`):**

```json
{
  "user": {
    "id": 1,
    "username": "testuser",
    "is_admin": false,
    "is_active": true
  },
  "reviews": [
    {
      "id": 1,
      "text": "Отличная игра, рекомендую!",
      "rating": 9,
      "author": "testuser",
      "timestamp": "2026-11-21T14:30:00+00:00",
      "boardgame_id": 1,
      "boardgame_name": "Каркассон"
    }
  ]
}
```

**Ошибка — дубликат логина (`400 Bad Request`):**

```json
{
  "message": "Пользователь с таким именем уже существует"
}
```

**Ошибка — неверный логин или пароль (`401 Unauthorized`):**

```json
{
  "message": "Неверный логин или пароль"
}
```

**Ошибка — заблокированный пользователь (`403 Forbidden`):**

```json
{
  "message": "Пользователь заблокирован"
}
```

**Ошибка — игра не найдена (`404 Not Found`):**

```json
{
  "message": "Игра с указанным id не найдена"
}
```

**Ошибка — нельзя редактировать чужой отзыв (`403 Forbidden`):**

```json
{
  "message": "Вы не можете редактировать чужой отзыв"
}
```

**Ошибка — нельзя забанить администратора (`403 Forbidden`):**

```json
{
  "message": "Нельзя забанить администратора"
}
```

**Ошибка — отсутствует JSON в запросе (`400 Bad Request`):**

```json
{
  "message": "В запросе отсутствует JSON тело"
}
```

**Ошибка — отсутствие обязательных полей (`400 Bad Request`):**

```json
{
  "message": "В запросе отсутствуют обязательные поля: text, rating, boardgame_id"
}
```

**Ошибка — игра не найдена по boardgame_id (`404 Not Found`):**

```json
{
  "message": "Игра с указанным boardgame_id не найдена"
}
```

**Ошибка — ошибка базы данных (`500 Internal Server Error`):**

```json
{
  "message": "Ошибка базы данных: ..."
}
```

## Структура проекта

```
play-today-app/
├── play_today_app/           # Основное приложение
│   ├── __init__.py           # Точка входа: создание Flask-приложения, инициализация расширений
│   ├── models.py             # SQLAlchemy-модели: User, Boardgame, Review
│   ├── views.py              # Веб-роуты (Jinja2 + Bootstrap)
│   ├── api_views.py          # JSON API (JWT, REST)
│   ├── forms.py              # WTForms (регистрация, вход, отзывы, игры)
│   ├── dropbox.py            # Асинхронная загрузка фото в Dropbox (aiohttp)
│   ├── cli_commands.py       # CLI: load_boardgames, create_first_superuser
│   ├── error_handlers.py     # Обработчики ошибок (403, 404, 500, InvalidAPIUsage)
│   ├── templates/            # Jinja2-шаблоны (14 HTML-файлов)
│   │   ├── base.html         # Базовый шаблон с Bootstrap 5 (CDN)
│   │   ├── header.html       # Навигация с выпадающим меню админа
│   │   ├── footer.html       # Подвал
│   │   ├── index.html        # Главная + страница игры
│   │   ├── register.html     # Регистрация
│   │   ├── login.html        # Вход
│   │   ├── add_boardgame.html# Добавление/редактирование игры
│   │   ├── add_review.html   # Добавление/редактирование отзыва
│   │   ├── admin_boardgames.html # Панель управления играми
│   │   ├── admin_users.html  # Панель управления пользователями
│   │   ├── profile.html      # Профиль пользователя
│   │   └── 403.html, 404.html, 500.html
│   └── static/               # Статические файлы
│       ├── css/              # style.css (bootstrap.min.css лежит, но не используется)
│       ├── fonts/            # Montserrat (Variable)
│       └── img/              # logo.svg, illustration.png, fav/, 403.png, 404.png, 500.png
├── migrations/               # Миграции Alembic (Flask-Migrate)
│   ├── alembic.ini
│   ├── env.py
│   └── versions/
│       └── 2bfb1cd08c60_initial_migration.py
├── .env.example              # Шаблон переменных окружения
├── .gitignore                # Исключения (venv, .env, instance/, *.sqlite3)
├── boardgames.csv            # Тестовые данные для CLI
├── settings.py               # Конфигурация (Config)
├── pyproject.toml            # black, isort, mypy (конфигурация)
├── requirements.txt          # Прикладные зависимости
├── requirements-dev.txt      # + линтеры (black, flake8, isort)
└── LICENSE
```

## Проверка кода

Зависимости для разработки и проверки кода находятся в `requirements-dev.txt`:

```bash
pip install -r requirements-dev.txt
flake8
```

`black` и `isort` настроены в `pyproject.toml` (line-length = 79, profile = "black").
`mypy` настроен в `pyproject.toml` (отключена ошибка import-untyped), но сам пакет не входит в зависимости.

## Использованные технологии

| Технология                  | Назначение                                            |
| --------------------------- | ----------------------------------------------------- |
| [Python](https://www.python.org/) | Язык программирования                            |
| [Flask](https://flask.palletsprojects.com/) | Веб-фреймворк                              |
| [Flask-SQLAlchemy](https://flask-sqlalchemy.palletsprojects.com/) | ORM для работы с БД |
| [Flask-Migrate](https://flask-migrate.readthedocs.io/) | Миграции базы данных (Alembic) |
| [Flask-Login](https://flask-login.readthedocs.io/) | Управление сессиями пользователей |
| [Flask-WTF](https://flask-wtf.readthedocs.io/) | Формы и CSRF-защита |
| [Flask-JWT-Extended](https://flask-jwt-extended.readthedocs.io/) | JWT-аутентификация |
| [SQLAlchemy](https://www.sqlalchemy.org/) | SQL-конвейер и ORM |
| [SQLite](https://www.sqlite.org/) | Локальная база данных |
| [WTForms](https://wtforms.readthedocs.io/) | Валидация форм |
| [Jinja2](https://jinja.palletsprojects.com/) | Шаблоны |
| [Bootstrap 5](https://getbootstrap.com/) | CSS-фреймворк для фронтенда (CDN) |
| [Dropbox API](https://www.dropbox.com/developers) | Облачное хранилище для фото |
| [aiohttp](https://docs.aiohttp.org/) | Асинхронный HTTP-клиент для Dropbox |
| [black](https://black.readthedocs.io/) | Форматирование кода |
| [isort](https://pycqa.github.io/isort/) | Сортировка импортов |
| [flake8](https://flake8.pycqa.org/) | Проверка стиля кода |

## Автор

| Имя | GitHub |
| --- | ------ |
| Юлия Тарханова | [@TAKOYAMItakoyami](https://github.com/TAKOYAMItakoyami) |

## Лицензия

Проект распространяется под лицензией MIT.
