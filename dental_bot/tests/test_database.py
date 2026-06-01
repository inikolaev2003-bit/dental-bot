import pytest
import aiosqlite
from datetime import datetime, timedelta

import database


@pytest.fixture(autouse=True)
async def setup_db(initialized_db):
    """Автоматически инициализирует БД перед каждым тестом"""
    pass


# ТЕСТЫ ИНИЦИАЛИЗАЦИИ

class TestDatabaseInit:

    async def test_init_creates_tables(self, initialized_db):
        """Проверяет создание всех таблиц"""
        async with aiosqlite.connect(initialized_db) as conn:
            async with conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ) as cursor:
                tables = {row[0] for row in await cursor.fetchall()}

        expected_tables = {"admins", "doctors", "services", "time_slots", "appointments"}
        assert expected_tables.issubset(tables)

    async def test_init_idempotent(self, initialized_db):
        """Повторная инициализация не ломает БД"""
        await database.init_db()
        await database.init_db()

        async with aiosqlite.connect(initialized_db) as conn:
            async with conn.execute(
                "SELECT COUNT(*) FROM sqlite_master WHERE type='table'"
            ) as cursor:
                count = (await cursor.fetchone())[0]
        assert count >= 5


# ТЕСТЫ АДМИНИСТРАТОРОВ

class TestAdminOperations:

    async def test_add_admin(self):
        """Добавление нового администратора"""
        await database.add_admin(999999, "test_admin")
        assert await database.is_admin(999999) is True

    async def test_add_admin_duplicate(self):
        """Повторное добавление не вызывает ошибку"""
        await database.add_admin(999999, "test_admin")
        await database.add_admin(999999, "test_admin")  # Не должно упасть
        assert await database.is_admin(999999) is True

    async def test_is_admin_returns_false_for_unknown(self):
        """Неизвестный пользователь не является админом"""
        assert await database.is_admin(0) is False

    async def test_remove_admin(self):
        """Удаление администратора"""
        await database.add_admin(999999, "test_admin")
        await database.remove_admin(999999)
        assert await database.is_admin(999999) is False

    async def test_remove_nonexistent_admin(self):
        """Удаление несуществующего админа не вызывает ошибку"""
        await database.remove_admin(0)  # Не должно упасть

    async def test_get_all_admins_empty(self):
        """Список администраторов пуст изначально"""
        admins = await database.get_all_admins()
        assert admins == []

    async def test_get_all_admins(self):
        """Получение списка всех администраторов"""
        await database.add_admin(111, "admin1")
        await database.add_admin(222, "admin2")
        admins = await database.get_all_admins()
        assert len(admins) == 2
        user_ids = {a[0] for a in admins}
        assert {111, 222} == user_ids

    async def test_admin_without_username(self):
        """Добавление администратора без username"""
        await database.add_admin(333, None)
        assert await database.is_admin(333) is True


# ТЕСТЫ ВРАЧЕЙ

