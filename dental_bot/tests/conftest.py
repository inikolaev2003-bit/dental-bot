import pytest
import asyncio
import aiosqlite
from unittest.mock import AsyncMock, MagicMock, patch
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey
from aiogram.types import (
    User, Chat, Message, CallbackQuery,
    Update, InlineKeyboardMarkup
)

# Путь к тестовой БД в памяти
TEST_DB_PATH = ":memory:"


# ФИКСТУРЫ БД 

@pytest.fixture
async def db_connection():
    """Соединение с тестовой БД в памяти"""
    async with aiosqlite.connect(TEST_DB_PATH) as conn:
        yield conn


@pytest.fixture
async def initialized_db(tmp_path, monkeypatch):
    """Инициализированная тестовая БД во временном файле"""
    db_file = tmp_path / "test_dental.db"
    monkeypatch.setattr("database.DB_PATH", str(db_file))

    import database
    await database.init_db()
    yield str(db_file)


# ФИКСТУРЫ ПОЛЬЗОВАТЕЛЕЙ 

@pytest.fixture
def make_user():
    """Фабрика пользователей Telegram"""
    def _make(
        user_id: int = 123456789,
        username: str = "testuser",
        first_name: str = "Test",
        last_name: str = "User",
        is_bot: bool = False
    ) -> User:
        user = MagicMock(spec=User)
        user.id = user_id
        user.username = username
        user.first_name = first_name
        user.last_name = last_name
        user.full_name = f"{first_name} {last_name}"
        user.is_bot = is_bot
        return user
    return _make


@pytest.fixture
def regular_user(make_user):
    return make_user(user_id=111111111, username="regular_user")


@pytest.fixture
def admin_user(make_user):
    return make_user(user_id=999999999, username="admin_user")


# ФИКСТУРЫ СООБЩЕНИЙ

@pytest.fixture
def make_chat():
    def _make(chat_id: int = 123456789, chat_type: str = "private") -> Chat:
        chat = MagicMock(spec=Chat)
        chat.id = chat_id
        chat.type = chat_type
        return chat
    return _make


@pytest.fixture
def make_message(make_user, make_chat):
    """Фабрика сообщений"""
    def _make(
        text: str = "test",
        user_id: int = 123456789,
        username: str = "testuser",
        message_id: int = 1,
        chat_id: int = 123456789
    ) -> Message:
        message = MagicMock(spec=Message)
        message.message_id = message_id
        message.text = text
        message.from_user = make_user(user_id=user_id, username=username)
        message.chat = make_chat(chat_id=chat_id)
        message.answer = AsyncMock(return_value=MagicMock(spec=Message))
        message.reply = AsyncMock()
        message.delete = AsyncMock()
        message.edit_text = AsyncMock()
        return message
    return _make


@pytest.fixture
def make_callback(make_user, make_message, make_chat):
    """Фабрика callback query"""
    def _make(
        data: str = "test_data",
        user_id: int = 123456789,
        username: str = "testuser",
        message_id: int = 1
    ) -> CallbackQuery:
        callback = MagicMock(spec=CallbackQuery)
        callback.id = "test_callback_id"
        callback.data = data
        callback.from_user = make_user(user_id=user_id, username=username)
        callback.message = make_message(
            user_id=user_id,
            username=username,
            message_id=message_id
        )
        callback.answer = AsyncMock()
        return callback
    return _make


# ФИКСТУРЫ FSM

@pytest.fixture
def make_state():
    """Фабрика FSM состояний"""
    def _make() -> FSMContext:
        state = MagicMock(spec=FSMContext)
        state.set_state = AsyncMock()
        state.get_state = AsyncMock(return_value=None)
        state.update_data = AsyncMock()
        state.get_data = AsyncMock(return_value={})
        state.clear = AsyncMock()
        return state
    return _make


# ФИКСТУРЫ БОТА

@pytest.fixture
def bot():
    """Мок бота"""
    mock_bot = MagicMock(spec=Bot)
    mock_bot.send_message = AsyncMock()
    mock_bot.edit_message_text = AsyncMock()
    mock_bot.token = "1234567890:TEST_TOKEN_FOR_TESTING_PURPOSES_ONLY"
    return mock_bot


# ТЕСТОВЫЕ ДАННЫЕ

@pytest.fixture
def sample_doctor():
    return {
        "id": 1,
        "name": "Иванов Иван Иванович",
        "specialization": "Терапевт",
        "description": "Опытный специалист",
        "is_active": 1
    }


@pytest.fixture
def sample_service():
    return {
        "id": 1,
        "name": "Лечение кариеса",
        "description": "Профессиональное лечение",
        "duration": 60,
        "price": 3000.0,
        "is_active": 1
    }


@pytest.fixture
def sample_slot():
    return {
        "id": 1,
        "doctor_id": 1,
        "slot_date": "25.12.2024",
        "slot_time": "10:00",
        "is_available": 1
    }


@pytest.fixture
def sample_appointment():
    return {
        "id": 1,
        "user_id": 111111111,
        "username": "testuser",
        "full_name": "Петров Пётр Петрович",
        "phone": "+7 999 123-45-67",
        "doctor_id": 1,
        "service_id": 1,
        "slot_id": 1,
        "status": "pending"
    }
