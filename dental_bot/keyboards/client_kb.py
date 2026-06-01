from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def main_menu_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📅 Записаться на приём")],
            [KeyboardButton(text="📋 Мои записи")],
            [KeyboardButton(text="ℹ️ О клинике"), KeyboardButton(text="📞 Контакты")],
        ],
        resize_keyboard=True
    )


def doctors_kb(doctors: list) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for doc in doctors:
        doc_id, name, spec, *_ = doc
        builder.button(
            text=f"👨‍⚕️ {name} — {spec}",
            callback_data=f"doc_{doc_id}"
        )
    builder.button(text="❌ Отмена", callback_data="cancel")
    builder.adjust(1)
    return builder.as_markup()


def services_kb(services: list) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for srv in services:
        srv_id, name, desc, duration, price, *_ = srv
        builder.button(
            text=f"🦷 {name} — {price}₽ ({duration} мин)",
            callback_data=f"srv_{srv_id}"
        )
    builder.button(text="⬅️ Назад", callback_data="back_to_doctors")
    builder.button(text="❌ Отмена", callback_data="cancel")
    builder.adjust(1)
    return builder.as_markup()


def slots_kb(slots: list) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for slot in slots:
        slot_id, slot_date, slot_time, _ = slot
        builder.button(
            text=f"🕐 {slot_date} в {slot_time}",
            callback_data=f"slot_{slot_id}"
        )
    builder.button(text="⬅️ Назад", callback_data="back_to_services")
    builder.button(text="❌ Отмена", callback_data="cancel")
    builder.adjust(1)
    return builder.as_markup()


def confirm_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Подтвердить", callback_data="confirm_appointment")
    builder.button(text="❌ Отмена", callback_data="cancel")
    builder.adjust(2)
    return builder.as_markup()


def my_appointments_kb(appointments: list) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for apt in appointments:
        apt_id, doctor, service, date, time, status, *_ = apt
        status_emoji = {"pending": "⏳", "confirmed": "✅", "cancelled": "❌"}.get(status, "❓")
        builder.button(
            text=f"{status_emoji} {date} {time} — {doctor}",
            callback_data=f"apt_{apt_id}"
        )
    builder.button(text="🔙 Главное меню", callback_data="main_menu")
    builder.adjust(1)
    return builder.as_markup()


def appointment_detail_kb(apt_id: int, status: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if status not in ("cancelled", "completed"):
        builder.button(text="❌ Отменить запись", callback_data=f"cancel_apt_{apt_id}")
    builder.button(text="⬅️ Назад", callback_data="back_to_appointments")
    builder.adjust(1)
    return builder.as_markup()