class TestDoctorOperations:

    async def test_add_doctor(self):
        """Добавление врача"""
        doc_id = await database.add_doctor("Иванов И.И.", "Терапевт", "Описание")
        assert doc_id is not None
        assert doc_id > 0

    async def test_add_doctor_without_description(self):
        """Добавление врача без описания"""
        doc_id = await database.add_doctor("Петров П.П.", "Хирург")
        assert doc_id is not None

    async def test_get_doctor(self):
        """Получение врача по ID"""
        doc_id = await database.add_doctor("Сидоров С.С.", "Ортодонт", "Специалист")
        doctor = await database.get_doctor(doc_id)

        assert doctor is not None
        assert doctor[0] == doc_id
        assert doctor[1] == "Сидоров С.С."
        assert doctor[2] == "Ортодонт"
        assert doctor[3] == "Специалист"
        assert doctor[4] == 1  # is_active

    async def test_get_nonexistent_doctor(self):
        """Получение несуществующего врача"""
        doctor = await database.get_doctor(99999)
        assert doctor is None

    async def test_get_all_doctors_empty(self):
        """Список врачей пуст изначально"""
        doctors = await database.get_all_doctors()
        assert doctors == []

    async def test_get_all_doctors(self):
        """Получение всех врачей"""
        await database.add_doctor("Врач 1", "Терапевт")
        await database.add_doctor("Врач 2", "Хирург")
        doctors = await database.get_all_doctors()
        assert len(doctors) == 2

    async def test_get_active_doctors_only(self):
        """Фильтрация только активных врачей"""
        doc_id = await database.add_doctor("Врач 1", "Терапевт")
        await database.add_doctor("Врач 2", "Хирург")
        await database.toggle_doctor(doc_id)  # Деактивируем первого

        active = await database.get_all_doctors(active_only=True)
        assert len(active) == 1
        assert active[0][1] == "Врач 2"

    async def test_toggle_doctor_deactivate(self):
        """Деактивация врача"""
        doc_id = await database.add_doctor("Врач", "Терапевт")
        await database.toggle_doctor(doc_id)
        doctor = await database.get_doctor(doc_id)
        assert doctor[4] == 0  # is_active = False

    async def test_toggle_doctor_reactivate(self):
        """Повторная активация врача"""
        doc_id = await database.add_doctor("Врач", "Терапевт")
        await database.toggle_doctor(doc_id)
        await database.toggle_doctor(doc_id)
        doctor = await database.get_doctor(doc_id)
        assert doctor[4] == 1  # is_active = True

    async def test_update_doctor(self):
        """Обновление данных врача"""
        doc_id = await database.add_doctor("Старое имя", "Старая спец", "Старое описание")
        await database.update_doctor(doc_id, "Новое имя", "Новая спец", "Новое описание")
        doctor = await database.get_doctor(doc_id)

        assert doctor[1] == "Новое имя"
        assert doctor[2] == "Новая спец"
        assert doctor[3] == "Новое описание"

    async def test_delete_doctor(self):
        """Удаление врача"""
        doc_id = await database.add_doctor("Врач", "Терапевт")
        await database.delete_doctor(doc_id)
        doctor = await database.get_doctor(doc_id)
        assert doctor is None

    async def test_delete_nonexistent_doctor(self):
        """Удаление несуществующего врача не вызывает ошибку"""
        await database.delete_doctor(99999)  # Не должно упасть


# ТЕСТЫ УСЛУГ

class TestServiceOperations:

    async def test_add_service(self):
        """Добавление услуги"""
        srv_id = await database.add_service("Лечение кариеса", "Описание", 60, 3000.0)
        assert srv_id is not None
        assert srv_id > 0

    async def test_get_service(self):
        """Получение услуги по ID"""
        srv_id = await database.add_service("Отбеливание", "Проф. отбеливание", 90, 5000.0)
        service = await database.get_service(srv_id)

        assert service is not None
        assert service[0] == srv_id
        assert service[1] == "Отбеливание"
        assert service[2] == "Проф. отбеливание"
        assert service[3] == 90
        assert service[4] == 5000.0
        assert service[5] == 1  # is_active

    async def test_get_nonexistent_service(self):
        """Получение несуществующей услуги"""
        service = await database.get_service(99999)
        assert service is None

    async def test_get_all_services(self):
        """Получение всех услуг"""
        await database.add_service("Услуга 1", "", 30, 1000.0)
        await database.add_service("Услуга 2", "", 60, 2000.0)
        services = await database.get_all_services()
        assert len(services) == 2

    async def test_get_active_services_only(self):
        """Фильтрация только активных услуг"""
        srv_id = await database.add_service("Услуга 1", "", 30, 1000.0)
        await database.add_service("Услуга 2", "", 60, 2000.0)
        await database.toggle_service(srv_id)

        active = await database.get_all_services(active_only=True)
        assert len(active) == 1
        assert active[0][1] == "Услуга 2"

    async def test_toggle_service(self):
        """Переключение статуса услуги"""
        srv_id = await database.add_service("Услуга", "", 30, 1000.0)
        await database.toggle_service(srv_id)
        service = await database.get_service(srv_id)
        assert service[5] == 0

        await database.toggle_service(srv_id)
        service = await database.get_service(srv_id)
        assert service[5] == 1

    async def test_update_service(self):
        """Обновление услуги"""
        srv_id = await database.add_service("Старое", "Старое описание", 30, 1000.0)
        await database.update_service(srv_id, "Новое", "Новое описание", 60, 2000.0)
        service = await database.get_service(srv_id)

        assert service[1] == "Новое"
        assert service[2] == "Новое описание"
        assert service[3] == 60
        assert service[4] == 2000.0

    async def test_delete_service(self):
        """Удаление у��луги"""
        srv_id = await database.add_service("Услуга", "", 30, 1000.0)
        await database.delete_service(srv_id)
        assert await database.get_service(srv_id) is None

    async def test_service_price_decimal(self):
        """Цена с копейками"""
        srv_id = await database.add_service("Услуга", "", 30, 1500.50)
        service = await database.get_service(srv_id)
        assert float(service[4]) == 1500.50


