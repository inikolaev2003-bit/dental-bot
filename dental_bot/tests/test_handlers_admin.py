import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from states.admin_states import (
    AdminAuthStates, AdminDoctorStates,
    AdminServiceStates, AdminSlotStates
)


class TestAdminAuth:

    async def test_admin_panel_existing_admin(self, make_message, make_state):
        """Существующий админ сразу попадает в панель"""
        from handlers.admin import admin_panel_cmd

        message = make_message(text="/adminpanel", user_id=999999)
        state = make_state()

        with patch("handlers.admin.db.is_admin", AsyncMock(return_value=True)):
            await admin_panel_cmd(message, state)

        state.clear.assert_called_once()
        message.answer.assert_called_once()
        text = message.answer.call_args[0][0]
        assert "панель" in text.lower() or "администратор" in text.lower()

    async def test_admin_panel_new_user_asks_password(self, make_message, make_state):
        """Новый пользователь должен ввести пароль"""
        from handlers.admin import admin_panel_cmd

        message = make_message(text="/adminpanel", user_id=111111)
        state = make_state()

        with patch("handlers.admin.db.is_admin", AsyncMock(return_value=False)):
            await admin_panel_cmd(message, state)

        state.set_state.assert_called_once_with(AdminAuthStates.waiting_password)
        message.answer.assert_called_once()

    async def test_correct_password_grants_access(self, make_message, make_state):
        """Правильный пароль даёт доступ"""
        from handlers.admin import check_admin_password

        message = make_message(text="admin123", user_id=111111, username="newadmin")
        state = make_state()
        message.delete = AsyncMock()

        with patch("handlers.admin.ADMIN_PASSWORD", "admin123"), \
             patch("handlers.admin.db.add_admin", AsyncMock()), \
             patch("handlers.admin.db.is_admin", AsyncMock(return_value=True)):
            await check_admin_password(message, state)

        message.delete.assert_called_once()
        state.clear.assert_called_once()

    async def test_wrong_password_denies_access(self, make_message, make_state):
        """Неправильный пароль отказывает в доступе"""
        from handlers.admin import check_admin_password

        message = make_message(text="wrongpassword", user_id=111111)
        state = make_state()
        message.delete = AsyncMock()

        with patch("handlers.admin.ADMIN_PASSWORD", "admin123"):
            await check_admin_password(message, state)

        message.delete.assert_called_once()
        state.clear.assert_called_once()
        text = message.answer.call_args[0][0]
        assert "неверн" in text.lower()

    async def test_password_message_is_deleted(self, make_message, make_state):
        """Сообщение с паролем удаляется"""
        from handlers.admin import check_admin_password

        message = make_message(text="anypassword")
        state = make_state()
        message.delete = AsyncMock()

        with patch("handlers.admin.ADMIN_PASSWORD", "admin123"):
            await check_admin_password(message, state)

        message.delete.assert_called_once()

    async def test_admin_exit(self, make_callback, make_state):
        """Выход из панели администратора"""
        from handlers.admin import admin_exit

        callback = make_callback(data="admin_exit")
        state = make_state()

        await admin_exit(callback, state)

        state.clear.assert_called_once()
        callback.message.delete.assert_called_once()


