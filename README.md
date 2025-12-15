# 🏕️ Туристические маршруты - Django приложение

Приложение для управления туристическими маршрутами с поддержкой Docker и PostgreSQL. Проект реализует CRUD-операции, AJAX-поиск, выбор хранилища данных (БД или XML), и миграцию с SQLite на PostgreSQL.

## 📋 Описание проекта

Приложение предоставляет:
- **CRUD операции** для управления туристическими маршрутами
- **Двойное хранилище**: база данных (SQLite/PostgreSQL) и XML файлы
- **AJAX поиск** по маршрутам в реальном времени
- **Проверка дубликатов** при добавлении новых маршрутов
- **Загрузка данных** из XML файлов
- **Docker контейнеризация** для простого развёртывания
- **Миграция с SQLite на PostgreSQL** для production-среды

## 🚀 Быстрый старт с Docker

### Требования

- **Docker** 20.10+
- **Docker Compose** 2.0+
- или **Python** 3.9+ для локальной разработки

### 1️⃣ Клонирование репозитория

```bash
git clone https://github.com/maxkond1/lab3.git
cd lab3
```

### 2️⃣ Подготовка переменных окружения

Создайте файл `.env` в корне проекта на основе `.env.example`:

```bash
cp .env.example .env
```

Отредактируйте `.env` и установите необходимые значения:

```env
# Django Settings
DEBUG=False
SECRET_KEY=your-super-secret-key-change-this-in-production
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0,yourdomain.com

# Database Configuration - PostgreSQL
DB_ENGINE=django.db.backends.postgresql
DB_NAME=tourist_routes_db
DB_USER=postgres
DB_PASSWORD=your-secure-password-here
DB_HOST=db
DB_PORT=5432

# Application Configuration
WEB_PORT=8000
```

### 3️⃣ Запуск приложения

#### Режим разработки (Development)

```bash
docker compose up -d
```

Приложение будет доступно по адресу: `http://localhost:8000`

#### Проверка логов

```bash
docker compose logs -f web
docker compose logs -f db
```

#### Остановка приложения

```bash
docker compose down
```

## 🐋 Docker конфигурация

### Структура Docker Compose

Проект использует два сервиса (Django + PostgreSQL):

```
┌──────────────┐
│    Django    │  (Gunicorn, Port 8000)
│     (web)    │
└──────┬───────┘
       │
┌──────▼───────┐
│  PostgreSQL   │  (Port 5432 внутри сети docker)
│     (db)      │
└──────────────┘
```

### Volumes (Хранилища)

| Том | Путь | Назначение |
|-----|------|-----------|
| `postgres_data` | `/var/lib/postgresql/data` | Данные PostgreSQL |
| `static_volume` | `/app/tourist_routes/staticfiles` | Статические файлы (collectstatic) |
| `media_volume` | `/app/tourist_routes/media` | Загруженные файлы (XML и т.д.) |

Docker Compose создаёт внутреннюю сеть автоматически.

## 📦 Миграция с SQLite на PostgreSQL

### Процесс миграции

#### Этап 1: Подготовка

```bash
# 1. Убедитесь, что .env содержит PostgreSQL credentials
# 2. Проверьте наличие данных в SQLite:
docker compose exec web python manage.py dbshell
# Или локально:
python tourist_routes/manage.py dbshell
```

#### Этап 2: Запуск контейнеров

```bash
# Запустите контейнеры (они автоматически применят миграции)
docker compose up -d
```

Entrypoint скрипт автоматически:
- Ожидает готовности PostgreSQL
- Применяет все миграции Django (`python manage.py migrate`)
- Собирает статические файлы (`python manage.py collectstatic`)

#### Этап 3: Верификация данных

```bash
# Проверить данные в новой БД
docker compose exec web python manage.py shell
```

```python
from routes_app.models import TouristRoute
print(f"Всего маршрутов: {TouristRoute.objects.count()}")
# Просмотр первого маршрута
route = TouristRoute.objects.first()
print(route.name, route.region, route.difficulty)
```

### Использование скрипта миграции (SQLite -> PostgreSQL)

В репозитории есть готовый скрипт, который:
1) делает `dumpdata` из SQLite (монтирует `tourist_routes/db.sqlite3` внутрь контейнера),
2) применяет миграции в PostgreSQL,
3) делает `loaddata` в PostgreSQL.

```bash
bash scripts/migrate_sqlite_to_postgres.sh
```

## 💾 Работа с базой данных

### Доступ к PostgreSQL изнутри контейнера

