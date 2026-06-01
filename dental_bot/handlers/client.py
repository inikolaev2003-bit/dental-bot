from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import CommandStart

import database as db
from keyboards.client_kb import (
    main_menu_kb, doctors_kb, services_kb, slots_kb,
    confirm_kb, my_appointments_kb, appointment_detail_kb
)
from states.client_states import AppointmentStates

router = Router()


# ==================== СТАРТ ====================

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        f"👋 Добро пожаловать в стоматологическую клинику!\n\n"
        f"Меня зовут <b>DentalBot</b> 🦷\n"
        f"Я помогу вам записаться на приём к нашим специалистам.\n\n"
        f"Выберите действие в меню ниже:",
        reply_markup=main_menu_kb(),
        parse_mode="HTML"
    )


@router.message(F.text == "ℹ️ О клинике")
async def about_clinic(message: Message):
    await message.answer(
        "🏥 <b>Стоматологическая клиника «Белая улыбка»</b>\n\n"
        "Мы работаем с 2010 года и предоставляем полный спектр\n"
        "стоматологических услуг для взрослых и детей.\n\n"
        "⏰ <b>Режим работы:</b>\n"
        "Пн-Пт: 9:00 — 20:00\n"
        "Сб: 10:00 — 18:00\n"
        "Вс: выходной\n\n"
        "🏆 <b>Наши преимущества:</b>\n"
        "• Опытные специалисты\n"
        "• Современное оборудование\n"
        "• Комфортная атмосфера\n"
        "• Доступные цены",
        parse_mode="HTML",
        reply_markup=main_menu_kb()
    )


@router.message(F.text == "📞 Контакты")
async def contacts(message: Message):
    await message.answer(
        "📞 <b>Контакты клиники</b>\n\n"
        "📍 Адрес: ул. Примерная, д. 1\n"
        "📱 Телефон: +7 (999) 123-45-67\n"
        "📧 Email: info@dental.ru\n"
        "🌐 Сайт: dental.ru\n\n"
        "Или запишитесь прямо здесь через бота! 😊",
        parse_mode="HTML",
        reply_markup=main_menu_kb()
    )


# ==================== ЗАПИСЬ НА ПРИЁМ ====================

@router.message(F.text == "📅 Записаться на приём")
async def start_appointment(message: Message, state: FSMContext):
    doctors = await db.get_all_doctors(active_only=True)
    if not doctors:
        await message.answer(
            "😔 К сожалению, сейчас нет доступных врачей.\n"
            "Попробуйте позже или свяжитесь с нами по телефону.",
            reply_markup=main_menu_kb()
        )
        return

    await state.set_state(AppointmentStates.choosing_doctor)
    await message.answer(
        "👨‍⚕️ <b>Выберите врача:</b>",
        reply_markup=doctors_kb(doctors),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("doc_"), AppointmentStates.choosing_doctor)
async def choose_doctor(callback: CallbackQuery, state: FSMContext):
    doctor_id = int(callback.data.split("_")[1])
    doctor = await db.get_doctor(doctor_id)
    if not doctor:
        await callback.answer("Врач не найден!", show_alert=True)
        return

    await state.update_data(doctor_id=doctor_id, doctor_name=doctor[1])

    services = await db.get_all_services(active_only=True)
    if not services:
        await callback.message.edit_text(
            "😔 Нет доступных услуг. Попробуйте позже.",
        )
        return

    await state.set_state(AppointmentStates.choosing_service)
    await callback.message.edit_text(
        f"✅ Врач: <b>{doctor[1]}</b> ({doctor[2]})\n\n"
        f"🦷 <b>Выберите услугу:</b>",
        reply_markup=services_kb(services),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "back_to_doctors")
async def back_to_doctors(callback: CallbackQuery, state: FSMContext):
    doctors = await db.get_all_doctors(active_only=True)
    await state.set_state(AppointmentStates.choosing_doctor)
    await callback.message.edit_text(
        "👨‍⚕️ <b>Выберите врача:</b>",
        reply_markup=doctors_kb(doctors),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("srv_"), AppointmentStates.choosing_service)