class TestAdminDoctors:

    async def test_admin_doctors_list(self, make_callback, make_state):
        """Список врачей в панели"""
        from handlers.admin import admin_doctors

        callback = make_callback(data="admin_doctors", user_id=999999)
        state = make_state()

        doctors = [(1, "Иванов", "Терапевт", "Описание", 1)]

        with patch("handlers.admin.db.is_admin", AsyncMock(return_value=True)), \
             patch("handlers.admin.db.get_all_doctors", AsyncMock(return_value=doctors)):
            await admin_doctors(callback, state)

        callback.message.edit_text.assert_called_once()

    async def test_admin_doctors_no_access(self, make_callback, make_state):
        """Доступ к врачам без прав"""
        from handlers.admin import admin_doctors

        callback = make_callback(data="admin_doctors", user_id=111111)
        state = make_state()

        with patch("handlers.admin.db.is_admin", AsyncMock(return_value=False)):
            await admin_doctors(callback, state)

        callback.answer.assert_called_once()
        assert callback.answer.call_args[1].get("show_alert") is True

    async def test_add_doctor_start(self, make_callback, make_state):
        """Начало добавления врача"""
        from handlers.admin import adm_add_doctor_start

        callback = make_callback(data="adm_add_doctor", user_id=999999)
        state = make_state()

        with patch("handlers.admin.db.is_admin", AsyncMock(return_value=True)):
            await adm_add_doctor_start(callback, state)

        state.set_state.assert_called_once_with(AdminDoctorStates.waiting_name)

    async def test_add_doctor_name_step(self, make_message, make_state):
        """Шаг ввода имени врача"""
        from handlers.admin import adm_doctor_name

        message = make_message(text="Иванов Иван Иванович")
        state = make_state()

        await adm_doctor_name(message, state)

        state.update_data.assert_called_with(doctor_name="Иванов Иван Иванович")
        state.set_state.assert_called_with(AdminDoctorStates.waiting_specialization)

    async def test_add_doctor_spec_step(self, make_message, make_state):
        """Шаг ввода специализации"""
        from handlers.admin import adm_doctor_spec

        message = make_message(text="Терапевт")
        state = make_state()

        await adm_doctor_spec(message, state)

        state.update_data.assert_called_with(doctor_spec="Терапевт")
        state.set_state.assert_called_with(AdminDoctorStates.waiting_description)

    async def test_add_doctor_desc_step_with_text(self, make_message, make_state):
        """Шаг ввода описания с текстом"""
        from handlers.admin import adm_doctor_desc

        message = make_message(text="Опытный специалист")
        state = make_state()
        state.get_data = AsyncMock(return_value={
            "doctor_name": "Иванов И.И.",
            "doctor_spec": "Терапевт"
        })

        with patch("handlers.admin.db.add_doctor", AsyncMock(return_value=1)):
            await adm_doctor_desc(message, state)

        state.clear.assert_called_once()

    async def test_add_doctor_desc_step_skip(self, make_message, make_state):
        """Шаг ввода описания — пропуск"""
        from handlers.admin import adm_doctor_desc

        message = make_message(text="-")
        state = make_state()
        state.get_data = AsyncMock(return_value={
            "doctor_name": "Иванов И.И.",
            "doctor_spec": "Терапевт"
        })

        with patch("handlers.admin.db.add_doctor", AsyncMock(return_value=1)) as mock_add:
            await adm_doctor_desc(message, state)

        # Описание должно быть пустым
        call_args = mock_add.call_args[0]
        assert call_args[2] == ""

    async def test_toggle_doctor(self, make_callback):
        """Переключение статуса врача"""
        from handlers.admin import adm_toggle_doctor

        callback = make_callback(data="adm_toggle_doc_1", user_id=999999)
        doctor = (1, "Иванов", "Терапевт", "Описание", 0)

        with patch("handlers.admin.db.is_admin", AsyncMock(return_value=True)), \
             patch("handlers.admin.db.toggle_doctor", AsyncMock()), \
             patch("handlers.admin.db.get_doctor", AsyncMock(return_value=doctor)):
            await adm_toggle_doctor(callback)

        callback.answer.assert_called_once()

    async def test_delete_doctor_confirm(self, make_callback):
        """Запрос подтверждения удаления врача"""
        from handlers.admin import adm_delete_doctor_confirm

        callback = make_callback(data="adm_del_doc_1", user_id=999999)
        doctor = (1, "Иванов", "Терапевт", "Описание", 1)

        with patch("handlers.admin.db.is_admin", AsyncMock(return_value=True)), \
             patch("handlers.admin.db.get_doctor", AsyncMock(return_value=doctor)):
            await adm_delete_doctor_confirm(callback)

        callback.message.edit_text.assert_called_once()
        text = callback.message.edit_text.call_args[0][0]
        assert "удалить" in text.lower()

    async def test_delete_doctor_confirmed(self, make_callback):
        """Подтверждённое удаление врача"""
        from handlers.admin import adm_delete_doctor

        callback = make_callback(data="confirm_del_doc_1")

        with patch("handlers.admin.db.delete_doctor", AsyncMock()), \
             patch("handlers.admin.db.get_all_doctors", AsyncMock(return_value=[])):
            await adm_delete_doctor(callback)

        callback.answer.assert_called_once()


