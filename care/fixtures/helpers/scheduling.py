from django.urls import reverse


class SchedulingFixturesMixin:
    """Schedules, slots, appointments, and token queues."""

    def create_schedule(self, facility_id, resource_type, resource_id, **kwargs):
        url = reverse("schedule-list", kwargs={"facility_external_id": facility_id})
        data = {
            "facility": facility_id,
            "name": "Default Schedule",
            "resource_type": resource_type,
            "resource_id": resource_id,
            "is_public": True,
            "availabilities": [],
            **kwargs,
        }
        return self.post(url, data)

    def get_slots_for_day(self, facility_id, resource_type, resource_id, day):
        url = reverse(
            "slot-get-slots-for-day",
            kwargs={"facility_external_id": facility_id},
        )
        data = {
            "resource_type": resource_type,
            "resource_id": resource_id,
            "day": day,
        }
        return self.post(url, data)

    def create_appointment(self, facility_id, slot_id, patient_id, note=""):
        url = reverse(
            "slot-create-appointment",
            kwargs={
                "facility_external_id": facility_id,
                "external_id": slot_id,
            },
        )
        return self.post(url, {"patient": patient_id, "note": note})

    def create_token_queue(self, facility_id, resource_type, resource_id, **kwargs):
        url = reverse("token-queue-list", kwargs={"facility_external_id": facility_id})
        data = {
            "name": "Default Queue",
            "resource_type": resource_type,
            "resource_id": resource_id,
            **kwargs,
        }
        return self.post(url, data)

    def create_token_sub_queue(self, facility_id, resource_type, resource_id, **kwargs):
        url = reverse(
            "token-sub-queue-list", kwargs={"facility_external_id": facility_id}
        )
        data = {
            "name": "Default Service Point",
            "status": "active",
            "resource_type": resource_type,
            "resource_id": resource_id,
            **kwargs,
        }
        return self.post(url, data)

    def create_token_category(self, facility_id, resource_type, **kwargs):
        url = reverse(
            "token-category-list", kwargs={"facility_external_id": facility_id}
        )
        data = {
            "name": f"{resource_type.capitalize()} Token Category",
            "resource_type": resource_type,
            "shorthand": resource_type[:5].upper(),
            **kwargs,
        }
        return self.post(url, data)
