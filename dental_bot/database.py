import aiosqlite
from datetime import datetime
from typing import Optional

DB_PATH = "dental.db"


async def init_db():
    """Инициализация базы данных"""
    async with aiosqlite.connect(DB_PATH) as db:
        # Таблица администраторов
        await db.execute("""
            CREATE TABLE IF NOT EXISTS admins (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER UNIQUE NOT NULL,
                username TEXT,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Таблица врачей
        await db.execute("""
            CREATE TABLE IF NOT EXISTS doctors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                specialization TEXT NOT NULL,
                description TEXT,
                is_active BOOLEAN DEFAULT 1
            )
        """)

        # Таблица услуг
        await db.execute("""
            CREATE TABLE IF NOT EXISTS services (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                duration INTEGER NOT NULL,
                price DECIMAL(10,2) NOT NULL,
                is_active BOOLEAN DEFAULT 1
            )
        """)

        # Таблица временных слотов
        await db.execute("""
            CREATE TABLE IF NOT EXISTS time_slots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                doctor_id INTEGER NOT NULL,
                slot_date TEXT NOT NULL,
                slot_time TEXT NOT NULL,
                is_available BOOLEAN DEFAULT 1,
                FOREIGN KEY (doctor_id) REFERENCES doctors(id)
            )
        """)

        # Таблица записей
        await db.execute("""
            CREATE TABLE IF NOT EXISTS appointments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                username TEXT,
                full_name TEXT NOT NULL,
                phone TEXT NOT NULL,
                doctor_id INTEGER NOT NULL,
                service_id INTEGER NOT NULL,
                slot_id INTEGER NOT NULL,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (doctor_id) REFERENCES doctors(id),
                FOREIGN KEY (service_id) REFERENCES services(id),
                FOREIGN KEY (slot_id) REFERENCES time_slots(id)
            )
        """)

        await db.commit()


# ADMINS 

async def is_admin(user_id: int) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT id FROM admins WHERE user_id = ?", (user_id,)
        ) as cursor:
            return await cursor.fetchone() is not None


async def add_admin(user_id: int, username: Optional[str] = None):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR IGNORE INTO admins (user_id, username) VALUES (?, ?)",
            (user_id, username)
        )
        await db.commit()


async def get_all_admins():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT user_id, username, added_at FROM admins"
        ) as cursor:
            return await cursor.fetchall()


async def remove_admin(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM admins WHERE user_id = ?", (user_id,))
        await db.commit()


# DOCTORS 

async def add_doctor(name: str, specialization: str, description: str = ""):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "INSERT INTO doctors (name, specialization, description) VALUES (?, ?, ?)",
            (name, specialization, description)
        )
        await db.commit()
        return cursor.lastrowid


async def get_all_doctors(active_only: bool = False):
    async with aiosqlite.connect(DB_PATH) as db:
        query = "SELECT id, name, specialization, description, is_active FROM doctors"
        if active_only:
            query += " WHERE is_active = 1"
        async with db.execute(query) as cursor:
            return await cursor.fetchall()


async def get_doctor(doctor_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT id, name, specialization, description, is_active FROM doctors WHERE id = ?",
            (doctor_id,)
        ) as cursor:
            return await cursor.fetchone()


async def update_doctor(doctor_id: int, name: str, specialization: str, description: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE doctors SET name=?, specialization=?, description=? WHERE id=?",
            (name, specialization, description, doctor_id)
        )
        await db.commit()


async def toggle_doctor(doctor_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE doctors SET is_active = NOT is_active WHERE id = ?",
            (doctor_id,)
        )
        await db.commit()


async def delete_doctor(doctor_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM doctors WHERE id = ?", (doctor_id,))
        await db.commit()


# SERVICES

async def add_service(name: str, description: str, duration: int, price: float):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "INSERT INTO services (name, description, duration, price) VALUES (?, ?, ?, ?)",
            (name, description, duration, price)
        )
        await db.commit()
        return cursor.lastrowid


async def get_all_services(active_only: bool = False):
    async with aiosqlite.connect(DB_PATH) as db:
        query = "SELECT id, name, description, duration, price, is_active FROM services"
        if active_only:
            query += " WHERE is_active = 1"
        async with db.execute(query) as cursor:
            return await cursor.fetchall()


async def get_service(service_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT id, name, description, duration, price, is_active FROM services WHERE id = ?",
            (service_id,)
        ) as cursor:
            return await cursor.fetchone()


async def update_service(service_id: int, name: str, description: str, duration: int, price: float):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE services SET name=?, description=?, duration=?, price=? WHERE id=?",
            (name, description, duration, price, service_id)
        )
        await db.commit()


async def toggle_service(service_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE services SET is_active = NOT is_active WHERE id = ?",
            (service_id,)
        )
        await db.commit()


async def delete_service(service_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM services WHERE id = ?", (service_id,))
        await db.commit()


# TIME SLOTS

async def add_time_slot(doctor_id: int, slot_date: str, slot_time: str):
    async with aiosqlite.connect(DB_PATH) as db:
        # Проверка на дубликат
        async with db.execute(
            "SELECT id FROM time_slots WHERE doctor_id=? AND slot_date=? AND slot_time=?",
            (doctor_id, slot_date, slot_time)
        ) as cursor:
            if await cursor.fetchone():
                return None
        cursor = await db.execute(
            "INSERT INTO time_slots (doctor_id, slot_date, slot_time) VALUES (?, ?, ?)",
            (doctor_id, slot_date, slot_time)
        )
        await db.commit()
        return cursor.lastrowid


async def get_slots_by_doctor(doctor_id: int, available_only: bool = False):
    async with aiosqlite.connect(DB_PATH) as db:
        query = """
            SELECT ts.id, ts.slot_date, ts.slot_time, ts.is_available
            FROM time_slots ts
            WHERE ts.doctor_id = ?
        """
        if available_only:
            query += " AND ts.is_available = 1"
        query += " ORDER BY ts.slot_date, ts.slot_time"
        async with db.execute(query, (doctor_id,)) as cursor:
            return await cursor.fetchall()


async def get_slot(slot_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT id, doctor_id, slot_date, slot_time, is_available FROM time_slots WHERE id = ?",
            (slot_id,)
        ) as cursor:
            return await cursor.fetchone()


async def delete_time_slot(slot_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM time_slots WHERE id = ?", (slot_id,))
        await db.commit()


async def toggle_slot(slot_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE time_slots SET is_available = NOT is_available WHERE id = ?",
            (slot_id,)
        )
        await db.commit()


async def book_slot(slot_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE time_slots SET is_available = 0 WHERE id = ?",
            (slot_id,)
        )
        await db.commit()


# APPOINTMENTS

async def create_appointment(
    user_id: int, username: str, full_name: str, phone: str,
    doctor_id: int, service_id: int, slot_id: int
):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """INSERT INTO appointments 
               (user_id, username, full_name, phone, doctor_id, service_id, slot_id)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (user_id, username, full_name, phone, doctor_id, service_id, slot_id)
        )
        await db.commit()
        return cursor.lastrowid