class TestAdminServices:

    async def test_admin_services_list(self, make_callback, make_state):
        """Список услуг в панели"""
        from handlers.admin import admin_services

        callback = make_callback(data="admin_services", user_id=999999)
        state = make_state()

        services = [(1, "Лечение", "Описание", 60, 3000.0, 1)]

        with patch("handlers.admin.db.is_admin", AsyncMock(return_value=True)), \
             patch("handlers.admin.db.get_all_services", AsyncMock(return_value=services)):
            await admin_services(callback, state)

        callback.message.edit_text.assert_called_once()

    async def test_add_service_name_step(self, make_message, make_state):
        """Шаг ввода названия услуги"""
        from handlers.admin import adm_service_name

        message = make_message(text="Лечение кариеса")
        state = make_state()

        await adm_service_name(message, state)

        state.update_data.assert_called_with(service_name="Лечение кариеса")
        state.set_state.assert_called_with(AdminServiceStates.waiting_description)

    async def test_add_service_duration_valid(self, make_message, make_state):
        """Корректная длительность услуги"""
        from handlers.admin import adm_service_duration

        message = make_message(text="60")
        state = make_state()

        await adm_service_duration(message, state)

        state.update_data.assert_called_with(service_duration=60)
        state.set_state.assert_called_with(AdminServiceStates.waiting_price)

    async def test_add_service_duration_invalid(self, make_message, make_state):
        """Некорректная длительность"""
        from handlers.admin import adm_service_duration

        message = make_message(text="abc")
        state = make_state()

        await adm_service_duration(message, state)

        state.update_data.assert_not_called()
        state.set_state.assert_not_called()

    async def test_add_service_duration_negative(self, make_message, make_state):
        """Отрицательная длительность"""
        from handlers.admin import adm_service_duration

        message = make_message(text="-10")
        state = make_state()

        await adm_service_duration(message, state)

        state.set_state.assert_not_called()

    @pytest.mark.parametrize("price_input,expected", [
        ("3000", 3000.0),
        ("1500.50", 1500.50),
        ("1500,50", 1500.50),
    ])
    async def test_add_service_price_valid(self, make_message, make_state, price_input, expected):
        """Корректная цена услуги"""
        from handlers.admin import adm_service_price

        message = make_message(text=price_input)
        state = make_state()
        state.get_data = AsyncMock(return_value={
            "service_name": "Лечение",
            "service_desc": "Описание",
            "service_duration": 60
        })

        with patch("handlers.admin.db.add_service", AsyncMock(return_value=1)) as mock_add:
            await adm_service_price(message, state)

        call_args = mock_add.call_args[0]
        assert call_args[3] == expected

    async def test_add_service_price_invalid(self, make_message, make_state):
        """Некорректная цена"""
        from handlers.admin import adm_service_price

        message = make_message(text="not_a_price")
        state = make_state()

        await adm_service_price(message, state)

        state.clear.assert_not_called()


class TestAdminSlots:

    async def test_admin_slots_shows_doctors(self, make_callback, make_state):
        """Управление слотами показывает список врачей"""
        from handlers.admin import admin_slots

        callback = make_callback(data="admin_slots", user_id=999999)
        state = make_state()

        doctors = [(1, "Иванов", "Терапевт", "Описание", 1)]

        with patch("handlers.admin.db.is_admin", AsyncMock(return_value=True)), \
             patch("handlers.admin.db.get_all_doctors", AsyncMock(return_value=doctors)):
            await admin_slots(callback, state)

        callback.message.edit_text.assert_called_once()

    async def test_add_slots_start(self, make_callback, make_state):
        """Начало добавления слотов"""
        from handlers.admin import adm_add_slots_start

        callback = make_callback(data="adm_add_slots_1", user_id=999999)
        state = make_state()

        with patch("handlers.admin.db.is_admin", AsyncMock(return_value=True)):
            await adm_add_slots_start(callback, state)

        state.set_state.assert_called_with(AdminSlotStates.waiting_date)


