import pytest
from unittest.mock import AsyncMock, MagicMock, patch

import database


class TestFullAppointmentFlow:
    """Интеграционные тесты полного цикла записи"""

    @pytest.fixture(autouse=True)
    async def setup(self, initialized_db):
        """Подготовка данных для интеграционных тестов"""
        self.doc_id = await database.add_doctor(
            "Иванов Иван Иванович", "Терапевт", "Опытный специалист"
        )
        self.srv_id = await database.add_service(
            "Лечение кариеса", "Профессиональное лечение", 60, 3000.0
        )
        self.slot_id = await database.add_time_slot(
            self.doc_id, "25.12.2024", "10:00"
        )

    async def test_full_booking_cycle(self):
        """Полный цикл: создание → бронирование → отмена"""
        # 1. Слот доступен
        slot = await database.get_slot(self.slot_id)
        assert slot[4] == 1

        # 2. Создаём запись
        apt_id = await database.create_appointment(
            user_id=111111,
            username="testuser",
            full_name="Петров Пётр Петрович",
            phone="+7 999 123-45-67",
            doctor_id=self.doc_id,
            service_id=self.srv_id,
            slot_id=self.slot_id
        )
        assert apt_id is not None

        # 3. Бронируем слот
        await database.book_slot(self.slot_id)
        slot = await database.get_slot(self.slot_id)
        assert slot[4] == 0  # Занят

        # 4. Слот недоступен для других
        available = await database.get_slots_by_doctor(self.doc_id, available_only=True)
        assert len(available) == 0

        # 5. Отменяем запись
        result = await database.cancel_appointment(apt_id, 111111)
        assert result is True

        # 6. Слот снова доступен
        slot = await database.get_slot(self.slot_id)
        assert slot[4] == 1

    async def test_admin_full_management_cycle(self):
        """Полный цикл управления через панель администратора"""
        # 1. Добавляем администратора
        await database.add_admin(999999, "admin")
        assert await database.is_admin(999999) is True

        # 2. Добавляем врача
        doc_id = await database.add_doctor("Новый Врач", "Хирург", "Специалист")
        doctor = await database.get_doctor(doc_id)
        assert doctor[4] == 1  # Активен

        # 3. Деактивируем врача
        await database.toggle_doctor(doc_id)
        doctor = await database.get_doctor(doc_id)
        assert doctor[4] == 0  # Неактивен

        # 4. Врач не отображается в активных
        active = await database.get_all_doctors(active_only=True)
        doc_ids = [d[0] for d in active]
        assert doc_id not in doc_ids

        # 5. Активируем снова
        await database.toggle_doctor(doc_id)
        doctor = await database.get_doctor(doc_id)
        assert doctor[4] == 1

        # 6. Удаляем врача
        await database.delete_doctor(doc_id)
        assert await database.get_doctor(doc_id) is None

        # 7. Удаляем администратора
        await database.remove_admin(999999)
        assert await database.is_admin(999999) is False

    async def test_multiple_slots_management(self):
        """Управление несколькими слотами"""
        # Добавляем несколько слотов
        slot_ids = []
        times = ["09:00", "10:00", "11:00", "12:00", "14:00"]
        for time in times:
            sid = await database.add_time_slot(self.doc_id, "26.12.2024", time)
            slot_ids.append(sid)

        # Все слоты доступны
        slots = await database.get_slots_by_doctor(self.doc_id, available_only=True)
        available_on_26 = [s for s in slots if s[1] == "26.12.2024"]
        assert len(available_on_26) == 5

        # Бронируем несколько
        await database.book_slot(slot_ids[0])
        await database.book_slot(slot_ids[1])

        slots = await database.get_slots_by_doctor(self.doc_id, available_only=True)
        available_on_26 = [s for s in slots if s[1] == "26.12.2024"]
        assert len(available_on_26) == 3

        # Удаляем один
        await database.delete_time_slot(slot_ids[2])
        slots = await database.get_slots_by_doctor(self.doc_id)
        all_on_26 = [s for s in slots if s[1] == "26.12.2024"]
        assert len(all_on_26) == 4

    async def test_appointment_status_flow(self):
        """Жизненный цикл статусов записи"""
        apt_id = await database.create_appointment(
            111111, "user", "Петров П.П.", "+7 999",
            self.doc_id, self.srv_id, self.slot_id
        )

        # pending → confirmed
        await database.update_appointment_status(apt_id, "confirmed")
        apts = await database.get_user_appointments(111111)
        assert apts[0][5] == "confirmed"

        # confirmed → completed
        await database.update_appointment_status(apt_id, "completed")
        apts = await database.get_user_appointments(111111)
        assert apts[0][5] == "completed"

    async def test_concurrent_slot_booking(self):
        """Конкурентное бронирование одного слота"""
        import asyncio

        results = []

        async def try_book():
            slot = await database.get_slot(self.slot_id)
            if slot and slot[4]:
                await database.book_slot(self.slot_id)
                results.append(True)
            else:
                results.append(False)

        # Запускаем параллельно (в реальности SQLite сериализует)
        await asyncio.gather(try_book(), try_book())

        # Слот должен быть занят
        slot = await database.get_slot(self.slot_id)
        assert slot[4] == 0

    async def test_doctor_with_multiple_services_and_slots(self):
        """Врач с несколькими услугами и слотами"""
        # Добавляем ещё услуги
        srv2 = await database.add_service("Удаление зуба", "", 45, 2000.0)
        srv3 = await database.add_service("Протезирование", "", 120, 15000.0)

        # Добавляем слоты на разные даты
        await database.add_time_slot(self.doc_id, "27.12.2024", "09:00")
        await database.add_time_slot(self.doc_id, "27.12.2024", "10:00")
        await database.add_time_slot(self.doc_id, "28.12.2024", "14:00")

        # Создаём записи на разные услуги
        slot2 = await database.add_time_slot(self.doc_id, "29.12.2024", "09:00")
        slot3 = await database.add_time_slot(self.doc_id, "29.12.2024", "10:00")

        apt1 = await database.create_appointment(
            111111, "user1", "Петров П.П.", "+7 999",
            self.doc_id, self.srv_id, self.slot_id
        )
        apt2 = await database.create_appointment(
            222222, "user2", "Сидоров С.С.", "+7 888",
            self.doc_id, srv2, slot2
        )

        # Проверяем что у каждого пользователя своя запись
        apts1 = await database.get_user_appointments(111111)
        apts2 = await database.get_user_appointments(222222)

        assert len(apts1) == 1
        assert len(apts2) == 1
        assert apts1[0][2] == "Лечение кариеса"
        assert apts2[0][2] == "Удаление зуба"

        # Все записи видны администратору
        all_apts = await database.get_all_appointments()
        assert len(all_apts) == 2