async def choose_service(callback: CallbackQuery, state: FSMContext):
    service_id = int(callback.data.split("_")[1])
    service = await db.get_service(service_id)
    if not service:
        await callback.answer("Услуга не найдена!", show_alert=True)
        return

    data = await state.get_data()
    await state.update_data(service_id=service_id, service_name=service[1], price=service[4])

    slots = await db.get_slots_by_doctor(data["doctor_id"], available_only=True)
    if not slots:
        await callback.message.edit_text(
            f"😔 У врача <b>{data['doctor_name']}</b> нет свободных слотов.\n"
            f"Выберите другого врача.",
            reply_markup=doctors_kb(await db.get_all_doctors(active_only=True)),
            parse_mode="HTML"
        )
        await state.set_state(AppointmentStates.choosing_doctor)
        return

    await state.set_state(AppointmentStates.choosing_slot)
    await callback.message.edit_text(
        f"✅ Услуга: <b>{service[1]}</b> — {service[4]}₽\n\n"
        f"🕐 <b>Выберите удобное время:</b>",
        reply_markup=slots_kb(slots),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "back_to_services")
async def back_to_services(callback: CallbackQuery, state: FSMContext):
    services = await db.get_all_services(active_only=True)
    await state.set_state(AppointmentStates.choosing_service)
    await callback.message.edit_text(
        "🦷 <b>Выберите услугу:</b>",
        reply_markup=services_kb(services),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("slot_"), AppointmentStates.choosing_slot)
async def choose_slot(callback: CallbackQuery, state: FSMContext):
    slot_id = int(callback.data.split("_")[1])
    slot = await db.get_slot(slot_id)
    if not slot or not slot[4]:
        await callback.answer("Этот слот уже занят!", show_alert=True)
        return

    await state.update_data(slot_id=slot_id, slot_date=slot[2], slot_time=slot[3])
    await state.set_state(AppointmentStates.entering_name)
    await callback.message.edit_text(
        f"✅ Время: <b>{slot[2]} в {slot[3]}</b>\n\n"
        f"👤 Введите ваше <b>ФИО</b>:",
        parse_mode="HTML"
    )


@router.message(AppointmentStates.entering_name)
async def enter_name(message: Message, state: FSMContext):
    name = message.text.strip()
    if len(name) < 3:
        await message.answer("❌ Пожалуйста, введите корректное ФИО (минимум 3 символа).")
        return

    await state.update_data(full_name=name)
    await state.set_state(AppointmentStates.entering_phone)
    await message.answer(
        f"✅ ФИО: <b>{name}</b>\n\n"
        f"📱 Введите ваш <b>номер телефона</b>:",
        parse_mode="HTML"
    )


@router.message(AppointmentStates.entering_phone)
async def enter_phone(message: Message, state: FSMContext):
    phone = message.text.strip()
    # Простая валидация телефона
    cleaned = phone.replace("+", "").replace("-", "").replace(" ", "").replace("(", "").replace(")", "")
    if not cleaned.isdigit() or len(cleaned) < 10:
        await message.answer("❌ Введите корректный номер телефона (например: +7 999 123-45-67)")
        return

    await state.update_data(phone=phone)
    data = await state.get_data()

    await state.set_state(AppointmentStates.confirming)
    await message.answer(
        f"📋 <b>Подтвердите запись:</b>\n\n"
        f"👨‍⚕️ Врач: <b>{data['doctor_name']}</b>\n"
        f"🦷 Услуга: <b>{data['service_name']}</b>\n"
        f"💰 Стоимость: <b>{data['price']}₽</b>\n"
        f"📅 Дата и время: <b>{data['slot_date']} в {data['slot_time']}</b>\n"
        f"👤 ФИО: <b>{data['full_name']}</b>\n"
        f"📱 Телефон: <b>{phone}</b>",
        reply_markup=confirm_kb(),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "confirm_appointment", AppointmentStates.confirming)