async def get_user_appointments(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            """SELECT a.id, d.name, s.name, ts.slot_date, ts.slot_time, 
                      a.status, a.full_name, a.phone
               FROM appointments a
               JOIN doctors d ON a.doctor_id = d.id
               JOIN services s ON a.service_id = s.id
               JOIN time_slots ts ON a.slot_id = ts.id
               WHERE a.user_id = ?
               ORDER BY ts.slot_date, ts.slot_time""",
            (user_id,)
        ) as cursor:
            return await cursor.fetchall()


async def get_all_appointments():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            """SELECT a.id, a.full_name, a.phone, a.username,
                      d.name, s.name, ts.slot_date, ts.slot_time, a.status
               FROM appointments a
               JOIN doctors d ON a.doctor_id = d.id
               JOIN services s ON a.service_id = s.id
               JOIN time_slots ts ON a.slot_id = ts.id
               ORDER BY ts.slot_date, ts.slot_time"""
        ) as cursor:
            return await cursor.fetchall()


async def update_appointment_status(appointment_id: int, status: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE appointments SET status = ? WHERE id = ?",
            (status, appointment_id)
        )
        await db.commit()


async def cancel_appointment(appointment_id: int, user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        # Получаем slot_id
        async with db.execute(
            "SELECT slot_id FROM appointments WHERE id = ? AND user_id = ?",
            (appointment_id, user_id)
        ) as cursor:
            row = await cursor.fetchone()
            if not row:
                return False
            slot_id = row[0]

        # Освобождаем слот
        await db.execute(
            "UPDATE time_slots SET is_available = 1 WHERE id = ?",
            (slot_id,)
        )
        # Обновляем статус записи
        await db.execute(
            "UPDATE appointments SET status = 'cancelled' WHERE id = ?",
            (appointment_id,)
        )
        await db.commit()
        return True
