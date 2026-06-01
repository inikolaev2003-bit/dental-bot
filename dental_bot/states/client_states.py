from aiogram.fsm.state import State, StatesGroup


class AppointmentStates(StatesGroup):
    choosing_doctor = State()
    choosing_service = State()
    choosing_slot = State()
    entering_name = State()
    entering_phone = State()
    confirming = State()