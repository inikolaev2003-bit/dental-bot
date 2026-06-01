import pytest
from unittest.mock import AsyncMock, MagicMock, patch, call
from aiogram.types import Message, CallbackQuery

from states.client_states import AppointmentStates


class TestStartHandler:

    async def test_cmd_start_sends_welcome(self, make_message, make_state):
        """Команда /start отправляет приветственное сообщение"""
        from handlers.client import cmd_start

        message = make_message(text="/start")
        state = make_state()

        await cmd_start(message, state)

        message.answer.assert_called_once()
        call_args = message.answer.call_args
        assert "Добро пожаловать" in call_args[0][0] or \
               "Добро пожаловать" in str(call_args)

    async def test_cmd_start_clears_state(self, make_message, make_state):
        """Команда /start сбрасывает состояние"""
        from handlers.client import cmd_start

        message = make_message(text="/start")
        state = make_state()

        await cmd_start(message, state)
        state.clear.assert_called_once()

    async def test_cmd_start_shows_keyboard(self, make_message, make_state):
        """Команда /start показывает клавиатуру"""
        from handlers.client import cmd_start

        message = make_message(text="/start")
        state = make_state()

        await cmd_start(message, state)

        call_kwargs = message.answer.call_args[1]
        assert "reply_markup" in call_kwargs


class TestAboutAndContacts:

    async def test_about_clinic(self, make_message):
        """Информация о клинике"""
        from handlers.client import about_clinic

        message = make_message(text="ℹ️ О клинике")
        await about_clinic(message)

        message.answer.assert_called_once()
        text = message.answer.call_args[0][0]
        assert "клиник" in text.lower()

    async def test_contacts(self, make_message):
        """Контактная информация"""
        from handlers.client import contacts

        message = make_message(text="📞 Контакты")
        await contacts(message)

        message.answer.assert_called_once()
        text = message.answer.call_args[0][0]
        assert "контакт" in text.lower() or "телефон" in text.lower() or "адрес" in text.lower()