class TestAdminAppointments:

    async def test_admin_appointments_list(self, make_callback, make_state):
        """Список всех записей"""
        from handlers.admin import admin_appointments

        callback = make_callback(data="admin_appointments", user_id=999999)
        state = make_state()

        appointments = [
            (1, "Петров П.П.", "+7 999", "user", "Иванов", "Лечение",
             "25.12.2024", "10:00", "pending")
        ]

        with patch("handlers.admin.db.is_admin", AsyncMock(return_value=True)), \
             patch("handlers.admin.db.get_all_appointments", AsyncMock(return_value=appointments)):
            await admin_appointments(callback, state)

        callback.message.edit_text.assert_called_once()

    async def test_admin_appointment_detail(self, make_callback):
        """Детали записи"""
        from handlers.admin import adm_appointment_detail

        callback = make_callback(data="adm_apt_1", user_id=999999)

        appointments = [
            (1, "Петров П.П.", "+7 999", "user", "Иванов", "Лечение",
             "25.12.2024", "10:00", "pending")
        ]

        with patch("handlers.admin.db.is_admin", AsyncMock(return_value=True)), \
             patch("handlers.admin.db.get_all_appointments", AsyncMock(return_value=appointments)):
            await adm_appointment_detail(callback)

        callback.message.edit_text.assert_called_once()

    async def test_admin_confirm_appointment(self, make_callback):
        """Подтверждение записи администратором"""
        from handlers.admin import adm_appointment_detail

        callback = make_callback(data="adm_apt_confirm_1", user_id=999999)
        appointments = [
            (1, "Петров П.П.", "+7 999", "user", "Иванов", "Лечение",
             "25.12.2024", "10:00", "pending")
        ]

        with patch("handlers.admin.db.is_admin", AsyncMock(return_value=True)), \
             patch("handlers.admin.db.update_appointment_status", AsyncMock()), \
             patch("handlers.admin.db.get_all_appointments", AsyncMock(return_value=appointments)):
            await adm_appointment_detail(callback)

        callback.answer.assert_called()


class TestAdminAdmins:

    async def test_admin_admins_list(self, make_callback, make_state):
        """Список администраторов"""
        from handlers.admin import admin_admins

        callback = make_callback(data="admin_admins", user_id=999999)
        state = make_state()

        admins = [(999999, "admin_user", "2024-01-01")]

        with patch("handlers.admin.db.is_admin", AsyncMock(return_value=True)), \
             patch("handlers.admin.db.get_all_admins", AsyncMock(return_value=admins)):
            await admin_admins(callback, state)

        callback.message.edit_text.assert_called_once()

    async def test_remove_admin(self, make_callback):
        """Удаление администратора"""
        from handlers.admin import adm_remove_admin

        callback = make_callback(data="adm_remove_admin_111111", user_id=999999)
        admins = [(999999, "admin_user", "2024-01-01")]

        with patch("handlers.admin.db.is_admin", AsyncMock(return_value=True)), \
             patch("handlers.admin.db.remove_admin", AsyncMock()), \
             patch("handlers.admin.db.get_all_admins", AsyncMock(return_value=admins)):
            await adm_remove_admin(callback)

        callback.answer.assert_called_once()

    async def test_cannot_remove_self(self, make_callback):
        """Нельзя удалить самого себя"""
        from handlers.admin import adm_self

        callback = make_callback(data="adm_self", user_id=999999)
        await adm_self(callback)

        callback.answer.assert_called_once()
        assert callback.answer.call_args[1].get("show_alert") is True