class TestEdgeCases:
    """Граничные случаи"""

    @pytest.fixture(autouse=True)
    async def setup(self, initialized_db):
        pass

    async def test_empty_database_queries(self):
        """Запросы к пустой БД не вызывают ошибок"""
        assert await database.get_all_doctors() == []
        assert await database.get_all_services() == []
        assert await database.get_all_admins() == []
        assert await database.get_all_appointments() == []
        assert await database.get_doctor(1) is None
        assert await database.get_service(1) is None
        assert await database.get_slot(1) is None

    async def test_large_number_of_slots(self):
        """Большое количество слотов"""
        doc_id = await database.add_doctor("Врач", "Терапевт")
        for hour in range(9, 19):
            for minute in ["00", "30"]:
                await database.add_time_slot(doc_id, "25.12.2024", f"{hour:02d}:{minute}")

        slots = await database.get_slots_by_doctor(doc_id)
        assert len(slots) == 20

    async def test_special_characters_in_names(self):
        """Специальные символы в именах"""
        doc_id = await database.add_doctor(
            "О'Брайен Джон-Пол", "Терапевт", "Описание с <тегами> & символами"
        )
        doctor = await database.get_doctor(doc_id)
        assert doctor[1] == "О'Брайен Джон-Пол"
        assert "<тегами>" in doctor[3]

    async def test_unicode_in_service_names(self):
        """Unicode в названиях услуг"""
        srv_id = await database.add_service(
            "Лечение 🦷", "Описание с эмодзи 😊", 60, 1000.0
        )
        service = await database.get_service(srv_id)
        assert "🦷" in service[1]
        assert "😊" in service[2]

    async def test_zero_price_service(self):
        """Услуга с нулевой ценой (бесплатная консультация)"""
        srv_id = await database.add_service("Консультация", "", 15, 0.0)
        service = await database.get_service(srv_id)
        assert float(service[4]) == 0.0

    async def test_appointment_for_nonexistent_slot(self):
        """Запись на несуществующий слот"""
        doc_id = await database.add_doctor("Врач", "Терапевт")
        srv_id = await database.add_service("Услуга", "", 30, 1000.0)

        # SQLite не проверяет FK по умолчанию, но запись создастся
        apt_id = await database.create_appointment(
            111111, "user", "Петров П.П.", "+7 999",
            doc_id, srv_id, 99999  # Несуществующий слот
        )
        # Тест проверяет поведение системы
        assert apt_id is not None