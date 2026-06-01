from datetime import datetime
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command

import database as db
from config import ADMIN_PASSWORD, ADMIN_COMMAND
from keyboards.admin_kb import (
    admin_main_kb, admin_doctors_kb, admin_doctor_detail_kb,
    confirm_delete_kb, admin_services_kb, admin_service_detail_kb,
    admin_slots_doctors_kb, admin_slots_kb, admin_slot_detail_kb,
    admin_appointments_kb, admin_appointment_detail_kb, admin_admins_kb
)
from keyboards.client_kb import main_menu_kb
from states.admin_states import (
    AdminAuthStates, AdminDoctorStates, AdminServiceStates, AdminSlotStates
)

router = Router()


# ==================== АВТОРИЗАЦИЯ ====================

@router.message(Command("admin"))
async def admin_panel_cmd(message: Message, state: FSMContext):
    if await db.is_admin(message.from_user.id):
        await state.clear()
        await show_admin_panel(message)
    else:
        await state.set_state(AdminAuthStates.waiting_password)
        await message.answer(
            "🔐 <b>Вход в панель администратора</b>\n\n"
            "Введите пароль для доступа:",
            parse_mode="HTML"
        )


@router.message(AdminAuthStates.waiting_password)
async def check_admin_password(message: Message, state: FSMContext):
    await message.delete()  # Удаляем сообщение с паролем
    if message.text == ADMIN_PASSWORD:
        await db.add_admin(message.from_user.id, message.from_user.username)
        await state.clear()
        await message.answer("✅ Пароль верный! Вы добавлены как администратор.")
        await show_admin_panel(message)
    else:
        await state.clear()
        await message.answer(
            "❌ Неверный пароль!\n"
            "Используйте команду /adminpanel для повторной попытки."
        )


async def show_admin_panel(message: Message):
    await message.answer(
        "⚙️ <b>Панель администратора</b>\n\n"
        "Выберите раздел для управления:",
        reply_markup=admin_main_kb(),
        parse_mode="HTML"
    )


# ==================== ГЛАВНОЕ МЕНЮ АДМИНА ====================

@router.callback_query(F.data == "admin_back_main")
async def admin_back_main(callback: CallbackQuery, state: FSMContext):
    if not await db.is_admin(callback.from_user.id):
        await callback.answer("Нет доступа!", show_alert=True)
        return
    await state.clear()
    await callback.message.edit_text(
        "⚙️ <b>Панель администратора</b>\n\nВыберите раздел:",
        reply_markup=admin_main_kb(),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "admin_exit")
