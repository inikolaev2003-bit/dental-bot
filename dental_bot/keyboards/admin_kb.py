from aiogram.types import InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def admin_main_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="👨‍⚕️ Врачи", callback_data="admin_doctors")
    builder.button(text="🦷 Услуги", callback_data="admin_services")
    builder.button(text="🕐 Временные слоты", callback_data="admin_slots")
    builder.button(text="📋 Записи", callback_data="admin_appointments")
    builder.button(text="👥 Администраторы", callback_data="admin_admins")
    builder.button(text="🚪 Выйти", callback_data="admin_exit")
    builder.adjust(2)
    return builder.as_markup()


# ===== DOCTORS =====

def admin_doctors_kb(doctors: list) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for doc in doctors:
        doc_id, name, spec, desc, is_active = doc
        status = "✅" if is_active else "❌"
        builder.button(
            text=f"{status} {name} ({spec})",
            callback_data=f"adm_doc_{doc_id}"
        )
    builder.button(text="➕ Добавить врача", callback_data="adm_add_doctor")
    builder.button(text="⬅️ Назад", callback_data="admin_back_main")
    builder.adjust(1)
    return builder.as_markup()


def admin_doctor_detail_kb(doc_id: int, is_active: bool) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✏️ Редактировать", callback_data=f"adm_edit_doc_{doc_id}")
    toggle_text = "🔴 Деактивировать" if is_active else "🟢 Активировать"
    builder.button(text=toggle_text, callback_data=f"adm_toggle_doc_{doc_id}")
    builder.button(text="🗑️ Удалить", callback_data=f"adm_del_doc_{doc_id}")
    builder.button(text="⬅️ Назад", callback_data="admin_doctors")
    builder.adjust(1)
    return builder.as_markup()


def confirm_delete_kb(entity: str, entity_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Да, удалить", callback_data=f"confirm_del_{entity}_{entity_id}")
    builder.button(text="❌ Отмена", callback_data=f"cancel_del_{entity}")
    builder.adjust(2)
    return builder.as_markup()


# ===== SERVICES =====

def admin_services_kb(services: list) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for srv in services:
        srv_id, name, desc, duration, price, is_active = srv
        status = "✅" if is_active else "❌"
        builder.button(
            text=f"{status} {name} — {price}₽",
            callback_data=f"adm_srv_{srv_id}"
        )
    builder.button(text="➕ Добавить услугу", callback_data="adm_add_service")
    builder.button(text="⬅️ Назад", callback_data="admin_back_main")
    builder.adjust(1)
    return builder.as_markup()


def admin_service_detail_kb(srv_id: int, is_active: bool) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✏️ Редактировать", callback_data=f"adm_edit_srv_{srv_id}")
    toggle_text = "🔴 Деактивировать" if is_active else "🟢 Активировать"
    builder.button(text=toggle_text, callback_data=f"adm_toggle_srv_{srv_id}")
    builder.button(text="🗑️ Удалить", callback_data=f"adm_del_srv_{srv_id}")
    builder.button(text="⬅️ Назад", callback_data="admin_services")
    builder.adjust(1)
    return builder.as_markup()


# ===== SLOTS =====

def admin_slots_doctors_kb(doctors: list) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for doc in doctors:
        doc_id, name, *_ = doc
        builder.button(
            text=f"👨‍⚕️ {name}",
            callback_data=f"adm_slots_doc_{doc_id}"
        )
    builder.button(text="⬅️ Назад", callback_data="admin_back_main")
    builder.adjust(1)
    return builder.as_markup()


def admin_slots_kb(slots: list, doctor_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for slot in slots:
        slot_id, slot_date, slot_time, is_available = slot
        status = "🟢" if is_available else "🔴"
        builder.button(
            text=f"{status} {slot_date} {slot_time}",
            callback_data=f"adm_slot_{slot_id}"
        )
    builder.button(text="➕ Добавить слоты", callback_data=f"adm_add_slots_{doctor_id}")
    builder.button(text="⬅️ Назад", callback_data="admin_slots")
    builder.adjust(1)
    return builder.as_markup()


def admin_slot_detail_kb(slot_id: int, is_available: bool) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    toggle_text = "🔴 Закрыть слот" if is_available else "🟢 Открыть слот"
    builder.button(text=toggle_text, callback_data=f"adm_toggle_slot_{slot_id}")
    builder.button(text="🗑️ Удалить", callback_data=f"adm_del_slot_{slot_id}")
    builder.button(text="⬅️ Назад", callback_data="back_to_doctor_slots")
    builder.adjust(1)
    return builder.as_markup()


# ===== APPOINTMENTS =====

def admin_appointments_kb(appointments: list) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    status_map = {"pending": "⏳", "confirmed": "✅", "cancelled": "❌", "completed": "🏁"}
    for apt in appointments:
        apt_id, full_name, phone, username, doctor, service, date, time, status = apt
        emoji = status_map.get(status, "❓")
        builder.button(
            text=f"{emoji} {date} {time} — {full_name}",
            callback_data=f"adm_apt_{apt_id}"
        )
    builder.button(text="⬅️ Назад", callback_data="admin_back_main")
    builder.adjust(1)
    return builder.as_markup()


def admin_appointment_detail_kb(apt_id: int, status: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if status == "pending":
        builder.button(text="✅ Подтвердить", callback_data=f"adm_apt_confirm_{apt_id}")
        builder.button(text="❌ Отменить", callback_data=f"adm_apt_cancel_{apt_id}")
    elif status == "confirmed":
        builder.button(text="🏁 Завершить", callback_data=f"adm_apt_complete_{apt_id}")
        builder.button(text="❌ Отменить", callback_data=f"adm_apt_cancel_{apt_id}")
    builder.button(text="⬅️ Назад", callback_data="admin_appointments")
    builder.adjust(2)
    return builder.as_markup()


# ===== ADMINS =====

def admin_admins_kb(admins: list, current_user_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for admin in admins:
        user_id, username, added_at = admin
        name = f"@{username}" if username else f"ID: {user_id}"
        if user_id != current_user_id:
            builder.button(
                text=f"👤 {name}",
                callback_data=f"adm_remove_admin_{user_id}"
            )
        else:
            builder.button(
                text=f"👑 {name} (вы)",
                callback_data="adm_self"
            )
    builder.button(text="⬅️ Назад", callback_data="admin_back_main")
    builder.adjust(1)
    return builder.as_markup()