# ТЕСТЫ ВРЕМЕННЫХ СЛОТОВ

class TestTimeSlotOperations:

    @pytest.fixture(autouse=True)
    async def setup_doctor(self):
        """Создаёт врача для тестов слотов"""
        self.doc_id = await database.add_doctor("Тестовый Врач", "Терапевт")

    async def test_add_time_slot(self):
        """Добавление временного слота"""
        slot_id = await database.add_time_slot(self.doc_id, "25.12.2024", "10:00")
        assert slot_id is not None
        assert slot_id > 0

    async def test_add_duplicate_slot_returns_none(self):
        """Дублирующийся слот не добавляется"""
        await database.add_time_slot(self.doc_id, "25.12.2024", "10:00")
        result = await database.add_time_slot(self.doc_id, "25.12.2024", "10:00")
        assert result is None

    async def test_get_slot(self):
        """Получение слота по ID"""
        slot_id = await database.add_time_slot(self.doc_id, "25.12.2024", "10:00")
        slot = await database.get_slot(slot_id)

        assert slot is not None
        assert slot[0] == slot_id
        assert slot[1] == self.doc_id
        assert slot[2] == "25.12.2024"
        assert slot[3] == "10:00"
        assert slot[4] == 1  # is_available

    async def test_get_nonexistent_slot(self):
        """Получение несуществующего слота"""
        slot = await database.get_slot(99999)
        assert slot is None

    async def test_get_slots_by_doctor(self):
        """Получение слотов врача"""
        await database.add_time_slot(self.doc_id, "25.12.2024", "09:00")
        await database.add_time_slot(self.doc_id, "25.12.2024", "10:00")
        await database.add_time_slot(self.doc_id, "25.12.2024", "11:00")

        slots = await database.get_slots_by_doctor(self.doc_id)
        assert len(slots) == 3

    async def test_toggle_slot(self):
        """Переключение доступности слота"""
        slot_id = await database.add_time_slot(self.doc_id, "25.12.2024", "10:00")
        await database.toggle_slot(slot_id)
        slot = await database.get_slot(slot_id)
        assert slot[4] == 0

        await database.toggle_slot(slot_id)
        slot = await database.get_slot(slot_id)
        assert slot[4] == 1

    async def test_book_slot(self):
        """Бронирование слота"""
        slot_id = await database.add_time_slot(self.doc_id, "25.12.2024", "10:00")
        await database.book_slot(slot_id)
        slot = await database.get_slot(slot_id)
        assert slot[4] == 0  # is_available = False

    async def test_delete_slot(self):
        """Удаление слота"""
        slot_id = await database.add_time_slot(self.doc_id, "25.12.2024", "10:00")
        await database.delete_time_slot(slot_id)
        assert await database.get_slot(slot_id) is None

    async def test_same_time_different_doctors(self):
        """Одинаковое время для разных врачей"""
        doc_id2 = await database.add_doctor("Второй Врач", "Хирург")
        slot1 = await database.add_time_slot(self.doc_id, "25.12.2024", "10:00")
        slot2 = await database.add_time_slot(doc_id2, "25.12.2024", "10:00")
        assert slot1 is not None
        assert slot2 is not None
        assert slot1 != slot2


# ТЕСТЫ ЗАПИСЕЙ