async def admin_exit(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.delete()
    await callback.message.answer(
        "👋 Вы вышли из панели администратора.",
        reply_markup=main_menu_kb()
    )


# ==================== ВРАЧИ ====================

@router.callback_query(F.data == "admin_doctors")
async def admin_doctors(callback: CallbackQuery, state: FSMContext):
    if not await db.is_admin(callback.from_user.id):
        await callback.answer("Нет доступа!", show_alert=True)
        return
    await state.clear()
    doctors = await db.get_all_doctors()
    text = "👨‍⚕️ <b>Управление врачами</b>\n\n"
    if not doctors:
        text += "Врачей пока нет."
    else:
        text += f"Всего врачей: {len(doctors)}"

    await callback.message.edit_text(
        text, reply_markup=admin_doctors_kb(doctors), parse_mode="HTML"
    )


@router.callback_query(F.data == "adm_add_doctor")
async def adm_add_doctor_start(callback: CallbackQuery, state: FSMContext):
    if not await db.is_admin(callback.from_user.id):
        await callback.answer("Нет доступа!", show_alert=True)
        return
    await state.set_state(AdminDoctorStates.waiting_name)
    await callback.message.edit_text(
        "➕ <b>Добавление врача</b>\n\nВведите ФИО врача:",
        parse_mode="HTML"
    )


@router.message(AdminDoctorStates.waiting_name)
async def adm_doctor_name(message: Message, state: FSMContext):
    await state.update_data(doctor_name=message.text.strip())
    await state.set_state(AdminDoctorStates.waiting_specialization)
    await message.answer("Введите специализацию врача (например: Терапевт, Хирург, Ортодонт):")


@router.message(AdminDoctorStates.waiting_specialization)
async def adm_doctor_spec(message: Message, state: FSMContext):
    await state.update_data(doctor_spec=message.text.strip())
    await state.set_state(AdminDoctorStates.waiting_description)
    await message.answer("Введите описание врача (или отправьте «-» чтобы пропустить):")


@router.message(AdminDoctorStates.waiting_description)
async def adm_doctor_desc(message: Message, state: FSMContext):
    desc = "" if message.text.strip() == "-" else message.text.strip()
    data = await state.get_data()

    doc_id = await db.add_doctor(data["doctor_name"], data["doctor_spec"], desc)
    await state.clear()

    await message.answer(
        f"✅ <b>Врач добавлен!</b>\n\n"
        f"👨‍⚕️ {data['doctor_name']}\n"
        f"🏥 {data['doctor_spec']}\n"
        f"ID: {doc_id}",
        parse_mode="HTML"
    )
    await show_admin_panel(message)


@router.callback_query(F.data.startswith("adm_doc_"))
async def adm_doctor_detail(callback: CallbackQuery, state: FSMContext):
    if not await db.is_admin(callback.from_user.id):
        await callback.answer("Нет доступа!", show_alert=True)
        return
    doc_id = int(callback.data.split("_")[2])
    doctor = await db.get_doctor(doc_id)
    if not doctor:
        await callback.answer("Врач не найден!", show_alert=True)
        return

    doc_id, name, spec, desc, is_active = doctor
    status = "✅ Активен" if is_active else "❌ Неактивен"

    await callback.message.edit_text(
        f"👨‍⚕️ <b>{name}</b>\n\n"
        f"🏥 Специализация: {spec}\n"
        f"📝 Описание: {desc or 'Не указано'}\n"
        f"📊 Статус: {status}",
        reply_markup=admin_doctor_detail_kb(doc_id, bool(is_active)),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("adm_toggle_doc_"))
async def adm_toggle_doctor(callback: CallbackQuery):
    if not await db.is_admin(callback.from_user.id):
        await callback.answer("Нет доступа!", show_alert=True)
        return
    doc_id = int(callback.data.split("_")[3])
    await db.toggle_doctor(doc_id)
    await callback.answer("✅ Статус врача изменён!")
    # Обновляем отображение
    doctor = await db.get_doctor(doc_id)
    doc_id, name, spec, desc, is_active = doctor
    status = "✅ Активен" if is_active else "❌ Неактивен"
    await callback.message.edit_text(
        f"👨‍⚕️ <b>{name}</b>\n\n"
        f"🏥 Специализация: {spec}\n"
        f"📝 Описание: {desc or 'Не указано'}\n"
        f"📊 Статус: {status}",
        reply_markup=admin_doctor_detail_kb(doc_id, bool(is_active)),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("adm_del_doc_"))
async def adm_delete_doctor_confirm(callback: CallbackQuery):
    if not await db.is_admin(callback.from_user.id):
        await callback.answer("Нет доступа!", show_alert=True)
        return
    doc_id = int(callback.data.split("_")[3])
    doctor = await db.get_doctor(doc_id)
    await callback.message.edit_text(
        f"🗑️ Удалить врача <b>{doctor[1]}</b>?\n\n"
        f"⚠️ Это действие нельзя отменить!",
        reply_markup=confirm_delete_kb("doc", doc_id),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("confirm_del_doc_"))
async def adm_delete_doctor(callback: CallbackQuery):
    doc_id = int(callback.data.split("_")[3])
    await db.delete_doctor(doc_id)
    await callback.answer("✅ Врач удалён!")
    doctors = await db.get_all_doctors()
    await callback.message.edit_text(
        "👨‍⚕️ <b>Управление врачами</b>",
        reply_markup=admin_doctors_kb(doctors),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "cancel_del_doc")
async def cancel_del_doc(callback: CallbackQuery):
    doctors = await db.get_all_doctors()
    await callback.message.edit_text(
        "👨‍⚕️ <b>Управление врачами</b>",
        reply_markup=admin_doctors_kb(doctors),
        parse_mode="HTML"
    )


# Редактирование врача
@router.callback_query(F.data.startswith("adm_edit_doc_"))
async def adm_edit_doctor_start(callback: CallbackQuery, state: FSMContext):
    if not await db.is_admin(callback.from_user.id):
        await callback.answer("Нет доступа!", show_alert=True)
        return
    doc_id = int(callback.data.split("_")[3])
    doctor = await db.get_doctor(doc_id)
    await state.update_data(editing_doc_id=doc_id)
    await state.set_state(AdminDoctorStates.editing_name)
    await callback.message.edit_text(
        f"✏️ <b>Редактирование врача</b>\n\n"
        f"Текущее имя: <b>{doctor[1]}</b>\n"
        f"Введите новое ФИО (или «-» чтобы оставить прежнее):",
        parse_mode="HTML"
    )


@router.message(AdminDoctorStates.editing_name)
async def adm_edit_doctor_name(message: Message, state: FSMContext):
    data = await state.get_data()
    doctor = await db.get_doctor(data["editing_doc_id"])
    new_name = doctor[1] if message.text.strip() == "-" else message.text.strip()
    await state.update_data(new_name=new_name)
    await state.set_state(AdminDoctorStates.editing_specialization)
    await message.answer(
        f"Текущая специализация: <b>{doctor[2]}</b>\n"
        f"Введите новую специализацию (или «-» чтобы оставить прежнее):",
        parse_mode="HTML"
    )


@router.message(AdminDoctorStates.editing_specialization)
async def adm_edit_doctor_spec(message: Message, state: FSMContext):
    data = await state.get_data()
    doctor = await db.get_doctor(data["editing_doc_id"])
    new_spec = doctor[2] if message.text.strip() == "-" else message.text.strip()
    await state.update_data(new_spec=new_spec)
    await state.set_state(AdminDoctorStates.editing_description)
    await message.answer(
        f"Текущее описание: <b>{doctor[3] or 'Не указано'}</b>\n"
        f"Введите новое описание (или «-» чтобы оставить прежнее):",
        parse_mode="HTML"
    )


@router.message(AdminDoctorStates.editing_description)
async def adm_edit_doctor_desc(message: Message, state: FSMContext):
    data = await state.get_data()
    doctor = await db.get_doctor(data["editing_doc_id"])
    new_desc = doctor[3] if message.text.strip() == "-" else message.text.strip()

    await db.update_doctor(data["editing_doc_id"], data["new_name"], data["new_spec"], new_desc)
    await state.clear()
    await message.answer(
        f"✅ <b>Врач обновлён!</b>\n\n"
        f"👨‍⚕️ {data['new_name']}\n"
        f"🏥 {data['new_spec']}",
        parse_mode="HTML"
    )
    await show_admin_panel(message)


# ==================== УСЛУГИ ====================

@router.callback_query(F.data == "admin_services")
async def admin_services(callback: CallbackQuery, state: FSMContext):
    if not await db.is_admin(callback.from_user.id):
        await callback.answer("Нет доступа!", show_alert=True)
        return
    await state.clear()
    services = await db.get_all_services()
    text = "🦷 <b>Управление услугами</b>\n\n"
    text += f"Всего услуг: {len(services)}" if services else "Услуг пока нет."
    await callback.message.edit_text(
        text, reply_markup=admin_services_kb(services), parse_mode="HTML"
    )


@router.callback_query(F.data == "adm_add_service")
async def adm_add_service_start(callback: CallbackQuery, state: FSMContext):
    if not await db.is_admin(callback.from_user.id):
        await callback.answer("Нет доступа!", show_alert=True)
        return
    await state.set_state(AdminServiceStates.waiting_name)
    await callback.message.edit_text(
        "➕ <b>Добавление услуги</b>\n\nВведите название услуги:",
        parse_mode="HTML"
    )


@router.message(AdminServiceStates.waiting_name)
async def adm_service_name(message: Message, state: FSMContext):
    await state.update_data(service_name=message.text.strip())
    await state.set_state(AdminServiceStates.waiting_description)
    await message.answer("Введите описание услуги (или «-» чтобы пропустить):")


@router.message(AdminServiceStates.waiting_description)
async def adm_service_desc(message: Message, state: FSMContext):
    desc = "" if message.text.strip() == "-" else message.text.strip()
    await state.update_data(service_desc=desc)
    await state.set_state(AdminServiceStates.waiting_duration)
    await message.answer("Введите длительность услуги в минутах (например: 30):")


@router.message(AdminServiceStates.waiting_duration)
async def adm_service_duration(message: Message, state: FSMContext):
    try:
        duration = int(message.text.strip())
        if duration <= 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Введите корректное число минут (например: 30):")
        return

    await state.update_data(service_duration=duration)
    await state.set_state(AdminServiceStates.waiting_price)
    await message.answer("Введите стоимость услуги в рублях (например: 1500):")


@router.message(AdminServiceStates.waiting_price)
async def adm_service_price(message: Message, state: FSMContext):
    try:
        price = float(message.text.strip().replace(",", "."))
        if price < 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Введите корректную стоимость (например: 1500):")
        return

    data = await state.get_data()
    srv_id = await db.add_service(
        data["service_name"], data["service_desc"],
        data["service_duration"], price
    )
    await state.clear()

    await message.answer(
        f"✅ <b>Услуга добавлена!</b>\n\n"
        f"🦷 {data['service_name']}\n"
        f"⏱ {data['service_duration']} мин\n"
        f"💰 {price}₽\n"
        f"ID: {srv_id}",
        parse_mode="HTML"
    )
    await show_admin_panel(message)


@router.callback_query(F.data.startswith("adm_srv_"))
async def adm_service_detail(callback: CallbackQuery):
    if not await db.is_admin(callback.from_user.id):
        await callback.answer("Нет доступа!", show_alert=True)
        return
    srv_id = int(callback.data.split("_")[2])
    service = await db.get_service(srv_id)
    if not service:
        await callback.answer("Услуга не найдена!", show_alert=True)
        return

    srv_id, name, desc, duration, price, is_active = service
    status = "✅ Активна" if is_active else "❌ Неактивна"

    await callback.message.edit_text(
        f"🦷 <b>{name}</b>\n\n"
        f"📝 Описание: {desc or 'Не указано'}\n"
        f"⏱ Длительность: {duration} мин\n"
        f"💰 Стоимость: {price}₽\n"
        f"📊 Статус: {status}",
        reply_markup=admin_service_detail_kb(srv_id, bool(is_active)),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("adm_toggle_srv_"))
async def adm_toggle_service(callback: CallbackQuery):
    if not await db.is_admin(callback.from_user.id):
        await callback.answer("Нет доступа!", show_alert=True)
        return
    srv_id = int(callback.data.split("_")[3])
    await db.toggle_service(srv_id)
    await callback.answer("✅ Статус услуги изменён!")
    service = await db.get_service(srv_id)
    srv_id, name, desc, duration, price, is_active = service
    status = "✅ Активна" if is_active else "❌ Неактивна"
    await callback.message.edit_text(
        f"🦷 <b>{name}</b>\n\n"
        f"📝 Описание: {desc or 'Не указано'}\n"
        f"⏱ Длительность: {duration} мин\n"
        f"💰 Стоимость: {price}₽\n"
        f"📊 Статус: {status}",
        reply_markup=admin_service_detail_kb(srv_id, bool(is_active)),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("adm_del_srv_"))
async def adm_delete_service_confirm(callback: CallbackQuery):
    if not await db.is_admin(callback.from_user.id):
        await callback.answer("Нет доступа!", show_alert=True)
        return
    srv_id = int(callback.data.split("_")[3])
    service = await db.get_service(srv_id)
    await callback.message.edit_text(
        f"🗑️ Удалить услугу <b>{service[1]}</b>?\n\n⚠️ Это действие нельзя отменить!",
        reply_markup=confirm_delete_kb("srv", srv_id),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("confirm_del_srv_"))
async def adm_delete_service(callback: CallbackQuery):
    srv_id = int(callback.data.split("_")[3])
    await db.delete_service(srv_id)
    await callback.answer("✅ Услуга удалена!")
    services = await db.get_all_services()
    await callback.message.edit_text(
        "🦷 <b>Управление услугами</b>",
        reply_markup=admin_services_kb(services),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "cancel_del_srv")
async def cancel_del_srv(callback: CallbackQuery):
    services = await db.get_all_services()
    await callback.message.edit_text(
        "🦷 <b>Управление услугами</b>",
        reply_markup=admin_services_kb(services),
        parse_mode="HTML"
    )


# Редактирование услуги
@router.callback_query(F.data.startswith("adm_edit_srv_"))
async def adm_edit_service_start(callback: CallbackQuery, state: FSMContext):
    if not await db.is_admin(callback.from_user.id):
        await callback.answer("Нет доступа!", show_alert=True)
        return
    srv_id = int(callback.data.split("_")[3])
    service = await db.get_service(srv_id)
    await state.update_data(editing_srv_id=srv_id)
    await state.set_state(AdminServiceStates.editing_name)
    await callback.message.edit_text(
        f"✏️ <b>Редактирование услуги</b>\n\n"
        f"Текущее название: <b>{service[1]}</b>\n"
        f"Введите новое название (или «-»):",
        parse_mode="HTML"
    )


@router.message(AdminServiceStates.editing_name)
async def adm_edit_srv_name(message: Message, state: FSMContext):
    data = await state.get_data()
    service = await db.get_service(data["editing_srv_id"])
    new_name = service[1] if message.text.strip() == "-" else message.text.strip()
    await state.update_data(new_name=new_name)
    await state.set_state(AdminServiceStates.editing_description)
    await message.answer(
        f"Текущее описание: <b>{service[2] or 'Не указано'}</b>\n"
        f"Введите новое описание (или «-»):",
        parse_mode="HTML"
    )


@router.message(AdminServiceStates.editing_description)
async def adm_edit_srv_desc(message: Message, state: FSMContext):
    data = await state.get_data()
    service = await db.get_service(data["editing_srv_id"])
    new_desc = service[2] if message.text.strip() == "-" else message.text.strip()
    await state.update_data(new_desc=new_desc)
    await state.set_state(AdminServiceStates.editing_duration)
    await message.answer(
        f"Текущая длительность: <b>{service[3]} мин</b>\n"
        f"Введите новую длительность в минутах (или «-»):",
        parse_mode="HTML"
    )


@router.message(AdminServiceStates.editing_duration)
async def adm_edit_srv_duration(message: Message, state: FSMContext):
    data = await state.get_data()
    service = await db.get_service(data["editing_srv_id"])
    if message.text.strip() == "-":
        new_duration = service[3]
    else:
        try:
            new_duration = int(message.text.strip())
        except ValueError:
            await message.answer("❌ Введите число минут:")
            return
    await state.update_data(new_duration=new_duration)
    await state.set_state(AdminServiceStates.editing_price)
    await message.answer(
        f"Текущая стоимость: <b>{service[4]}₽</b>\n"
        f"Введите новую стоимость (или «-»):",
        parse_mode="HTML"
    )


@router.message(AdminServiceStates.editing_price)
async def adm_edit_srv_price(message: Message, state: FSMContext):
    data = await state.get_data()
    service = await db.get_service(data["editing_srv_id"])
    if message.text.strip() == "-":
        new_price = service[4]
    else:
        try:
            new_price = float(message.text.strip().replace(",", "."))
        except ValueError:
            await message.answer("❌ Введите корректную стоимость:")
            return

    await db.update_service(
        data["editing_srv_id"], data["new_name"],
        data["new_desc"], data["new_duration"], new_price
    )
    await state.clear()
    await message.answer(
        f"✅ <b>Услуга обновлена!</b>\n\n"
        f"🦷 {data['new_name']}\n"
        f"⏱ {data['new_duration']} мин — {new_price}₽",
        parse_mode="HTML"
    )
    await show_admin_panel(message)


# ==================== ВРЕМЕННЫЕ СЛОТЫ ====================

@router.callback_query(F.data == "admin_slots")
async def admin_slots(callback: CallbackQuery, state: FSMContext):
    if not await db.is_admin(callback.from_user.id):
        await callback.answer("Нет доступа!", show_alert=True)
        return
    await state.clear()
    doctors = await db.get_all_doctors(active_only=True)
    await callback.message.edit_text(
        "🕐 <b>Управление временными слотами</b>\n\n"
        "Выберите врача:",
        reply_markup=admin_slots_doctors_kb(doctors),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("adm_slots_doc_"))
async def adm_slots_for_doctor(callback: CallbackQuery, state: FSMContext):
    if not await db.is_admin(callback.from_user.id):
        await callback.answer("Нет доступа!", show_alert=True)
        return
    doc_id = int(callback.data.split("_")[3])
    doctor = await db.get_doctor(doc_id)
    slots = await db.get_slots_by_doctor(doc_id)

    await state.update_data(current_doctor_id=doc_id)

    text = f"🕐 <b>Слоты врача {doctor[1]}</b>\n\n"
    text += f"Всего слотов: {len(slots)}" if slots else "Слотов пока нет."

    await callback.message.edit_text(
        text,
        reply_markup=admin_slots_kb(slots, doc_id),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("adm_add_slots_"))
async def adm_add_slots_start(callback: CallbackQuery, state: FSMContext):
    if not await db.is_admin(callback.from_user.id):
        await callback.answer("Нет доступа!", show_alert=True)
        return
    doc_id = int(callback.data.split("_")[3])
    await state.update_data(adding_slots_doc_id=doc_id)
    await state.set_state(AdminSlotStates.waiting_date)
    await callback.message.edit_text(
        "📅 <b>Добавление слотов</b>\n\n"
        "Введите дату в формате <b>ДД.ММ.ГГГГ</b>\n"
        "Например: 25.12.2026",
        parse_mode="HTML"
    )


@router.message(AdminSlotStates.waiting_date)
async def adm_slot_date(message: Message, state: FSMContext):
    from datetime import datetime
    date_str = message.text.strip()
    try:
        date_obj = datetime.strptime(date_str, "%d.%m.%Y")
        if date_obj.date() < datetime.now().date():
            await message.answer("❌ Нельзя добавить слот на прошедшую дату!")
            return
        formatted_date = date_obj.strftime("%d.%m.%Y")
    except ValueError:
        await message.answer("❌ Неверный формат даты. Введите в формате ДД.ММ.ГГГГ:")
        return

    await state.update_data(slot_date=formatted_date)
    await state.set_state(AdminSlotStates.waiting_times)
    await message.answer(
        f"✅ Дата: <b>{formatted_date}</b>\n\n"
        f"⏰ Введите время(я) через запятую в формате <b>ЧЧ:ММ</b>\n"
        f"Например: <b>09:00, 10:00, 11:30, 14:00</b>",
        parse_mode="HTML"
    )


@router.message(AdminSlotStates.waiting_times)
async def adm_slot_times(message: Message, state: FSMContext):
    times_raw = message.text.strip().split(",")
    data = await state.get_data()

    added = []
    skipped = []
    errors = []

    for t in times_raw:
        t = t.strip()
        try:
            from datetime import datetime
            datetime.strptime(t, "%H:%M")
            result = await db.add_time_slot(data["adding_slots_doc_id"], data["slot_date"], t)
            if result:
                added.append(t)
            else:
                skipped.append(t)
        except ValueError:
            errors.append(t)

    await state.clear()

    text = f"📊 <b>Результат добавления слотов на {data['slot_date']}:</b>\n\n"
    if added:
        text += f"✅ Добавлено: {', '.join(added)}\n"
    if skipped:
        text += f"⚠️ Уже существуют: {', '.join(skipped)}\n"
    if errors:
        text += f"❌ Ошибка формата: {', '.join(errors)}\n"

    await message.answer(text, parse_mode="HTML")
    await show_admin_panel(message)


@router.callback_query(F.data.startswith("adm_slot_"))
async def adm_slot_detail(callback: CallbackQuery, state: FSMContext):
    if not await db.is_admin(callback.from_user.id):
        await callback.answer("Нет доступа!", show_alert=True)
        return
    slot_id = int(callback.data.split("_")[2])
    slot = await db.get_slot(slot_id)
    if not slot:
        await callback.answer("Слот не найден!", show_alert=True)
        return

    slot_id, doc_id, slot_date, slot_time, is_available = slot
    await state.update_data(current_doctor_id=doc_id)

    status = "🟢 Свободен" if is_available else "🔴 Занят/Закрыт"
    doctor = await db.get_doctor(doc_id)

    await callback.message.edit_text(
        f"🕐 <b>Слот #{slot_id}</b>\n\n"
        f"👨‍⚕️ Врач: {doctor[1]}\n"
        f"📅 Дата: {slot_date}\n"
        f"⏰ Время: {slot_time}\n"
        f"📊 Статус: {status}",
        reply_markup=admin_slot_detail_kb(slot_id, bool(is_available)),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("adm_toggle_slot_"))
async def adm_toggle_slot(callback: CallbackQuery, state: FSMContext):
    if not await db.is_admin(callback.from_user.id):
        await callback.answer("Нет доступа!", show_alert=True)
        return
    slot_id = int(callback.data.split("_")[3])
    await db.toggle_slot(slot_id)
    await callback.answer("✅ Статус слота изменён!")
    slot = await db.get_slot(slot_id)
    slot_id, doc_id, slot_date, slot_time, is_available = slot
    status = "🟢 Свободен" if is_available else "🔴 Занят/Закрыт"
    doctor = await db.get_doctor(doc_id)
    await callback.message.edit_text(
        f"🕐 <b>Слот #{slot_id}</b>\n\n"
        f"👨‍⚕️ Врач: {doctor[1]}\n"
        f"📅 Дата: {slot_date}\n"
        f"⏰ Время: {slot_time}\n"
        f"📊 Статус: {status}",
        reply_markup=admin_slot_detail_kb(slot_id, bool(is_available)),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("adm_del_slot_"))
async def adm_delete_slot(callback: CallbackQuery):
    if not await db.is_admin(callback.from_user.id):
        await callback.answer("Нет доступа!", show_alert=True)
        return
    slot_id = int(callback.data.split("_")[3])
    slot = await db.get_slot(slot_id)
    doc_id = slot[1]
    await db.delete_time_slot(slot_id)
    await callback.answer("✅ Слот удалён!")
    slots = await db.get_slots_by_doctor(doc_id)
    doctor = await db.get_doctor(doc_id)
    await callback.message.edit_text(
        f"🕐 <b>Слоты врача {doctor[1]}</b>",
        reply_markup=admin_slots_kb(slots, doc_id),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "back_to_doctor_slots")
async def back_to_doctor_slots(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    doc_id = data.get("current_doctor_id")
    if not doc_id:
        await admin_slots(callback, state)
        return
    doctor = await db.get_doctor(doc_id)
    slots = await db.get_slots_by_doctor(doc_id)
    await callback.message.edit_text(
        f"🕐 <b>Слоты врача {doctor[1]}</b>",
        reply_markup=admin_slots_kb(slots, doc_id),
        parse_mode="HTML"
    )


# ==================== ЗАПИСИ ====================

@router.callback_query(F.data == "admin_appointments")
async def admin_appointments(callback: CallbackQuery, state: FSMContext):
    if not await db.is_admin(callback.from_user.id):
        await callback.answer("Нет доступа!", show_alert=True)
        return
    await state.clear()
    appointments = await db.get_all_appointments()
    text = "📋 <b>Все записи</b>\n\n"
    text += f"Всего: {len(appointments)}" if appointments else "Записей пока нет."
    await callback.message.edit_text(
        text,
        reply_markup=admin_appointments_kb(appointments),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("adm_apt_"))
async def adm_appointment_detail(callback: CallbackQuery):
    if not await db.is_admin(callback.from_user.id):
        await callback.answer("Нет доступа!", show_alert=True)
        return

    parts = callback.data.split("_")

    # Обработка действий: adm_apt_confirm_ID, adm_apt_cancel_ID, adm_apt_complete_ID
    if len(parts) == 4:
        action = parts[2]
        apt_id = int(parts[3])
        status_map = {"confirm": "confirmed", "cancel": "cancelled", "complete": "completed"}
        new_status = status_map.get(action)
        if new_status:
            await db.update_appointment_status(apt_id, new_status)
            if new_status == "cancelled":
                # Освобождаем слот
                appointments = await db.get_all_appointments()
                apt = next((a for a in appointments if a[0] == apt_id), None)
            await callback.answer(f"✅ Статус обновлён!")
            appointments = await db.get_all_appointments()
            await callback.message.edit_text(
                "📋 <b>Все записи</b>",
                reply_markup=admin_appointments_kb(appointments),
                parse_mode="HTML"
            )
            return

    # Просмотр деталей: adm_apt_ID
    apt_id = int(parts[2])
    appointments = await db.get_all_appointments()
    apt = next((a for a in appointments if a[0] == apt_id), None)
    if not apt:
        await callback.answer("Запись не найдена!", show_alert=True)
        return

    apt_id, full_name, phone, username, doctor, service, date, time, status = apt
    status_text = {
        "pending": "⏳ Ожидает",
        "confirmed": "✅ Подтверждена",
        "cancelled": "❌ Отменена",
        "completed": "🏁 Завершена"
    }.get(status, status)

    user_info = f"@{username}" if username else f"ID: {apt[0]}"

    await callback.message.edit_text(
        f"📋 <b>Запись #{apt_id}</b>\n\n"
        f"👤 Клиент: <b>{full_name}</b>\n"
        f"📱 Телефон: <b>{phone}</b>\n"
        f"💬 Telegram: {user_info}\n"
        f"👨‍⚕️ Врач: <b>{doctor}</b>\n"
        f"🦷 Услуга: <b>{service}</b>\n"
        f"📅 Дата: <b>{date}</b>\n"
        f"🕐 Время: <b>{time}</b>\n"
        f"📊 Статус: <b>{status_text}</b>",
        reply_markup=admin_appointment_detail_kb(apt_id, status),
        parse_mode="HTML"
    )


# ==================== АДМИНИСТРАТОРЫ ====================

@router.callback_query(F.data == "admin_admins")
async def admin_admins(callback: CallbackQuery, state: FSMContext):
    if not await db.is_admin(callback.from_user.id):
        await callback.answer("Нет доступа!", show_alert=True)
        return
    await state.clear()
    admins = await db.get_all_admins()
    await callback.message.edit_text(
        f"👥 <b>Администраторы</b>\n\n"
        f"Всего: {len(admins)}\n\n"
        f"Нажмите на администратора чтобы удалить его.\n"
        f"Для добавления нового — поделитесь паролем и командой /admin",
        reply_markup=admin_admins_kb(admins, callback.from_user.id),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("adm_remove_admin_"))
async def adm_remove_admin(callback: CallbackQuery):
    if not await db.is_admin(callback.from_user.id):
        await callback.answer("Нет доступа!", show_alert=True)
        return
    target_id = int(callback.data.split("_")[3])
    await db.remove_admin(target_id)
    await callback.answer("✅ Администратор удалён!")
    admins = await db.get_all_admins()
    await callback.message.edit_text(
        f"👥 <b>Администраторы</b>\n\nВсего: {len(admins)}",
        reply_markup=admin_admins_kb(admins, callback.from_user.id),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "adm_self")
async def adm_self(callback: CallbackQuery):
    await callback.answer("Это вы! Нельзя удалить самого себя.", show_alert=True)