class TestAppointmentFlow:

    async def test_start_appointment_no_doctors(self, make_message, make_state):
        """Запись невозможна если нет врачей"""
        from handlers.client import start_appointment

        message = make_message(text="📅 Записаться на приём")
        state = make_state()

        with patch("handlers.client.db.get_all_doctors", AsyncMock(return_value=[])):
            await start_appointment(message, state)

        text = message.answer.call_args[0][0]
        assert "нет" in text.lower() or "недоступ" in text.lower()

    async def test_start_appointment_with_doctors(self, make_message, make_state):
        """Запись показывает список врачей"""
        from handlers.client import start_appointment

        message = make_message(text="📅 Записаться на приём")
        state = make_state()

        doctors = [(1, "Иванов И.И.", "Терапевт", "Описание", 1)]

        with patch("handlers.client.db.get_all_doctors", AsyncMock(return_value=doctors)):
            await start_appointment(message, state)

        state.set_state.assert_called_once_with(AppointmentStates.choosing_doctor)
        message.answer.assert_called_once()

    async def test_choose_doctor_valid(self, make_callback, make_state):
        """Выбор врача переходит к выбору услуги"""
        from handlers.client import choose_doctor

        callback = make_callback(data="doc_1")
        state = make_state()

        doctor = (1, "Иванов И.И.", "Терапевт", "Описание", 1)
        services = [(1, "Лечение", "Описание", 60, 3000.0, 1)]

        with patch("handlers.client.db.get_doctor", AsyncMock(return_value=doctor)), \
             patch("handlers.client.db.get_all_services", AsyncMock(return_value=services)):
            await choose_doctor(callback, state)

        state.update_data.assert_called()
        state.set_state.assert_called_with(AppointmentStates.choosing_service)

    async def test_choose_doctor_not_found(self, make_callback, make_state):
        """Выбор несуществующего врача показывает ошибку"""
        from handlers.client import choose_doctor

        callback = make_callback(data="doc_999")
        state = make_state()

        with patch("handlers.client.db.get_doctor", AsyncMock(return_value=None)):
            await choose_doctor(callback, state)

        callback.answer.assert_called_once()
        assert callback.answer.call_args[1].get("show_alert") is True

    async def test_choose_service_valid(self, make_callback, make_state):
        """Выбор услуги переходит к выбору слота"""
        from handlers.client import choose_service

        callback = make_callback(data="srv_1")
        state = make_state()
        state.get_data = AsyncMock(return_value={
            "doctor_id": 1,
            "doctor_name": "Иванов И.И."
        })

        service = (1, "Лечение", "Описание", 60, 3000.0, 1)
        slots = [(1, "25.12.2024", "10:00", 1)]

        with patch("handlers.client.db.get_service", AsyncMock(return_value=service)), \
             patch("handlers.client.db.get_slots_by_doctor", AsyncMock(return_value=slots)):
            await choose_service(callback, state)

        state.set_state.assert_called_with(AppointmentStates.choosing_slot)

    async def test_choose_service_no_slots(self, make_callback, make_state):
        """Выбор услуги без слотов возвращает к врачам"""
        from handlers.client import choose_service

        callback = make_callback(data="srv_1")
        state = make_state()
        state.get_data = AsyncMock(return_value={
            "doctor_id": 1,
            "doctor_name": "Иванов И.И."
        })

        service = (1, "Лечение", "Описание", 60, 3000.0, 1)
        doctors = [(1, "Иванов И.И.", "Терапевт", "Описание", 1)]

        with patch("handlers.client.db.get_service", AsyncMock(return_value=service)), \
             patch("handlers.client.db.get_slots_by_doctor", AsyncMock(return_value=[])), \
             patch("handlers.client.db.get_all_doctors", AsyncMock(return_value=doctors)):
            await choose_service(callback, state)

        state.set_state.assert_called_with(AppointmentStates.choosing_doctor)

    async def test_choose_slot_valid(self, make_callback, make_state):
        """Выбор слота переходит к вводу имени"""
        from handlers.client import choose_slot

        callback = make_callback(data="slot_1")
        state = make_state()

        slot = (1, 1, "25.12.2024", "10:00", 1)

        with patch("handlers.client.db.get_slot", AsyncMock(return_value=slot)):
            await choose_slot(callback, state)

        state.set_state.assert_called_with(AppointmentStates.entering_name)

    async def test_choose_slot_unavailable(self, make_callback, make_state):
        """Выбор занятого слота показывает ошибку"""
        from handlers.client import choose_slot

        callback = make_callback(data="slot_1")
        state = make_state()

        slot = (1, 1, "25.12.2024", "10:00", 0)  # is_available = 0

        with patch("handlers.client.db.get_slot", AsyncMock(return_value=slot)):
            await choose_slot(callback, state)

        callback.answer.assert_called_once()
        assert callback.answer.call_args[1].get("show_alert") is True

    async def test_enter_name_valid(self, make_message, make_state):
        """Ввод корректного имени"""
        from handlers.client import enter_name

        message = make_message(text="Петров Пётр Петрович")
        state = make_state()

        await enter_name(message, state)

        state.update_data.assert_called_with(full_name="Петров Пётр Петрович")
        state.set_state.assert_called_with(AppointmentStates.entering_phone)

    async def test_enter_name_too_short(self, make_message, make_state):
        """Слишком короткое имя отклоняется"""
        from handlers.client import enter_name

        message = make_message(text="АБ")
        state = make_state()

        await enter_name(message, state)

        state.update_data.assert_not_called()
        state.set_state.assert_not_called()
        message.answer.assert_called_once()

    @pytest.mark.parametrize("phone,valid", [
        ("+7 999 123-45-67", True),
        ("89991234567", True),
        ("+79991234567", True),
        ("123", False),
        ("abc", False),
        ("", False),
    ])
    async def test_enter_phone_validation(self, make_message, make_state, phone, valid):
        """Валидация номера телефона"""
        from handlers.client import enter_phone

        message = make_message(text=phone)
        state = make_state()
        state.get_data = AsyncMock(return_value={
            "doctor_name": "Врач",
            "service_name": "Услуга",
            "price": 3000,
            "slot_date": "25.12.2024",
            "slot_time": "10:00",
            "full_name": "Петров П.П."
        })

        await enter_phone(message, state)

        if valid:
            state.set_state.assert_called_with(AppointmentStates.confirming)
        else:
            state.set_state.assert_not_called()

    async def test_confirm_appointment_success(self, make_callback, make_state):
        """Успешное подтверждение записи"""
        from handlers.client import confirm_appointment

        callback = make_callback(data="confirm_appointment")
        state = make_state()
        state.get_data = AsyncMock(return_value={
            "slot_id": 1,
            "doctor_id": 1,
            "service_id": 1,
            "doctor_name": "Иванов И.И.",
            "service_name": "Лечение",
            "price": 3000,
            "slot_date": "25.12.2024",
            "slot_time": "10:00",
            "full_name": "Петров П.П.",
            "phone": "+7 999 000-00-00"
        })

        slot = (1, 1, "25.12.2024", "10:00", 1)

        with patch("handlers.client.db.get_slot", AsyncMock(return_value=slot)), \
             patch("handlers.client.db.create_appointment", AsyncMock(return_value=1)), \
             patch("handlers.client.db.book_slot", AsyncMock()):
            await confirm_appointment(callback, state)

        state.clear.assert_called_once()
        callback.message.edit_text.assert_called_once()

    async def test_confirm_appointment_slot_taken(self, make_callback, make_state):
        """Подтверждение записи на занятый слот"""
        from handlers.client import confirm_appointment

        callback = make_callback(data="confirm_appointment")
        state = make_state()
        state.get_data = AsyncMock(return_value={"slot_id": 1})

        slot = (1, 1, "25.12.2024", "10:00", 0)  # Слот занят

        with patch("handlers.client.db.get_slot", AsyncMock(return_value=slot)):
            await confirm_appointment(callback, state)

        state.clear.assert_called_once()
        # Запись не должна создаваться


