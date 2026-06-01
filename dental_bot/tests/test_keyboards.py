import pytest
from aiogram.types import InlineKeyboardMarkup, ReplyKeyboardMarkup

from keyboards.client_kb import (
    main_menu_kb, doctors_kb, services_kb,
    slots_kb, confirm_kb, my_appointments_kb, appointment_detail_kb
)
from keyboards.admin_kb import (
    admin_main_kb, admin_doctors_kb, admin_doctor_detail_kb,
    confirm_delete_kb, admin_services_kb, admin_service_detail_kb,
    admin_slots_doctors_kb, admin_slots_kb, admin_slot_detail_kb,
    admin_appointments_kb, admin_appointment_detail_kb, admin_admins_kb
)


class TestClientKeyboards:

    def test_main_menu_kb_type(self):
        """Главное меню — ReplyKeyboard"""
        kb = main_menu_kb()
        assert isinstance(kb, ReplyKeyboardMarkup)

    def test_main_menu_kb_has_buttons(self):
        """Главное меню содержит кнопки"""
        kb = main_menu_kb()
        all_buttons = [btn.text for row in kb.keyboard for btn in row]
        assert "📅 Записаться на приём" in all_buttons
        assert "📋 Мои записи" in all_buttons

    def test_doctors_kb_empty(self):
        """Клавиатура врачей без врачей содержит только отмену"""
        kb = doctors_kb([])
        assert isinstance(kb, InlineKeyboardMarkup)
        buttons = [btn.callback_data for row in kb.inline_keyboard for btn in row]
        assert "cancel" in buttons

    def test_doctors_kb_with_doctors(self):
        """Клавиатура врачей содержит кнопки для каждого врача"""
        doctors = [
            (1, "Иванов", "Терапевт", "Описание", 1),
            (2, "Петров", "Хирург", "Описание", 1),
        ]
        kb = doctors_kb(doctors)
        buttons = [btn.callback_data for row in kb.inline_keyboard for btn in row]
        assert "doc_1" in buttons
        assert "doc_2" in buttons

    def test_services_kb_with_services(self):
        """Клавиатура услуг содержит кнопки"""
        services = [(1, "Лечение", "Описание", 60, 3000.0, 1)]
        kb = services_kb(services)
        buttons = [btn.callback_data for row in kb.inline_keyboard for btn in row]
        assert "srv_1" in buttons
        assert "back_to_doctors" in buttons

    def test_slots_kb_with_slots(self):
        """Клавиатура слотов содержит кнопки"""
        slots = [(1, "25.12.2024", "10:00", 1)]
        kb = slots_kb(slots)
        buttons = [btn.callback_data for row in kb.inline_keyboard for btn in row]
        assert "slot_1" in buttons
        assert "back_to_services" in buttons

    def test_confirm_kb_has_both_buttons(self):
        """Клавиатура подтверждения имеет обе кнопки"""
        kb = confirm_kb()
        buttons = [btn.callback_data for row in kb.inline_keyboard for btn in row]
        assert "confirm_appointment" in buttons
        assert "cancel" in buttons

    def test_my_appointments_kb(self):
        """Клавиатура записей пользователя"""
        appointments = [
            (1, "Иванов", "Лечение", "25.12.2024", "10:00", "pending", "Петров", "+7 999")
        ]
        kb = my_appointments_kb(appointments)
        buttons = [btn.callback_data for row in kb.inline_keyboard for btn in row]
        assert "apt_1" in buttons

    def test_appointment_detail_kb_pending(self):
        """Детали записи — статус pending"""
        kb = appointment_detail_kb(1, "pending")
        buttons = [btn.callback_data for row in kb.inline_keyboard for btn in row]
        assert "cancel_apt_1" in buttons

    def test_appointment_detail_kb_cancelled(self):
        """Детали отменённой записи — нет кнопки отмены"""
        kb = appointment_detail_kb(1, "cancelled")
        buttons = [btn.callback_data for row in kb.inline_keyboard for btn in row]
        assert "cancel_apt_1" not in buttons

    def test_appointment_detail_kb_completed(self):
        """Детали завершённой записи — нет кнопки отмены"""
        kb = appointment_detail_kb(1, "completed")
        buttons = [btn.callback_data for row in kb.inline_keyboard for btn in row]
        assert "cancel_apt_1" not in buttons


