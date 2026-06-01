from aiogram.fsm.state import State, StatesGroup


class AdminAuthStates(StatesGroup):
    waiting_password = State()


class AdminDoctorStates(StatesGroup):
    waiting_name = State()
    waiting_specialization = State()
    waiting_description = State()
    editing_choice = State()
    editing_name = State()
    editing_specialization = State()
    editing_description = State()


class AdminServiceStates(StatesGroup):
    waiting_name = State()
    waiting_description = State()
    waiting_duration = State()
    waiting_price = State()
    editing_choice = State()
    editing_name = State()
    editing_description = State()
    editing_duration = State()
    editing_price = State()


class AdminSlotStates(StatesGroup):
    choosing_doctor = State()
    waiting_date = State()
    waiting_times = State()
    managing_slots = State()