class TestMyAppointments:

    async def test_my_appointments_empty(self, make_message, make_state):
        """Пустой список записей"""
        from handlers.client import my_appointments

        message = make_message(text="📋 Мои записи")
        state = make_state()

        with patch("handlers.client.db.get_user_appointments", AsyncMock(return_value=[])):
            await my_appointments(message, state)

        text = message.answer.call_args[0][0]
        assert "нет" in text.lower() or "пока" in text.lower()

    async def test_my_appointments_with_data(self, make_message, make_state):
        """Список записей с данными"""
        from handlers.client import my_appointments

        message = make_message(text="📋 Мои записи")
        state = make_state()

        appointments = [
            (1, "Иванов", "Лечение", "25.12.2024", "10:00", "pending", "Петров П.П.", "+7 999")
        ]

        with patch("handlers.client.db.get_user_appointments", AsyncMock(return_value=appointments)):
            await my_appointments(message, state)

        message.answer.assert_called_once()

    async def test_cancel_appointment_success(self, make_callback):
        """Успешная отмена записи"""
        from handlers.client import cancel_appointment

        callback = make_callback(data="cancel_apt_1")

        with patch("handlers.client.db.cancel_appointment", AsyncMock(return_value=True)):
            await cancel_appointment(callback)

        callback.message.edit_text.assert_called_once()

    async def test_cancel_appointment_failure(self, make_callback):
        """Неудачная отмена записи"""
        from handlers.client import cancel_appointment

        callback = make_callback(data="cancel_apt_1")

        with patch("handlers.client.db.cancel_appointment", AsyncMock(return_value=False)):
            await cancel_appointment(callback)

        callback.answer.assert_called_once()
        assert callback.answer.call_args[1].get("show_alert") is True