class TestAdminKeyboards:

    def test_admin_main_kb_sections(self):
        """Главное меню админа содержит все разделы"""
        kb = admin_main_kb()
        buttons = [btn.callback_data for row in kb.inline_keyboard for btn in row]
        assert "admin_doctors" in buttons
        assert "admin_services" in buttons
        assert "admin_slots" in buttons
        assert "admin_appointments" in buttons
        assert "admin_admins" in buttons
        assert "admin_exit" in buttons

    def test_admin_doctors_kb_with_doctors(self):
        """Клавиатура врачей в панели"""
        doctors = [(1, "Иванов", "Терапевт", "Описание", 1)]
        kb = admin_doctors_kb(doctors)
        buttons = [btn.callback_data for row in kb.inline_keyboard for btn in row]
        assert "adm_doc_1" in buttons
        assert "adm_add_doctor" in buttons
        assert "admin_back_main" in buttons

    def test_admin_doctor_detail_kb_active(self):
        """Детали активного врача"""
        kb = admin_doctor_detail_kb(1, True)
        buttons = [btn.callback_data for row in kb.inline_keyboard for btn in row]
        assert "adm_edit_doc_1" in buttons
        assert "adm_toggle_doc_1" in buttons
        assert "adm_del_doc_1" in buttons

        texts = [btn.text for row in kb.inline_keyboard for btn in row]
        assert any("Деактивировать" in t for t in texts)

    def test_admin_doctor_detail_kb_inactive(self):
        """Детали неактивного врача"""
        kb = admin_doctor_detail_kb(1, False)
        texts = [btn.text for row in kb.inline_keyboard for btn in row]
        assert any("Активировать" in t for t in texts)

    def test_confirm_delete_kb(self):
        """Клавиатура подтверждения удаления"""
        kb = confirm_delete_kb("doc", 1)
        buttons = [btn.callback_data for row in kb.inline_keyboard for btn in row]
        assert "confirm_del_doc_1" in buttons
        assert "cancel_del_doc" in buttons

    def test_admin_services_kb(self):
        """Клавиатура услуг в панели"""
        services = [(1, "Лечение", "Описание", 60, 3000.0, 1)]
        kb = admin_services_kb(services)
        buttons = [btn.callback_data for row in kb.inline_keyboard for btn in row]
        assert "adm_srv_1" in buttons
        assert "adm_add_service" in buttons

    def test_admin_service_detail_kb(self):
        """Детали услуги"""
        kb = admin_service_detail_kb(1, True)
        buttons = [btn.callback_data for row in kb.inline_keyboard for btn in row]
        assert "adm_edit_srv_1" in buttons
        assert "adm_toggle_srv_1" in buttons
        assert "adm_del_srv_1" in buttons

    def test_admin_slots_kb_with_slots(self):
        """Клавиатура слотов в панели"""
        slots = [
            (1, "25.12.2024", "10:00", 1),
            (2, "25.12.2024", "11:00", 0),
        ]
        kb = admin_slots_kb(slots, doctor_id=1)
        buttons = [btn.callback_data for row in kb.inline_keyboard for btn in row]
        assert "adm_slot_1" in buttons
        assert "adm_slot_2" in buttons
        assert "adm_add_slots_1" in buttons

    def test_admin_slot_detail_kb_available(self):
        """Детали доступного слота"""
        kb = admin_slot_detail_kb(1, True)
        texts = [btn.text for row in kb.inline_keyboard for btn in row]
        assert any("Закрыть" in t for t in texts)

    def test_admin_slot_detail_kb_unavailable(self):
        """Детали недоступного слота"""
        kb = admin_slot_detail_kb(1, False)
        texts = [btn.text for row in kb.inline_keyboard for btn in row]
        assert any("Открыть" in t for t in texts)

    def test_admin_appointments_kb_status_icons(self):
        """Иконки статусов в записях"""
        appointments = [
            (1, "Петров", "+7 999", "user", "Иванов", "Лечение", "25.12.2024", "10:00", "pending"),
            (2, "Сидоров", "+7 888", "user2", "Иванов", "Лечение", "26.12.2024", "11:00", "confirmed"),
        ]
        kb = admin_appointments_kb(appointments)
        texts = [btn.text for row in kb.inline_keyboard for btn in row]
        assert any("⏳" in t for t in texts)
        assert any("✅" in t for t in texts)

    def test_admin_appointment_detail_kb_pending(self):
        """Кнопки для записи в статусе pending"""
        kb = admin_appointment_detail_kb(1, "pending")
        buttons = [btn.callback_data for row in kb.inline_keyboard for btn in row]
        assert "adm_apt_confirm_1" in buttons
        assert "adm_apt_cancel_1" in buttons

    def test_admin_appointment_detail_kb_confirmed(self):
        """Кнопки для подтверждённой записи"""
        kb = admin_appointment_detail_kb(1, "confirmed")
        buttons = [btn.callback_data for row in kb.inline_keyboard for btn in row]
        assert "adm_apt_complete_1" in buttons
        assert "adm_apt_cancel_1" in buttons

    def test_admin_admins_kb_self_marked(self):
        """Текущий пользователь помечен в списке"""
        admins = [
            (999999, "admin_user", "2024-01-01"),
            (111111, "other_admin", "2024-01-02"),
        ]
        kb = admin_admins_kb(admins, current_user_id=999999)
        texts = [btn.text for row in kb.inline_keyboard for btn in row]
        assert any("вы" in t.lower() for t in texts)

    def test_admin_admins_kb_self_not_removable(self):
        """Текущий пользователь не может удалить себя через кнопку"""
        admins = [(999999, "admin_user", "2024-01-01")]
        kb = admin_admins_kb(admins, current_user_id=999999)
        buttons = [btn.callback_data for row in kb.inline_keyboard for btn in row]
        assert "adm_remove_admin_999999" not in buttons
        assert "adm_self" in buttons