async def confirm_appointment(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()

    # Проверяем, что слот ещё свободен
    slot = await db.get_slot(data["slot_id"])
    if not slot or not slot[4]:
        await callback.message.edit_text(
            "😔 К сожалению, этот слот уже занят.\n"
            "Пожалуйста, выберите другое время.",
        )
        await state.clear()
        return

    # Создаём запись
    apt_id = await db.create_appointment(
        user_id=callback.from_user.id,
        username=callback.from_user.username,
        full_name=data["full_name"],
        phone=data["phone"],
        doctor_id=data["doctor_id"],
        service_id=data["service_id"],
        slot_id=data["slot_id"]
    )

    # Бронируем слот
    await db.book_slot(data["slot_id"])
    await state.clear()

    await callback.message.edit_text(
        f"🎉 <b>Запись успешно создана!</b>\n\n"
        f"📋 Номер записи: <b>#{apt_id}</b>\n"
        f"👨‍⚕️ Врач: <b>{data['doctor_name']}</b>\n"
        f"🦷 Услуга: <b>{data['service_name']}</b>\n"
        f"📅 Дата и время: <b>{data['slot_date']} в {data['slot_time']}</b>\n\n"
        f"Мы свяжемся с вами для подтверждения.\n"
        f"Ждём вас! 😊",
        parse_mode="HTML"
    )
    await callback.message.answer("Главное меню:", reply_markup=main_menu_kb())


# ==================== МОИ ЗАПИСИ ====================

@router.message(F.text == "📋 Мои записи")
async def my_appointments(message: Message, state: FSMContext):
    await state.clear()
    appointments = await db.get_user_appointments(message.from_user.id)
    if not appointments:
        await message.answer(
            "📋 У вас пока нет записей.\n"
            "Нажмите «📅 Записаться на приём» чтобы создать запись.",
            reply_markup=main_menu_kb()
        )
        return

    await message.answer(
        "📋 <b>Ваши записи:</b>\n"
        "Нажмите на запись для подробностей:",
        reply_markup=my_appointments_kb(appointments),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("apt_"))
async def appointment_detail(callback: CallbackQuery):
    apt_id = int(callback.data.split("_")[1])
    appointments = await db.get_user_appointments(callback.from_user.id)

    apt = next((a for a in appointments if a[0] == apt_id), None)
    if not apt:
        await callback.answer("Запись не найдена!", show_alert=True)
        return

    apt_id, doctor, service, date, time, status, full_name, phone = apt
    status_text = {
        "pending": "⏳ Ожидает подтверждения",
        "confirmed": "✅ Подтверждена",
        "cancelled": "❌ Отменена",
        "completed": "🏁 Завершена"
    }.get(status, status)

    await callback.message.edit_text(
        f"📋 <b>Запись #{apt_id}</b>\n\n"
        f"👨‍⚕️ Врач: <b>{doctor}</b>\n"
        f"🦷 Услуга: <b>{service}</b>\n"
        f"📅 Дата: <b>{date}</b>\n"
        f"🕐 Время: <b>{time}</b>\n"
        f"📊 Статус: <b>{status_text}</b>",
        reply_markup=appointment_detail_kb(apt_id, status),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("cancel_apt_"))
async def cancel_appointment(callback: CallbackQuery):
    apt_id = int(callback.data.split("_")[2])
    success = await db.cancel_appointment(apt_id, callback.from_user.id)

    if success:
        await callback.message.edit_text(
            f"✅ Запись <b>#{apt_id}</b> успешно отменена.",
            parse_mode="HTML"
        )
        await callback.message.answer("Главное меню:", reply_markup=main_menu_kb())
    else:
        await callback.answer("Не удалось отменить запись!", show_alert=True)


@router.callback_query(F.data == "back_to_appointments")
async def back_to_appointments(callback: CallbackQuery):
    appointments = await db.get_user_appointments(callback.from_user.id)
    if not appointments:
        await callback.message.edit_text("📋 У вас нет записей.")
        return
    await callback.message.edit_text(
        "📋 <b>Ваши записи:</b>",
        reply_markup=my_appointments_kb(appointments),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "main_menu")
async def to_main_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.delete()
    await callback.message.answer("Главное меню:", reply_markup=main_menu_kb())


@router.callback_query(F.data == "cancel")
async def cancel_action(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.delete()
    await callback.message.answer(
        "❌ Действие отменено.",
        reply_markup=main_menu_kb()
    )