```bash
# Подключиться к bash контейнера
docker compose exec db psql -U postgres -d tourist_routes_db

# Основные команды SQL
\dt                      # Список таблиц
\d routes_app_touristroute  # Структура таблицы
SELECT COUNT(*) FROM routes_app_touristroute;  # Количество записей
```

### Доступ к PostgreSQL снаружи контейнера

```bash
# Используя psql (если установлен)
psql -h localhost -U postgres -d tourist_routes_db -p 5432
```

Параметры подключения:
- Host: `localhost`
- Port: `5432` (или значение `DB_PORT` из `.env`)
- Database: `tourist_routes_db` (или значение `DB_NAME` из `.env`)
- User: `postgres` (или значение `DB_USER` из `.env`)

### Резервное копирование БД

```bash
# Создать дамп PostgreSQL
docker compose exec db pg_dump -U postgres -d tourist_routes_db > backup_$(date +%Y%m%d_%H%M%S).sql

# Восстановить из дампа
docker compose exec -T db psql -U postgres -d tourist_routes_db < backup_20240101_120000.sql
```

## 🛠️ Локальная разработка (без Docker)

### Требования

- Python 3.9+
- PostgreSQL 12+ (или SQLite для разработки)
- pip

### Установка

```bash
# 1. Создать виртуальное окружение
python -m venv venv

# 2. Активировать окружение
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 3. Установить зависимости
pip install -r requirements.txt

# 4. Создать .env файл
cp .env.example .env

# 5. Применить миграции
cd tourist_routes
python manage.py migrate

# 6. Создать суперпользователя (опционально)
python manage.py createsuperuser

# 7. Собрать статические файлы
python manage.py collectstatic --noinput

# 8. Запустить dev сервер
python manage.py runserver
```

Приложение будет доступно по адресу: `http://127.0.0.1:8000`

## 📚 Функциональность приложения

### 1. Управление маршрутами (CRUD)

- **Create** (Создание): `/routes/add/` - форма для добавления нового маршрута
- **Read** (Чтение): `/` - список всех маршрутов
- **Update** (Обновление): `/routes/<id>/edit/` - редактирование маршрута
- **Delete** (Удаление): `/routes/<id>/delete/` - удаление маршрута

### 2. Выбор хранилища (Storage Selection)

При создании маршрута можно выбрать:
- **БД** - сохранить в PostgreSQL/SQLite
- **XML** - сохранить в `media/tourist_routes.xml`

### 3. AJAX поиск

Поле поиска на главной странице позволяет:
- Искать по названию маршрута
- Искать по названию региона
- Получать результаты в реальном времени (без перезагрузки страницы)

### 4. Загрузка из XML

- `/routes/upload-xml/` - форма для загрузки XML файла
- Автоматическая проверка дубликатов
- Импорт маршрутов в БД

### 5. Проверка дубликатов

При добавлении маршрута система проверяет:
- В БД: уникальность комбинации (name, region, length_km)
- В XML: отсутствие маршрута с тем же названием и регионом

## 📁 Структура проекта

```
lab3/
├── Dockerfile                      # Конфигурация образа Django
├── docker-compose.yml              # Оркестрация контейнеров
├── .dockerignore                   # Исключения для Docker образа
├── entrypoint.sh                   # Скрипт инициализации Docker
├── .env.example                    # Пример переменных окружения
├── .gitignore                      # Исключения для Git
├── requirements.txt                # Python зависимости
├── README.md                       # Этот файл
├── scripts/                        # Вспомогательные скрипты
│   ├── init-db.sql                 # (опционально) SQL инициализация
│   └── migrate_sqlite_to_postgres.sh  # Миграция данных SQLite -> PostgreSQL
└── tourist_routes/                 # Главная папка Django проекта
    ├── manage.py                   # Django управление
    ├── db.sqlite3                  # SQLite (для локальной разработки)
    ├── media/                      # Загруженные файлы
    │   └── tourist_routes.xml      # XML хранилище маршрутов
    ├── staticfiles/                # Собранные статические файлы
    ├── tourist_routes/             # Конфигурация проекта
    │   ├── settings.py             # Настройки Django (с поддержкой .env)
    │   ├── urls.py                 # Главные URL маршруты
    │   ├── wsgi.py                 # WSGI конфигурация
    │   └── asgi.py                 # ASGI конфигурация
    └── routes_app/                 # Основное приложение
        ├── models.py               # Модель TouristRoute
        ├── views.py                # Представления (CRUD, AJAX, XML)
        ├── urls.py                 # URL маршруты приложения
        ├── admin.py                # Admin интерфейс
        ├── migrations/             # Миграции БД
        └── templates/              # HTML шаблоны
            └── routes_app/
                ├── base.html       # Базовый шаблон
                ├── index.html      # Главная страница со списком
                ├── routes_list.html    # Список маршрутов
                ├── add_route.html      # Форма добавления
                ├── edit_route.html     # Форма редактирования
                ├── confirm_delete.html # Подтверждение удаления
                └── upload_xml.html     # Загрузка XML
```

