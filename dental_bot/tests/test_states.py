import pytest
from aiogram.fsm.state import State, StatesGroup

from states.client_states import AppointmentStates
from states.admin_states import (
    AdminAuthStates, AdminDoctorStates,
    AdminServiceStates, AdminSlotStates
)


class TestClientStates:

    def test_appointment_states_exist(self):
        """Все состояния записи существуют"""
        assert hasattr(AppointmentStates, "choosing_doctor")
        assert hasattr(AppointmentStates, "choosing_service")
        assert hasattr(AppointmentStates, "choosing_slot")
        assert hasattr(AppointmentStates, "entering_name")
        assert hasattr(AppointmentStates, "entering_phone")
        assert hasattr(AppointmentStates, "confirming")

    def test_appointment_states_are_states(self):
        """Состояния являются экземплярами State"""
        assert isinstance(AppointmentStates.choosing_doctor, State)
        assert isinstance(AppointmentStates.choosing_service, State)
        assert isinstance(AppointmentStates.choosing_slot, State)
        assert isinstance(AppointmentStates.entering_name, State)
        assert isinstance(AppointmentStates.entering_phone, State)
        assert isinstance(AppointmentStates.confirming, State)

    def test_appointment_states_are_unique(self):
        """Все состояния уникальны"""
        states = [
            AppointmentStates.choosing_doctor,
            AppointmentStates.choosing_service,
            AppointmentStates.choosing_slot,
            AppointmentStates.entering_name,
            AppointmentStates.entering_phone,
            AppointmentStates.confirming,
        ]
        state_names = [str(s) for s in states]
        assert len(state_names) == len(set(state_names))


class TestAdminStates:

    def test_auth_states_exist(self):
        """Состояния авторизации существуют"""
        assert hasattr(AdminAuthStates, "waiting_password")
        assert isinstance(AdminAuthStates.waiting_password, State)

    def test_doctor_states_exist(self):
        """Состояния управления врачами существуют"""
        expected = [
            "waiting_name", "waiting_specialization", "waiting_description",
            "editing_name", "editing_specialization", "editing_description"
        ]
        for state_name in expected:
            assert hasattr(AdminDoctorStates, state_name), f"Missing state: {state_name}"

    def test_service_states_exist(self):
        """Состояния управления услугами существуют"""
        expected = [
            "waiting_name", "waiting_description", "waiting_duration", "waiting_price",
            "editing_name", "editing_description", "editing_duration", "editing_price"
        ]
        for state_name in expected:
            assert hasattr(AdminServiceStates, state_name), f"Missing state: {state_name}"

    def test_slot_states_exist(self):
        """Состояния управления слотами существуют"""
        expected = ["choosing_doctor", "waiting_date", "waiting_times", "managing_slots"]
        for state_name in expected:
            assert hasattr(AdminSlotStates, state_name), f"Missing state: {state_name}"

    def test_all_states_are_state_instances(self):
        """Все состояния являются экземплярами State"""
        all_states = [
            AdminAuthStates.waiting_password,
            AdminDoctorStates.waiting_name,
            AdminDoctorStates.waiting_specialization,
            AdminServiceStates.waiting_name,
            AdminServiceStates.waiting_price,
            AdminSlotStates.waiting_date,
            AdminSlotStates.waiting_times,
        ]
        for state in all_states:
            assert isinstance(state, State)