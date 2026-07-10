from datetime import timedelta

from django.utils import timezone

from care.fixtures.constants import DEFAULT_AVAILABILITY


def load_scheduling(base, facility_id, created_users, patients, departments, roles):
    """Create schedules, token slots, queues, and sample appointments."""
    now = timezone.now()
    valid_from = (now + timedelta(days=1)).strftime("%Y-%m-%dT00:00:00")
    valid_to = (now + timedelta(days=8)).strftime("%Y-%m-%dT23:59:59")

    doctor = created_users.get("Doctor")
    if not doctor:
        return

    admin_org = departments.get("Administration")
    doctor_role = roles.get("Doctor")
    if admin_org and doctor_role:
        base.add_user_to_facility_organization(
            facility_id, admin_org.id, doctor.id, doctor_role.id
        )

    base.create_schedule(
        facility_id,
        resource_type="practitioner",
        resource_id=doctor.id,
        name="Doctor Consultation Schedule",
        valid_from=valid_from,
        valid_to=valid_to,
        availabilities=[DEFAULT_AVAILABILITY],
    )

    tomorrow = (now + timedelta(days=1)).strftime("%Y-%m-%d")
    base.create_token_queue(
        facility_id,
        resource_type="practitioner",
        resource_id=doctor.id,
        date=tomorrow,
    )
    base.create_token_sub_queue(
        facility_id,
        resource_type="practitioner",
        resource_id=doctor.id,
        name="Consultation Room 1",
    )
    base.create_token_category(
        facility_id,
        resource_type="practitioner",
        name="General Consultation",
        shorthand="GEN",
    )

    slots_response = base.get_slots_for_day(
        facility_id,
        resource_type="practitioner",
        resource_id=doctor.id,
        day=tomorrow,
    )
    slots = slots_response.get("results", [])
    if slots:
        booked_patients = patients[: min(3, len(patients), len(slots))]
        for idx, patient in enumerate(booked_patients):
            base.create_appointment(
                facility_id,
                slot_id=slots[idx].id,
                patient_id=patient.id,
                note=f"Auto-booked fixture appointment {idx + 1}",
            )