## 🔒 Безопасность

### Переменные окружения

Все конфиденциальные данные передаются через `.env` файл:

```env
SECRET_KEY=your-secret-key
DB_PASSWORD=secure-password
ALLOWED_HOSTS=your-domain.com
DEBUG=False  # Обязательно False в production
```

### .env в .gitignore

Файл `.env` добавлен в `.gitignore` и не будет загружаться в репозиторий.

### Рекомендации

- ✅ Используйте сложные пароли для БД
- ✅ Генерируйте новый SECRET_KEY для production
- ✅ Установите DEBUG=False в production
- ✅ Используйте HTTPS для production
- ✅ Регулярно обновляйте зависимости
- ✅ Создавайте резервные копии БД

## 🐛 Траблшутинг

### Проблема: Контейнер web не запускается

```bash
# Проверить логи
docker compose logs web

# Возможные причины:
# 1. PostgreSQL не готов - wait for db healthcheck
# 2. SECRET_KEY не установлен - проверить .env файл
# 3. ALLOWED_HOSTS пуст - установить localhost,127.0.0.1
```

### Проблема: Ошибка подключения к БД

```bash
# Проверить статус PostgreSQL
docker compose ps db

# Проверить логи БД
docker compose logs db

# Переподключиться к БД
docker compose down
docker compose up -d
```

### Проблема: Статические файлы не загружаются

```bash
# Собрать статические файлы вручную
docker compose exec web python manage.py collectstatic --noinput

# Проверить наличие файлов
docker compose exec web ls -la /app/tourist_routes/staticfiles/
```

### Проблема: Данные не мигрировались

```bash
# Проверить миграции
docker compose exec web python manage.py showmigrations

# Применить миграции вручную
docker compose exec web python manage.py migrate

# Проверить данные в БД
docker compose exec web python manage.py shell
```

## 🌐 Production развёртывание

### Рекомендуемые шаги

1. **Сгенерируйте новый SECRET_KEY**:
   ```python
   from django.core.management.utils import get_random_secret_key
   print(get_random_secret_key())
   ```

2. **Установите переменные окружения**:
   ```env
   DEBUG=False
   SECRET_KEY=<generated-key>
   ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
   DB_PASSWORD=<strong-password>
   ```

3. **Используйте внешнюю БД** (например, AWS RDS, Heroku Postgres)

4. **Настройте HTTPS** (используя Let's Encrypt и Nginx)

5. **Используйте reverse proxy** (Nginx с SSL)

6. **Мониторьте логи** и используйте сервис логирования

7. **Настройте резервные копии** БД

### Масштабирование

```yaml
# docker-compose.prod.yml
web:
  deploy:
    replicas: 2  # Несколько экземпляров для load balancing
```

## 📝 Схема базы данных

### Таблица TouristRoute

```sql
CREATE TABLE routes_app_touristroute (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,
    length_km DECIMAL(6, 2) NOT NULL,
    duration_days INTEGER NOT NULL,
    difficulty VARCHAR(10) NOT NULL,
    region VARCHAR(100) NOT NULL,
    best_season VARCHAR(100),
    kolvo_chel DECIMAL(6, 2),
    source VARCHAR(10) DEFAULT 'db',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (name, region, length_km)
);

CREATE INDEX idx_difficulty ON routes_app_touristroute(difficulty);
CREATE INDEX idx_region ON routes_app_touristroute(region);
```

## 🔄 CI/CD интеграция

### GitHub Actions пример

```yaml
name: Docker Build and Push

on:
  push:
    branches: [ main ]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Build and push Docker image
        run: |
          docker build -t myregistry/tourist-routes:latest .
          docker push myregistry/tourist-routes:latest
```

## 📞 Контакты и поддержка

- **Автор**: maxkond1
- **Repository**: https://github.com/maxkond1/lab3
- **Issues**: https://github.com/maxkond1/lab3/issues

## 📄 Лицензия

Проект распространяется без лицензии (приватный проект для обучения).

## 🔗 Полезные ссылки

- [Django Documentation](https://docs.djangoproject.com/)
- [Docker Documentation](https://docs.docker.com/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Docker Compose Reference](https://docs.docker.com/compose/compose-file/)

---

**Версия**: 1.0.0  
**Последнее обновление**: Декабрь 2025  
**Статус**: Production Ready ✅
