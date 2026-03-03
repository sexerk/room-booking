Room Booking API
REST API для бронирования переговорных комнат. Пользователи могут просматривать комнаты, создавать и отменять бронирования. Администраторы управляют комнатами и удобствами.
Технологии

FastAPI — веб-фреймворк с автоматической OpenAPI документацией
SQLAlchemy 2.0 + asyncpg — асинхронный ORM
PostgreSQL — основная база данных
Redis — кэширование
RabbitMQ + Celery — фоновые задачи
JWT — аутентификация
Alembic — миграции БД
Docker + docker-compose — контейнеризация
pytest — тестирование

Роли пользователей
РольВозможностиАнонимПросмотр активных комнат и доступностиАвторизованныйСоздание, просмотр и отмена своих бронированийАдминистраторУправление комнатами/удобствами, просмотр всех бронирований
Архитектура
Проект построен по принципу чистой архитектуры с разделением на слои:
app/
├── api/endpoints/       # API слой — роутеры, Pydantic схемы, зависимости
├── services/            # Service слой — бизнес-логика
├── repositories/        # Repository слой — работа с БД (SQLAlchemy)
├── cache/               # Cache слой — Redis кэширование
├── tasks/               # Task слой — Celery фоновые задачи
├── models/              # SQLAlchemy модели
├── schemas/             # Pydantic схемы
├── db/                  # Подключение к БД, сессии
└── core/                # Конфигурация, безопасность, исключения
Принцип: тонкий API слой → бизнес-логика в сервисах → доступ к БД через репозитории.
Быстрый старт
Предварительные требования

Docker
docker-compose

Установка и запуск

Клонируйте репозиторий:

bashgit clone <repository-url>
cd room-booking

Создайте .env файл на основе примера:

bashcp .env.example .env

Запустите все сервисы:

bashdocker-compose up -d
или через Makefile:
bashmake up

Примените миграции:

bashdocker-compose exec api alembic upgrade head
или:
bashmake migrate

Откройте документацию: http://localhost:8000/docs

Документация API
URLОписаниеhttp://localhost:8000/docsSwagger UIhttp://localhost:8000/redocReDoc
Базовый префикс всех эндпоинтов: /api/v1/
Основные эндпоинты
Аутентификация:

POST /api/v1/auth/register — регистрация
POST /api/v1/auth/login — получить JWT токены
POST /api/v1/auth/refresh — обновить access токен
GET /api/v1/auth/me — профиль текущего пользователя

Комнаты:

GET /api/v1/rooms — список активных комнат
GET /api/v1/rooms/{room_id} — детальная информация
GET /api/v1/rooms/availability — поиск доступных комнат по интервалу
POST /api/v1/rooms — создать комнату (Admin)
PATCH /api/v1/rooms/{room_id} — изменить комнату (Admin)
DELETE /api/v1/rooms/{room_id} — деактивировать комнату (Admin)

Бронирования:

GET /api/v1/bookings — мои бронирования
POST /api/v1/bookings — создать бронирование
GET /api/v1/bookings/{booking_id} — детальное бронирование
POST /api/v1/bookings/{booking_id}/confirm — подтвердить
POST /api/v1/bookings/{booking_id}/cancel — отменить
GET /api/v1/admin/bookings — все бронирования (Admin)

Создание администратора
bashdocker-compose exec api python -c "
import asyncio
from app.db.session import async_session_maker
from app.models.user import User
from app.core.security import get_password_hash

async def create_admin():
    async with async_session_maker() as db:
        admin = User(
            email='admin@example.com',
            username='admin',
            hashed_password=get_password_hash('adminpassword'),
            full_name='Administrator',
            is_active=True,
            is_admin=True
        )
        db.add(admin)
        await db.commit()
        print('Admin created!')

asyncio.run(create_admin())
"
Тестирование
Запустить все тесты:
bashdocker-compose exec api pytest -v
или:
bashmake test
Тесты покрывают:

Аутентификация (регистрация, логин, профиль)
Бронирования (создание, подтверждение, отмена, конфликты)

Фоновые задачи (Celery)
ЗадачаОписаниеexpire_pending_bookingПереводит PENDING → EXPIRED через N минут если не подтвержденоsend_booking_reminderОтправляет напоминание за M минут до начала (в лог)expire_pending_bookingsПериодическая очистка просроченных бронирований
Кэширование (Redis)

GET /rooms — TTL 5 минут
GET /rooms/availability — TTL 60 секунд
Инвалидация кэша при создании/подтверждении/отмене бронирования

Docker сервисы
СервисНазначениеПортapiFastAPI приложение8000dbPostgreSQL5432redisКэш6379rabbitmqБрокер сообщений5672, 15672workerCelery worker—
RabbitMQ Management UI: http://localhost:15672 (guest/guest)
Makefile команды
bashmake up          # Запустить все сервисы
make down        # Остановить все сервисы
make logs        # Следить за логами
make migrate     # Применить миграции
make test        # Запустить тесты
make shell       # Открыть shell в api контейнере
make clean       # Удалить контейнеры и volumes