class TestAppointmentOperations:

    @pytest.fixture(autouse=True)
    async def setup_data(self):
        """Создаёт тестовые данные"""
        self.doc_id = await database.add_doctor("Тестовый Врач", "Терапевт")
        self.srv_id = await database.add_service("Лечение", "", 60, 3000.0)
        self.slot_id = await database.add_time_slot(self.doc_id, "25.12.2024", "10:00")

    async def test_create_appointment(self):
        """Создание записи"""
        apt_id = await database.create_appointment(
            user_id=111111,
            username="testuser",
            full_name="Петров П.П.",
            phone="+7 999 000-00-00",
            doctor_id=self.doc_id,
            service_id=self.srv_id,
            slot_id=self.slot_id
        )
        assert apt_id is not None
        assert apt_id > 0

    async def test_get_user_appointments(self):
        """Получение записей пользователя"""
        await database.create_appointment(
            111111, "user", "Петров П.П.", "+7 999 000-00-00",
            self.doc_id, self.srv_id, self.slot_id
        )
        appointments = await database.get_user_appointments(111111)
        assert len(appointments) == 1
        assert appointments[0][6] == "Петров П.П."

    async def test_get_user_appointments_empty(self):
        """Пустой список записей для нового пользователя"""
        appointments = await database.get_user_appointments(999999)
        assert appointments == []

    async def test_get_all_appointments(self):
        """Получение всех записей"""
        slot_id2 = await database.add_time_slot(self.doc_id, "26.12.2024", "11:00")
        await database.create_appointment(
            111111, "user1", "Петров П.П.", "+7 999 000-00-00",
            self.doc_id, self.srv_id, self.slot_id
        )
        await database.create_appointment(
            222222, "user2", "Сидоров С.С.", "+7 888 000-00-00",
            self.doc_id, self.srv_id, slot_id2
        )
        appointments = await database.get_all_appointments()
        assert len(appointments) == 2

    async def test_appointment_default_status_pending(self):
        """Статус новой записи — pending"""
        await database.create_appointment(
            111111, "user", "Петров П.П.", "+7 999 000-00-00",
            self.doc_id, self.srv_id, self.slot_id
        )
        appointments = await database.get_user_appointments(111111)
        assert appointments[0][5] == "pending"

    async def test_update_appointment_status(self):
        """Обновление статуса записи"""
        apt_id = await database.create_appointment(
            111111, "user", "Петров П.П.", "+7 999 000-00-00",
            self.doc_id, self.srv_id, self.slot_id
        )
        await database.update_appointment_status(apt_id, "confirmed")
        appointments = await database.get_user_appointments(111111)
        assert appointments[0][5] == "confirmed"

    async def test_cancel_appointment_frees_slot(self):
        """Отмена записи освобождает слот"""
        apt_id = await database.create_appointment(
            111111, "user", "Петров П.П.", "+7 999 000-00-00",
            self.doc_id, self.srv_id, self.slot_id
        )
        await database.book_slot(self.slot_id)

        # Убеждаемся что слот занят
        slot = await database.get_slot(self.slot_id)
        assert slot[4] == 0

        result = await database.cancel_appointment(apt_id, 111111)
        assert result is True

        # Слот должен освободиться
        slot = await database.get_slot(self.slot_id)
        assert slot[4] == 1

    async def test_cancel_appointment_wrong_user(self):
        """Отмена чужой записи невозможна"""
        apt_id = await database.create_appointment(
            111111, "user", "Петров П.П.", "+7 999 000-00-00",
            self.doc_id, self.srv_id, self.slot_id
        )
        result = await database.cancel_appointment(apt_id, 999999)  # Другой пользователь
        assert result is False

    async def test_cancel_appointment_sets_cancelled_status(self):
        """Отмена устанавливает статус cancelled"""
        apt_id = await database.create_appointment(
            111111, "user", "Петров П.П.", "+7 999 000-00-00",
            self.doc_id, self.srv_id, self.slot_id
        )
        await database.cancel_appointment(apt_id, 111111)
        appointments = await database.get_user_appointments(111111)
        assert appointments[0][5] == "cancelled"

    async def test_appointment_contains_correct_data(self):
        """Запись содержит корректные данные"""
        await database.create_appointment(
            111111, "testuser", "Петров П.П.", "+7 999 000-00-00",
            self.doc_id, self.srv_id, self.slot_id
        )
        appointments = await database.get_user_appointments(111111)
        apt = appointments[0]

        # apt: id, doctor_name, service_name, date, time, status, full_name, phone
        assert apt[1] == "Тестовый Врач"
        assert apt[2] == "Лечение"
        assert apt[3] == "25.12.2024"
        assert apt[4] == "10:00"
        assert apt[6] == "Петров П.П."
        assert apt[7] == "+7 999 000-00-00"
